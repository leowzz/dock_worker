import time
from typing import Any

import requests
from loguru import logger

from dock_worker.core import config
from dock_worker.schemas import ImageArgs, Workflow, WorkflowsResponse, WorkflowDetails, JobStatusEnum, \
    status_2_progress_number
from dock_worker.utils import execute_command


def update_job_info(current_run, image_args, running_job_id):
    from dock_worker.core.db import Jobs, get_db
    from dock_worker.schemas import JobInDB
    with get_db() as session:
        job_db = session.query(Jobs).filter(Jobs.distinct_id == image_args.distinct_id).first()
        if not job_db:
            logger.error(f"Job {image_args.distinct_id} not found")
            return False
        logger.info(f'{current_run["status"]=}, {job_db.id=}')
        job_db.status = current_run["status"]
        job_db.run_id = running_job_id
        job_db.run_number = current_run["run_number"]
        res_job_info = JobInDB.model_validate(job_db)
        session.commit()
        return res_job_info


class GitHubActionManager:
    api_endpoint = "https://api.github.com"
    proxy = (
        {"http": config.http_proxy, "https": config.http_proxy}
        if config.http_proxy
        else None
    )
    github_username = config.github_username
    github_repo = config.github_repo
    name_space = config.name_space
    image_repositories_endpoint = config.image_repositories_endpoint

    @property
    def headers(self):
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {config.github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def __init__(self):
        self.workflows = self.get_workflows()
        self.workflow_name = config.default_workflow_name
        self.workflow: Workflow = next(
            (wf for wf in self.workflows.workflows if wf.name == self.workflow_name),
            None,
        )

    def get_workflows(self) -> WorkflowsResponse:
        response = requests.get(
            url=f"{self.api_endpoint}/repos/{self.github_username}/{self.github_repo}/actions/workflows",
            headers=self.headers,
            proxies=self.proxy,
        )
        resp_json = response.json()
        logger.debug(f"get workers: {resp_json}")
        res = WorkflowsResponse.model_validate(resp_json)
        return res

    def get_workflow_info(self, workflow_id):
        response = requests.get(
            url=f"{self.api_endpoint}/repos/{self.github_username}/{self.github_repo}/"
                f"actions/workflows/{workflow_id}",
            headers=self.headers,
            proxies=self.proxy,
        )
        resp_json = response.json()
        res = WorkflowDetails.model_validate(resp_json)
        return res

    def get_workflow_runs(
            self, workflow_id, status=None, per_page=3, page=1, event="workflow_dispatch"
    ):
        query_params = {
            "event": event,
            "workflow_id": workflow_id,
            "per_page": per_page,
            "page": page,
        }
        if status:
            query_params.update({"status": status})

        response = requests.get(
            url=f"{self.api_endpoint}/repos/{self.github_username}/{self.github_repo}/"
                f"actions/workflows/{workflow_id}/runs",
            headers=self.headers,
            proxies=self.proxy,
            params=query_params,
        )
        resp_json = response.json()
        return resp_json

    def get_workflow_run_info(self, run_id=10679854711):
        """
        ok = resp_json.get('status') == 'completed'
        :param run_id:
        :return:
        """
        response = requests.get(
            url=f"{self.api_endpoint}/repos/{self.github_username}/{self.github_repo}/actions/runs/{run_id}",
            headers=self.headers,
            proxies=self.proxy,
        )
        resp_json = response.json()
        return resp_json

    def create_workflow_dispatch_event(
            self,
            workflow: Workflow | WorkflowDetails,
            ref="main",
            image_args: ImageArgs = None,
    ):
        if not image_args:
            logger.error("image_args is required")
            return
        response = requests.post(
            url=f"{self.api_endpoint}/repos/{self.github_username}/{self.github_repo}/"
                f"actions/workflows/{workflow.id}/dispatches",
            headers=self.headers,
            proxies=self.proxy,
            json={
                "ref": ref,
                "inputs": image_args.model_dump(),
            },
        )
        logger.debug(f"{response.text=}")
        if response.status_code == 204:
            logger.success(
                f"Workflow {workflow.name} triggered successfully. distinct_id: {image_args.distinct_id}"
            )
            return True
        return False

    def make_image_full_name(self, image_name: str) -> str:
        return f"{self.image_repositories_endpoint}/{self.name_space}/{image_name}"

    def pull_image(self, image_name: str) -> bool:
        pull_cmd = f"docker pull {self.make_image_full_name(image_name)}"
        return execute_command(pull_cmd)

    def tag_image(self, source_image: str, target_image: str) -> bool:
        tag_cmd = f"docker tag {self.make_image_full_name(source_image)} {target_image}"
        return execute_command(tag_cmd)

    def fork_and_pull(self, image_args: ImageArgs, test_mode=False) -> bool:
        if not self.fork_image(image_args=image_args, test_mode=test_mode):
            return False
        if not self.pull_image(image_args.target):
            return False
        if not self.tag_image(image_args.source, image_args.target):
            return False
        return True

    def fork_image(self, image_args: ImageArgs, test_mode=False):
        """
        Forks a Docker image from the origin to the self repository.
        :return: True if the workflow was triggered successfully, False otherwise.
        """
        logger.debug(f"{image_args=}")

        if not self.workflow:
            logger.error(f"Workflow `{self.workflow_name}` not found.")
            return False

        if not test_mode:
            if not self.create_workflow_dispatch_event(
                    workflow=self.workflow, image_args=image_args
            ):
                return False

        from dock_worker.schemas import JobNew

        return JobNew(
            source=image_args.source,
            target=image_args.target,
            distinct_id=image_args.distinct_id,
            repo_url=config.image_repositories_endpoint,
            repo_namespace=self.name_space,
            workflow_id=self.workflow.id,
            workflow_name=self.workflow.name,
            full_url=self.make_image_full_name(image_args.target),
        )

    def wait_for_workflow_complete(self, image_args: ImageArgs, test_mode=False, using_db: bool = False):
        # 每隔2s发一次请求, 查看状态是否是 completed
        from rich.progress import Progress

        with Progress() as progress:
            running_job_id, updated = self.get_run_id_by_distinct_id(image_args, test_mode, using_db)
            if not running_job_id:
                logger.error("Workflow run not found")
                return False
            if running_job_id == -1:
                logger.error("Timeout waiting for workflow run")
                return False
            task_id = progress.add_task(f"Waiting for workflow run {running_job_id} to complete", total=100)
            progress.update(task_id, completed=20)
            while True:
                current_run = self.get_workflow_run_info(run_id=running_job_id)
                status = current_run['status']
                if status not in JobStatusEnum.__members__.values():
                    logger.warning(f"Unknown status: {status}")
                else:
                    progress.update(task_id, completed=status_2_progress_number[status])

                if status == JobStatusEnum.completed:
                    if current_run["conclusion"] == "success":
                        break
                    else:
                        logger.warning(f"Workflow {status}, but conclusion is not success")
                        return False
                time.sleep(1)
        logger.success(
            f"Workflow completed successfully!\n"
            f"You can pull it with: \ndocker pull {self.make_image_full_name(image_args.target)}"
        )
        return True

    def get_run_id_by_distinct_id(self, image_args, test_mode, using_db) -> tuple[int, bool | Any]:
        start_time = time.time()
        while True:
            if time.time() - start_time > 10:
                logger.error("Timeout waiting for workflow run")
                return -1, False

            workflow_runs = self.get_workflow_runs(self.workflow.id)
            if not workflow_runs:
                logger.error("Workflow runs not found")
                continue
            for run_info in workflow_runs["workflow_runs"]:
                if test_mode:
                    running_job_id = run_info["id"]
                    logger.info(
                        f"Current run number: {run_info['run_number']}, {running_job_id=}"
                    )
                    return running_job_id, True
                if f"[{image_args.distinct_id}]" in run_info["name"]:
                    running_job_id = run_info["id"]
                    logger.info(
                        f"Current run number: {run_info['run_number']}, {running_job_id=}, \n{run_info['name']=}"
                    )
                    if image_args.distinct_id and using_db:
                        if updated := update_job_info(run_info, image_args, running_job_id):
                            return running_job_id, updated
                    return running_job_id, True
            time.sleep(1)


action_trigger = GitHubActionManager()
if __name__ == "__main__":
    action_trigger.fork_image(ImageArgs(source="ubuntu:20.04", target=None))

    # workflows = action_trigger.get_workflows()
    # selected_workflow = workflows.workflows[0]
    # logger.info(f"{selected_workflow=}")
    # info = action_trigger.get_workflow_runs(selected_workflow.id)
    # logger.info(f"{info=}")
    # action_trigger.create_workflow_dispatch_event(
    #     selected_workflow, image_args=action_trigger.ImageArgs(
    #         source="ubuntu:20.04",
    #         target="ubuntu:20.04",
    #     )
    # )
    # info = action_trigger.get_workflow_run_info()
    # logger.info(f"{info=}")
