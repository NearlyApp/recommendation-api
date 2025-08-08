import os
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr
from typing import List

from worker.lib.pydantic.data_models import DataModel

EMBEDDING_MODEL = "text-embedding-3-small"

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OpenAI API key is not set in environment variables.")

model = OpenAIEmbeddings(api_key=SecretStr(openai_api_key), model=EMBEDDING_MODEL)


def embed_data(data: DataModel) -> List[float] | None:
    """
    Uses OpenAIEmbeddings to generate embeddings for the given data model.
    """
    try:
        text = data.text
        embeddings = model.embed_documents([text])
        return embeddings[0] if embeddings else None
    except Exception as e:
        print(f"Error embedding data: {e}")
        return None
