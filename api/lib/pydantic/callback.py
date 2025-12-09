import pydantic

from api.worker.lib.pydantic.data_models import DataStatus


class CallbackIngestResult(pydantic.BaseModel):
    post_id: str = pydantic.Field(..., description="Unique identifier for the post")
    status: DataStatus = pydantic.Field(..., description="Ingestion status of the post")
