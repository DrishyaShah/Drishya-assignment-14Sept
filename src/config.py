import os
from dotenv import load_dotenv

load_dotenv()

# Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Supabase/Postgres
DB_USER = os.getenv("user")
DB_PASSWORD = os.getenv("password")
DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port")
DB_NAME = os.getenv("dbname")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
)

# Chroma persistent directory (USE WHEN RUNNING THE CODE LOCALLY)
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_atlan")


# LangGraph settings
THREAD_ID = os.getenv("THREAD_ID", "demo-thread")