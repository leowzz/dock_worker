import os
from pydantic_settings import BaseSettings

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONFIG_DIR = os.path.expanduser("~/.config/dock_worker")
CONFIG_PATH = os.path.join(CONFIG_DIR, "conf.env")

# 确保配置目录存在
os.makedirs(CONFIG_DIR, exist_ok=True)

# 如果配置文件不存在则创建默认配置
if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write("""\
# Github配置
GITHUB_TOKEN=your_token_here
GITHUB_USERNAME=
GITHUB_REPO=dock_worker

# 镜像仓库配置
IMAGE_REPOSITORIES_ENDPOINT=registry.cn-heyuan.aliyuncs.com
NAME_SPACE=
DEFAULT_WORKFLOW_NAME=ApiDockerImagePusher

# 代理配置(可选)
HTTP_PROXY=
HTTPS_PROXY=
""")


class Settings(BaseSettings):
    github_token: str  # 你的访问令牌 https://docs.github.com/zh/rest/actions/workflows?apiVersion=2022-11-28
    image_repositories_endpoint: str = "registry.cn-heyuan.aliyuncs.com"
    name_space: str = "leo03w"
    default_workflow_name: str = "ApiDockerImagePusher"
    http_proxy: str | None = None
    https_proxy: str | None = None
    github_username: str = "leowzz"  # github用户名
    github_repo: str = "dock_worker"  # github仓库名, fork此项目后的仓库名

    db_path: str = os.path.join(CONFIG_DIR, "dock_worker.sqlite")

    class Config:
        env_file = CONFIG_PATH


config = Settings()
from loguru import logger

logger.debug(f"{config=}")
