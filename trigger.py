import requests
from config import settings
from loguru import logger
from pydantic import BaseModel
from datetime import datetime


class GitHubActionTrigger:
    github_api_endpoint = "https://api.github.com"
    proxy = (
        {"http": settings.http_proxy, "https": settings.http_proxy}
        if settings.http_proxy
        else None
    )

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
        self_repo_image: str  # 私有仓库镜像, aliyun.com/your_space/{self_repo_image}

    def get_workflows(self, owner, repo):
        response = requests.get(
            url=f"{self.github_api_endpoint}/repos/{owner}/{repo}/actions/workflows",
            headers=self.headers,
            proxies=self.proxy,
        )
        resp_json = response.json()
        res = self.WorkflowsResponse.model_validate(resp_json)
        return res

    def get_workflow_info(self, owner, repo, workflow_id):
        response = requests.get(
            url=f"{self.github_api_endpoint}/repos/{owner}/{repo}/actions/workflows/{workflow_id}",
            headers=self.headers,
            proxies=self.proxy,
        )
        resp_json = response.json()
        res = self.WorkflowDetails.model_validate(resp_json)
        return res

    def create_workflow_dispatch_event(
            self,
            owner,
            repo,
            workflow: Workflow | WorkflowDetails,
            ref="main",
            trigger_args: WorkflowTriggerArgs = None,
    ):
        if not trigger_args:
            logger.error("trigger_args is required")
            return
        response = requests.post(
            url=f"{self.github_api_endpoint}/repos/{owner}/{repo}/actions/workflows/{workflow.id}/dispatches",
            headers=self.headers,
            proxies=self.proxy,
            json={
                "ref": ref,
                "inputs": trigger_args.model_dump(),
            },
        )
        if response.status_code == 204:
            logger.success(f"Workflow {workflow.name} triggered successfully")


if __name__ == "__main__":
    action_trigger = GitHubActionTrigger()
    workflows = action_trigger.get_workflows("leowzz", "docker_image_pusher")
    selected_workflow = workflows.workflows[0]
    logger.info(f"{selected_workflow=}")
    trigger_args = action_trigger.WorkflowTriggerArgs(
        origin_image="python:3.10.14-slim-bullseye",
        self_repo_image="python_self:3.10.14-slim-bullseye",
    )
    action_trigger.create_workflow_dispatch_event(
        "leowzz", "docker_image_pusher", selected_workflow, trigger_args=trigger_args
    )
