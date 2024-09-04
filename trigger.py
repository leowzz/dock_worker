import requests
from config import settings
from loguru import logger
from pydantic import BaseModel, field_validator
from datetime import datetime


class GitHubActionTrigger:
    github_api_endpoint = "https://api.github.com"
    proxy = (
        {"http": settings.http_proxy, "https": settings.http_proxy}
        if settings.http_proxy
        else None
    )
    github_username = settings.github_username
    github_repo = settings.github_repo

    @property
    def headers(self):
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {settings.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    class Workflow(BaseModel):
        id: int
        node_id: str
        name: str
        path: str
        state: str
        created_at: datetime
        updated_at: datetime
        url: str
        html_url: str
        badge_url: str

    class WorkflowsResponse(BaseModel):
        total_count: int
        workflows: list["GitHubActionTrigger.Workflow"]

    class WorkflowDetails(BaseModel):
        id: int
        node_id: str
        name: str
        path: str
        state: str
        created_at: datetime
        updated_at: datetime
        url: str
        html_url: str
        badge_url: str

    class WorkflowTriggerArgs(BaseModel):
        origin_image: str
        self_repo_image: str = None  # 私有仓库镜像, aliyun.com/your_space/{self_repo_image}

        @field_validator('self_repo_image', mode='before')
        @classmethod
        def set_default_self_repo_image(cls, v, values):
            logger.debug(f"{v=}, {values=}")
            if v is None:
                return values.data.get('origin_image')
            return v

    def get_workflows(self):
        response = requests.get(
            url=f"{self.github_api_endpoint}/repos/{self.github_username}/{self.github_repo}/actions/workflows",
            headers=self.headers,
            proxies=self.proxy,
        )
        resp_json = response.json()
        logger.debug(f"get workers: {resp_json}")
        res = self.WorkflowsResponse.model_validate(resp_json)
        return res

    def get_workflow_info(self, workflow_id):
        response = requests.get(
            url=f"{self.github_api_endpoint}/repos/{self.github_username}/{self.github_repo}/"
                f"actions/workflows/{workflow_id}",
            headers=self.headers,
            proxies=self.proxy,
        )
        resp_json = response.json()
        res = self.WorkflowDetails.model_validate(resp_json)
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
            url=f"{self.github_api_endpoint}/repos/{self.github_username}/{self.github_repo}/"
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
            url=f"{self.github_api_endpoint}/repos/{self.github_username}/{self.github_repo}/actions/runs/{run_id}",
            headers=self.headers,
            proxies=self.proxy,
        )
        resp_json = response.json()
        return resp_json

    def create_workflow_dispatch_event(
            self,
            workflow: Workflow | WorkflowDetails,
            ref="main",
            trigger_args: WorkflowTriggerArgs = None,
    ):
        if not trigger_args:
            logger.error("trigger_args is required")
            return
        response = requests.post(
            url=f"{self.github_api_endpoint}/repos/{self.github_username}/{self.github_repo}/"
                f"actions/workflows/{workflow.id}/dispatches",
            headers=self.headers,
            proxies=self.proxy,
            json={
                "ref": ref,
                "inputs": trigger_args.model_dump(),
            },
        )
        logger.debug(f"{response.text=}")
        if response.status_code == 204:
            logger.success(f"Workflow {workflow.name} triggered successfully")
            return True
        return False

    def fork_image(self, trigger_args: WorkflowTriggerArgs):
        """
        Forks a Docker image from the origin to the self repository.
        :return: True if the workflow was triggered successfully, False otherwise.
        """
        logger.debug(f"{trigger_args=}")
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

        if not self.create_workflow_dispatch_event(
                workflow=selected_workflow,
                trigger_args=trigger_args
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
                            if run_info['run_number'] > last_run_number:
                                running_job_id = run_info['id']
                                logger.info(f"Current run number: {run_info['run_number']}, {running_job_id=}")
                                continue
                else:
                    current_run = self.get_workflow_run_info(running_job_id)
                    if current_run['status'] == 'completed':
                        if current_run['conclusion'] == 'success':
                            progress.update(task, description="[green]Workflow completed successfully", total=100,
                                            completed=100)
                            logger.success("Workflow completed successfully")
                            return True
                        else:
                            progress.update(task, description="[red]Workflow did not complete successfully",
                                            total=100, completed=100)
                            logger.error("Workflow did not complete successfully")
                            return False
                    else:
                        progress.update(task, description=f"[yellow]Current status: {current_run['status']}")


if __name__ == "__main__":
    action_trigger = GitHubActionTrigger()

    action_trigger.fork_image(GitHubActionTrigger.WorkflowTriggerArgs(
        origin_image="ubuntu:20.04", self_repo_image=None
    ))

    # workflows = action_trigger.get_workflows()
    # selected_workflow = workflows.workflows[0]
    # logger.info(f"{selected_workflow=}")
    # info = action_trigger.get_workflow_runs(selected_workflow.id)
    # logger.info(f"{info=}")
    # action_trigger.create_workflow_dispatch_event(
    #     selected_workflow, trigger_args=action_trigger.WorkflowTriggerArgs(
    #         origin_image="ubuntu:20.04",
    #         self_repo_image="ubuntu:20.04",
    #     )
    # )
    # info = action_trigger.get_workflow_run_info()
    # logger.info(f"{info=}")
