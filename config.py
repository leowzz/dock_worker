from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    token: str  # 你的访问令牌 https://docs.github.com/zh/rest/actions/workflows?apiVersion=2022-11-28
    default_workflow_name: str = "ApiDockerImagePusher"
    http_proxy: str | None = None
    https_proxy: str | None = None
    owner: str = "leowzz"  # github用户名
    repo: str = "docker_image_pusher"  # github仓库名, fork此项目后的仓库名

    class Config:
        env_file = ".env"


settings = Settings()
