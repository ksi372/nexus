"""
Tree Parity Machine (TPM) Implementation
Neural cryptography for secure key exchange

The TPM is a special type of neural network used for mutual learning.
Two TPMs can synchronize their weights by exchanging only their outputs,
creating a shared secret key that an eavesdropper cannot learn.
"""

import numpy as np
import hashlib
from typing import Tuple, Literal

LearningRule = Literal["hebbian", "anti_hebbian", "random_walk"]


class TreeParityMachine:
    """
    Tree Parity Machine for Neural Key Exchange
    
    Architecture:
    - K hidden neurons (perceptrons)
    - N inputs per hidden neuron
    - Weights bounded by [-L, L]
    - Output τ = product of all hidden outputs σ
    """
    
    def __init__(self, K: int = 3, N: int = 4, L: int = 3):
        self.K = K
        self.N = N
        self.L = L
        # Initialize weights randomly in range [-L, L]
        self.weights = np.random.randint(-L, L + 1, size=(K, N))
    
    def compute_output(self, X: np.ndarray) -> Tuple[int, np.ndarray]:
        """
        Compute TPM output for given input
        
        Args:
            X: Input array of shape (K, N) with values in {-1, +1}
            
        Returns:
            tau: Final output (-1 or +1), product of hidden outputs
            sigma: Hidden neuron outputs array of shape (K,)
        """
        # Compute local field (weighted sum) for each hidden neuron
        local_fields = np.sum(X * self.weights, axis=1)
        
        # Hidden neuron outputs: sign of local field
        sigma = np.sign(local_fields).astype(np.int32)
        # Replace zeros with 1 (convention when local field is 0)
        sigma[sigma == 0] = 1
        
        # Final output: product of all hidden outputs
        tau = int(np.prod(sigma))
        
        return tau, sigma
    
    def update_weights(
        self, 
        X: np.ndarray, 
        tau_self: int, 
        tau_other: int, 
        sigma: np.ndarray,
        rule: LearningRule = "hebbian"
    ) -> bool:
        """
        Update weights based on learning rule
        
        Only updates when both TPMs produce the same output (τ_A == τ_B).
        Uses Hebbian rule: w_k += x_k * σ_k for neurons where σ_k == τ
        """
        if tau_self != tau_other:
            return False
        
        tau = tau_self  # They're equal
        
        for k in range(self.K):
            # Only update neurons that agree with the output
            if sigma[k] == tau:
                if rule == "hebbian":
                    # Hebbian: w += x * sigma
                    self.weights[k] = self.weights[k] + X[k] * sigma[k]
                elif rule == "anti_hebbian":
                    self.weights[k] = self.weights[k] - X[k] * sigma[k]
                elif rule == "random_walk":
                    self.weights[k] = self.weights[k] + X[k]
                
                # Clip weights to valid range [-L, L]
                self.weights[k] = np.clip(self.weights[k], -self.L, self.L)
        
        return True
    
    def get_key(self, length: int = 32) -> bytes:
        """
        Derive encryption key from synchronized weights
        """
        weight_bytes = self.weights.astype(np.int32).tobytes()
        return hashlib.sha256(weight_bytes).digest()[:length]
    
    def get_key_hex(self) -> str:
        """Get key as hexadecimal string for display"""
        return self.get_key().hex()
    
    def __repr__(self) -> str:
        return f"TreeParityMachine(K={self.K}, N={self.N}, L={self.L})"
