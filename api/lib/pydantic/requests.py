from pydantic import BaseModel, Field
from typing import List, Optional
from api.worker.lib.pydantic.data_models import DataModelCreate, DataLocation, DataModel


class IngestRequest(BaseModel):
    data: DataModelCreate = Field(..., description="Data model containing post information")

    model_config = {"extra": "forbid"}


class RecommendationRequest(BaseModel):
    candidates: List[DataModel] = Field(..., description="List of candidate data models")
    location: DataLocation = Field(..., description="Location for recommendation context")
    distance: Optional[str] = Field(default="50km", description="Distance metric for recommendations, example: '50km'")

    model_config = {"extra": "forbid"}