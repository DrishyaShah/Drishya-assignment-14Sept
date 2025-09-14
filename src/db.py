import logging
from sqlalchemy import create_engine, MetaData, Table, Column, String, Text, DateTime, Sequence
from sqlalchemy.sql import func, text
from src.config import DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL)
metadata = MetaData()

ticket_seq = Sequence("ticket_seq", start=1, increment=1)
tickets = Table(
    "tickets",
    metadata,
    Column("ticket_id", String, primary_key=True),
    Column("user_query", Text, nullable=False),
    Column("topic", String, nullable=False),
    Column("sentiment", String, nullable=False),
    Column("priority", String, nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("display_id", String, unique=True, server_default=("'TICKET-' || nextval('ticket_seq')")),
    Column("subject", Text, nullable=False),
)

def test_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("DB connection OK")
        return True
    except Exception as e:
        logger.error("DB connection failed: %s", e)
        return False

def insert_ticket(ticket_id, topic, query, sentiment, priority, subject):
    """Insert a ticket into the DB and return its display_id."""
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO tickets (ticket_id, topic, user_query, sentiment, priority, subject)
                    VALUES (:ticket_id, :topic, :query, :sentiment, :priority, :subject)
                    RETURNING display_id
                """),
                {
                    "ticket_id": ticket_id,
                    "topic": topic,
                    "query": query,
                    "sentiment": sentiment,
                    "priority": priority,
                    "subject": subject,
                },
            )
            return result.scalar_one()
    except Exception as e:
        logger.error(f"DB insert failed: {e}")
        return None
