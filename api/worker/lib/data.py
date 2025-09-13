import boto3
import os
from .pydantic.data_models import DataModel

# dynamodb client
dynamodb = boto3.resource("dynamodb")
table_name = os.getenv("DATA_TABLE_NAME")
table = dynamodb.Table(name=table_name)


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
        response = table.put_item(Item=data.model_dump())
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
