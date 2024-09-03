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
    owner = settings.owner
    repo = settings.repo

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

    def get_workflows(self):
        response = requests.get(
            url=f"{self.github_api_endpoint}/repos/{self.owner}/{self.repo}/actions/workflows",
            headers=self.headers,
            proxies=self.proxy,
        )
        resp_json = response.json()
        logger.debug(f"get workers: {resp_json}")
        res = self.WorkflowsResponse.model_validate(resp_json)
        return res

    def get_workflow_info(self, workflow_id):
        response = requests.get(
            url=f"{self.github_api_endpoint}/repos/{self.owner}/{self.repo}/actions/workflows/{workflow_id}",
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
            url=f"{self.github_api_endpoint}/repos/{self.owner}/{self.repo}/actions/workflows/{workflow_id}/runs",
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
            url=f"{self.github_api_endpoint}/repos/{self.owner}/{self.repo}/actions/runs/{run_id}",
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
            url=f"{self.github_api_endpoint}/repos/{self.owner}/{self.repo}/actions/workflows/{workflow.id}/dispatches",
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


if __name__ == "__main__":
    action_trigger = GitHubActionTrigger()
    workflows = action_trigger.get_workflows()
    selected_workflow = workflows.workflows[0]
    logger.info(f"{selected_workflow=}")
    info = action_trigger.get_workflow_runs(selected_workflow.id)
    logger.info(f"{info=}")
    # # todo: 记录最后的 run_number
    # action_trigger.create_workflow_dispatch_event(
    #     selected_workflow, trigger_args=action_trigger.WorkflowTriggerArgs(
    #         origin_image="ubuntu:20.04",
    #         self_repo_image="ubuntu:20.04",
    #     )
    # )
    # todo: get workflow runs, 如果[0]run_number == 刚记录的 delay 1s, resent req
    # todo: rich 加载条, 每隔2s发一次请求, 查看状态是否是 completed

    # info = action_trigger.get_workflow_run_info()
    # logger.info(f"{info=}")

    info = {'total_count': 32, 'workflow_runs': [
        {'id': 10679854711, 'name': 'Making ubuntu:20.04 by @leowzz to ubuntu:20.04',
         'node_id': 'WFR_kwLOMqT8_s8AAAACfJGmdw', 'head_branch': 'main',
         'head_sha': '1c37ead48050bf74065d72964b24bf5475b2ac43', 'path': '.github/workflows/api_hook.yaml',
         'display_title': 'Making ubuntu:20.04 by @leowzz to ubuntu:20.04', 'run_number': 20,
         'event': 'workflow_dispatch', 'status': 'completed', 'conclusion': 'success', 'workflow_id': 114917830,
         'check_suite_id': 27910468863, 'check_suite_node_id': 'CS_kwDOMqT8_s8AAAAGf5f0_w',
         'url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10679854711',
         'html_url': 'https://github.com/leowzz/docker_image_pusher/actions/runs/10679854711', 'pull_requests': [],
         'created_at': '2024-09-03T09:02:12Z', 'updated_at': '2024-09-03T09:02:49Z',
         'actor': {'login': 'leowzz', 'id': 72735229, 'node_id': 'MDQ6VXNlcjcyNzM1MjI5',
                   'avatar_url': 'https://avatars.githubusercontent.com/u/72735229?v=4', 'gravatar_id': '',
                   'url': 'https://api.github.com/users/leowzz', 'html_url': 'https://github.com/leowzz',
                   'followers_url': 'https://api.github.com/users/leowzz/followers',
                   'following_url': 'https://api.github.com/users/leowzz/following{/other_user}',
                   'gists_url': 'https://api.github.com/users/leowzz/gists{/gist_id}',
                   'starred_url': 'https://api.github.com/users/leowzz/starred{/owner}{/repo}',
                   'subscriptions_url': 'https://api.github.com/users/leowzz/subscriptions',
                   'organizations_url': 'https://api.github.com/users/leowzz/orgs',
                   'repos_url': 'https://api.github.com/users/leowzz/repos',
                   'events_url': 'https://api.github.com/users/leowzz/events{/privacy}',
                   'received_events_url': 'https://api.github.com/users/leowzz/received_events', 'type': 'User',
                   'site_admin': False}, 'run_attempt': 1, 'referenced_workflows': [],
         'run_started_at': '2024-09-03T09:02:12Z',
         'triggering_actor': {'login': 'leowzz', 'id': 72735229, 'node_id': 'MDQ6VXNlcjcyNzM1MjI5',
                              'avatar_url': 'https://avatars.githubusercontent.com/u/72735229?v=4', 'gravatar_id': '',
                              'url': 'https://api.github.com/users/leowzz', 'html_url': 'https://github.com/leowzz',
                              'followers_url': 'https://api.github.com/users/leowzz/followers',
                              'following_url': 'https://api.github.com/users/leowzz/following{/other_user}',
                              'gists_url': 'https://api.github.com/users/leowzz/gists{/gist_id}',
                              'starred_url': 'https://api.github.com/users/leowzz/starred{/owner}{/repo}',
                              'subscriptions_url': 'https://api.github.com/users/leowzz/subscriptions',
                              'organizations_url': 'https://api.github.com/users/leowzz/orgs',
                              'repos_url': 'https://api.github.com/users/leowzz/repos',
                              'events_url': 'https://api.github.com/users/leowzz/events{/privacy}',
                              'received_events_url': 'https://api.github.com/users/leowzz/received_events',
                              'type': 'User', 'site_admin': False},
         'jobs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10679854711/jobs',
         'logs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10679854711/logs',
         'check_suite_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/check-suites/27910468863',
         'artifacts_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10679854711/artifacts',
         'cancel_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10679854711/cancel',
         'rerun_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10679854711/rerun',
         'previous_attempt_url': None,
         'workflow_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/workflows/114917830',
         'head_commit': {'id': '1c37ead48050bf74065d72964b24bf5475b2ac43',
                         'tree_id': '7a4ba3a4110f86f19d15a90654f4c2f82a52af16', 'message': 'add more todo',
                         'timestamp': '2024-08-31T09:01:38Z',
                         'author': {'name': 'WangZhanze', 'email': 'wangzhanze@huoban.ai'},
                         'committer': {'name': 'WangZhanze', 'email': 'wangzhanze@huoban.ai'}},
         'repository': {'id': 849673470, 'node_id': 'R_kgDOMqT8_g', 'name': 'docker_image_pusher',
                        'full_name': 'leowzz/docker_image_pusher', 'private': False,
                        'owner': {'login': 'leowzz', 'id': 72735229, 'node_id': 'MDQ6VXNlcjcyNzM1MjI5',
                                  'avatar_url': 'https://avatars.githubusercontent.com/u/72735229?v=4',
                                  'gravatar_id': '', 'url': 'https://api.github.com/users/leowzz',
                                  'html_url': 'https://github.com/leowzz',
                                  'followers_url': 'https://api.github.com/users/leowzz/followers',
                                  'following_url': 'https://api.github.com/users/leowzz/following{/other_user}',
                                  'gists_url': 'https://api.github.com/users/leowzz/gists{/gist_id}',
                                  'starred_url': 'https://api.github.com/users/leowzz/starred{/owner}{/repo}',
                                  'subscriptions_url': 'https://api.github.com/users/leowzz/subscriptions',
                                  'organizations_url': 'https://api.github.com/users/leowzz/orgs',
                                  'repos_url': 'https://api.github.com/users/leowzz/repos',
                                  'events_url': 'https://api.github.com/users/leowzz/events{/privacy}',
                                  'received_events_url': 'https://api.github.com/users/leowzz/received_events',
                                  'type': 'User', 'site_admin': False},
                        'html_url': 'https://github.com/leowzz/docker_image_pusher',
                        'description': '使用Github Action将国外的Docker镜像转存到阿里云私有仓库，供国内服务器使用，免费易用. 支持api调用, streamlit/cli调用',
                        'fork': True, 'url': 'https://api.github.com/repos/leowzz/docker_image_pusher',
                        'forks_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/forks',
                        'keys_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/keys{/key_id}',
                        'collaborators_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/collaborators{/collaborator}',
                        'teams_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/teams',
                        'hooks_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/hooks',
                        'issue_events_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues/events{/number}',
                        'events_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/events',
                        'assignees_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/assignees{/user}',
                        'branches_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/branches{/branch}',
                        'tags_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/tags',
                        'blobs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/blobs{/sha}',
                        'git_tags_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/tags{/sha}',
                        'git_refs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/refs{/sha}',
                        'trees_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/trees{/sha}',
                        'statuses_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/statuses/{sha}',
                        'languages_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/languages',
                        'stargazers_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/stargazers',
                        'contributors_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/contributors',
                        'subscribers_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/subscribers',
                        'subscription_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/subscription',
                        'commits_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/commits{/sha}',
                        'git_commits_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/commits{/sha}',
                        'comments_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/comments{/number}',
                        'issue_comment_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues/comments{/number}',
                        'contents_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/contents/{+path}',
                        'compare_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/compare/{base}...{head}',
                        'merges_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/merges',
                        'archive_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/{archive_format}{/ref}',
                        'downloads_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/downloads',
                        'issues_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues{/number}',
                        'pulls_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/pulls{/number}',
                        'milestones_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/milestones{/number}',
                        'notifications_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/notifications{?since,all,participating}',
                        'labels_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/labels{/name}',
                        'releases_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/releases{/id}',
                        'deployments_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/deployments'},
         'head_repository': {'id': 849673470, 'node_id': 'R_kgDOMqT8_g', 'name': 'docker_image_pusher',
                             'full_name': 'leowzz/docker_image_pusher', 'private': False,
                             'owner': {'login': 'leowzz', 'id': 72735229, 'node_id': 'MDQ6VXNlcjcyNzM1MjI5',
                                       'avatar_url': 'https://avatars.githubusercontent.com/u/72735229?v=4',
                                       'gravatar_id': '', 'url': 'https://api.github.com/users/leowzz',
                                       'html_url': 'https://github.com/leowzz',
                                       'followers_url': 'https://api.github.com/users/leowzz/followers',
                                       'following_url': 'https://api.github.com/users/leowzz/following{/other_user}',
                                       'gists_url': 'https://api.github.com/users/leowzz/gists{/gist_id}',
                                       'starred_url': 'https://api.github.com/users/leowzz/starred{/owner}{/repo}',
                                       'subscriptions_url': 'https://api.github.com/users/leowzz/subscriptions',
                                       'organizations_url': 'https://api.github.com/users/leowzz/orgs',
                                       'repos_url': 'https://api.github.com/users/leowzz/repos',
                                       'events_url': 'https://api.github.com/users/leowzz/events{/privacy}',
                                       'received_events_url': 'https://api.github.com/users/leowzz/received_events',
                                       'type': 'User', 'site_admin': False},
                             'html_url': 'https://github.com/leowzz/docker_image_pusher',
                             'description': '使用Github Action将国外的Docker镜像转存到阿里云私有仓库，供国内服务器使用，免费易用. 支持api调用, streamlit/cli调用',
                             'fork': True, 'url': 'https://api.github.com/repos/leowzz/docker_image_pusher',
                             'forks_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/forks',
                             'keys_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/keys{/key_id}',
                             'collaborators_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/collaborators{/collaborator}',
                             'teams_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/teams',
                             'hooks_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/hooks',
                             'issue_events_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues/events{/number}',
                             'events_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/events',
                             'assignees_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/assignees{/user}',
                             'branches_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/branches{/branch}',
                             'tags_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/tags',
                             'blobs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/blobs{/sha}',
                             'git_tags_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/tags{/sha}',
                             'git_refs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/refs{/sha}',
                             'trees_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/trees{/sha}',
                             'statuses_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/statuses/{sha}',
                             'languages_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/languages',
                             'stargazers_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/stargazers',
                             'contributors_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/contributors',
                             'subscribers_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/subscribers',
                             'subscription_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/subscription',
                             'commits_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/commits{/sha}',
                             'git_commits_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/commits{/sha}',
                             'comments_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/comments{/number}',
                             'issue_comment_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues/comments{/number}',
                             'contents_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/contents/{+path}',
                             'compare_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/compare/{base}...{head}',
                             'merges_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/merges',
                             'archive_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/{archive_format}{/ref}',
                             'downloads_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/downloads',
                             'issues_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues{/number}',
                             'pulls_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/pulls{/number}',
                             'milestones_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/milestones{/number}',
                             'notifications_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/notifications{?since,all,participating}',
                             'labels_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/labels{/name}',
                             'releases_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/releases{/id}',
                             'deployments_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/deployments'}},
        {'id': 10644003658, 'name': 'Making apache/airflow:2.8.4-python3.10 by @leowzz to airflow:2.8.4-python3.10',
         'node_id': 'WFR_kwLOMqT8_s8AAAACem6bSg', 'head_branch': 'main',
         'head_sha': 'd1528161ac4de6a11caa4a1d4bf040da0cddf2c2', 'path': '.github/workflows/api_hook.yaml',
         'display_title': 'Making apache/airflow:2.8.4-python3.10 by @leowzz to airflow:2.8.4-python3.10',
         'run_number': 19, 'event': 'workflow_dispatch', 'status': 'completed', 'conclusion': 'success',
         'workflow_id': 114917830, 'check_suite_id': 27827440541, 'check_suite_node_id': 'CS_kwDOMqT8_s8AAAAGeqULnQ',
         'url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10644003658',
         'html_url': 'https://github.com/leowzz/docker_image_pusher/actions/runs/10644003658', 'pull_requests': [],
         'created_at': '2024-08-31T08:58:51Z', 'updated_at': '2024-08-31T09:00:30Z',
         'actor': {'login': 'leowzz', 'id': 72735229, 'node_id': 'MDQ6VXNlcjcyNzM1MjI5',
                   'avatar_url': 'https://avatars.githubusercontent.com/u/72735229?v=4', 'gravatar_id': '',
                   'url': 'https://api.github.com/users/leowzz', 'html_url': 'https://github.com/leowzz',
                   'followers_url': 'https://api.github.com/users/leowzz/followers',
                   'following_url': 'https://api.github.com/users/leowzz/following{/other_user}',
                   'gists_url': 'https://api.github.com/users/leowzz/gists{/gist_id}',
                   'starred_url': 'https://api.github.com/users/leowzz/starred{/owner}{/repo}',
                   'subscriptions_url': 'https://api.github.com/users/leowzz/subscriptions',
                   'organizations_url': 'https://api.github.com/users/leowzz/orgs',
                   'repos_url': 'https://api.github.com/users/leowzz/repos',
                   'events_url': 'https://api.github.com/users/leowzz/events{/privacy}',
                   'received_events_url': 'https://api.github.com/users/leowzz/received_events', 'type': 'User',
                   'site_admin': False}, 'run_attempt': 1, 'referenced_workflows': [],
         'run_started_at': '2024-08-31T08:58:51Z',
         'triggering_actor': {'login': 'leowzz', 'id': 72735229, 'node_id': 'MDQ6VXNlcjcyNzM1MjI5',
                              'avatar_url': 'https://avatars.githubusercontent.com/u/72735229?v=4', 'gravatar_id': '',
                              'url': 'https://api.github.com/users/leowzz', 'html_url': 'https://github.com/leowzz',
                              'followers_url': 'https://api.github.com/users/leowzz/followers',
                              'following_url': 'https://api.github.com/users/leowzz/following{/other_user}',
                              'gists_url': 'https://api.github.com/users/leowzz/gists{/gist_id}',
                              'starred_url': 'https://api.github.com/users/leowzz/starred{/owner}{/repo}',
                              'subscriptions_url': 'https://api.github.com/users/leowzz/subscriptions',
                              'organizations_url': 'https://api.github.com/users/leowzz/orgs',
                              'repos_url': 'https://api.github.com/users/leowzz/repos',
                              'events_url': 'https://api.github.com/users/leowzz/events{/privacy}',
                              'received_events_url': 'https://api.github.com/users/leowzz/received_events',
                              'type': 'User', 'site_admin': False},
         'jobs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10644003658/jobs',
         'logs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10644003658/logs',
         'check_suite_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/check-suites/27827440541',
         'artifacts_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10644003658/artifacts',
         'cancel_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10644003658/cancel',
         'rerun_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10644003658/rerun',
         'previous_attempt_url': None,
         'workflow_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/workflows/114917830',
         'head_commit': {'id': 'd1528161ac4de6a11caa4a1d4bf040da0cddf2c2',
                         'tree_id': '95aa520878fe9e3fa788bb1fcfa29ccb0667ebd2', 'message': 'add todo',
                         'timestamp': '2024-08-31T08:56:13Z',
                         'author': {'name': 'WangZhanze', 'email': 'wangzhanze@huoban.ai'},
                         'committer': {'name': 'WangZhanze', 'email': 'wangzhanze@huoban.ai'}},
         'repository': {'id': 849673470, 'node_id': 'R_kgDOMqT8_g', 'name': 'docker_image_pusher',
                        'full_name': 'leowzz/docker_image_pusher', 'private': False,
                        'owner': {'login': 'leowzz', 'id': 72735229, 'node_id': 'MDQ6VXNlcjcyNzM1MjI5',
                                  'avatar_url': 'https://avatars.githubusercontent.com/u/72735229?v=4',
                                  'gravatar_id': '', 'url': 'https://api.github.com/users/leowzz',
                                  'html_url': 'https://github.com/leowzz',
                                  'followers_url': 'https://api.github.com/users/leowzz/followers',
                                  'following_url': 'https://api.github.com/users/leowzz/following{/other_user}',
                                  'gists_url': 'https://api.github.com/users/leowzz/gists{/gist_id}',
                                  'starred_url': 'https://api.github.com/users/leowzz/starred{/owner}{/repo}',
                                  'subscriptions_url': 'https://api.github.com/users/leowzz/subscriptions',
                                  'organizations_url': 'https://api.github.com/users/leowzz/orgs',
                                  'repos_url': 'https://api.github.com/users/leowzz/repos',
                                  'events_url': 'https://api.github.com/users/leowzz/events{/privacy}',
                                  'received_events_url': 'https://api.github.com/users/leowzz/received_events',
                                  'type': 'User', 'site_admin': False},
                        'html_url': 'https://github.com/leowzz/docker_image_pusher',
                        'description': '使用Github Action将国外的Docker镜像转存到阿里云私有仓库，供国内服务器使用，免费易用. 支持api调用, streamlit/cli调用',
                        'fork': True, 'url': 'https://api.github.com/repos/leowzz/docker_image_pusher',
                        'forks_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/forks',
                        'keys_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/keys{/key_id}',
                        'collaborators_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/collaborators{/collaborator}',
                        'teams_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/teams',
                        'hooks_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/hooks',
                        'issue_events_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues/events{/number}',
                        'events_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/events',
                        'assignees_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/assignees{/user}',
                        'branches_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/branches{/branch}',
                        'tags_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/tags',
                        'blobs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/blobs{/sha}',
                        'git_tags_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/tags{/sha}',
                        'git_refs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/refs{/sha}',
                        'trees_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/trees{/sha}',
                        'statuses_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/statuses/{sha}',
                        'languages_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/languages',
                        'stargazers_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/stargazers',
                        'contributors_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/contributors',
                        'subscribers_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/subscribers',
                        'subscription_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/subscription',
                        'commits_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/commits{/sha}',
                        'git_commits_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/commits{/sha}',
                        'comments_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/comments{/number}',
                        'issue_comment_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues/comments{/number}',
                        'contents_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/contents/{+path}',
                        'compare_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/compare/{base}...{head}',
                        'merges_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/merges',
                        'archive_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/{archive_format}{/ref}',
                        'downloads_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/downloads',
                        'issues_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues{/number}',
                        'pulls_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/pulls{/number}',
                        'milestones_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/milestones{/number}',
                        'notifications_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/notifications{?since,all,participating}',
                        'labels_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/labels{/name}',
                        'releases_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/releases{/id}',
                        'deployments_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/deployments'},
         'head_repository': {'id': 849673470, 'node_id': 'R_kgDOMqT8_g', 'name': 'docker_image_pusher',
                             'full_name': 'leowzz/docker_image_pusher', 'private': False,
                             'owner': {'login': 'leowzz', 'id': 72735229, 'node_id': 'MDQ6VXNlcjcyNzM1MjI5',
                                       'avatar_url': 'https://avatars.githubusercontent.com/u/72735229?v=4',
                                       'gravatar_id': '', 'url': 'https://api.github.com/users/leowzz',
                                       'html_url': 'https://github.com/leowzz',
                                       'followers_url': 'https://api.github.com/users/leowzz/followers',
                                       'following_url': 'https://api.github.com/users/leowzz/following{/other_user}',
                                       'gists_url': 'https://api.github.com/users/leowzz/gists{/gist_id}',
                                       'starred_url': 'https://api.github.com/users/leowzz/starred{/owner}{/repo}',
                                       'subscriptions_url': 'https://api.github.com/users/leowzz/subscriptions',
                                       'organizations_url': 'https://api.github.com/users/leowzz/orgs',
                                       'repos_url': 'https://api.github.com/users/leowzz/repos',
                                       'events_url': 'https://api.github.com/users/leowzz/events{/privacy}',
                                       'received_events_url': 'https://api.github.com/users/leowzz/received_events',
                                       'type': 'User', 'site_admin': False},
                             'html_url': 'https://github.com/leowzz/docker_image_pusher',
                             'description': '使用Github Action将国外的Docker镜像转存到阿里云私有仓库，供国内服务器使用，免费易用. 支持api调用, streamlit/cli调用',
                             'fork': True, 'url': 'https://api.github.com/repos/leowzz/docker_image_pusher',
                             'forks_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/forks',
                             'keys_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/keys{/key_id}',
                             'collaborators_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/collaborators{/collaborator}',
                             'teams_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/teams',
                             'hooks_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/hooks',
                             'issue_events_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues/events{/number}',
                             'events_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/events',
                             'assignees_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/assignees{/user}',
                             'branches_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/branches{/branch}',
                             'tags_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/tags',
                             'blobs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/blobs{/sha}',
                             'git_tags_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/tags{/sha}',
                             'git_refs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/refs{/sha}',
                             'trees_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/trees{/sha}',
                             'statuses_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/statuses/{sha}',
                             'languages_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/languages',
                             'stargazers_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/stargazers',
                             'contributors_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/contributors',
                             'subscribers_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/subscribers',
                             'subscription_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/subscription',
                             'commits_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/commits{/sha}',
                             'git_commits_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/commits{/sha}',
                             'comments_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/comments{/number}',
                             'issue_comment_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues/comments{/number}',
                             'contents_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/contents/{+path}',
                             'compare_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/compare/{base}...{head}',
                             'merges_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/merges',
                             'archive_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/{archive_format}{/ref}',
                             'downloads_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/downloads',
                             'issues_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues{/number}',
                             'pulls_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/pulls{/number}',
                             'milestones_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/milestones{/number}',
                             'notifications_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/notifications{?since,all,participating}',
                             'labels_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/labels{/name}',
                             'releases_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/releases{/id}',
                             'deployments_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/deployments'}},
        {'id': 10643959071,
         'name': 'Making apache/airflow:2.8.4-python3.10 by @leowzz to apache/airflow:2.8.4-python3.10',
         'node_id': 'WFR_kwLOMqT8_s8AAAACem3tHw', 'head_branch': 'main',
         'head_sha': 'ffa603039570af3fbff200f151c7d069df755b35', 'path': '.github/workflows/api_hook.yaml',
         'display_title': 'Making apache/airflow:2.8.4-python3.10 by @leowzz to apache/airflow:2.8.4-python3.10',
         'run_number': 18, 'event': 'workflow_dispatch', 'status': 'completed', 'conclusion': 'failure',
         'workflow_id': 114917830, 'check_suite_id': 27827333360, 'check_suite_node_id': 'CS_kwDOMqT8_s8AAAAGeqNo8A',
         'url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10643959071',
         'html_url': 'https://github.com/leowzz/docker_image_pusher/actions/runs/10643959071', 'pull_requests': [],
         'created_at': '2024-08-31T08:48:37Z', 'updated_at': '2024-08-31T08:49:41Z',
         'actor': {'login': 'leowzz', 'id': 72735229, 'node_id': 'MDQ6VXNlcjcyNzM1MjI5',
                   'avatar_url': 'https://avatars.githubusercontent.com/u/72735229?v=4', 'gravatar_id': '',
                   'url': 'https://api.github.com/users/leowzz', 'html_url': 'https://github.com/leowzz',
                   'followers_url': 'https://api.github.com/users/leowzz/followers',
                   'following_url': 'https://api.github.com/users/leowzz/following{/other_user}',
                   'gists_url': 'https://api.github.com/users/leowzz/gists{/gist_id}',
                   'starred_url': 'https://api.github.com/users/leowzz/starred{/owner}{/repo}',
                   'subscriptions_url': 'https://api.github.com/users/leowzz/subscriptions',
                   'organizations_url': 'https://api.github.com/users/leowzz/orgs',
                   'repos_url': 'https://api.github.com/users/leowzz/repos',
                   'events_url': 'https://api.github.com/users/leowzz/events{/privacy}',
                   'received_events_url': 'https://api.github.com/users/leowzz/received_events', 'type': 'User',
                   'site_admin': False}, 'run_attempt': 1, 'referenced_workflows': [],
         'run_started_at': '2024-08-31T08:48:37Z',
         'triggering_actor': {'login': 'leowzz', 'id': 72735229, 'node_id': 'MDQ6VXNlcjcyNzM1MjI5',
                              'avatar_url': 'https://avatars.githubusercontent.com/u/72735229?v=4', 'gravatar_id': '',
                              'url': 'https://api.github.com/users/leowzz', 'html_url': 'https://github.com/leowzz',
                              'followers_url': 'https://api.github.com/users/leowzz/followers',
                              'following_url': 'https://api.github.com/users/leowzz/following{/other_user}',
                              'gists_url': 'https://api.github.com/users/leowzz/gists{/gist_id}',
                              'starred_url': 'https://api.github.com/users/leowzz/starred{/owner}{/repo}',
                              'subscriptions_url': 'https://api.github.com/users/leowzz/subscriptions',
                              'organizations_url': 'https://api.github.com/users/leowzz/orgs',
                              'repos_url': 'https://api.github.com/users/leowzz/repos',
                              'events_url': 'https://api.github.com/users/leowzz/events{/privacy}',
                              'received_events_url': 'https://api.github.com/users/leowzz/received_events',
                              'type': 'User', 'site_admin': False},
         'jobs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10643959071/jobs',
         'logs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10643959071/logs',
         'check_suite_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/check-suites/27827333360',
         'artifacts_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10643959071/artifacts',
         'cancel_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10643959071/cancel',
         'rerun_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/runs/10643959071/rerun',
         'previous_attempt_url': None,
         'workflow_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/actions/workflows/114917830',
         'head_commit': {'id': 'ffa603039570af3fbff200f151c7d069df755b35',
                         'tree_id': '13f1f6840303540c1d1a6ee4c8033ff4d654f30c', 'message': 'update readme',
                         'timestamp': '2024-08-31T07:41:28Z',
                         'author': {'name': 'WangZhanze', 'email': 'wangzhanze@huoban.ai'},
                         'committer': {'name': 'WangZhanze', 'email': 'wangzhanze@huoban.ai'}},
         'repository': {'id': 849673470, 'node_id': 'R_kgDOMqT8_g', 'name': 'docker_image_pusher',
                        'full_name': 'leowzz/docker_image_pusher', 'private': False,
                        'owner': {'login': 'leowzz', 'id': 72735229, 'node_id': 'MDQ6VXNlcjcyNzM1MjI5',
                                  'avatar_url': 'https://avatars.githubusercontent.com/u/72735229?v=4',
                                  'gravatar_id': '', 'url': 'https://api.github.com/users/leowzz',
                                  'html_url': 'https://github.com/leowzz',
                                  'followers_url': 'https://api.github.com/users/leowzz/followers',
                                  'following_url': 'https://api.github.com/users/leowzz/following{/other_user}',
                                  'gists_url': 'https://api.github.com/users/leowzz/gists{/gist_id}',
                                  'starred_url': 'https://api.github.com/users/leowzz/starred{/owner}{/repo}',
                                  'subscriptions_url': 'https://api.github.com/users/leowzz/subscriptions',
                                  'organizations_url': 'https://api.github.com/users/leowzz/orgs',
                                  'repos_url': 'https://api.github.com/users/leowzz/repos',
                                  'events_url': 'https://api.github.com/users/leowzz/events{/privacy}',
                                  'received_events_url': 'https://api.github.com/users/leowzz/received_events',
                                  'type': 'User', 'site_admin': False},
                        'html_url': 'https://github.com/leowzz/docker_image_pusher',
                        'description': '使用Github Action将国外的Docker镜像转存到阿里云私有仓库，供国内服务器使用，免费易用. 支持api调用, streamlit/cli调用',
                        'fork': True, 'url': 'https://api.github.com/repos/leowzz/docker_image_pusher',
                        'forks_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/forks',
                        'keys_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/keys{/key_id}',
                        'collaborators_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/collaborators{/collaborator}',
                        'teams_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/teams',
                        'hooks_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/hooks',
                        'issue_events_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues/events{/number}',
                        'events_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/events',
                        'assignees_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/assignees{/user}',
                        'branches_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/branches{/branch}',
                        'tags_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/tags',
                        'blobs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/blobs{/sha}',
                        'git_tags_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/tags{/sha}',
                        'git_refs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/refs{/sha}',
                        'trees_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/trees{/sha}',
                        'statuses_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/statuses/{sha}',
                        'languages_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/languages',
                        'stargazers_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/stargazers',
                        'contributors_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/contributors',
                        'subscribers_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/subscribers',
                        'subscription_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/subscription',
                        'commits_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/commits{/sha}',
                        'git_commits_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/commits{/sha}',
                        'comments_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/comments{/number}',
                        'issue_comment_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues/comments{/number}',
                        'contents_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/contents/{+path}',
                        'compare_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/compare/{base}...{head}',
                        'merges_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/merges',
                        'archive_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/{archive_format}{/ref}',
                        'downloads_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/downloads',
                        'issues_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues{/number}',
                        'pulls_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/pulls{/number}',
                        'milestones_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/milestones{/number}',
                        'notifications_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/notifications{?since,all,participating}',
                        'labels_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/labels{/name}',
                        'releases_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/releases{/id}',
                        'deployments_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/deployments'},
         'head_repository': {'id': 849673470, 'node_id': 'R_kgDOMqT8_g', 'name': 'docker_image_pusher',
                             'full_name': 'leowzz/docker_image_pusher', 'private': False,
                             'owner': {'login': 'leowzz', 'id': 72735229, 'node_id': 'MDQ6VXNlcjcyNzM1MjI5',
                                       'avatar_url': 'https://avatars.githubusercontent.com/u/72735229?v=4',
                                       'gravatar_id': '', 'url': 'https://api.github.com/users/leowzz',
                                       'html_url': 'https://github.com/leowzz',
                                       'followers_url': 'https://api.github.com/users/leowzz/followers',
                                       'following_url': 'https://api.github.com/users/leowzz/following{/other_user}',
                                       'gists_url': 'https://api.github.com/users/leowzz/gists{/gist_id}',
                                       'starred_url': 'https://api.github.com/users/leowzz/starred{/owner}{/repo}',
                                       'subscriptions_url': 'https://api.github.com/users/leowzz/subscriptions',
                                       'organizations_url': 'https://api.github.com/users/leowzz/orgs',
                                       'repos_url': 'https://api.github.com/users/leowzz/repos',
                                       'events_url': 'https://api.github.com/users/leowzz/events{/privacy}',
                                       'received_events_url': 'https://api.github.com/users/leowzz/received_events',
                                       'type': 'User', 'site_admin': False},
                             'html_url': 'https://github.com/leowzz/docker_image_pusher',
                             'description': '使用Github Action将国外的Docker镜像转存到阿里云私有仓库，供国内服务器使用，免费易用. 支持api调用, streamlit/cli调用',
                             'fork': True, 'url': 'https://api.github.com/repos/leowzz/docker_image_pusher',
                             'forks_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/forks',
                             'keys_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/keys{/key_id}',
                             'collaborators_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/collaborators{/collaborator}',
                             'teams_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/teams',
                             'hooks_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/hooks',
                             'issue_events_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues/events{/number}',
                             'events_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/events',
                             'assignees_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/assignees{/user}',
                             'branches_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/branches{/branch}',
                             'tags_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/tags',
                             'blobs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/blobs{/sha}',
                             'git_tags_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/tags{/sha}',
                             'git_refs_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/refs{/sha}',
                             'trees_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/trees{/sha}',
                             'statuses_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/statuses/{sha}',
                             'languages_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/languages',
                             'stargazers_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/stargazers',
                             'contributors_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/contributors',
                             'subscribers_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/subscribers',
                             'subscription_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/subscription',
                             'commits_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/commits{/sha}',
                             'git_commits_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/git/commits{/sha}',
                             'comments_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/comments{/number}',
                             'issue_comment_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues/comments{/number}',
                             'contents_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/contents/{+path}',
                             'compare_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/compare/{base}...{head}',
                             'merges_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/merges',
                             'archive_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/{archive_format}{/ref}',
                             'downloads_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/downloads',
                             'issues_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/issues{/number}',
                             'pulls_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/pulls{/number}',
                             'milestones_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/milestones{/number}',
                             'notifications_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/notifications{?since,all,participating}',
                             'labels_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/labels{/name}',
                             'releases_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/releases{/id}',
                             'deployments_url': 'https://api.github.com/repos/leowzz/docker_image_pusher/deployments'}}]}
