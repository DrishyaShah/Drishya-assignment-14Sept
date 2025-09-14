from typing import Literal, Optional
from pydantic import BaseModel

class TopicSchema(BaseModel):
    label: Literal["How-to","Product","Connector","Lineage","API/SDK",
                   "SSO","Glossary","Best practices","Sensitive data",
                   "unclear","out_of_scope"]
    

class SentimentSchema(BaseModel):
    label: Literal["Frustrated", "Neutral", "Curious", "Angry"]
    

class PrioritySchema(BaseModel):
    label: Literal["P0", "P1", "P2"]
    

class EscalationSchema(BaseModel):
    escalate: bool
    explanation: str

#Can add confidence/explanation outputs if required for debugging or transparency