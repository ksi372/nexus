# 🧠 Nexus - Neural Key Exchange

**Secure communication through synchronized neural networks.**

Nexus implements the Tree Parity Machine (TPM) neural cryptography protocol for secure key exchange, combined with AES-256-GCM encryption for end-to-end encrypted messaging.

## 🔐 How It Works

### Neural Key Exchange (NKE)

Instead of traditional key exchange algorithms, Nexus uses **neural network synchronization**:

1. **Two parties** each have a Tree Parity Machine (TPM) - a special neural network
2. **Random inputs** are presented to both TPMs simultaneously
3. **Outputs are exchanged** and used to update weights (only when outputs match)
4. **After ~300-500 rounds**, both TPMs have identical weights
5. **The synchronized weights** become the shared encryption key

```
┌─────────────────┐                    ┌─────────────────┐
│   Alice (TPM)   │◄──── Exchange ────►│    Bob (TPM)    │
│  weights: W_a   │     outputs τ      │  weights: W_b   │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         ▼                                      ▼
   After synchronization: W_a = W_b = SHARED SECRET KEY
```

### Why Is This Secure?

An eavesdropper (Eve) who observes the exchanges cannot synchronize her own TPM fast enough. The mutual learning rule ensures that only the two communicating parties converge to the same weights.

## 🛠️ Tech Stack

- **Backend**: FastAPI + Python
  - Tree Parity Machine implementation with NumPy
  - WebSocket server for real-time sync
  - AES-256-GCM encryption with PyCryptodome

- **Frontend**: React + TypeScript + Vite
  - Real-time neural sync visualization
  - Web Crypto API for client-side encryption
  - Framer Motion for animations

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Unix/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

### Usage

1. Open http://localhost:5173 in your browser
2. Click **"Create Session"** to generate a session code
3. Share the code with your partner
4. Your partner clicks **"Join Session"** and enters the code
5. Watch the neural networks synchronize in real-time
6. Once synced, start sending encrypted messages!

## 📡 API Endpoints

### REST

- `GET /` - API info
- `GET /health` - Health check
- `POST /sessions` - Create new session
- `GET /sessions/{id}` - Get session status

### WebSocket

- `WS /ws/{session_id}/{user_id}` - Connect to session

#### Message Types

```typescript
// Server → Client
{ type: "session_info", participant_count, is_synced, tpm_config }
{ type: "user_joined", user_id, participant_count }
{ type: "sync_start", session_id, tpm_config }
{ type: "sync_progress", round, agreed, progress }
{ type: "sync_complete", rounds, key_fingerprint }
{ type: "message", sender_id, ciphertext, timestamp }

// Client → Server
{ type: "message", ciphertext }
{ type: "request_sync" }
```

## 🔧 TPM Configuration

The Tree Parity Machine can be configured with these parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| K | 8 | Number of hidden neurons |
| N | 16 | Inputs per hidden neuron |
| L | 6 | Weight range [-L, L] |

Higher values increase security but take longer to synchronize.

## 📚 References

- Kanter, I., Kinzel, W., & Kanter, E. (2002). Secure exchange of information by synchronization of neural networks. *Europhysics Letters*
- Ruttor, A. (2006). Neural Synchronization and Cryptography. *arXiv:0711.2411*

## 📄 License

MIT License - See LICENSE file for details.

---

Built with 🧠 by exploring the intersection of neural networks and cryptography.
