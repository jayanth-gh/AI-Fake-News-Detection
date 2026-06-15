from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class PredictionRequest(BaseModel):
    text: str

class SourceItem(BaseModel):
    title: str
    url: str
    stance: str
    domain: Optional[str] = None
    weight: Optional[float] = None
    prediction: Optional[str] = None

class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    reasoning: str
    sources: List[SourceItem]
    result: Optional[str] = None

class HistoryItem(BaseModel):
    id: int
    text: str
    prediction: str
    confidence: float
    timestamp: datetime

    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_predictions: int
    fake_count: int
    real_count: int

class LinkPredictionRequest(BaseModel):
    url: str

class LinkPredictionResponse(BaseModel):
    result: str
    confidence: float
    original_url: str
    expanded_url: str
    domain: str
    flags: List[str]
    sources_used: List[SourceItem]
