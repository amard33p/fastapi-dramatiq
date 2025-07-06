from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class AddressSchema(BaseModel):
    street: str
    suite: str
    city: str
    zipcode: str
    geo: Dict[str, str]


class CompanySchema(BaseModel):
    name: str
    catchPhrase: str
    bs: str


class UserCreate(BaseModel):
    name: str
    username: str
    email: EmailStr
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[AddressSchema] = None
    company: Optional[CompanySchema] = None


class UserResponse(BaseModel):
    id: int
    name: str
    username: str
    email: str
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    company: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobStatusResponse(BaseModel):
    id: UUID
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProcessUsersResponse(BaseModel):
    job_id: str
    message: str


class ExternalUser(BaseModel):
    """Schema for external API user data"""

    id: int
    name: str
    username: str
    email: str
    phone: str
    website: str
    address: AddressSchema
    company: CompanySchema
