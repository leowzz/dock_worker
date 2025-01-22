from datetime import datetime
import uuid
from enum import Enum

from pydantic import BaseModel

from dock_worker.utils import normalize_image_name


class ImageArgs(BaseModel):
    source: str
    target: str | None = None  # 私有仓库镜像, aliyun.com/your_space/{target}
    distinct_id: str | None = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.target is None:
            self.target = self.source
        self.target = normalize_image_name(self.target, remove_namespace=True)
        self.distinct_id = self.distinct_id or uuid.uuid4().hex[:6]


class JobQueryReq(ImageArgs):
    source: str | None = None


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


class TriggerRequest(BaseModel):
    source: str
    target: str | None = None


class JobBase(ImageArgs):
    source: str
    target: str | None = None
    run_number: int | None = None
    run_id: int | None = None
    distinct_id: str | None = None
    status: str = "pending"
    repo_url: str | None = None
    repo_namespace: str | None = None
    workflow_id: int | None = None
    workflow_name: str | None = None
    full_url: str | None = None


class JobInDB(JobBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobNew(JobBase):
    pass


class JobStatusEnum(str, Enum):
    pending = "pending"  # 非github 状态, 仅用于初始值
    queued = "queued"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


status_2_progress_number = {
    JobStatusEnum.pending: 20,
    JobStatusEnum.queued: 30,
    JobStatusEnum.in_progress: 50,
    JobStatusEnum.completed: 100,
    JobStatusEnum.failed: 0,
}
