import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import uuid
import logging
from typing import Any, Dict

import streamlit as st

# Backend modules
from src.workflow import workflow  # compiled LangGraph workflow
from src.ticketing import create_ticket as create_ticket_fn

# Configure logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())  


def app():
    st.set_page_config(page_title="Atlan Support Agent", layout="wide")


    def _safe_label(val: Any, default: str = "N/A") -> str:
        """Return label from pydantic-like object/dict/string safely."""
        if val is None:
            return default
        if hasattr(val, "label"):
            return getattr(val, "label")
        if isinstance(val, dict) and "label" in val:
            return val["label"]
        return str(val)

    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = str(uuid.uuid4())

    def _run_workflow(message: str) -> Dict[str, Any]:
        """Invoke the LangGraph workflow and return a plain dict state."""
        inputs = {"message": message}
        config = {"configurable": {"thread_id": st.session_state["thread_id"]}}
        try:
            result = workflow.invoke(inputs, config=config)
            return dict(result) if not isinstance(result, dict) else result
        except Exception as e:
            logger.exception("Workflow invocation failed: %s", e)
            return {"answer": "Internal error: failed to run assistant."}


    # --- Header ---
    st.markdown(
        """
        <h2 style="text-align:center; margin-bottom:0;">🤖 Atlan AI Support Agent</h2>
        <p style="text-align:center; color:gray; margin-top:4px;">
        Ask a question — the assistant will answer or offer to raise a ticket.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Initialize session-state keys
    if "state" not in st.session_state:
        st.session_state["state"] = {}
    if "ticket_saved" not in st.session_state:
        st.session_state["ticket_saved"] = False
    if "user_input" not in st.session_state:
        st.session_state["user_input"] = ""
    if "should_rerun" not in st.session_state:
        st.session_state["should_rerun"]= False

    def clear_form():
        st.session_state["state"] = {}
        st.session_state["ticket_saved"] = False
        st.session_state["user_input"] = ""
        st.session_state["should_rerun"] = True
        

    # --- Input area ---
    user_input = st.text_area(
        "Your message",
        placeholder="How do I set up SSO with Atlan?",
        height=140,
        key="user_input",
    )

    col_run, col_clear, _ = st.columns([1, 1, 6])
    with col_run:
        run = st.button("Submit", type="primary")
    with col_clear:
        clear = st.button("Clear", on_click=clear_form)

    if st.session_state.get("should_rerun"):
        st.session_state.pop("should_rerun")  # remove flag
        st.rerun()



    if run:
        if not user_input or not user_input.strip():
            st.warning("Please enter a message before submitting.")
        else:
            with st.spinner("⚡ Running AI workflow..."):
                state = _run_workflow(user_input.strip())
                st.session_state["state"] = state
                st.session_state["ticket_saved"] = False

    # --- Results ---
    state = st.session_state.get("state", {})

    if state.get("answer"):
        # Two-column layout: answer | sources
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Answer")
            st.info(state.get("answer", "No answer generated."))

            # If there are follow-up suggestions or explanation show them
            if state.get("escalation_reason"):
                st.caption(f"Escalation note: {state.get('escalation_reason')}")

        with col2:
            st.subheader("Sources")
            if state.get("docs"):
                seen = set()
                for doc in state["docs"]:
                    url = None
                    try:
                        metadata = getattr(doc, "metadata", {}) or {}
                        url = metadata.get("url") or metadata.get("source")
                    except Exception:
                        url = None
                    if url and url not in seen:
                        seen.add(url)
                        st.markdown(f"- [{url}]({url})")
            else:
                st.write("No source documents found.")

        # Ticket flow
        if state.get("needs_ticket_offer"):
            st.warning("⚠️This issue may need escalation.")
            if not st.session_state.get("ticket_saved", False):
                if st.button("Raise Ticket", type="primary"):
                    with st.spinner("Creating ticket..."):
                        try:
                            new_state = create_ticket_fn(dict(state))
                            st.session_state["state"] = new_state
                            st.session_state["ticket_saved"] = True
                            st.success("Ticket created successfully.")
                        except Exception as e:
                            logger.exception("Ticket creation failed: %s", e)
                            st.error("Failed to create ticket. Try again later.")

        # Show created ticket details
        if st.session_state.get("ticket_saved"):
            s = st.session_state["state"]
            st.subheader("Ticket Created")
            st.write(f"**Subject:** {s.get('ticket_subject', 'N/A')}")
            st.write(f"**Topic:** {_safe_label(s.get('ticket_topic'))}")
            st.write(f"**Query:** {s.get('ticket_query', 'N/A')}")
            st.write(f"**Priority:** {_safe_label(s.get('ticket_priority'))}")
            st.write(f"**Sentiment:** {_safe_label(s.get('ticket_sentiment'))}")

        # Footer metrics
        st.markdown("---")
        col1m, col2m, col3m = st.columns(3)
        col1m.metric("Topic", _safe_label(state.get("topic", "N/A")))
        col2m.metric("Sentiment", _safe_label(state.get("sentiment", "N/A")))
        col3m.metric("Priority", _safe_label(state.get("priority", "N/A")))

    elif state.get("ticket_message"):
        st.subheader("Ticket Created")
        st.markdown(state["ticket_message"])
    else:
        st.info("Ask a question to get started.")
