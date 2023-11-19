from typing import List
import openai
import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()


import redis
from redis.commands.search.indexDefinition import (
    IndexDefinition,
    IndexType
)
from redis.commands.search.query import Query
from redis.commands.search.field import (
    TextField,
    VectorField
)

openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()

REDIS_HOST =  os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

def getConnection():
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=""
    )
    return redis_client

def index_pdf_documents(client: redis.Redis, prefix: str, documents: pd.DataFrame) -> None:
    records = documents.to_dict("records")
    for doc in records:
        key = f"{prefix}:{str(doc['embedding_id'])}"

        # create byte vectors for title and content
        title_embedding = np.array(doc["title_embedding"], dtype=np.float32).tobytes()
        content_embedding = np.array(doc["content_embedding"], dtype=np.float32).tobytes()

        # replace list of floats with byte vectors
        doc["title_embedding"] = title_embedding
        doc["content_embedding"] = content_embedding

        client.hset(key, mapping = doc)

def search_pdf_redis(
    redis_client: redis.Redis,
    user_query: str,
    index_name: str = "embeddings-index",
    vector_field: str = "title_embedding",
    return_fields: list = ["title", "url", "text", "vector_score"],
    hybrid_fields = "*",
    k: int = 20,
    print_results: bool = True,
) -> List[dict]:

    # Creates embedding vector from user query
    embedded_query = client.embeddings.create(input = [user_query], model="text-embedding-ada-002").data[0].embedding

    # Prepare the Query
    base_query = f'{hybrid_fields}=>[KNN {k} @{vector_field} $vector AS vector_score]'
    query = (
        Query(base_query)
         .return_fields(*return_fields)
         .sort_by("vector_score")
         .paging(0, k)
         .dialect(2)
    )
    params_dict = {"vector": np.array(embedded_query).astype(dtype=np.float32).tobytes()}

    # perform vector search
    results = redis_client.ft(index_name).search(query, params_dict)
    if print_results:
        for i, article in enumerate(results.docs):
            score = 1 - float(article.vector_score)
            print(f"{i}. {article.title} (Score: {round(score ,3) })")

    output = {
        "documents": [],
    }
    for doc in results.docs:
        document = {
            "content": doc.id,
            "payload": doc.payload,
            "vector_score": 1 - float(doc.vector_score),
            "title": doc.title
        }
        output['documents'].append(document)

    return output

