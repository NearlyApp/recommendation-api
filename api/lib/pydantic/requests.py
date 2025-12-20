from pydantic import BaseModel, Field
from typing import List, Optional
from api.worker.lib.pydantic.data_models import DataModelCreate, DataLocation, DataModel


class IngestRequest(BaseModel):
    data: DataModelCreate = Field(
        ..., description="Data model containing post information"
    )
    callback_url: Optional[str] = Field(
        None, description="Optional callback URL to notify after ingestion"
    )

    model_config = {"extra": "forbid"}


class RecommendationFilter(BaseModel):
    post_ids: Optional[List[str]] = Field(
        None, description="List of post IDs to exclude from recommendations"
    )
    author_ids: Optional[List[str]] = Field(
        None, description="List of author IDs to exclude from recommendations"
    )

    model_config = {"extra": "forbid"}


class RecommendationRequest(BaseModel):
    candidates: List[DataModel] = Field(
        ..., description="List of candidate data models"
    )
    location: DataLocation = Field(
        ..., description="Location for recommendation context"
    )
    distance: Optional[str] = Field(
        default="50km",
        description="Distance metric for recommendations, example: '50km'",
    )
    filters: Optional[RecommendationFilter] = Field(
        None, description="Optional filter to exclude specific posts or authors"
    )

    model_config = {"extra": "forbid"}
