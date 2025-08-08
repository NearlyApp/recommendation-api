from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


class DataLocation(BaseModel):
    lat: float = Field(..., description="Latitude of the post location")
    lon: float = Field(..., description="Longitude of the post location")


class DataMetadata(BaseModel):
    location: DataLocation = Field(..., description="Geographical location of the post")

    model_config = ConfigDict(extra="forbid")


class DataModel(BaseModel):
    post_id: str = Field(..., description="Unique identifier for the post")
    metadata: DataMetadata = Field(..., description="Metadata associated with the post")
    status: Literal["WAITING_FOR_PROCESSING", "PROCESSING", "PROCESSED"] = Field(
        "WAITING_FOR_PROCESSING", description="Current status of the post"
    )
    text: str = Field(..., description="Text content of the post")
