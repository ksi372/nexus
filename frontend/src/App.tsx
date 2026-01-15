import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { LandingScreen } from './components/LandingScreen'
import { SyncRoom } from './components/SyncRoom'

type AppState = 'landing' | 'session'

interface SessionConfig {
  sessionId: string
  userId: string
}

export default function App() {
  const [state, setState] = useState<AppState>('landing')
  const [sessionConfig, setSessionConfig] = useState<SessionConfig | null>(null)

  const handleJoinSession = (sessionId: string, userId: string) => {
    setSessionConfig({ sessionId, userId })
    setState('session')
  }

  const handleLeaveSession = () => {
    setSessionConfig(null)
    setState('landing')
  }

  return (
    <div className="app">
      <AnimatePresence mode="wait">
        {state === 'landing' && (
          <motion.div
            key="landing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <LandingScreen onJoinSession={handleJoinSession} />
          </motion.div>
        )}

        {state === 'session' && sessionConfig && (
          <motion.div
            key="session"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3 }}
            style={{ height: '100%' }}
          >
            <SyncRoom 
              sessionId={sessionConfig.sessionId}
              userId={sessionConfig.userId}
              onLeave={handleLeaveSession}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
