import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { roomsAPI } from '../services/api'

interface Room {
  id: string
  name: string
  status: string
  created_at: string
}

export default function DashboardPage() {
  const [rooms, setRooms] = useState<Room[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newRoomName, setNewRoomName] = useState('')
  const { user, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    loadRooms()
  }, [])

  const loadRooms = async () => {
    try {
      const data = await roomsAPI.list('active')
      setRooms(data)
    } catch (error) {
      console.error('Failed to load rooms:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateRoom = async () => {
    if (!newRoomName.trim()) return

    try {
      const room = await roomsAPI.create(newRoomName)
      setShowCreateModal(false)
      setNewRoomName('')
      navigate(`/meeting/${room.id}`)
    } catch (error) {
      console.error('Failed to create room:', error)
    }
  }

  const handleJoinRoom = async (roomId: string) => {
    navigate(`/meeting/${roomId}`)
  }

  const handleLogout = () => {
    clearAuth()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <nav className="bg-gray-800 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-white">AI Meeting</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-300">
                {user?.full_name || user?.username}
                {user?.is_admin && (
                  <span className="ml-2 px-2 py-1 bg-blue-600 text-xs rounded">
                    Admin
                  </span>
                )}
              </span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-3xl font-bold text-white">Meeting Rooms</h2>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Create Room
            </button>
          </div>

          {loading ? (
            <div className="text-center text-gray-400">Loading...</div>
          ) : rooms.length === 0 ? (
            <div className="text-center text-gray-400 py-12">
              <p>No active rooms. Create one to get started!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {rooms.map((room) => (
                <div
                  key={room.id}
                  className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition"
                >
                  <h3 className="text-xl font-semibold text-white mb-2">
                    {room.name}
                  </h3>
                  <p className="text-gray-400 text-sm mb-4">
                    Created {new Date(room.created_at).toLocaleDateString()}
                  </p>
                  <button
                    onClick={() => handleJoinRoom(room.id)}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    Join Room
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Create Room Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-2xl font-bold text-white mb-4">Create Room</h3>
            <input
              type="text"
              placeholder="Room name"
              className="w-full px-4 py-2 bg-gray-700 text-white rounded mb-4"
              value={newRoomName}
              onChange={(e) => setNewRoomName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleCreateRoom()}
            />
            <div className="flex space-x-4">
              <button
                onClick={handleCreateRoom}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Create
              </button>
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
