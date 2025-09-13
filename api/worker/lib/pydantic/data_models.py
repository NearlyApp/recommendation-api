from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional
from decimal import Decimal
from datetime import datetime, timezone


class DataLocation(BaseModel):
    lat: Decimal = Field(..., description="Latitude of the post location")
    lon: Decimal = Field(..., description="Longitude of the post location")

    model_config = ConfigDict(json_encoders={Decimal: lambda v: float(v)})


class DataMetadata(BaseModel):
    location: DataLocation = Field(..., description="Geographical location of the post")

    model_config = ConfigDict(json_encoders={Decimal: lambda v: float(v)}, extra="forbid")


class DataModel(BaseModel):
    post_id: str = Field(..., description="Unique identifier for the post")
    metadata: DataMetadata = Field(..., description="Metadata associated with the post")
    status: Literal["WAITING_FOR_PROCESSING", "PROCESSING", "PROCESSED"] = Field(
        "WAITING_FOR_PROCESSING", description="Current status of the post"
    )
    text: str = Field(..., description="Text content of the post")
    created_at: str = Field(
        datetime.now(timezone.utc).isoformat(),
        description="Creation timestamp of the post",
    )
    updated_at: str = Field(
        datetime.now(timezone.utc).isoformat(),
        description="Last update timestamp of the post",
    )

    model_config = ConfigDict(json_encoders={Decimal: lambda v: float(v)}, extra="forbid")

class DataModelCreate(BaseModel):
    post_id: str = Field(..., description="Unique identifier for the post")
    metadata: DataMetadata = Field(..., description="Metadata associated with the post")
    text: str = Field(..., description="Text content of the post")

    created_at: Optional[str] = Field(
        datetime.now(timezone.utc).isoformat(),
        description="Creation timestamp of the post. If not provided, will be set to current time.",
    )
    updated_at: Optional[str] = Field(
        datetime.now(timezone.utc).isoformat(),
        description="Last update timestamp of the post. If not provided, will be set to current time.",
    )

    model_config = ConfigDict(json_encoders={Decimal: lambda v: float(v)}, extra="forbid")