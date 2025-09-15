# Customer Support Copilot — Atlan Assignment

## Overview
This project implements a **Customer Support Copilot** to streamline support operations using:
- An **interactive agent** for answering queries with citations.  
- Automated ticket **classification (Topic, Sentiment, Priority)**
- **Retrieval-Augmented Generation (RAG)** grounded in Atlan Docs & Developer Hub
- **Smart escalation** when documentation is insufficient
- **Dashboards** for monitoring classification, routing, and triage performance

  **Note**: For simplicity, both the **dashboard** and the **interactive agent** are packaged in the same Streamlit application. In a real-world deployment:  
- These would likely be **separate services** (agent for end-users, dashboard for internal staff).  
- The **dashboard** would be restricted to **admins or support leads** via authentication and role-based access.  


The solution was built with **Streamlit** for the UI, **Google Gemini 2.5 Flash** for language processing, and **Chroma Vector DB** for semantic retrieval. Ticket persistence is managed using **Supabase (Postgres)**.

---

## Problem Statement & Objective
Support teams face:
- Mounting response delays as organizations scale  
- High volume of repetitive questions  
- Inefficient routing impacting customer satisfaction  

**Objectives of the Copilot:**
- Classify support tickets automatically by topic, sentiment, and priority  
- Generate knowledge-grounded answers from Atlan Docs & Developer Hub  
- Auto-raise tickets when answers are incomplete/unavailable  
- Provide dashboards for continuous monitoring and improvement  

---

##  High-Level Architecture

![System Architecture](https://github.com/DrishyaShah/Drishya-assignment-14Sept/blob/main/atlan_customer_support_architecture.png)
![Workflow Diagram](https://github.com/DrishyaShah/Drishya-assignment-14Sept/blob/main/atlan_customer_support_workflow.png)

### 1. Ingestion & Knowledge Base
- Crawl docs via sitemap → clean HTML → normalize formatting  
- Chunk text with **RecursiveCharacterTextSplitter** (~800 tokens, 150 overlap)  
- Embed chunks (`all-MiniLM-L6-v2`) → stored in **Chroma Vector DB**  
- Metadata includes source URL + chunk ID for traceability  

### 2. Orchestration Layer (LangGraph)
- **Input Node**: Accepts queries or sample tickets  
- **RAG Node**: Retrieves + grounds answers in documentation  
- **Classifier Nodes**: Topic, Sentiment, Priority (parallel execution)  
- **Ticket Creation Node**: Stores enriched tickets in Postgres  

### 3. Retrieval-Augmented Generation (RAG)
- Retriever: Chroma returns top-3 chunks  
- Gemini 2.5 Flash → outputs:
  - JSON (topic, sentiment, priority, citations)  
  - Natural language answer with sources  
- Few-shot + structured output prompts for consistency  

### 4. Dashboard & UI (Streamlit)
- **Interactive Chat UI**: Agent view with classification inline + sources cited  
- **Bulk Dashboard**: Classifies sample tickets on load  
- **Analytics**: Pie charts, heatmaps, KPIs for volume, priority, sentiment  

---

## Technology Stack & Design Decisions
- **Framework:** LangGraph (workflow orchestration, state management)  
- **LLM:** Google Gemini 2.5 Flash (fast, cost-effective, structured outputs)  
- **Vector DB:** Chroma + HuggingFace embeddings (lightweight, no vendor lock-in)  
- **Frontend:** Streamlit (rapid prototyping, deployment-ready)  
- **Database:** Supabase (Postgres) for reliable ticket persistence  

---

## Project Structure
```
Drishya_assignment_Sept2025/
├── apps/
│   ├── streamlit_agent.py       # Interactive AI agent
│   └── streamlit_dashboard.py   # Ticket analytics dashboard
├── src/
│   ├── workflow.py              # LangGraph orchestration
│   ├── llm.py                   # Gemini client + structured outputs
│   ├── retriever.py             # RAG pipeline
│   ├── ticketing.py             # Ticket creation logic
│   ├── db.py                    # Database models
│   ├── scraping.py              # Sitemap scraping
│   ├── schemas.py               # Pydantic models
│   └── config.py                # Config management
├── main.py                      # App entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment config
└── README.md
```

---

## Classification Schema
- **Topic Tags:** How-to, Product, Connector, Lineage, API/SDK, SSO, Glossary, Best practices, Sensitive data  
- **Sentiment:** Frustrated, Curious, Angry, Neutral  
- **Priority:** P0 (High), P1 (Medium), P2 (Low)  

---

## RAG Strategy & Guardrails
- Retrieval: top-3 chunks, cosine similarity scoring  
- Sources restricted to `docs.atlan.com` & `developer.atlan.com`  
- Answering: model must cite URLs + chunk IDs  
- Guardrails:
  - “Answer only from provided context”  
  - If insufficient → refuse & route ticket  
  - Confidence score + CTA: *“Not satisfied? Raise ticket”*  

---

##  Ticketing, Routing & Dashboard
- Auto-raise ticket when no context retrieved or user dissatisfied  
- Store metadata in Postgres (topic, sentiment, priority, squad)  
- **KPIs visualized:**
  - Distribution of topics  
  - Ticket inflow  
  - Sentiment heatmap  
  

---

##  Deliverables
- **Live App:** [https://drishya-assignment-14sept-fktnrf58tr7wqbq2gnm4zx.streamlit.app/]
- **Code Repo:** [https://github.com/DrishyaShah/Drishya-assignment-14Sept]  
- **README:** [https://github.com/DrishyaShah/Drishya-assignment-14Sept/blob/main/README.md]

---

##  Known Limitations & Next Steps
### Current Limitations
- **Latency**: The current RAG + classification pipeline can introduce noticeable response delays, especially under high load or when multiple retrievals are required.
- **Rate Limits**: The deployed solution depends on the Gemini API, which enforces strict quota and rate limits. This can lead to request failures or throttling during peak usage.
- **Single Model Dependency**: All classification and generation tasks rely on Gemini. Outages, quota exhaustion, or degraded performance directly affect system reliability.
- **Scalability Constraints**: The system currently runs on a single Streamlit instance, which may not scale well under concurrent traffic.
- **Evaluation Coverage**: While manual review of sample tickets to assess classification of topic, sentiment and priority along with citation checks is done, continuous automated evaluation for drift and hallucinations is limited.
- **Security/Access Controls**: Role-based access and SSO for internal agents are not yet implemented.
- **Caching**: Current caching strategy is minimal; repeat queries may still incur full retrieval and generation cost.
- **VectorDB Persistence**: On the first run of the deployed app, embeddings are generated and stored locally in a Chroma `persist_directory`. On subsequent runs, the persisted store is reused. However, this approach ties persistence to the container filesystem, which may not be reliable across deployments. A better approach would be:  
  - Store persisted embeddings in external cloud storage (e.g., AWS S3, GCP Cloud Storage).  
  - Or switch to a managed cloud vector database (e.g., Pinecone, Weaviate, Qdrant Cloud) for durability and scalability.  

### Next Steps
- **Latency Optimizations**: 
  - Introduce semantic caching for common queries.  
  - Explore hybrid retrieval (BM25 + embeddings) to reduce over-fetching.  
  - Parallelize retrieval and classification workflows where possible.
- **Mitigating Rate Limits**: 
  - Add exponential backoff, retries, and request batching.  
  - Evaluate introducing a lightweight fallback model (e.g., local LLM) for classification-only tasks.
- **Multi-Model Strategy**: 
  - Split workloads (e.g., classification via lightweight models, generation via Gemini).  
  - Considering multiple task specific models to avoid single-point dependency.
- **Scalability**: 
  - Containerize the backend for deployment on cloud platform.  
  - Add autoscaling for high-traffic scenarios.
- **Enhanced Evaluation**: 
  - Build an automated evaluation harness with golden-set queries.  
  - Track hallucination rate, latency breakdowns, and escalation accuracy over time.
  - Add feedback-driven improvements (prompt tuning, error logging, user feedback loop).  
- **Security & Access**: 
  - Integrate SSO and role-based access control for support agents.  
  - Expand PII handling (masking, redaction in retrieval logs).

---


## Local Setup Instructions

### Prerequisites

- Python 3.12 recommended
- [pip](https://pip.pypa.io/en/stable/)
- (Optional) [virtualenv](https://virtualenv.pypa.io/en/latest/) for isolated environments

### 1. Clone the Repository

```sh
git clone https://github.com/DrishyaShah/Drishya-assignment-14Sept.git
cd Drishya_assignment_Sept2025
```

### 2. Create and Activate Virtual Environment (Recommended)

```sh
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

### 4. Environment Variables


- Create a `.env` file and add necessary keys (API keys, DB paths, etc).
#### Sample `.env` file:

```bash
# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here

# Database (PostgreSQL via Supabase)
user=your_db_username
password=your_db_password
host=your_db_host
port=6543
dbname=your_db_name
```

### 5. Database Setup

- The project uses a local SQLite database at `chroma_atlan/chroma.sqlite3`.
- The project also uses a Supabase PostgreSQL databsase for storing tickets. The schema is given in db.py file. 

### 6. Run Main Application

```sh
streamlit run main.py
```

### 7. Streamlit Apps

To run the agent or dashboard UI:

```sh
streamlit run apps/streamlit_agent.py
# or
streamlit run apps/streamlit_dashboard.py
```

### 8. Development Workflow

- Source code is in [`src/`](src/)
- For workflow logic, see [`src/workflow.py`](src/workflow.py)
- For LLM config, see [`src/llm.py`](src/llm.py)
- For retrieval, see [`src/retriever.py`](src/retriever.py)



### 9. Troubleshooting

- Ensure all environment variables are set.
- Check `requirements.txt` for missing packages.
- For DB issues, verify `chroma_atlan/chroma.sqlite3` exists and is accessible.


##  Author
Assignment submission by **Drishya Shah**

---
