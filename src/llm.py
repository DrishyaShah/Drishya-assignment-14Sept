from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import GOOGLE_API_KEY
from src.schemas import TopicSchema, SentimentSchema, PrioritySchema, EscalationSchema
import logging 

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY) 

# Structured-output variants
topic_llm = llm.with_structured_output(TopicSchema)
sentiment_llm = llm.with_structured_output(SentimentSchema)
priority_llm = llm.with_structured_output(PrioritySchema)
escalation_llm = llm.with_structured_output(EscalationSchema) 

def safe_invoke_structured(llm_structured, prompt: str):
    """Invoke a structured-output LLM wrapper and guard against exceptions.


    Returns the structured object on success or None on failure.
    """
    try:
        return llm_structured.invoke(prompt)
    except Exception as e:
        logger.exception("LLM invocation failed: %s", e)
        return None 
    

def safe_invoke_text(prompt: str):
    try:
        return llm.invoke(prompt)
    except Exception as e:
        logger.exception("LLM text invoke failed: %s", e)
        return None