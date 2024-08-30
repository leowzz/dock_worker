import requests
from config import settings
from loguru import logger
from pydantic import BaseModel
from datetime import datetime

github_api_endpoint = "https://api.github.com"
# 代理服务器的 URL
proxy = {"http": settings.http_proxy, "https": settings.http_proxy}


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
    workflows: list[Workflow]


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


def get_workflows(owner, repo):
    response = requests.get(
        url=f"{github_api_endpoint}/repos/{owner}/{repo}/actions/workflows",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {settings.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        proxies=proxy if settings.http_proxy else None,
    )
    resp_json = response.json()
    res = WorkflowsResponse.model_validate(resp_json)
    return res


def get_workflow_info(owner, repo, workflow_id):
    response = requests.get(
        url=f"{github_api_endpoint}/repos/{owner}/{repo}/actions/workflows/{workflow_id}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {settings.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        proxies=proxy if settings.http_proxy else None,
    )
    resp_json = response.json()
    res = WorkflowDetails.model_validate(resp_json)
    return res


# python:3.10.14-slim-bullseye

if __name__ == "__main__":
    workflows = get_workflows("leowzz", "docker_image_pusher")
    logger.info(workflows)
    workflow_id = workflows.workflows[0].id
    workflow_info = get_workflow_info("leowzz", "docker_image_pusher", workflow_id)
    logger.info(workflow_info)

# response = requests.post(url, headers=headers, json=data)
# response = requests.get(url, headers=headers)
# print(response.status_code)
# print(response.text)
# if response.status_code == 204:
#     print("Request was successful.")
# else:
#     print(f"Request failed with status code: {response.status_code}")
