from pydantic import BaseModel, Field
from worker.lib.pydantic.data_models import DataModel


class IngestRequest(BaseModel):
    data: DataModel = Field(..., description="Data model containing post information")
    model_config = {"extra": "forbid"}
