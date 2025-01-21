import requests
from loguru import logger

from config import settings
from schemas import ImageArgs, Workflow, WorkflowsResponse, WorkflowDetails
from utils import execute_command


class GitHubActionManager:
    api_endpoint = "https://api.github.com"
    proxy = (
        {"http": settings.http_proxy, "https": settings.http_proxy}
        if settings.http_proxy
        else None
    )
    github_username = settings.github_username
    github_repo = settings.github_repo
    name_space = settings.name_space
    image_repositories_endpoint = settings.image_repositories_endpoint

    @property
    def headers(self):
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {settings.github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_workflows(self):
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

    def get_workflow_runs(self, workflow_id, status=None, per_page=3, page=1, event='workflow_dispatch'):
        query_params = {
            "event": event,
            "workflow_id": workflow_id,
            "per_page": per_page,
            "page": page
        }
        if status:
            query_params.update({"status": status})

        response = requests.get(
            url=f"{self.api_endpoint}/repos/{self.github_username}/{self.github_repo}/"
                f"actions/workflows/{workflow_id}/runs",
            headers=self.headers,
            proxies=self.proxy,
            params=query_params
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
            logger.success(f"Workflow {workflow.name} triggered successfully. distinct_id: {image_args.distinct_id}")
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
        workflows = self.get_workflows()
        workflow_name = settings.default_workflow_name
        selected_workflow = next(
            (wf for wf in workflows.workflows if wf.name == workflow_name), None
        )
        if not selected_workflow:
            logger.error(f"Workflow `{workflow_name}` not found.")
            return False

        # 记录最后的 run_number
        last_run_number = None
        workflow_runs = self.get_workflow_runs(selected_workflow.id)
        if workflow_runs and workflow_runs['workflow_runs']:
            last_run_number = workflow_runs['workflow_runs'][0]['run_number']
            logger.info(f"Last run number: {last_run_number}")

        if not test_mode:
            if not self.create_workflow_dispatch_event(
                    workflow=selected_workflow,
                    image_args=image_args
            ):
                return False

        # 每隔2s发一次请求, 查看状态是否是 completed
        import time
        from rich.progress import Progress

        with Progress() as progress:
            task = progress.add_task("[cyan]Waiting for workflow to complete...", total=None)
            running_job_id = None
            while True:
                time.sleep(1)
                if not running_job_id:
                    workflow_runs = self.get_workflow_runs(selected_workflow.id)
                    if workflow_runs and workflow_runs['workflow_runs']:
                        for run_info in workflow_runs['workflow_runs']:
                            if test_mode:
                                running_job_id = run_info['id']
                                logger.info(f"Current run number: {run_info['run_number']}, {running_job_id=}")
                                break
                            if run_info['run_number'] > last_run_number and f'[{image_args.distinct_id}]' in run_info[
                                'name']:
                                running_job_id = run_info['id']
                                logger.info(
                                    f"Current run number: {run_info['run_number']}, {running_job_id=}, {run_info['name']=}")
                                continue
                else:
                    current_run = self.get_workflow_run_info(running_job_id)
                    if current_run['status'] == 'completed':
                        if current_run['conclusion'] == 'success':
                            progress.update(task, description="[green]Workflow completed successfully", total=100,
                                            completed=100)
                            logger.success(
                                f"Workflow completed successfully!\n"
                                f"You can pull it with: docker pull {self.make_image_full_name(image_args.target)}")
                            return True
                        else:
                            progress.update(task, description="[red]Workflow did not complete successfully",
                                            total=100, completed=100)
                            logger.error("Workflow did not complete successfully")
                            return False
                    else:
                        progress.update(task, description=f"[yellow]Current status: {current_run['status']}")


if __name__ == "__main__":
    action_trigger = GitHubActionManager()

    action_trigger.fork_image(ImageArgs(
        source="ubuntu:20.04", target=None
    ))

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
