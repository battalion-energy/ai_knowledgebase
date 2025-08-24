'use client'

import { useEffect, useRef } from 'react'

export default function GradientBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId: number
    let time = 0

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }

    const createGradient = (x: number, y: number, color: string, size: number) => {
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, size)
      gradient.addColorStop(0, color)
      gradient.addColorStop(1, 'transparent')
      return gradient
    }

    const animate = () => {
      time += 0.002
      
      // Clear with subtle background
      ctx.fillStyle = 'rgba(249, 250, 251, 0.02)' // Very subtle gray
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Animated gradient blobs
      const blobs = [
        {
          x: canvas.width * 0.3 + Math.sin(time) * 100,
          y: canvas.height * 0.3 + Math.cos(time * 0.8) * 100,
          color: 'rgba(139, 92, 246, 0.15)', // Purple
          size: 400
        },
        {
          x: canvas.width * 0.7 + Math.cos(time * 0.9) * 150,
          y: canvas.height * 0.4 + Math.sin(time * 0.7) * 100,
          color: 'rgba(59, 130, 246, 0.15)', // Blue
          size: 350
        },
        {
          x: canvas.width * 0.5 + Math.sin(time * 1.1) * 120,
          y: canvas.height * 0.7 + Math.cos(time * 0.6) * 80,
          color: 'rgba(16, 185, 129, 0.15)', // Green
          size: 300
        },
        {
          x: canvas.width * 0.2 + Math.cos(time * 0.8) * 100,
          y: canvas.height * 0.6 + Math.sin(time * 0.9) * 120,
          color: 'rgba(251, 146, 60, 0.12)', // Orange
          size: 320
        },
        {
          x: canvas.width * 0.8 + Math.sin(time * 0.7) * 90,
          y: canvas.height * 0.2 + Math.cos(time * 1.2) * 110,
          color: 'rgba(236, 72, 153, 0.12)', // Pink
          size: 280
        }
      ]

      // Draw each blob
      blobs.forEach(blob => {
        ctx.fillStyle = createGradient(blob.x, blob.y, blob.color, blob.size)
        ctx.fillRect(0, 0, canvas.width, canvas.height)
      })

      animationFrameId = requestAnimationFrame(animate)
    }

    resize()
    animate()

    window.addEventListener('resize', resize)

    return () => {
      window.removeEventListener('resize', resize)
      cancelAnimationFrame(animationFrameId)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 -z-10 opacity-60"
      style={{ filter: 'blur(100px)' }}
    />
  )
}