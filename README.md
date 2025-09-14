# Local Setup Instructions

## Prerequisites

- Python 3.12 recommended
- [pip](https://pip.pypa.io/en/stable/)
- (Optional) [virtualenv](https://virtualenv.pypa.io/en/latest/) for isolated environments

## 1. Clone the Repository

```sh
git clone https://github.com/DrishyaShah/Drishya-assignment-14Sept.git
cd Drishya_assignment_Sept2025
```

## 2. Create and Activate Virtual Environment (Recommended)

```sh
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

## 3. Install Dependencies

```sh
pip install -r requirements.txt
```

## 4. Environment Variables


- Create a `.env` file and add necessary keys (API keys, DB paths, etc).

## 5. Database Setup

- The project uses a local SQLite database at `chroma_atlan/chroma.sqlite3`.
- The project also uses a Supabase PostgreSQL databsase for storing tickets. The schema is given in db.py file. 

## 6. Run Main Application

```sh
streamlit run main.py
```

## 7. Streamlit Apps

To run the agent or dashboard UI:

```sh
streamlit run apps/streamlit_agent.py
# or
streamlit run apps/streamlit_dashboard.py
```

## 8. Development Workflow

- Source code is in [`src/`](src/)
- For workflow logic, see [`src/workflow.py`](src/workflow.py)
- For LLM config, see [`src/llm.py`](src/llm.py)
- For retrieval, see [`src/retriever.py`](src/retriever.py)



## 9. Troubleshooting

- Ensure all environment variables are set.
- Check `requirements.txt` for missing packages.
- For DB issues, verify `chroma_atlan/chroma.sqlite3` exists and is accessible.

---
