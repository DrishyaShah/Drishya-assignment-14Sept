"""Ticket creation and subject-generation logic."""
import uuid
import logging
from src.llm import safe_invoke_text
from src.db import insert_ticket


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def generate_subject_from_query(query: str) -> str:
    prompt = f"""
Generate a **single-line** concise ticket subject based on this user query:


{query}


Do NOT provide multiple options, just one short, descriptive line.
"""
    result = safe_invoke_text(prompt)
    if not result:
        return "Support request"
# Some LLM responses are objects; be defensive
    text = getattr(result, "content", None) or str(result)
    return text.strip().split("\n")[0][:200] 


def create_ticket(state: dict) -> dict:
    """Create ticket record from `state`. Returns updated state with ticket info.


    Expects state to possibly contain structured objects in fields like 'topic', 'sentiment', 'priority'.
    """
    ticket_id = str(uuid.uuid4())[:10]


    user_query = state.get("message", "No query provided.")


# Safely extract labels (works for pydantic models or dicts)
    def get_label(obj, default="Unknown"):
        if obj is None:
            return default
        if hasattr(obj, "label"):
            return getattr(obj, "label")
        if isinstance(obj, dict) and "label" in obj:
            return obj["label"]
        return default


    topic = get_label(state.get("topic"), "General")
    sentiment = get_label(state.get("sentiment"), "Neutral")
    priority = get_label(state.get("priority"), "P2")


    subject = generate_subject_from_query(user_query)


    display_id = insert_ticket(ticket_id, topic, user_query, sentiment, priority, subject)
    if not display_id:
# DB insert failed — return failure message in state
        state["answer"] = "Sorry — failed to create ticket due to a server error."
        logger.error("Ticket creation failed for %s", ticket_id)
        return state


# Populate user-facing fields
    state.update(
    {
    "ticket_id": ticket_id,
    "ticket_topic": topic,
    "ticket_query": user_query,
    "ticket_sentiment": sentiment,
    "ticket_priority": priority,
    "ticket_subject": subject,
    "ticket_message": (
        f" **Ticket Created**\n\n"
        f"**ID:** {display_id}\n\n"
        f"**Topic:** {topic}\n\n"
        f"**Query:** {user_query}\n\n"
        f"**Priority:** {priority}\n\n"
        "This ticket has been routed to the appropriate support team."
    ),
    }
    )


    return state
