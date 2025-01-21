from pydantic import BaseModel, field_validator
from datetime import datetime
from utils import normalize_image_name
import uuid

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