"""Retriever: embeddings + Chroma vectorstore setup."""
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
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
if not os.path.exists(persist_dir) or not os.listdir(persist_dir):
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "atlan_docs_cleaned.csv"))



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
        persist_directory=persist_dir
    )
    vectordb.persist()
    print(f"Loaded {len(chunks)} chunks into Chroma")

vectordb = Chroma(persist_directory=persist_dir, embedding_function=embeddings)





retriever = vectordb.as_retriever(search_kwargs={"k": 3})




def get_docs(query: str):
    return retriever.get_relevant_documents(query)