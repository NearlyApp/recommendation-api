import requests
from api.lib.pydantic.callback import CallbackIngestResult


def callback_ingest_result(callback_url: str, payload: CallbackIngestResult) -> bool:
    """
    Sends a callback with the ingestion result to the specified URL.
    """
    try:
        response = requests.post(
            callback_url,
            json=payload.model_dump(mode="json"),
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        # info print the response status code
        print(f"Callback response status: {response.status_code}")
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending callback to {callback_url}: {e}")
        return False
