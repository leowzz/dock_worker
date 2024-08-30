import requests
from config import settings

github_repo_endpoint = "https://api.github.com/repos"
# 代理服务器的 URL
proxy = {
    'http': settings.http_proxy,
    'https': settings.http_proxy
}


def get_workflows(user, repo):
    response = requests.get(
        url=f"{github_repo_endpoint}/{user}/{repo}/actions/workflows",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {settings.token}",
            "X-GitHub-Api-Version": "2022-11-28"
        },
        proxies=proxy if settings.http_proxy else None
    )
    return response.json()


url = "https://api.github.com/repos/leowzz/docker_image_pusher/actions/workflows"
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {settings.token}",
    "X-GitHub-Api-Version": "2022-11-28"
}
data = {
    "event_type": "on-demand-test",
    "client_payload": {
        "unit": False,
        "integration": True
    }
}

# python:3.10.14-slim-bullseye

if __name__ == '__main__':
    print(get_workflows("leowzz", "docker_image_pusher"))

# response = requests.post(url, headers=headers, json=data)
# response = requests.get(url, headers=headers)
# print(response.status_code)
# print(response.text)
# if response.status_code == 204:
#     print("Request was successful.")
# else:
#     print(f"Request failed with status code: {response.status_code}")
