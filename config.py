from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    token: str  # 你的访问令牌 https://docs.github.com/zh/rest/actions/workflows?apiVersion=2022-11-28
    image_repositories_endpoint: str = "registry.cn-heyuan.aliyuncs.com"
    name_space: str = "leowzz"
    default_workflow_name: str = "ApiDockerImagePusher"
    http_proxy: str | None = None
    https_proxy: str | None = None
    github_username: str = "leowzz"  # github用户名
    github_repo: str = "docker_image_pusher"  # github仓库名, fork此项目后的仓库名

    class Config:
        env_file = ".env"


settings = Settings()
