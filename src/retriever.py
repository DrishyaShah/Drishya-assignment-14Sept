"""Retriever: embeddings + Chroma vectorstore setup."""
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# from src.config import CHROMA_PERSIST_DIR
import logging
import pandas as pd
import os 
from langchain_community.document_loaders import DataFrameLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2") 
persist_dir = "./chroma_atlan"

# ----FOR LOCAL------
# if not os.path.exists(persist_dir) or not os.listdir(persist_dir):
#     df = pd.read_csv(os.path.join(os.path.dirname(__file__), "atlan_docs_cleaned.csv"))
#     #Fill NaN with empty string
#     df["content"] = df["content"].fillna("")

#     #drop rows with empty content
#     df = df[df["content"].str.strip() != ""]


#     loader = DataFrameLoader(df, page_content_column="content")
#     docs = loader.load()
#     for i, doc in enumerate(docs):
#         doc.metadata["url"] = df.iloc[i]["url"]
#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=800,
#         chunk_overlap=150
#     )
#     chunks = splitter.split_documents(docs) 

#     persist_dir = "./chroma_atlan"
#     vectordb = Chroma.from_documents(
#         documents=chunks,
#         embedding=embeddings,
#         persist_directory=persist_dir
#     )
#     vectordb.persist()
#     print(f"Loaded {len(chunks)} chunks into Chroma")

# -----FOR CLOUD--------
if not os.path.exists(persist_dir) or not os.listdir(persist_dir):
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "atlan_docs_cleaned.csv"))
    #Fill NaN with empty string
    df["content"] = df["content"].fillna("")

    #drop rows with empty content
    df = df[df["content"].str.strip() != ""]


    loader = DataFrameLoader(df, page_content_column="content")
    docs = loader.load()
    for i, doc in enumerate(docs):
        doc.metadata["url"] = df.iloc[i]["url"]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )
    chunks = splitter.split_documents(docs) 

    persist_dir = "./chroma_atlan"
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
        client_settings={"chroma_db_impl": "duckdb+parquet"}
    )
    vectordb.persist()
    print(f"Loaded {len(chunks)} chunks into Chroma")

#FOR LOCAL 
# vectordb = Chroma(persist_directory=persist_dir, embedding_function=embeddings) 

#FOR CLOUD
vectordb = Chroma(
    persist_directory=persist_dir,
    embedding_function=embeddings,
    client_settings={"chroma_db_impl": "duckdb+parquet"}  # key change
)





retriever = vectordb.as_retriever(search_kwargs={"k": 3})




def get_docs(query: str):
    return retriever.get_relevant_documents(query)