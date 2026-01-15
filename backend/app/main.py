"""
Nexus - Neural Key Exchange API

FastAPI backend for Neural Network Encrypted Communication
"""

import uuid
import asyncio
import os
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .websocket.handler import manager, SyncSession
from .models.schemas import SessionCreate, SessionResponse, SessionStatus

app = FastAPI(
    title="Nexus",
    description="Neural Network Encrypted Communication",
    version="1.0.0"
)

# CORS configuration - supports both development and production
cors_origins_str = os.getenv("CORS_ORIGINS", "*")
cors_origins = cors_origins_str.split(",") if cors_origins_str != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Nexus",
        "version": "1.0.0",
        "description": "Neural Key Exchange Communication System",
        "status": "online"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_sessions": len(manager.sessions),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/sessions", response_model=SessionResponse)
async def create_session(config: SessionCreate = None):
    """
    Create a new synchronization session
    
    Returns a session ID that both parties can use to connect.
    """
    config = config or SessionCreate()
    session_id = str(uuid.uuid4())[:8]
    
    # Pre-create the session
    manager.sessions[session_id] = SyncSession(
        session_id=session_id,
        tpm_k=config.tpm_k,
        tpm_n=config.tpm_n,
        tpm_l=config.tpm_l
    )
    
    return SessionResponse(
        session_id=session_id,
        created_at=datetime.utcnow(),
        participant_count=0,
        is_synced=False,
        tpm_config={
            "K": config.tpm_k,
            "N": config.tpm_n,
            "L": config.tpm_l
        }
    )


@app.get("/sessions/{session_id}", response_model=SessionStatus)
async def get_session(session_id: str):
    """Get session status"""
    if session_id not in manager.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = manager.sessions[session_id]
    return SessionStatus(
        session_id=session_id,
        participants=list(session.participants.keys()),
        sync_state={
            "round": session.sync_round,
            "is_synced": session.is_synced
        },
        created_at=session.created_at
    )


@app.websocket("/ws/{session_id}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    session_id: str, 
    user_id: str,
    tpm_k: int = Query(default=3),
    tpm_n: int = Query(default=4),
    tpm_l: int = Query(default=3)
):
    """
    WebSocket endpoint for Neural Key Exchange
    
    Protocol:
    1. Connect with session_id and user_id
    2. Wait for partner to connect
    3. Sync starts automatically when both connected
    4. After sync, exchange encrypted messages
    """
    session = None
    try:
        session = await manager.connect(
            websocket, 
            session_id, 
            user_id,
            tpm_k=tpm_k,
            tpm_n=tpm_n,
            tpm_l=tpm_l
        )
        
        print(f"User {user_id} connected to session {session_id}, participants: {len(session.participants)}")
        
        # Start sync when both parties connected (as background task)
        if session.is_ready() and not session.is_synced and not session.is_syncing:
            print(f"Starting sync for session {session_id}")
            manager.start_sync_background(session)
        
        # Message handling loop with timeout to allow checking state
        while True:
            try:
                # Use wait_for with timeout so we can check connection state
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )
                
                if data.get("type") == "message":
                    # Relay encrypted message to others
                    await manager.relay_message(
                        session, 
                        user_id, 
                        data.get("ciphertext", "")
                    )
                
                elif data.get("type") == "request_sync":
                    # Manual sync request
                    if session.is_ready() and not session.is_synced and not session.is_syncing:
                        manager.start_sync_background(session)
                
                elif data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
    
    except WebSocketDisconnect:
        print(f"User {user_id} disconnected from session {session_id}")
    except ValueError as e:
        print(f"ValueError: {e}")
    except Exception as e:
        print(f"WebSocket error for {user_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if session:
            await manager.disconnect(session_id, user_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
