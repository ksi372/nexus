import { motion } from 'framer-motion'
import styles from './NeuralVisualizer.module.css'

interface NeuralVisualizerProps {
  state: 'connecting' | 'waiting' | 'syncing' | 'synced' | 'error'
  progress: number
  round: number
  activity: boolean[]
  attackerProgress?: number
  attackerSynced?: boolean
}

export function NeuralVisualizer({ 
  state, 
  progress, 
  round, 
  activity,
  attackerProgress = 0,
  attackerSynced = false
}: NeuralVisualizerProps) {
  const neurons = Array.from({ length: 64 }, (_, i) => i)
  
  return (
    <div className={styles.container}>
      {/* Title */}
      <motion.h2 
        className={styles.title}
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {state === 'waiting' && 'Awaiting Connection'}
        {state === 'connecting' && 'Establishing Link'}
        {state === 'syncing' && 'Neural Synchronization'}
        {state === 'synced' && 'Synchronized'}
      </motion.h2>

      {/* Security Notice */}
      {state === 'syncing' && (
        <motion.div 
          className={styles.securityNotice}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <span className={styles.warningIcon}>⚠️</span>
          <span>Eavesdropper detected - attempting to intercept key exchange</span>
        </motion.div>
      )}

      {/* Neural Grid */}
      <div className={styles.neuralGrid}>
        {/* Left Brain */}
        <div className={styles.brain}>
          <div className={styles.brainLabel}>ALICE</div>
          <div className={styles.neuronGrid}>
            {neurons.map((_, i) => {
              const isActive = state === 'syncing' && activity[activity.length - 1 - (i % activity.length)]
              return (
                <motion.div
                  key={`left-${i}`}
                  className={`${styles.neuron} ${isActive ? styles.active : ''}`}
                  animate={isActive ? {
                    scale: [1, 1.4, 1],
                    opacity: [0.3, 1, 0.3]
                  } : {}}
                  transition={{ duration: 0.3 }}
                  style={{
                    animationDelay: `${i * 10}ms`
                  }}
                />
              )
            })}
          </div>
        </div>

        {/* Connection */}
        <div className={styles.connection}>
          <svg viewBox="0 0 100 200" className={styles.connectionSvg}>
            <defs>
              <linearGradient id="connGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#00f0ff" />
                <stop offset="50%" stopColor="#8b5cf6" />
                <stop offset="100%" stopColor="#00f0ff" />
              </linearGradient>
            </defs>
            
            {/* Data flow lines */}
            {state === 'syncing' && (
              <>
                {[20, 50, 80, 110, 140, 170].map((y, i) => (
                  <motion.line
                    key={i}
                    x1="0"
                    y1={y}
                    x2="100"
                    y2={y}
                    stroke="url(#connGrad)"
                    strokeWidth="2"
                    strokeDasharray="10 5"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{
                      duration: 1,
                      delay: i * 0.1,
                      repeat: Infinity,
                      repeatType: 'loop'
                    }}
                  />
                ))}
              </>
            )}
            
            {/* Waiting pulse */}
            {state === 'waiting' && (
              <motion.circle
                cx="50"
                cy="100"
                r="20"
                fill="none"
                stroke="#f97316"
                strokeWidth="2"
                initial={{ scale: 0.5, opacity: 1 }}
                animate={{ scale: 2, opacity: 0 }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  repeatType: 'loop'
                }}
              />
            )}
          </svg>
          
          {state === 'syncing' && (
            <div className={styles.syncStats}>
              <div className={styles.syncStat}>
                <span className={styles.syncStatValue}>{round}</span>
                <span className={styles.syncStatLabel}>Rounds</span>
              </div>
              <div className={styles.syncStat}>
                <span className={styles.syncStatValue}>{progress.toFixed(1)}%</span>
                <span className={styles.syncStatLabel}>Sync</span>
              </div>
            </div>
          )}
        </div>

        {/* Right Brain */}
        <div className={styles.brain}>
          <div className={styles.brainLabel}>BOB</div>
          <div className={styles.neuronGrid}>
            {neurons.map((_, i) => {
              const isActive = state === 'syncing' && activity[activity.length - 1 - ((i + 32) % activity.length)]
              return (
                <motion.div
                  key={`right-${i}`}
                  className={`${styles.neuron} ${isActive ? styles.active : ''}`}
                  animate={isActive ? {
                    scale: [1, 1.4, 1],
                    opacity: [0.3, 1, 0.3]
                  } : {}}
                  transition={{ duration: 0.3 }}
                  style={{
                    animationDelay: `${(63 - i) * 10}ms`
                  }}
                />
              )
            })}
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      {state === 'syncing' && (
        <div className={styles.progressContainer}>
          <div className={styles.progressTrack}>
            <motion.div 
              className={styles.progressBar}
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
            <div className={styles.progressGlow} style={{ width: `${progress}%` }} />
          </div>
          <div className={styles.progressLabels}>
            <span>Synchronizing weights...</span>
            <span>{progress.toFixed(1)}%</span>
          </div>
        </div>
      )}

      {/* Activity Stream */}
      {state === 'syncing' && activity.length > 0 && (
        <div className={styles.activityStream}>
          {activity.slice(-40).map((agreed, i) => (
            <div
              key={i}
              className={`${styles.activityDot} ${agreed ? styles.agreed : styles.disagreed}`}
              style={{ animationDelay: `${i * 20}ms` }}
            />
          ))}
        </div>
      )}

      {/* Attacker Visualization */}
      {state === 'syncing' && (
        <motion.div 
          className={styles.attackerSection}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className={styles.attackerHeader}>
            <span className={styles.attackerIcon}>🕵️</span>
            <span className={styles.attackerLabel}>EVE (Eavesdropper)</span>
            {attackerSynced ? (
              <span className={styles.attackerStatusDanger}>⚠️ SYNCHRONIZED</span>
            ) : (
              <span className={styles.attackerStatusSafe}>✗ FAILED</span>
            )}
          </div>
          
          <div className={styles.attackerBrain}>
            <div className={styles.neuronGrid}>
              {neurons.slice(0, 32).map((_, i) => {
                const isActive = state === 'syncing' && Math.random() > 0.7
                return (
                  <motion.div
                    key={`attacker-${i}`}
                    className={`${styles.neuron} ${styles.attackerNeuron} ${isActive ? styles.active : ''}`}
                    animate={isActive ? {
                      scale: [1, 1.2, 1],
                      opacity: [0.2, 0.6, 0.2]
                    } : {}}
                    transition={{ duration: 0.5 }}
                  />
                )
              })}
            </div>
          </div>
          
          <div className={styles.attackerProgress}>
            <div className={styles.attackerProgressTrack}>
              <motion.div 
                className={styles.attackerProgressBar}
                initial={{ width: 0 }}
                animate={{ width: `${(attackerProgress || 0) * 100}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
            <div className={styles.attackerProgressLabel}>
              <span>Eve's synchronization attempt: {((attackerProgress || 0) * 100).toFixed(1)}%</span>
              <span className={styles.attackerExplanation}>
                (Cannot synchronize without internal states)
              </span>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
