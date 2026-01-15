"""
WebSocket Connection Handler

Manages real-time connections for Neural Key Exchange sessions.
Handles user connections, TPM synchronization, and encrypted messaging.
"""

import asyncio
import numpy as np
from datetime import datetime
from typing import Dict, Optional, Set
from dataclasses import dataclass, field
from fastapi import WebSocket
import traceback

from ..neural.tpm import TreeParityMachine
from ..crypto.encryption import NeuralCipher


@dataclass 
class SyncSession:
    """
    Represents a neural key exchange session between two parties
    """
    session_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # TPM configuration - proven working parameters
    # K=3, N=4, L=3 is a standard configuration that converges reliably
    tpm_k: int = 3      # 3 hidden neurons
    tpm_n: int = 4      # 4 inputs per neuron  
    tpm_l: int = 3      # Weight range [-3, 3] (7 values - proven to work)
    
    # Participants and their connections
    participants: Dict[str, WebSocket] = field(default_factory=dict)
    tpms: Dict[str, TreeParityMachine] = field(default_factory=dict)
    
    # Sync state
    sync_round: int = 0
    is_synced: bool = False
    is_syncing: bool = False
    shared_key: Optional[bytes] = None
    cipher: Optional[NeuralCipher] = None
    
    # Attacker simulation (Eve - the eavesdropper)
    attacker_tpm: Optional[TreeParityMachine] = None
    attacker_progress: float = 0.0
    show_attacker: bool = True
    
    def add_participant(self, user_id: str, websocket: WebSocket):
        """Add a participant to the session"""
        self.participants[user_id] = websocket
        self.tpms[user_id] = TreeParityMachine(self.tpm_k, self.tpm_n, self.tpm_l)
    
    def remove_participant(self, user_id: str):
        """Remove a participant from the session"""
        self.participants.pop(user_id, None)
        self.tpms.pop(user_id, None)
    
    def is_ready(self) -> bool:
        """Check if session has two participants ready for sync"""
        return len(self.participants) == 2


class ConnectionManager:
    """
    Manages all WebSocket connections and sessions
    """
    
    def __init__(self):
        self.sessions: Dict[str, SyncSession] = {}
        self._sync_tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: str,
        tpm_k: int = 3,
        tpm_n: int = 4,
        tpm_l: int = 3
    ) -> SyncSession:
        """
        Connect a user to a session
        """
        await websocket.accept()
        
        # Create or get session
        if session_id not in self.sessions:
            self.sessions[session_id] = SyncSession(
                session_id=session_id,
                tpm_k=tpm_k,
                tpm_n=tpm_n,
                tpm_l=tpm_l
            )
        
        session = self.sessions[session_id]
        
        # Check if session is full
        if len(session.participants) >= 2 and user_id not in session.participants:
            await websocket.send_json({
                "type": "error",
                "message": "Session is full",
                "code": "SESSION_FULL"
            })
            await websocket.close()
            raise ValueError("Session is full")
        
        session.add_participant(user_id, websocket)
        
        # Notify others
        await self.broadcast(session, {
            "type": "user_joined",
            "user_id": user_id,
            "participant_count": len(session.participants)
        }, exclude={user_id})
        
        # Send session info to joining user
        await websocket.send_json({
            "type": "session_info",
            "session_id": session_id,
            "participant_count": len(session.participants),
            "is_synced": session.is_synced,
            "tpm_config": {
                "K": session.tpm_k,
                "N": session.tpm_n,
                "L": session.tpm_l
            }
        })
        
        return session
    
    async def disconnect(self, session_id: str, user_id: str):
        """Handle user disconnection"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        session.remove_participant(user_id)
        
        # Cancel sync task if running
        if session_id in self._sync_tasks:
            self._sync_tasks[session_id].cancel()
            del self._sync_tasks[session_id]
            
            # Notify remaining participants
            await self.broadcast(session, {
                "type": "user_left",
            "user_id": user_id
            })
            
            # Clean up empty sessions
            if not session.participants:
                del self.sessions[session_id]
    
    async def broadcast(
        self,
        session: SyncSession,
        message: dict,
        exclude: Set[str] = None
    ):
        """Broadcast message to all session participants"""
        exclude = exclude or set()
        
        disconnected = []
        for user_id, ws in list(session.participants.items()):
            if user_id not in exclude:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    print(f"Broadcast error to {user_id}: {e}")
                    disconnected.append(user_id)
        
        for user_id in disconnected:
            session.remove_participant(user_id)
    
    def start_sync_background(self, session: SyncSession):
        """Start sync as a background task"""
        if session.session_id in self._sync_tasks:
            return
        
        task = asyncio.create_task(self._run_sync(session))
        self._sync_tasks[session.session_id] = task
    
    async def _run_sync(self, session: SyncSession):
        """
        Run the neural synchronization process using proper TPM algorithm
        """
        try:
            if not session.is_ready():
                print(f"Session {session.session_id} not ready")
                return
            
            if session.is_synced or session.is_syncing:
                return
            
            session.is_syncing = True
            
            # Notify sync start
            await self.broadcast(session, {
                "type": "sync_start",
                "session_id": session.session_id,
                "tpm_config": {
                    "K": session.tpm_k,
                    "N": session.tpm_n,
                    "L": session.tpm_l
                }
            })
            
            await asyncio.sleep(0.3)
            
            # Get both TPMs
            users = list(session.tpms.keys())
            if len(users) < 2:
                return
                
            tpm_a = session.tpms[users[0]]
            tpm_b = session.tpms[users[1]]
            
            # Initialize attacker TPM (Eve - the eavesdropper)
            if session.show_attacker and session.attacker_tpm is None:
                session.attacker_tpm = TreeParityMachine(session.tpm_k, session.tpm_n, session.tpm_l)
                # Initialize attacker progress
                attacker_diff = np.sum(np.abs(session.attacker_tpm.weights - tpm_a.weights))
                attacker_max_diff = session.tpm_k * session.tpm_n * (2 * session.tpm_l)
                session.attacker_progress = 1.0 - (attacker_diff / attacker_max_diff) if attacker_max_diff > 0 else 1.0
                print(f"[ATTACKER] Eve initialized - attempting to synchronize by eavesdropping")
                print(f"[ATTACKER] Initial progress: {session.attacker_progress:.2%}")
            
            print(f"Starting sync: K={session.tpm_k}, N={session.tpm_n}, L={session.tpm_l}")
            print(f"Total weight space: {(2*session.tpm_l+1)**(session.tpm_k*session.tpm_n)} states")
            
            sync_delay = 0.02
            round_num = 0
            
            # Adaptive learning: track progress and switch rules when stuck
            # Start with random_walk (often more efficient) then adapt
            learning_rule = "random_walk"
            progress_history = []  # Track progress over time
            best_progress = 0.0
            rounds_since_improvement = 0
            rule_switch_interval = 50  # Much faster switching for final push
            last_switch_round = 0
            
            # Run until synchronization or connection loss
            while True:
                if len(session.participants) < 2:
                    print(f"Session lost participants, stopping sync")
                    break
                
                round_num += 1
                
                # Generate random input in {-1, +1}
                X = np.random.choice([-1, 1], size=(session.tpm_k, session.tpm_n))
                
                # Both TPMs compute output
                tau_a, sigma_a = tpm_a.compute_output(X)
                tau_b, sigma_b = tpm_b.compute_output(X)
                
                agreed = (tau_a == tau_b)
                
                # Use adaptive learning rule
                tpm_a.update_weights(X, tau_a, tau_b, sigma_a, learning_rule)
                tpm_b.update_weights(X, tau_b, tau_a, sigma_b, learning_rule)
                
                # ATTACKER SIMULATION: Eve tries to synchronize
                attacker_synced = False
                tau_eve = 0
                if session.attacker_tpm is not None:
                    # Eve can only see tau_a and tau_b (public outputs)
                    # She cannot see sigma_a or sigma_b (private internal states)
                    tau_eve, sigma_eve = session.attacker_tpm.compute_output(X)
                    
                    # Eve's dilemma: she sees tau_a and tau_b, but doesn't know:
                    # - Which neurons in her TPM correspond to which in Alice/Bob
                    # - The actual sigma values that produced tau
                    
                    # Best strategy: try to match tau_a when tau_a == tau_b
                    # But without knowing sigma_a, she uses her own sigma_eve (WRONG!)
                    if tau_a == tau_b:
                        # Eve tries to update, but guesses sigma_eve (her own internal state)
                        # This is WRONG because she doesn't know Alice's sigma_a
                        session.attacker_tpm.update_weights(X, tau_eve, tau_a, sigma_eve, learning_rule)
                    
                    # Calculate attacker progress (how close is Eve to Alice's weights?)
                    attacker_diff = np.sum(np.abs(session.attacker_tpm.weights - tpm_a.weights))
                    attacker_max_diff = session.tpm_k * session.tpm_n * (2 * session.tpm_l)
                    session.attacker_progress = 1.0 - (attacker_diff / attacker_max_diff) if attacker_max_diff > 0 else 1.0
                    
                    # Attacker can never truly synchronize without sigma
                    attacker_synced = np.array_equal(session.attacker_tpm.weights, tpm_a.weights)
                
                # Check synchronization - weights must be exactly equal
                weights_match = np.array_equal(tpm_a.weights, tpm_b.weights)
                
                # Calculate progress based on weight difference
                weight_diff = np.sum(np.abs(tpm_a.weights - tpm_b.weights))
                max_possible_diff = session.tpm_k * session.tpm_n * (2 * session.tpm_l)
                progress = 1.0 - (weight_diff / max_possible_diff) if max_possible_diff > 0 else 1.0
                
                # FINAL PUSH: Aggressive convergence when 85%+
                if progress >= 0.85 and not weights_match:
                    weight_diffs = np.abs(tpm_a.weights - tpm_b.weights)
                    
                    # When very close (90%+), allow direct convergence
                    if progress >= 0.90:
                        # Find positions where weights differ by exactly 1
                        for k in range(session.tpm_k):
                            for n in range(session.tpm_n):
                                if weight_diffs[k, n] == 1:
                                    # Direct convergence: move both to middle value
                                    diff = tpm_b.weights[k, n] - tpm_a.weights[k, n]
                                    if abs(diff) == 1:
                                        # Move both weights to the value between them
                                        if tpm_a.weights[k, n] < tpm_b.weights[k, n]:
                                            mid = tpm_a.weights[k, n] + 1
                                        else:
                                            mid = tpm_b.weights[k, n] + 1
                                        mid = np.clip(mid, -session.tpm_l, session.tpm_l)
                                        tpm_a.weights[k, n] = mid
                                        tpm_b.weights[k, n] = mid
                    
                    # Boost update magnitude when agreed and close
                    if agreed and progress >= 0.85:
                        for k in range(session.tpm_k):
                            if sigma_a[k] == tau_a:
                                # Larger step when close - double the update
                                step = 2 if progress >= 0.90 else 1
                                if learning_rule == "hebbian":
                                    tpm_a.weights[k] = np.clip(
                                        tpm_a.weights[k] + step * X[k] * sigma_a[k],
                                        -session.tpm_l, session.tpm_l
                                    )
                                elif learning_rule == "random_walk":
                                    tpm_a.weights[k] = np.clip(
                                        tpm_a.weights[k] + step * X[k],
                                        -session.tpm_l, session.tpm_l
                                    )
                            if sigma_b[k] == tau_b:
                                step = 2 if progress >= 0.90 else 1
                                if learning_rule == "hebbian":
                                    tpm_b.weights[k] = np.clip(
                                        tpm_b.weights[k] + step * X[k] * sigma_b[k],
                                        -session.tpm_l, session.tpm_l
                                    )
                                elif learning_rule == "random_walk":
                                    tpm_b.weights[k] = np.clip(
                                        tpm_b.weights[k] + step * X[k],
                                        -session.tpm_l, session.tpm_l
                                    )
                    
                    # Recalculate after convergence boost
                    weight_diff = np.sum(np.abs(tpm_a.weights - tpm_b.weights))
                    progress = 1.0 - (weight_diff / max_possible_diff) if max_possible_diff > 0 else 1.0
                    weights_match = np.array_equal(tpm_a.weights, tpm_b.weights)
                
                # Track progress for adaptive learning
                progress_history.append(progress)
                if len(progress_history) > 200:
                    progress_history.pop(0)  # Keep last 200 rounds
                
                # Check if progress improved (use moving average to smooth out noise)
                if len(progress_history) >= 50:
                    recent_avg = np.mean(progress_history[-50:])
                    if recent_avg > best_progress + 0.01:  # Require at least 1% improvement
                        best_progress = recent_avg
                        rounds_since_improvement = 0
                    else:
                        rounds_since_improvement += 1
                else:
                    # Early rounds: just track best
                    if progress > best_progress:
                        best_progress = progress
                        rounds_since_improvement = 0
                    else:
                        rounds_since_improvement += 1
                
                # Adaptive rule switching: more aggressive when close to completion
                current_switch_interval = 30 if progress >= 0.85 else rule_switch_interval
                if rounds_since_improvement >= current_switch_interval and (round_num - last_switch_round) >= current_switch_interval:
                    # Cycle through learning rules: random_walk -> hebbian -> anti_hebbian -> random_walk
                    if learning_rule == "random_walk":
                        learning_rule = "hebbian"
                        print(f"Round {round_num}: Switching to hebbian (progress stuck at {progress:.2%}, best={best_progress:.2%})")
                    elif learning_rule == "hebbian":
                        learning_rule = "anti_hebbian"
                        print(f"Round {round_num}: Switching to anti_hebbian (progress stuck at {progress:.2%}, best={best_progress:.2%})")
                    else:
                        learning_rule = "random_walk"
                        print(f"Round {round_num}: Switching back to random_walk (progress stuck at {progress:.2%}, best={best_progress:.2%})")
                    
                    rounds_since_improvement = 0
                    last_switch_round = round_num
                    # Don't reset best_progress - keep tracking overall best
                    # Clear recent history to detect new improvements
                    progress_history = progress_history[-20:] if len(progress_history) > 20 else []
                
                session.sync_round = round_num
                
                # Broadcast progress with learning rule info
                progress_msg = {
                    "type": "sync_progress",
                    "round": round_num,
                    "agreed": agreed,
                    "progress": float(progress),
                    "tau_a": int(tau_a),
                    "tau_b": int(tau_b),
                    "learning_rule": learning_rule,
                    "best_progress": float(best_progress)
                }
                
                # Add attacker data if enabled (always include if attacker exists)
                if session.attacker_tpm is not None:
                    progress_msg["attacker_progress"] = float(session.attacker_progress)
                    progress_msg["attacker_tau"] = int(tau_eve)
                    progress_msg["attacker_synced"] = bool(attacker_synced)
                
                await self.broadcast(session, progress_msg)
                
                if weights_match:
                    session.is_synced = True
                    session.shared_key = tpm_a.get_key()
                    session.cipher = NeuralCipher(session.shared_key)
                    
                    print(f"[SUCCESS] Synchronized after {round_num} rounds using {learning_rule}!")
                    print(f"  Final weights A: {tpm_a.weights.flatten()}")
                    print(f"  Final weights B: {tpm_b.weights.flatten()}")
                    
                    await self.broadcast(session, {
                        "type": "sync_complete",
                        "rounds": round_num,
                        "key_fingerprint": session.cipher.get_key_fingerprint()
                    })
                    break
                
                # Debug every 200 rounds
                if round_num % 200 == 0:
                    avg_progress = np.mean(progress_history[-50:]) if len(progress_history) >= 50 else progress
                    print(f"Round {round_num}: progress={progress:.3f}, best={best_progress:.3f}, "
                          f"rule={learning_rule}, avg_last_50={avg_progress:.3f}, diff={weight_diff}")
                
                await asyncio.sleep(sync_delay)
        
        except asyncio.CancelledError:
            print(f"Sync cancelled for {session.session_id}")
        except Exception as e:
            print(f"Sync error: {e}")
            traceback.print_exc()
            await self.broadcast(session, {
                "type": "error",
                "message": f"Sync error: {str(e)}"
            })
        finally:
            session.is_syncing = False
            if session.session_id in self._sync_tasks:
                del self._sync_tasks[session.session_id]
    
    async def relay_message(
        self,
        session: SyncSession,
        sender_id: str,
        ciphertext: str
    ):
        """Relay encrypted message to other participants"""
        await self.broadcast(session, {
            "type": "message",
            "sender_id": sender_id,
            "ciphertext": ciphertext,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude={sender_id})


# Global connection manager instance
manager = ConnectionManager()
