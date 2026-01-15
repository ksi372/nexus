import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { NeuralVisualizer } from './NeuralVisualizer'
import { ChatInterface } from './ChatInterface'
import styles from './SyncRoom.module.css'

interface SyncRoomProps {
  sessionId: string
  userId: string
  onLeave: () => void
}

interface Message {
  id: string
  sender: string
  content: string
  timestamp: Date
  isOwn: boolean
}

type ConnectionState = 'connecting' | 'waiting' | 'syncing' | 'synced' | 'error'

export function SyncRoom({ sessionId, userId, onLeave }: SyncRoomProps) {
  const [connectionState, setConnectionState] = useState<ConnectionState>('connecting')
  const [participantCount, setParticipantCount] = useState(1)
  const [syncProgress, setSyncProgress] = useState(0)
  const [syncRound, setSyncRound] = useState(0)
  const [neuralActivity, setNeuralActivity] = useState<boolean[]>([])
  const [keyFingerprint, setKeyFingerprint] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [attackerProgress, setAttackerProgress] = useState(0)
  const [attackerSynced, setAttackerSynced] = useState(false)
  
  const wsRef = useRef<WebSocket | null>(null)
  const encryptionKeyRef = useRef<CryptoKey | null>(null)

  // Derive encryption key from fingerprint
  const deriveKey = useCallback(async (fingerprint: string): Promise<CryptoKey> => {
    const encoder = new TextEncoder()
    const data = encoder.encode(fingerprint + sessionId + 'nexus-key-derivation')
    const hashBuffer = await crypto.subtle.digest('SHA-256', data)
    
    const key = await crypto.subtle.importKey(
      'raw',
      hashBuffer,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    )
    
    return key
  }, [sessionId])

  // Encrypt message
  const encryptMessage = useCallback(async (plaintext: string): Promise<string> => {
    const key = encryptionKeyRef.current
    if (!key) throw new Error('No encryption key')
    
    const encoder = new TextEncoder()
    const data = encoder.encode(plaintext)
    const iv = crypto.getRandomValues(new Uint8Array(12))
    
    const encrypted = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      key,
      data
    )
    
    // Combine IV + ciphertext
    const combined = new Uint8Array(iv.length + encrypted.byteLength)
    combined.set(iv)
    combined.set(new Uint8Array(encrypted), iv.length)
    
    return btoa(String.fromCharCode(...combined))
  }, [])

  // Decrypt message
  const decryptMessage = useCallback(async (ciphertext: string): Promise<string> => {
    const key = encryptionKeyRef.current
    if (!key) throw new Error('No encryption key')
    
    const combined = Uint8Array.from(atob(ciphertext), c => c.charCodeAt(0))
    const iv = combined.slice(0, 12)
    const data = combined.slice(12)
    
    const decrypted = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv },
      key,
      data
    )
    
    return new TextDecoder().decode(decrypted)
  }, [])

  // WebSocket connection
  useEffect(() => {
    console.log('Connecting to WebSocket...')
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
    const ws = new WebSocket(`${wsUrl}/ws/${sessionId}/${userId}`)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected to session:', sessionId)
      setConnectionState('connecting')
    }

    ws.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log('Received:', data.type, data)
        
        switch (data.type) {
          case 'session_info':
            setParticipantCount(data.participant_count)
            setConnectionState(data.participant_count < 2 ? 'waiting' : 'syncing')
            break
            
          case 'user_joined':
            setParticipantCount(data.participant_count)
            if (data.participant_count >= 2) {
              setConnectionState('syncing')
            }
            break
            
          case 'user_left':
            setParticipantCount(p => Math.max(1, p - 1))
            break
            
          case 'sync_start':
            console.log('Sync started!')
            setConnectionState('syncing')
            setSyncProgress(0)
            setNeuralActivity([])
            break
            
          case 'sync_progress':
            setSyncRound(data.round)
            setSyncProgress(data.progress * 100)
            setNeuralActivity(prev => [...prev.slice(-100), data.agreed])
            
            // Update attacker progress if present
            if (data.attacker_progress !== undefined) {
              setAttackerProgress(data.attacker_progress)
              setAttackerSynced(data.attacker_synced || false)
            }
            break
            
          case 'sync_complete':
            console.log('Sync complete!', data)
            setConnectionState('synced')
            setSyncProgress(100)
            setKeyFingerprint(data.key_fingerprint)
            // Derive encryption key
            try {
              const key = await deriveKey(data.key_fingerprint)
              encryptionKeyRef.current = key
              console.log('Encryption key derived')
            } catch (e) {
              console.error('Failed to derive key:', e)
            }
            break
            
          case 'sync_failed':
            console.error('Sync failed:', data.message)
            setConnectionState('error')
            break
            
          case 'message':
            try {
              const decrypted = await decryptMessage(data.ciphertext)
              setMessages(prev => [...prev, {
                id: Date.now().toString(),
                sender: data.sender_id,
                content: decrypted,
                timestamp: new Date(data.timestamp),
                isOwn: false
              }])
            } catch (e) {
              console.error('Failed to decrypt message:', e)
            }
            break
          
          case 'ping':
            // Respond to server ping
            ws.send(JSON.stringify({ type: 'pong' }))
            break
            
          case 'pong':
            // Server responded to our ping
            break
            
          case 'error':
            console.error('Server error:', data.message)
            if (data.code !== 'SESSION_FULL') {
              // Don't show error for non-critical issues
            }
            break
            
          case 'already_synced':
            console.log('Session already synced')
            break
        }
      } catch (e) {
        console.error('Error processing message:', e)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnectionState('error')
    }

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason)
      // Only show error if we weren't already synced
      if (connectionState !== 'synced') {
        // Don't immediately show error, might be temporary
      }
    }

    return () => {
      console.log('Closing WebSocket')
      ws.close()
    }
  }, [sessionId, userId, deriveKey, decryptMessage])

  // Send message
  const handleSendMessage = useCallback(async (content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected')
      return
    }
    
    if (!encryptionKeyRef.current) {
      console.error('No encryption key')
      return
    }
    
    try {
      const ciphertext = await encryptMessage(content)
      
      wsRef.current.send(JSON.stringify({
        type: 'message',
        ciphertext
      }))
      
      // Add to local messages
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        sender: userId,
        content,
        timestamp: new Date(),
        isOwn: true
      }])
    } catch (e) {
      console.error('Failed to send message:', e)
    }
  }, [userId, encryptMessage])

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.sessionInfo}>
          <span className={styles.sessionLabel}>SESSION</span>
          <span className={styles.sessionId}>{sessionId}</span>
        </div>
        
        <div className={styles.status}>
          <div className={`${styles.statusDot} ${styles[connectionState]}`} />
          <span className={styles.statusText}>
            {connectionState === 'connecting' && 'Connecting...'}
            {connectionState === 'waiting' && 'Waiting for partner...'}
            {connectionState === 'syncing' && 'Synchronizing neural networks...'}
            {connectionState === 'synced' && 'Secure channel established'}
            {connectionState === 'error' && 'Connection error'}
          </span>
        </div>
        
        <div className={styles.headerActions}>
          <div className={styles.participants}>
            <span className={styles.participantIcon}>👤</span>
            <span>{participantCount}/2</span>
          </div>
          <button className={styles.leaveButton} onClick={onLeave}>
            Leave
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className={styles.main}>
        <AnimatePresence mode="wait">
          {/* Waiting / Syncing View */}
          {(connectionState === 'waiting' || connectionState === 'syncing' || connectionState === 'connecting') && (
            <motion.div
              key="sync"
              className={styles.syncView}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <NeuralVisualizer 
                state={connectionState}
                progress={syncProgress}
                round={syncRound}
                activity={neuralActivity}
                attackerProgress={attackerProgress}
                attackerSynced={attackerSynced}
              />
              
              {connectionState === 'waiting' && (
                <div className={styles.sharePrompt}>
                  <p>Share this code with your partner:</p>
                  <div className={styles.codeDisplay}>
                    <code>{sessionId}</code>
                    <button 
                      className={styles.copyButton}
                      onClick={() => navigator.clipboard.writeText(sessionId)}
                    >
                      Copy
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* Chat View */}
          {connectionState === 'synced' && (
            <motion.div
              key="chat"
              className={styles.chatView}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <div className={styles.securityBanner}>
                <span className={styles.lockIcon}>🔐</span>
                <span>End-to-end encrypted</span>
                <span className={styles.fingerprint}>Key: {keyFingerprint}</span>
              </div>
              
              <ChatInterface 
                messages={messages}
                onSendMessage={handleSendMessage}
                userId={userId}
              />
            </motion.div>
          )}

          {/* Error View */}
          {connectionState === 'error' && (
            <motion.div
              key="error"
              className={styles.errorView}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <span className={styles.errorIcon}>⚠️</span>
              <h2>Connection Error</h2>
              <p>Failed to establish secure connection.</p>
              <button className={styles.retryButton} onClick={onLeave}>
                Return to Home
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}
