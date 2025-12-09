import boto3
import os
from decimal import Decimal
from typing import Any
from .pydantic.data_models import DataModel

# dynamodb client
dynamodb = boto3.resource("dynamodb")
table_name = os.getenv("DATA_TABLE_NAME")
table = dynamodb.Table(name=table_name)


def convert_floats_to_decimal(obj: Any) -> Any:
    """
    Recursively converts float values to Decimal for DynamoDB compatibility.
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(i) for i in obj]
    return obj


def get_data(id: str) -> DataModel | None:
    """
    Fetches data from DynamoDB table by ID.
    """
    try:
        response = table.get_item(Key={"post_id": id})
        if "Item" in response:
            parsed_data = DataModel(**response["Item"])
            return parsed_data
        return None

    except Exception as e:
        print(f"Error fetching data for ID {id}: {e}")
        return None


def put_data(data: DataModel) -> dict | None:
    """
    Puts data into DynamoDB table.
    """
    try:
        item = convert_floats_to_decimal(data.model_dump(mode="json"))
        response = table.put_item(Item=item)
        return response
    except Exception as e:
        print(f"Error putting data: {e}")
        return None


def delete_data(id: str) -> dict | None:
    """
    Deletes data from DynamoDB table by ID.
    """
    try:
        response = table.delete_item(Key={"post_id": id}, ReturnValues="ALL_OLD")
        return response["Attributes"] if "Attributes" in response else None
    except Exception as e:
        print(f"Error deleting data for ID {id}: {e}")
        return None
