import { useState } from 'react'
import { motion } from 'framer-motion'
import { NeuralBackground } from './NeuralBackground'
import styles from './LandingScreen.module.css'

interface LandingScreenProps {
  onJoinSession: (sessionId: string, userId: string) => void
}

export function LandingScreen({ onJoinSession }: LandingScreenProps) {
  const [mode, setMode] = useState<'choice' | 'create' | 'join'>('choice')
  const [sessionId, setSessionId] = useState('')
  const [userId, setUserId] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  const generateUserId = () => {
    return 'user_' + Math.random().toString(36).substring(2, 8)
  }

  const handleCreateSession = async () => {
    setIsCreating(true)
    try {
      const response = await fetch('http://localhost:8000/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tpm_k: 8, tpm_n: 16, tpm_l: 6 })
      })
      const data = await response.json()
      const newUserId = generateUserId()
      setSessionId(data.session_id)
      setUserId(newUserId)
      onJoinSession(data.session_id, newUserId)
    } catch (error) {
      console.error('Failed to create session:', error)
      setIsCreating(false)
    }
  }

  const handleJoinSession = () => {
    if (!sessionId.trim()) return
    const newUserId = userId.trim() || generateUserId()
    onJoinSession(sessionId.trim(), newUserId)
  }

  return (
    <div className={styles.container}>
      <NeuralBackground />
      
      <motion.div 
        className={styles.content}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        {/* Logo */}
        <motion.div 
          className={styles.logo}
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className={styles.logoIcon}>
            <svg viewBox="0 0 100 100" className={styles.logoSvg}>
              <defs>
                <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#00f0ff" />
                  <stop offset="100%" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
              <circle cx="50" cy="50" r="45" fill="none" stroke="url(#logoGrad)" strokeWidth="2"/>
              <circle cx="50" cy="25" r="5" fill="#00f0ff" className={styles.neuronNode}/>
              <circle cx="25" cy="60" r="5" fill="#00f0ff" className={styles.neuronNode}/>
              <circle cx="75" cy="60" r="5" fill="#00f0ff" className={styles.neuronNode}/>
              <circle cx="50" cy="50" r="8" fill="url(#logoGrad)" className={styles.neuronCenter}/>
              <line x1="50" y1="25" x2="50" y2="42" stroke="#00f0ff" strokeWidth="2" className={styles.neuronLink}/>
              <line x1="25" y1="60" x2="42" y2="52" stroke="#00f0ff" strokeWidth="2" className={styles.neuronLink}/>
              <line x1="75" y1="60" x2="58" y2="52" stroke="#00f0ff" strokeWidth="2" className={styles.neuronLink}/>
            </svg>
          </div>
          <h1 className={styles.title}>NEXUS</h1>
          <p className={styles.subtitle}>Neural Key Exchange</p>
        </motion.div>

        {/* Description */}
        <motion.p 
          className={styles.description}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          Secure communication through synchronized neural networks.
          <br />
          Two minds, one key.
        </motion.p>

        {/* Action Buttons */}
        {mode === 'choice' && (
          <motion.div 
            className={styles.buttonGroup}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <button 
              className={styles.primaryButton}
              onClick={handleCreateSession}
              disabled={isCreating}
            >
              <span className={styles.buttonIcon}>⚡</span>
              {isCreating ? 'Initializing...' : 'Create Session'}
            </button>
            
            <button 
              className={styles.secondaryButton}
              onClick={() => setMode('join')}
            >
              <span className={styles.buttonIcon}>🔗</span>
              Join Session
            </button>
          </motion.div>
        )}

        {/* Join Form */}
        {mode === 'join' && (
          <motion.div 
            className={styles.form}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className={styles.inputGroup}>
              <label>Session ID</label>
              <input
                type="text"
                placeholder="Enter session code"
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                autoFocus
              />
            </div>
            
            <div className={styles.inputGroup}>
              <label>Your Name (optional)</label>
              <input
                type="text"
                placeholder="Anonymous"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
              />
            </div>

            <div className={styles.formButtons}>
              <button 
                className={styles.backButton}
                onClick={() => setMode('choice')}
              >
                ← Back
              </button>
              <button 
                className={styles.primaryButton}
                onClick={handleJoinSession}
                disabled={!sessionId.trim()}
              >
                Connect
              </button>
            </div>
          </motion.div>
        )}

        {/* Tech specs */}
        <motion.div 
          className={styles.specs}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
        >
          <div className={styles.specItem}>
            <span className={styles.specLabel}>Protocol</span>
            <span className={styles.specValue}>TPM Sync</span>
          </div>
          <div className={styles.specDivider}>/</div>
          <div className={styles.specItem}>
            <span className={styles.specLabel}>Encryption</span>
            <span className={styles.specValue}>AES-256-GCM</span>
          </div>
          <div className={styles.specDivider}>/</div>
          <div className={styles.specItem}>
            <span className={styles.specLabel}>Key Size</span>
            <span className={styles.specValue}>256-bit</span>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}
