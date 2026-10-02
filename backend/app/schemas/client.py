from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

EMAIL_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class ClientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Full client name or organization name")
    email: str = Field(..., pattern=EMAIL_PATTERN, description="Client primary contact email address")
    phone: Optional[str] = Field(None, max_length=50, description="Client telephone/mobile number")
    company: Optional[str] = Field(None, max_length=150, description="Company or business name")
    address: Optional[str] = Field(None, max_length=300, description="Physical / billing address")
    notes: Optional[str] = Field(None, max_length=2000, description="Operational notes or customer comments")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom key-value metadata attributes")


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    email: Optional[str] = Field(None, pattern=EMAIL_PATTERN)
    phone: Optional[str] = Field(None, max_length=50)
    company: Optional[str] = Field(None, max_length=150)
    address: Optional[str] = Field(None, max_length=300)
    notes: Optional[str] = Field(None, max_length=2000)
    metadata: Optional[Dict[str, Any]] = None


class ClientResponse(ClientBase):
    id: str = Field(..., description="MongoDB string representation of ObjectId")
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = Field(None, description="Username of EdgeStore operator who created the record")


class ClientListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[ClientResponse]
