"""
src/workflow.py

Complete LangGraph StateGraph assembly for the Atlan AI support agent.

This file defines:
- AgentState typed dict
- Node functions used in the workflow
- Graph construction and compilation to produce `workflow`
"""

from typing import TypedDict, List, Optional, Any, Dict
import logging
import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA 
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document

# Local modules
from src.schemas import TopicSchema, SentimentSchema, PrioritySchema
from src.llm import (
    safe_invoke_structured,
    safe_invoke_text,
    topic_llm,
    sentiment_llm,
    priority_llm,
    escalation_llm,
    # llm is available inside safe_invoke_text results when needed by RetrievalQA creation
)
from src.retriever import retriever
from src.ticketing import create_ticket as ticketing_create_ticket

# If your project exposes a top-level llm instance (used by RetrievalQA) you can import it:
from src.llm import llm as llm_instance

# Optional: import Document type for typing convenience (if available in your langchain variant)
try:
    from langchain_core.documents import Document  # type: ignore
except Exception:
    Document = dict  # fallback typing

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# -----------------------------------------------------------------------------
# AgentState
# -----------------------------------------------------------------------------
class AgentState(TypedDict, total=False):
    message: str
    topic: Optional[TopicSchema]
    sentiment: Optional[SentimentSchema]
    priority: Optional[PrioritySchema]
    docs: Optional[List[Document]]
    answer: Optional[str]
    is_topic_valid: Optional[bool]
    ticket_id: Optional[str]
    ticket_topic: Optional[str]
    ticket_subject: Optional[str]
    ticket_query: Optional[str]
    ticket_sentiment: Optional[str]
    ticket_priority: Optional[str]
    needs_ticket_offer: Optional[bool]
    escalation_reason: Optional[str]
    ticket_message: str


# -----------------------------------------------------------------------------
# Node functions
# -----------------------------------------------------------------------------
def sentiment_analysis(state: AgentState) -> AgentState:
    """
    Run sentiment classification using the structured-output LLM wrapper.
    Returns a partial state with 'sentiment' key when successful.
    """
    message = state.get("message", "")
    if not message:
        return {}

    prompt = f"""
You are a sentiment classifier for Atlan customer support queries.

Label the sentiment of the following user message:
- Frustrated: user is annoyed but not hostile
- Neutral: user is calm, not emotional
- Curious: user is asking questions with interest
- Angry: user is angry, rude, or aggressive

User message: \"{message}\"
"""
    result = safe_invoke_structured(sentiment_llm, prompt)
    if result:
        return {"sentiment": result}
    logger.warning("sentiment_analysis returned no result")
    return {}


def topic_classification(state: AgentState) -> AgentState:
    """
    Classify topic using structured-output LLM.
    """
    message = state.get("message", "")
    if not message:
        return {}

    prompt = f"""
You are a classifier for Atlan customer support queries.

Classify the following user message into one of these topics:
- How-to: step-by-step usage questions
- Product: general product questions / features
- Connector: integration issues
- Lineage: data lineage-related queries
- API/SDK: programmatic usage
- SSO: authentication / login issues
- Glossary: terminology, business metadata
- Best practices: recommended usage patterns
- Sensitive data: compliance, governance
- unclear: insufficient information to classify
- out_of_scope: irrelevant to Atlan

User message: \"{message}\"
"""
    result = safe_invoke_structured(topic_llm, prompt)
    if result:
        return {"topic": result}
    logger.warning("topic_classification returned no result")
    return {}


def priority_classification(state: AgentState) -> AgentState:
    """
    Classify support priority using structured-output LLM.
    """
    message = state.get("message", "")
    if not message:
        return {}

    prompt = f"""
You are a support priority classifier for Atlan customer support queries.

Classify the urgency level:
- P0 (High): blocking issue, critical failure, user/team cannot proceed
- P1 (Medium): important issue but there is a workaround
- P2 (Low): minor inconvenience, cosmetic, general query

User message: \"{message}\"
"""
    result = safe_invoke_structured(priority_llm, prompt)
    if result:
        return {"priority": result}
    logger.warning("priority_classification returned no result")
    return {}


def validate_topic(state: AgentState) -> AgentState:
    """
    Decide whether the topic is suitable for the RAG pipeline (i.e., handled via docs)
    or needs manual ticketing / escalation (e.g., unclear / out_of_scope).
    """
    valid_topics = {"How-to", "Product", "Best practices", "API/SDK", "SSO"}
    topic_obj = state.get("topic", "")

    # Extract a label robustly from pydantic object/dict/string
    if hasattr(topic_obj, "label"):
        topic_label = getattr(topic_obj, "label")
    elif isinstance(topic_obj, dict) and "label" in topic_obj:
        topic_label = topic_obj["label"]
    else:
        topic_label = str(topic_obj)

    is_valid = topic_label in valid_topics
    return {"is_topic_valid": is_valid}


def retrieve_docs(state: AgentState) -> AgentState:
    """
    Use the vector retriever to fetch relevant documents for the user's message.
    """
    message = state.get("message", "")
    if not message:
        return {}

    try:
        docs = retriever.get_relevant_documents(message)
        return {"docs": docs}
    except Exception as e:
        logger.exception("retrieve_docs failed: %s", e)
        return {"docs": []}


def generate_answer(state: AgentState) -> AgentState:
    message = state.get("message", "")
    if not message:
        return {"answer": "No message provided."}

    template = """You are an Atlan customer support assistant. 
Your role is to help users by answering questions clearly, accurately, 
and in a friendly manner using the provided documentation.
Guidelines:
- Use ONLY the provided context to answer. Do not invent features or details not present in the context.
- If the answer is not in the context, politely say you don’t know and suggest contacting Atlan support.
- Give answers in a helpful, step-by-step format when explaining workflows.
- Keep the tone professional, approachable, and concise.

Context:
{context}

Question:
{question}

Answer:"""
    prompt = PromptTemplate(template=template, input_variables=[ "question", "context"])

    try:
        # New style: build doc chain
        qa = RetrievalQA.from_chain_type(llm=llm_instance, 
        retriever=retriever, 
        chain_type="stuff",
        return_source_documents=True, 
        chain_type_kwargs={"prompt": prompt}, 
        )

        result = qa({"query":message})
        answer_text = result.get("result", "")
        docs = result.get("source_documents", [])

        escalation_prompt = f"""
You are an Atlan support supervisor AI. Review the assistant's answer and decide if it should be escalated.

Answer:
{answer_text}

Escalate (True) if:
- Documentation is missing.
- The answer says to contact Atlan support.
- The question is unclear or out of scope.
- The problem is not fully solved.

Do NOT escalate (False) if the answer is clear, complete, and actionable.
"""
        escalation_result = safe_invoke_structured(escalation_llm, escalation_prompt)

        needs_ticket_offer = False
        escalation_reason = ""
        if escalation_result:
            needs_ticket_offer = getattr(escalation_result, "escalate", False)
            escalation_reason = getattr(escalation_result, "explanation", "")

        return {
            "answer": answer_text,
            "docs": docs,
            "needs_ticket_offer": needs_ticket_offer,
            "escalation_reason": escalation_reason,
        }

    except Exception as e:
        logger.exception("generate_answer failed: %s", e)
        return {"answer": "Sorry, I couldn't generate an answer right now. Please try again later."}


def create_ticket_node(state: AgentState) -> AgentState:
    """
    Node wrapper that calls the ticketing.create_ticket function.
    Accepts partial state and returns an updated state (with ticket fields).
    """
    try:
        updated_state = ticketing_create_ticket(dict(state))
        # ticketing.create_ticket returns the updated state; ensure dict type
        return dict(updated_state)
    except Exception as e:
        logger.exception("create_ticket_node failed: %s", e)
        # Return a state with an error answer so UI can show the failure
        return {"answer": "Failed to create ticket due to server error."}


# -----------------------------------------------------------------------------
# Graph assembly
# -----------------------------------------------------------------------------
memory = MemorySaver()
graph = StateGraph(AgentState)

# Register nodes
graph.add_node("sentiment_analysis", sentiment_analysis)
graph.add_node("topic_classification", topic_classification)
graph.add_node("priority_classification", priority_classification)
graph.add_node("validate_topic", validate_topic)
graph.add_node("retrieve_docs", retrieve_docs)
graph.add_node("generate_answer", generate_answer)
graph.add_node("create_ticket", create_ticket_node)

# Add edges
graph.add_edge(START, "sentiment_analysis")
graph.add_edge(START, "topic_classification")
graph.add_edge(START, "priority_classification")

graph.add_edge("topic_classification", "validate_topic")
graph.add_edge("sentiment_analysis", "validate_topic")
graph.add_edge("priority_classification", "validate_topic")

# Conditional routing: valid -> retrieve_docs ; invalid -> create_ticket
def routing_function(state: AgentState) -> str:
    return "valid" if state.get("is_topic_valid") else "invalid"

graph.add_conditional_edges(
    source="validate_topic",
    path=routing_function,
    path_map={"valid": "retrieve_docs", "invalid": "create_ticket"},
)

graph.add_edge("retrieve_docs", "generate_answer")
graph.add_edge("create_ticket", END)
graph.add_edge("generate_answer", END)

# Compile workflow (exposed variable)
workflow = graph.compile(checkpointer=memory)


# Optional helper: convenience wrapper to run the workflow with a message

def run_workflow_for_message(message: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience helper to invoke the compiled workflow with a simple message.
    Returns the resulting state as a dict.
    """
    inputs = {"message": message}
    if config:
        result = workflow.invoke(inputs, config=config)
    else:
        result = workflow.invoke(inputs)
    # Ensure a plain dict is returned
    return dict(result) if not isinstance(result, dict) else result
