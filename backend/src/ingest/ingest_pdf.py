import pdfplumber
import pandas as pd
import numpy as np
import openai
import os
from ast import literal_eval
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
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR="src/ingest/output/"

openai.api_key = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI()

def parsePDFs(folder_path):
    # Load PDFs and extract text into documents
    pdf_documents = []

    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

    for i, pdf_file in enumerate(pdf_files):
        with pdfplumber.open(os.path.join(folder_path, pdf_file)) as pdf:
            for page in pdf.pages:
                pdf_documents.append({
                    "embedding_id": i,
                    "title": os.path.basename(pdf_file) + " - Page: " + str(page.page_number),
                    "content": page.extract_text()
            })

    # Convert list of dictionaries to DataFrame
    df = pd.DataFrame(pdf_documents)
    return df

def get_embedding(text, model="text-embedding-ada-002"):
   text = text.replace("\n", " ")
   response = client.embeddings.create(input = [text], model=model)
   return response.data[0].embedding

def generateEmbeddings():
    df = parsePDFs("./src/ingest/data/pdf/")
    print(df.head())

    # Apply function to title and content columns
    df['embedding_id'] = df['title'] + df['content']
    df['title_embedding'] = df['title'].apply(get_embedding)
    df['content_embedding'] = df['content'].apply(get_embedding)
    df.to_csv(OUTPUT_DIR + 'embedded_speeches.csv', index=False)

    return df

def getPDFEmbeddings():

    if os.path.isfile(OUTPUT_DIR + "embedded_speeches.csv"):
        df = pd.read_csv(OUTPUT_DIR + "embedded_speeches.csv")
    else: 
        df =  generateEmbeddings()

    df['title_embedding'] = df.title_embedding.apply(literal_eval)
    df['content_embedding'] = df.content_embedding.apply(literal_eval)
    df['embedding_id'] = df['embedding_id'].apply(str)
    return df


import redis
import sys
sys.path.append('../')
from redis_vector_db.vector_db import index_pdf_documents, search_pdf_redis


def ingest(redis_client):
    df = getPDFEmbeddings()

    # Create a search index
    # Constants
    VECTOR_DIM = len(df['title_embedding'][0]) # length of the vectors
    VECTOR_NUMBER = len(df)                 # initial number of vectors
    INDEX_NAME = "embeddings-index"           # name of the search index
    PREFIX = "doc"                            # prefix for the document keys
    DISTANCE_METRIC = "COSINE"                # distance metric for the vectors (ex. COSINE, IP, L2)

    # Define RediSearch fields for each of the columns in the dataset
    title = TextField(name="title")
    text = TextField(name="content")
    title_embedding = VectorField("title_embedding",
        "FLAT", {
            "TYPE": "FLOAT32",
            "DIM": VECTOR_DIM,
            "DISTANCE_METRIC": DISTANCE_METRIC,
            "INITIAL_CAP": VECTOR_NUMBER,
        }
    )
    text_embedding = VectorField("content_embedding",
        "FLAT", {
            "TYPE": "FLOAT32",
            "DIM": VECTOR_DIM,
            "DISTANCE_METRIC": DISTANCE_METRIC,
            "INITIAL_CAP": VECTOR_NUMBER,
        }
    )
    fields = [title, text, title_embedding, text_embedding]

    # Check if index exists
    try:
        redis_client.ft(INDEX_NAME).info()
        print("Index already exists")
    except:
        # Create RediSearch Index
        redis_client.ft(INDEX_NAME).create_index(
            fields = fields,
            definition = IndexDefinition(prefix=[PREFIX], index_type=IndexType.HASH)
        )
        print("Index Created")

    index_pdf_documents(redis_client, PREFIX, df)
    print(f"Loaded {redis_client.info()['db0']['keys']} documents in Redis search index with name: {INDEX_NAME}")

