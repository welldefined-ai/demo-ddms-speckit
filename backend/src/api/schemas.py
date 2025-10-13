"""
Pydantic request/response schemas per OpenAPI spec
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum


# Enums
class UserRoleSchema(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    READ_ONLY = "read_only"


class DeviceStatusSchema(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    language_preference: str = Field(default="en", regex="^(en|zh)$")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRoleSchema


class UserResponse(UserBase):
    id: UUID
    role: UserRoleSchema
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Device Schemas
class DeviceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    modbus_ip: str
    modbus_port: int = Field(default=502, ge=1, le=65535)
    modbus_slave_id: int = Field(..., ge=1, le=247)
    modbus_register: int = Field(..., ge=0)
    modbus_register_count: int = Field(default=1, ge=1)
    unit: str = Field(..., max_length=20)
    sampling_interval: int = Field(..., ge=1)
    threshold_warning_lower: Optional[float] = None
    threshold_warning_upper: Optional[float] = None
    threshold_critical_lower: Optional[float] = None
    threshold_critical_upper: Optional[float] = None
    retention_days: int = Field(default=90, ge=1)

    @validator('threshold_warning_upper')
    def validate_warning_thresholds(cls, v, values):
        if v is not None and 'threshold_warning_lower' in values:
            lower = values['threshold_warning_lower']
            if lower is not None and v <= lower:
                raise ValueError('threshold_warning_upper must be greater than threshold_warning_lower')
        return v


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    modbus_ip: Optional[str] = None
    modbus_port: Optional[int] = Field(None, ge=1, le=65535)
    modbus_slave_id: Optional[int] = Field(None, ge=1, le=247)
    modbus_register: Optional[int] = Field(None, ge=0)
    modbus_register_count: Optional[int] = Field(None, ge=1)
    unit: Optional[str] = Field(None, max_length=20)
    sampling_interval: Optional[int] = Field(None, ge=1)
    threshold_warning_lower: Optional[float] = None
    threshold_warning_upper: Optional[float] = None
    threshold_critical_lower: Optional[float] = None
    threshold_critical_upper: Optional[float] = None
    retention_days: Optional[int] = Field(None, ge=1)


class DeviceResponse(DeviceBase):
    id: UUID
    status: DeviceStatusSchema
    last_reading_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Reading Schemas
class ReadingBase(BaseModel):
    timestamp: datetime
    value: float


class ReadingResponse(ReadingBase):
    device_id: UUID

    class Config:
        from_attributes = True


class LatestReadingResponse(ReadingResponse):
    device_name: str
    unit: str
    status: str  # normal, warning, critical


# Group Schemas
class GroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    device_ids: Optional[List[UUID]] = None


class GroupResponse(GroupBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    device_count: int = 0

    class Config:
        from_attributes = True


# Configuration Schemas
class ConfigurationBase(BaseModel):
    system_name: str = Field(..., max_length=100)
    data_retention_days_default: int = Field(..., ge=1)
    backup_enabled: bool
    backup_schedule: str = Field(..., max_length=100)


class ConfigurationUpdate(BaseModel):
    system_name: Optional[str] = Field(None, max_length=100)
    data_retention_days_default: Optional[int] = Field(None, ge=1)
    backup_enabled: Optional[bool] = None
    backup_schedule: Optional[str] = Field(None, max_length=100)


class ConfigurationResponse(ConfigurationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Health Check Schema
class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime
