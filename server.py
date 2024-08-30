import requests
from config import settings

url = "https://api.github.com/repos/leowzz/docker_image_pusher/repository_dispatch"
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

# response = requests.post(url, headers=headers, json=data)
response = requests.get(url, headers=headers)
print(response.status_code)
print(response.text)
if response.status_code == 204:
    print("Request was successful.")
else:
    print(f"Request failed with status code: {response.status_code}")