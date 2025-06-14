from dotenv import load_dotenv 
import os

from llama_index.core import VectorStoreIndex, Settings, PromptTemplate
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
import streamlit as st

load_dotenv(".env")
GEMINI_KEY = os.environ.get("GEMINI_KEY")
QDRANT_KEY = os.environ.get("QDRANT_KEY")
COLLECTION = os.environ.get("COLLECTION")

gemini_model = "models/gemini-2.0-flash"
embed_model = "models/gemini-embedding-exp-03-07"

# Connect service client.
qdrant_client = QdrantClient(
    url="https://2fca434a-57ac-427f-9488-377cd4093eaa.europe-west3-0.gcp.cloud.qdrant.io:6333", 
    api_key=QDRANT_KEY
)

# Setting the llama_index contect models.
Settings.llm = Gemini(model=gemini_model,api_key=GEMINI_KEY, temperature=0.5)
Settings.embed_model = GeminiEmbedding(
    model_name=embed_model, api_key=GEMINI_KEY, title="this is a document"
)

gemini = Gemini(model=gemini_model,api_key=GEMINI_KEY, temperature=0.5)
# Define the preprompt
preprompt = """
You are a helpful assistant that provides accurate and concise answers based on the provided documents.
If the user ask you about yourself, please tell them that you are the assistant to retrieve the data from qdrant database.
Always ensure your responses are clear, relevant, and directly address the user's question.
You can also use your known knowledge to address the user's question. 
If the user ask depart from English, please use their used language to answer.
"""

rephrase_prompt = """
Please rephrase the user's prompt into a suitable format to improve the quality and relevant for qdrant search engine, 
and only response the rephrased sentencs. Please answer it concisely.

user's prompt: {prompt}
"""

# Create a custom prompt template
query_prompt_template = PromptTemplate(
    template=preprompt + "\n\nUser Query: {query_str}"
)

rephrase_prompt_template = PromptTemplate(
    template=rephrase_prompt
)


db_map = {'麥肯錫文章':{"db":'mckinsey-data-example', "description":"包含了五篇麥肯錫顧問討論人資與AI之相關議題的文章"},
          '紫外光研究文獻': {"db":'scholar-data-example', "description":"包含了三篇有關紫外光殺菌研究論文"}}

title_lst = [title for title in db_map.keys()]
description_lst = [v["description"] for v in db_map.values()]

st.title("知識管理聊天AI範例")
st.text("「知識管理聊天 AI 範例」是一款智慧助手，幫你快速整理、搜尋、應用各種知識。透過 AI 對話，你可以輕鬆獲取資訊、提升工作效率，還能優化決策流程。不管是學習、研究，還是日常管理，這款 APP 都能成為你的好幫手，讓知識隨手可得、輕鬆運用！")

selected_db = st.radio('選擇範例資料庫', 
                       title_lst, 
                       captions=description_lst)

COLLECTION = db_map[selected_db]["db"]
print(COLLECTION)

vector_store = QdrantVectorStore(client=qdrant_client, collection_name=COLLECTION)
# Create a VectorStoreIndex from the documents
index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
# Query the index
query_engine = index.as_query_engine(similarity_top_k=10, text_qa_template=query_prompt_template)

# TODO: build up the memory for chatbot


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me something..."):
    with st.chat_message(name="user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role":"user", "content":prompt})

    # rephrase the prompt.
    rephrased_prompt = gemini.complete(prompt=rephrase_prompt.format(prompt=prompt))

    response = query_engine.query(rephrased_prompt.text)

    with st.chat_message(name="assistent"):
        st.markdown(response)
    st.session_state.messages.append({"role":"assistent", "content":response})