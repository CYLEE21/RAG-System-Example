"""
This file shows the example of embedding using Google Gemini
"""

import google.generativeai as genai

from llama_index.core import Document
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore

from qdrant_client import QdrantClient
from qdrant_client.http import models

GEMINI_KEY = ''
QDRANT_KEY = ''

gemini_client = genai.configure(api_key=GEMINI_KEY)

embed_model_name = "models/gemini-embedding-exp-03-07"
collection_name = "scholar-data-example"
vector_size = 3072  # Size of the vector (should match your embedding vector size)
distance_metric = "Cosine"  # Options: 'Cosine', 'Euclid', 'Dot'

qdrant_client = QdrantClient(
    url="https://2fca434a-57ac-427f-9488-377cd4093eaa.europe-west3-0.gcp.cloud.qdrant.io:6333", 
    api_key=QDRANT_KEY
)

# Step 3: Create the collection
qdrant_client.recreate_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(size=vector_size, distance=distance_metric)
)

vector_store = QdrantVectorStore(client=qdrant_client, collection_name=collection_name)

embed_model = GeminiEmbedding(
    model_name=embed_model_name, api_key=GEMINI_KEY, title="this is a document"
)

from scholar_dict import payloads
import time
# Create the documents from payloads's text
documents = []
for payload in payloads:
    documents.append(Document(text=payload["text"]))

ids_ = []
vec_ = []
for doc in documents:
    doc.embedding = embed_model.get_text_embedding(doc.text)
    ids_.append(doc.id_)
    vec_.append(doc.embedding)
    time.sleep(10)
    #vector_store.(doc.id_, doc.embedding, payload={"text": doc.text})
    #break
vec_[0]
qdrant_client.upsert(
    collection_name=collection_name,
    points=models.Batch(
        ids=ids_,
        vectors=vec_,
        payloads=payloads
    )
)

# qdrant create payload index
qdrant_client.create_payload_index(collection_name=collection_name, field_name="title", field_schema="keyword")

