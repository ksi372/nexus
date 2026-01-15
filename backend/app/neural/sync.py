"""
Neural Synchronization Protocol

Manages the TPM synchronization process between two parties.
Handles input generation, output exchange, and convergence detection.
"""

import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass, field
from .tpm import TreeParityMachine, LearningRule


@dataclass
class SyncState:
    """State of a synchronization session"""
    round: int = 0
    agreements: int = 0
    is_synced: bool = False
    key_hash: Optional[str] = None


@dataclass
class SyncRoundResult:
    """Result of a single synchronization round"""
    round: int
    input_seed: int
    tau_a: int
    tau_b: int
    agreed: bool
    sync_progress: float
    weights_match: bool


class NeuralSyncProtocol:
    """
    Orchestrates the Neural Key Exchange protocol
    
    The protocol works as follows:
    1. Both parties initialize their TPMs with random weights
    2. Each round, they receive the same random input
    3. They compute outputs and exchange them
    4. If outputs match, both update weights using the same rule
    5. Process repeats until weights synchronize
    
    Parameters:
        K, N, L: TPM architecture parameters
        learning_rule: Weight update rule
        max_rounds: Maximum synchronization attempts
    """
    
    def __init__(
        self,
        K: int = 8,
        N: int = 16,
        L: int = 6,
        learning_rule: LearningRule = "hebbian",
        max_rounds: int = 2000
    ):
        self.K = K
        self.N = N
        self.L = L
        self.learning_rule = learning_rule
        self.max_rounds = max_rounds
        
        # Initialize both TPMs
        self.tpm_a = TreeParityMachine(K, N, L)
        self.tpm_b = TreeParityMachine(K, N, L)
        
        self.state = SyncState()
        self._rng = np.random.default_rng()
    
    def generate_input(self, seed: Optional[int] = None) -> np.ndarray:
        """
        Generate random input for synchronization round
        
        Input values are in {-1, +1}
        """
        if seed is not None:
            rng = np.random.default_rng(seed)
        else:
            rng = self._rng
            
        # Generate random bits and map to {-1, +1}
        X = rng.integers(0, 2, size=(self.K, self.N)) * 2 - 1
        return X
    
    def run_round(self, X: Optional[np.ndarray] = None) -> SyncRoundResult:
        """
        Execute a single synchronization round
        
        Args:
            X: Input array (generated if not provided)
            
        Returns:
            SyncRoundResult with round details
        """
        if self.state.is_synced:
            raise RuntimeError("Already synchronized")
        
        # Generate input if not provided
        seed = int(self._rng.integers(0, 2**31))
        if X is None:
            X = self.generate_input(seed)
        
        # Both TPMs compute output
        tau_a, sigma_a = self.tpm_a.compute_output(X)
        tau_b, sigma_b = self.tpm_b.compute_output(X)
        
        agreed = tau_a == tau_b
        if agreed:
            self.state.agreements += 1
        
        # Update weights (only happens if outputs match)
        self.tpm_a.update_weights(X, tau_a, tau_b, sigma_a, self.learning_rule)
        self.tpm_b.update_weights(X, tau_b, tau_a, sigma_b, self.learning_rule)
        
        # Check if weights have synchronized
        weights_match = np.array_equal(self.tpm_a.weights, self.tpm_b.weights)
        
        if weights_match:
            self.state.is_synced = True
            self.state.key_hash = self.tpm_a.get_key_hex()[:16]
        
        self.state.round += 1
        
        # Calculate sync progress
        sync_progress = self._calculate_progress()
        
        return SyncRoundResult(
            round=self.state.round,
            input_seed=seed,
            tau_a=tau_a,
            tau_b=tau_b,
            agreed=agreed,
            sync_progress=sync_progress,
            weights_match=weights_match
        )
    
    def run_full_sync(self) -> Tuple[bool, int, bytes]:
        """
        Run complete synchronization until success or max rounds
        
        Returns:
            success: Whether synchronization succeeded
            rounds: Number of rounds taken
            key: Derived encryption key
        """
        while not self.state.is_synced and self.state.round < self.max_rounds:
            self.run_round()
        
        return (
            self.state.is_synced,
            self.state.round,
            self.tpm_a.get_key() if self.state.is_synced else b''
        )
    
    def _calculate_progress(self) -> float:
        """Estimate synchronization progress"""
        if self.state.round == 0:
            return 0.0
        
        # Agreement rate contributes to progress
        agreement_rate = self.state.agreements / self.state.round
        
        # Weight similarity also indicates progress
        weight_diff = np.abs(self.tpm_a.weights - self.tpm_b.weights)
        max_diff = self.L * 2
        similarity = 1 - (np.mean(weight_diff) / max_diff)
        
        # Combine metrics
        progress = (agreement_rate * 0.3 + similarity * 0.7)
        
        return min(progress, 0.99) if not self.state.is_synced else 1.0
    
    def get_keys(self) -> Tuple[bytes, bytes]:
        """Get derived keys from both TPMs (should match if synced)"""
        return self.tpm_a.get_key(), self.tpm_b.get_key()
    
    def reset(self):
        """Reset protocol for new synchronization"""
        self.tpm_a.reset()
        self.tpm_b.reset()
        self.state = SyncState()
