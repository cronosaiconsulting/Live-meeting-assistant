import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { LiveKitRoom, VideoConference } from '@livekit/components-react'
import '@livekit/components-styles'
import { useAuthStore } from '../stores/authStore'
import { roomsAPI } from '../services/api'
import { config } from '../config'

export default function MeetingPage() {
  const { roomId } = useParams<{ roomId: string }>()
  const [livekitToken, setLivekitToken] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const { user } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    if (!roomId) {
      setError('Invalid room ID')
      setLoading(false)
      return
    }

    const joinRoom = async () => {
      try {
        const response = await roomsAPI.join(roomId, user?.full_name || user?.username)
        setLivekitToken(response.livekit_token)
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to join room')
      } finally {
        setLoading(false)
      }
    }

    joinRoom()
  }, [roomId, user])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-white text-xl">Loading meeting...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-gray-900">
        <div className="text-red-500 text-xl mb-4">{error}</div>
        <button
          onClick={() => navigate('/dashboard')}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Back to Dashboard
        </button>
      </div>
    )
  }

  return (
    <div className="h-screen">
      <LiveKitRoom
        token={livekitToken}
        serverUrl={config.liveKitUrl}
        data-lk-theme="default"
        style={{ height: '100vh' }}
      >
        <VideoConference />
        {user?.is_admin && (
          <div className="absolute top-4 right-4 bg-blue-600 text-white px-4 py-2 rounded shadow-lg">
            Admin View - Transcript & AI Panel (To be implemented)
          </div>
        )}
      </LiveKitRoom>
    </div>
  )
}
