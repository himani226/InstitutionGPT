from __future__ import annotations
from pydantic import BaseModel, Field
from typing   import Optional


class ChatRequest(BaseModel):
    query:      str  = Field(..., min_length=3, max_length=1000)
    role:       str  = Field("student", description="student | faculty | admin | general")
    session_id: Optional[str]  = Field(None,  description="Omit to start a new session")
    debug:      bool = Field(False, description="Include routing scores in response")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "query":      "What is the last date to apply for B.Tech?",
                "role":       "student",
                "session_id": None,
                "debug":      False,
            }]
        }
    }


class RoutingInfo(BaseModel):
    agent:      str
    score:      float
    allowed:    list[str]
    all_scores: dict[str, float]


class ChatResponse(BaseModel):
    answer:     str
    agent:      str
    sources:    list[str]
    role:       str
    session_id: str
    routing:    Optional[RoutingInfo] = None   # only when debug=True


class AgentInfo(BaseModel):
    key:           str
    name:          str
    description:   str
    accessible_by: list[str]


class HealthResponse(BaseModel):
    status:        str
    version:       str
    models_loaded: bool
    chunks_in_db:  int
    message:       str