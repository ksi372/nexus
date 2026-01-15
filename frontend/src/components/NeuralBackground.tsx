import { useEffect, useRef } from 'react'
import styles from './NeuralBackground.module.css'

interface Node {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  connections: number[]
}

export function NeuralBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number>()
  const nodesRef = useRef<Node[]>([])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resizeCanvas = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
      initNodes()
    }

    const initNodes = () => {
      const nodeCount = Math.floor((canvas.width * canvas.height) / 25000)
      nodesRef.current = []

      for (let i = 0; i < nodeCount; i++) {
        nodesRef.current.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * 0.5,
          vy: (Math.random() - 0.5) * 0.5,
          radius: Math.random() * 2 + 1,
          connections: []
        })
      }
    }

    const drawNode = (node: Node, index: number) => {
      // Glow effect
      const gradient = ctx.createRadialGradient(
        node.x, node.y, 0,
        node.x, node.y, node.radius * 4
      )
      gradient.addColorStop(0, 'rgba(0, 240, 255, 0.8)')
      gradient.addColorStop(0.5, 'rgba(0, 240, 255, 0.2)')
      gradient.addColorStop(1, 'rgba(0, 240, 255, 0)')

      ctx.beginPath()
      ctx.arc(node.x, node.y, node.radius * 4, 0, Math.PI * 2)
      ctx.fillStyle = gradient
      ctx.fill()

      // Core
      ctx.beginPath()
      ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2)
      ctx.fillStyle = index % 3 === 0 ? '#8b5cf6' : '#00f0ff'
      ctx.fill()
    }

    const drawConnection = (node1: Node, node2: Node, distance: number, maxDistance: number) => {
      const opacity = 1 - (distance / maxDistance)
      
      ctx.beginPath()
      ctx.moveTo(node1.x, node1.y)
      ctx.lineTo(node2.x, node2.y)
      
      const gradient = ctx.createLinearGradient(node1.x, node1.y, node2.x, node2.y)
      gradient.addColorStop(0, `rgba(0, 240, 255, ${opacity * 0.3})`)
      gradient.addColorStop(0.5, `rgba(139, 92, 246, ${opacity * 0.2})`)
      gradient.addColorStop(1, `rgba(0, 240, 255, ${opacity * 0.3})`)
      
      ctx.strokeStyle = gradient
      ctx.lineWidth = opacity * 1.5
      ctx.stroke()
    }

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const maxDistance = 150
      const nodes = nodesRef.current

      // Update positions
      nodes.forEach(node => {
        node.x += node.vx
        node.y += node.vy

        // Bounce off edges
        if (node.x < 0 || node.x > canvas.width) node.vx *= -1
        if (node.y < 0 || node.y > canvas.height) node.vy *= -1

        // Keep in bounds
        node.x = Math.max(0, Math.min(canvas.width, node.x))
        node.y = Math.max(0, Math.min(canvas.height, node.y))
      })

      // Draw connections
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x
          const dy = nodes[i].y - nodes[j].y
          const distance = Math.sqrt(dx * dx + dy * dy)

          if (distance < maxDistance) {
            drawConnection(nodes[i], nodes[j], distance, maxDistance)
          }
        }
      }

      // Draw nodes
      nodes.forEach((node, index) => drawNode(node, index))

      animationRef.current = requestAnimationFrame(animate)
    }

    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)
    animate()

    return () => {
      window.removeEventListener('resize', resizeCanvas)
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [])

  return <canvas ref={canvasRef} className={styles.canvas} />
}
