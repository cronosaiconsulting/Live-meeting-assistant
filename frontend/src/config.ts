/**
 * Frontend configuration from environment variables.
 */

export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  liveKitUrl: import.meta.env.VITE_LIVEKIT_URL || 'ws://localhost:7880',
}
