"""
Pydantic schemas for API requests/responses and WebSocket messages
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# === WebSocket Message Types ===

class WSMessage(BaseModel):
    """Base WebSocket message"""
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SyncStartMessage(WSMessage):
    """Sent when both parties are connected and sync begins"""
    type: Literal["sync_start"] = "sync_start"
    session_id: str
    tpm_config: dict


class SyncProgressMessage(WSMessage):
    """Sent each synchronization round"""
    type: Literal["sync_progress"] = "sync_progress"
    round: int
    agreed: bool
    progress: float
    tau: int


class SyncCompleteMessage(WSMessage):
    """Sent when TPMs have synchronized"""
    type: Literal["sync_complete"] = "sync_complete"
    rounds: int
    key_fingerprint: str


class EncryptedMessage(WSMessage):
    """Encrypted chat message"""
    type: Literal["message"] = "message"
    sender_id: str
    ciphertext: str
    nonce: Optional[str] = None


class UserJoinedMessage(WSMessage):
    """Sent when a user joins the session"""
    type: Literal["user_joined"] = "user_joined"
    user_id: str
    participant_count: int


class UserLeftMessage(WSMessage):
    """Sent when a user leaves the session"""
    type: Literal["user_left"] = "user_left"
    user_id: str


class ErrorMessage(WSMessage):
    """Error notification"""
    type: Literal["error"] = "error"
    message: str
    code: Optional[str] = None


# === HTTP API Schemas ===

class SessionCreate(BaseModel):
    """Request to create a new session"""
    tpm_k: int = Field(default=3, ge=1, le=32, description="Hidden neurons")
    tpm_n: int = Field(default=4, ge=1, le=64, description="Inputs per neuron")
    tpm_l: int = Field(default=3, ge=1, le=10, description="Weight range")


class SessionResponse(BaseModel):
    """Session information response"""
    session_id: str
    created_at: datetime
    participant_count: int
    is_synced: bool
    tpm_config: dict


class SessionStatus(BaseModel):
    """Detailed session status"""
    session_id: str
    participants: list[str]
    sync_state: dict
    created_at: datetime
