# AI-Enhanced Video Meeting PoC - Architecture Specification

**Document Version:** 1.0
**Date:** November 2025
**Status:** Production-Ready Design

---

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [Exact Tech Stack & Libraries](#2-exact-tech-stack--libraries)
3. [Database Schema](#3-database-schema)
4. [Repository Structure](#4-repository-structure)
5. [Configuration & Environment Design](#5-configuration--environment-design)
6. [README and Setup Flow](#6-readme-and-setup-flow)
7. [Implementation Plan and Risks](#7-implementation-plan-and-risks)

---

## 1. High-Level Architecture

### 1.1 System Overview

The system consists of **6 primary components** orchestrated through Docker Compose on a dedicated Ubuntu server:

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLIENT BROWSERS                            │
│  ┌──────────────────┐              ┌──────────────────┐            │
│  │  Admin User      │              │  Participant     │            │
│  │  - Video Grid    │              │  - Video Grid    │            │
│  │  - Transcript UI │              │  - Basic UI      │            │
│  │  - Thought Board │              │                  │            │
│  └────────┬─────────┘              └────────┬─────────┘            │
└───────────┼──────────────────────────────────┼──────────────────────┘
            │                                  │
            │ HTTPS/WSS                        │ HTTPS/WSS
            │                                  │
┌───────────┼──────────────────────────────────┼──────────────────────┐
│           │         NGINX REVERSE PROXY      │                      │
│           │         (Port 443/80)            │                      │
└───────────┼──────────────────────────────────┼──────────────────────┘
            │                                  │
    ┌───────┴────────┐                ┌───────┴────────┐
    │                │                │                │
┌───▼──────────┐ ┌──▼─────────────┐ ┌▼────────────────▼─┐
│  FRONTEND    │ │  BACKEND       │ │  LIVEKIT SFU      │
│  (React+TS)  │ │  (FastAPI)     │ │  (Media Server)   │
│  Port: 3000  │ │  Port: 8000    │ │  Port: 7880/7881  │
│              │ │                │ │                   │
│  - LiveKit   │ │  - Auth        │ │  - WebRTC         │
│    SDK       │ │  - WebSocket   │ │  - Audio/Video    │
│  - Video UI  │ │    Server      │ │    Routing        │
│  - WS Client │ │  - REST API    │ │                   │
└──────────────┘ └────┬───────────┘ └─────────┬─────────┘
                      │                       │
                      │                       │
                      │                  ┌────▼──────────┐
                      │                  │  LIVEKIT      │
                      │                  │  AGENT        │
                      │                  │  (Python)     │
                      │                  │               │
                      │                  │  - Track      │
                      │                  │    Subscribe  │
                      │                  │  - Audio      │
                      │                  │    Extraction │
                      │                  └────┬──────────┘
                      │                       │
                      │                       │ Audio
                      │                       │ Chunks
                      │                       │
                ┌─────▼───────┐         ┌─────▼──────────┐
                │ POSTGRESQL  │         │ STT SERVICE    │
                │ Port: 5432  │         │ (WhisperLive)  │
                │             │         │ Port: 9090     │
                │ - users     │         │                │
                │ - rooms     │         │ - WebSocket    │
                │ - trans...  │         │ - faster-      │
                │ - ai_tho... │         │   whisper      │
                └─────┬───────┘         └────┬───────────┘
                      │                      │
                      │                      │ Transcript
                      │                      │ Results
                      │                      │
                      └──────────┬───────────┘
                                 │
                                 │
                         ┌───────▼────────┐
                         │  LLM SERVICE   │
                         │  (KIMI K2)     │
                         │  External API  │
                         │                │
                         │  - Receives    │
                         │    Transcripts │
                         │  - Generates   │
                         │    Insights    │
                         └────────────────┘
```

### 1.2 Key Data Flows

#### Flow 1: User Authentication & Room Join

```
1. User opens browser → Frontend
2. Frontend → Backend: POST /api/auth/login {username, password}
3. Backend → PostgreSQL: Verify credentials
4. Backend → Frontend: JWT token + user metadata (is_admin flag)
5. Frontend stores JWT in localStorage

6. User clicks "Join Meeting" → Frontend
7. Frontend → Backend: POST /api/rooms/join {room_id, JWT}
8. Backend validates JWT, checks permissions
9. Backend → LiveKit: Generate access token (using LiveKit API)
10. Backend → PostgreSQL: Insert participant record
11. Backend → Frontend: {livekit_token, room_name, participant_id}

12. Frontend → LiveKit SFU: Connect with token (WebRTC signaling)
13. LiveKit SFU ↔ Frontend: Establish WebRTC media streams
```

#### Flow 2: Real-Time Audio Transcription

```
1. LiveKit Agent starts on room creation
2. Agent → LiveKit SFU: Subscribe to all participant audio tracks
3. Agent receives real-time audio frames (PCM format)

4. For each participant:
   a. Agent buffers audio chunks (e.g., 0.5-1 second segments)
   b. Agent → STT Service: Stream audio via WebSocket
      {
        "participant_id": "user123",
        "audio": "<base64_encoded_pcm>",
        "sample_rate": 16000,
        "timestamp": 1700000000.123
      }

5. STT Service (WhisperLive):
   a. Receives audio chunks
   b. Applies Voice Activity Detection (VAD)
   c. Processes through faster-whisper model
   d. Generates partial/incremental transcripts

6. STT Service → Agent: Transcript results via WebSocket
   {
     "participant_id": "user123",
     "text": "Hello, how are you doing today?",
     "is_final": false,
     "timestamp": 1700000001.456,
     "confidence": 0.94
   }

7. Agent → Backend API: POST /api/transcripts/segment
   {
     "room_id": "room456",
     "participant_id": "user123",
     "text": "Hello, how are you doing today?",
     "timestamp": 1700000001.456,
     "is_final": false,
     "confidence": 0.94
   }

8. Backend:
   a. Saves to PostgreSQL (transcript_segments table)
   b. Broadcasts to all admin WebSocket clients
      via internal pub/sub (Redis)

9. Backend → Frontend (Admin): WebSocket message
   {
     "type": "transcript_update",
     "data": {
       "participant_id": "user123",
       "participant_name": "John Doe",
       "text": "Hello, how are you doing today?",
       "timestamp": 1700000001.456,
       "is_final": false
     }
   }

10. Frontend (Admin): Updates transcript UI in right panel
```

#### Flow 3: AI "Thought Board" Generation

```
1. Backend has aggregator service running
2. Aggregator monitors new transcript_segments
   (via PostgreSQL LISTEN/NOTIFY or polling)

3. When N new segments accumulated (e.g., every 5-10 seconds):
   a. Aggregator fetches recent context:
      - Last 20 transcript segments
      - Current thought board state
      - Participant metadata

   b. Aggregator → KIMI K2 API: POST /v1/chat/completions
      {
        "model": "kimi-k2-instruct",
        "messages": [
          {
            "role": "system",
            "content": "You are an AI meeting assistant analyzing a live conversation..."
          },
          {
            "role": "user",
            "content": "Transcripts:\n[John]: Hello, how are you...\n[Jane]: I'm doing well...\n\nPrevious insights:\n- Topic: Greetings\n\nGenerate updated insights in JSON format..."
          }
        ],
        "temperature": 0.7,
        "stream": false
      }

   c. KIMI K2 API → Aggregator: Response
      {
        "choices": [{
          "message": {
            "content": "{\"topics\": [...], \"action_items\": [...], \"questions\": [...], \"summaries\": [...]}"
          }
        }]
      }

   d. Aggregator parses JSON response
   e. Aggregator → PostgreSQL: Insert/Update ai_thoughts table

   f. Aggregator → Backend WebSocket: Broadcast event

4. Backend → Frontend (Admin): WebSocket message
   {
     "type": "thought_board_update",
     "data": {
       "topics": [
         {"id": "t1", "name": "Project Timeline", "mentions": 3}
       ],
       "action_items": [
         {"id": "a1", "text": "Schedule follow-up", "assignee": "John"}
       ],
       "questions": [
         {"id": "q1", "text": "What's the budget?", "asked_by": "Jane"}
       ],
       "summaries": [
         {"participant": "John", "stance": "Optimistic about timeline"}
       ],
       "timestamp": 1700000010.789
     }
   }

5. Frontend (Admin): Updates thought board UI in right panel
```

### 1.3 Future Extension Points

The architecture is designed with clear extension points for future AI capabilities:

#### Extension Point 1: Video Analytics Module

**Location:** New microservice container `video-analytics`

**Integration:**
```
┌─────────────────┐
│ LIVEKIT AGENT  │
│ (Enhanced)     │
└────┬───────────┘
     │
     ├─ Audio Track → STT Service (existing)
     │
     └─ Video Track → Video Analytics Service (new)
                      │
                      ├─ Facial Expression Detection
                      ├─ Gaze Tracking
                      ├─ Posture Analysis
                      └─ Engagement Scoring
```

**Interface:**
- Protocol: gRPC streaming or WebSocket
- Input: H.264/VP8 video frames @ 15-30 FPS
- Output: JSON events with emotion scores, attention metrics
- Storage: New table `video_analytics_events`

**Constraints:**
- GPU required (NVIDIA T4 or better)
- ~4-8 GB VRAM per concurrent stream
- Latency target: 200-500ms per frame
- Bandwidth: ~1-3 Mbps per video track

#### Extension Point 2: Audio Analytics Module

**Location:** Parallel processing in LiveKit Agent or separate service

**Integration:**
```
┌─────────────────┐
│ LIVEKIT AGENT  │
│ (Enhanced)     │
└────┬───────────┘
     │
     └─ Audio Track ─┬─ STT Service (existing)
                     │
                     └─ Audio Analytics (new)
                        │
                        ├─ Emotion Detection (prosody)
                        ├─ Tone Analysis
                        ├─ Speaking Rate
                        └─ Voice Stress Detection
```

**Interface:**
- Input: Raw PCM audio (same as STT input)
- Models: wav2vec2-based emotion classifiers, prosody analyzers
- Output: JSON events with emotion labels, confidence scores
- Storage: New table `audio_analytics_events`

**Constraints:**
- CPU-intensive (can run on same hardware as STT)
- ~2-4 CPU cores per concurrent stream
- Latency: 300-800ms (can be async to transcription)

#### Extension Point 3: Multimodal AI Reasoning

**Location:** Enhanced LLM aggregator service

**Integration:**
```
┌──────────────────────────────────────┐
│     ENHANCED AGGREGATOR SERVICE      │
└──┬───────────────────────────────────┘
   │
   ├─ Transcript Segments (existing)
   ├─ Video Analytics Events (new)
   ├─ Audio Analytics Events (new)
   └─ Screen Share Content (future)
        │
        ├─ Combine all inputs
        └─ Send to multimodal LLM
           (e.g., GPT-4V, Gemini Pro Vision, or KIMI K2 multimodal)
```

**Implementation:**
- Use message queue (Redis Streams or RabbitMQ) to aggregate events
- Batch multimodal inputs every 5-15 seconds
- Feed combined context to LLM with vision capabilities
- Generate richer insights (e.g., "John looks confused while discussing budget")

#### Extension Point 4: Event Bus Architecture (Recommended for Scale)

For production scale, introduce a message broker:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ STT Service │────▶│   REDIS     │◀────│Video Analyt.│
└─────────────┘     │   STREAMS   │     └─────────────┘
                    │   (or       │
┌─────────────┐     │  RabbitMQ)  │     ┌─────────────┐
│Audio Analyt.│────▶│             │◀────│ Aggregator  │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Benefits:**
- Decouples services
- Enables replay/debugging
- Supports horizontal scaling
- Allows multiple consumers

---

## 2. Exact Tech Stack & Libraries

### 2.1 Frontend Stack

#### Core Framework
- **React 18.3+** with **TypeScript 5.3+**
  - *Justification:* Industry standard for building interactive UIs. TypeScript provides type safety crucial for complex WebRTC/real-time state management. React 18's concurrent features help with smooth UI updates during high-frequency transcript/video stream updates.

- **Vite 5.x** (Build Tool)
  - *Justification:* Fastest dev server with HMR, superior to Create React App or Webpack. ESBuild-based bundling is 10-100x faster than traditional bundlers. Native ESM support aligns with modern JavaScript. Simpler configuration than Next.js for a SPA-focused app like this PoC.

#### UI & Styling
- **TailwindCSS 3.4+**
  - *Justification:* Utility-first CSS enables rapid UI development without CSS file overhead. Tree-shaking removes unused styles. Works seamlessly with component libraries. Better than styled-components for prototyping speed.

- **shadcn/ui** (Component Library)
  - *Justification:* Accessible, customizable React components built on Radix UI primitives. Copy-paste approach (not npm package) means full control. Pre-built with TailwindCSS. Includes essential components: buttons, modals, dropdowns, etc. Better than Material-UI (less opinionated) or Ant Design (heavier).

#### WebRTC & Real-Time
- **@livekit/components-react ^2.6+**
  - *Justification:* Official LiveKit React components including VideoConference pre-built UI, participant grids, audio/video controls. Handles 90% of WebRTC UI complexity out-of-the-box.

- **@livekit/react-core ^1.6+**
  - *Justification:* React hooks for LiveKit: `useRoom`, `useParticipants`, `useTrack`, etc. Provides programmatic access to LiveKit state for custom UI.

- **livekit-client ^2.6+**
  - *Justification:* Core TypeScript SDK for LiveKit. Manages WebRTC connections, media tracks, signaling.

#### WebSocket Client
- **Socket.io-client ^4.7+** or **native WebSocket API**
  - *Justification:* For backend real-time communication (transcripts, thought board updates). Socket.io provides automatic reconnection, fallback transports, rooms/namespaces. Native WebSocket is lighter if you implement reconnection logic manually. **Recommendation: Socket.io-client** for robustness.

#### State Management
- **Zustand 4.x** (lightweight) or **React Context** (built-in)
  - *Justification:* Zustand is minimal (1KB), no boilerplate, perfect for global state (user auth, room metadata, transcript history). Avoids Redux complexity. React Context works for smaller state scope.

#### Key NPM Packages
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "livekit-client": "^2.6.0",
    "@livekit/components-react": "^2.6.0",
    "@livekit/react-core": "^1.6.0",
    "socket.io-client": "^4.7.2",
    "zustand": "^4.5.0",
    "axios": "^1.6.0",
    "react-router-dom": "^6.21.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.3",
    "vite": "^5.0.11",
    "tailwindcss": "^3.4.1",
    "autoprefixer": "^10.4.17",
    "postcss": "^8.4.33",
    "eslint": "^8.56.0",
    "prettier": "^3.2.0"
  }
}
```

---

### 2.2 Backend Stack

#### Core Framework
- **FastAPI 0.109+**
  - *Justification:* Modern async Python framework built on Starlette (ASGI). Native async/await support crucial for WebSocket handling and concurrent I/O (database, STT, LLM). Automatic OpenAPI docs. Type hints with Pydantic validation. Superior to Flask (sync-first) or Django (monolithic).

- **Uvicorn 0.27+** (ASGI Server)
  - *Justification:* Lightning-fast ASGI server using uvloop (async I/O library). Production-ready. Better than Hypercorn or Daphne for raw performance.

#### Database ORM & Migrations
- **SQLAlchemy 2.0+** (async mode)
  - *Justification:* Industry-standard ORM with mature async support (since 1.4, refined in 2.0). Supports complex queries, relationships, transactions. Works with asyncpg driver.

- **asyncpg 0.29+**
  - *Justification:* Fastest PostgreSQL driver for Python (3-5x faster than psycopg). Built from ground-up for asyncio. Required for SQLAlchemy async engine.

- **Alembic 1.13+**
  - *Justification:* Official migration tool for SQLAlchemy. Supports async mode. Handles schema versioning, rollbacks.

#### Authentication
- **python-jose[cryptography] 3.3+**
  - *Justification:* JWT creation/validation. Supports RS256, HS256 algorithms.

- **passlib[bcrypt] 1.7+**
  - *Justification:* Password hashing with bcrypt (OWASP recommended). Slow hashing prevents brute-force.

- **python-multipart 0.0.6+**
  - *Justification:* Required for FastAPI form data parsing (login endpoints).

#### LiveKit Integration
- **livekit 0.12+** (LiveKit Server SDK)
  - *Justification:* Official Python SDK for LiveKit server APIs. Generates access tokens, manages rooms, participants. Provides `AccessToken` class.

- **livekit-agents 1.2+** (LiveKit Agents Framework)
  - *Justification:* Framework for building server-side participants that can subscribe to audio/video tracks. Handles track subscriptions, audio buffering, frame processing. Essential for extracting participant audio for STT.

#### STT Integration
- **websockets 12.0+**
  - *Justification:* Async WebSocket client for connecting to WhisperLive service. Standard library for Python async WebSocket.

#### LLM Integration
- **httpx 0.26+**
  - *Justification:* Modern async HTTP client. Used for calling KIMI K2 API. Supports connection pooling, timeouts, retries. Better than requests (sync) or aiohttp (lower-level).

#### WebSocket Server (for frontend)
- **Socket.IO** via **python-socketio 5.11+** + **aiohttp** integration
  - *Justification:* Provides Socket.IO protocol support on backend. Auto-handles reconnection, rooms, broadcasting. Integrates with FastAPI via middleware.
  - *Alternative:* FastAPI native WebSocket (lighter but requires manual reconnection logic).
  - **Recommendation: python-socketio** for feature parity with frontend.

#### Message Broker (for pub/sub)
- **Redis 5.0+** via **redis[hiredis] 5.0+** (Python client)
  - *Justification:* In-memory pub/sub for broadcasting transcript/thought board updates to multiple WebSocket connections. Also used for caching. Hiredis parser for speed.

#### Configuration Management
- **pydantic-settings 2.1+**
  - *Justification:* Type-safe environment variable loading. Integrates with Pydantic. Supports .env files, validation, defaults.

#### Key Python Packages
```
# requirements.txt
fastapi==0.109.2
uvicorn[standard]==0.27.1
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.6.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
livekit==0.12.0
livekit-agents==1.2.18
websockets==12.0
httpx==0.26.0
redis[hiredis]==5.0.1
python-socketio==5.11.0
python-dotenv==1.0.0
```

---

### 2.3 LiveKit SFU

#### Deployment
- **LiveKit Server (Docker Image)**
  - Image: `livekit/livekit-server:v1.7+`
  - *License:* Apache 2.0 (commercial use allowed)
  - *Justification:* Official Docker image with all dependencies. Self-hosted, no vendor lock-in. Supports 100k+ concurrent users with horizontal scaling.

#### Configuration
- **livekit.yaml** config file mounted to container
  - Defines ports, API keys, TURN server (optional), logging

---

### 2.4 STT Service

#### Selected Engine: **WhisperLive** (by Collabora)

**Comparison of Top 3 Options:**

| Feature | WhisperLive | Vosk | whisper_streaming |
|---------|-------------|------|-------------------|
| **Streaming Support** | ✅ WebSocket streaming | ✅ WebSocket/gRPC | ✅ HTTP streaming |
| **Backend** | faster-whisper (CTranslate2) | Kaldi-based models | Whisper + chunking |
| **Latency** | ~300-800ms (with VAD) | ~100-300ms | ~500-1500ms |
| **Accuracy** | High (Whisper-based) | Medium | High (Whisper) |
| **GPU Support** | ✅ CUDA, OpenVINO, TensorRT | ❌ CPU only | ✅ CUDA |
| **CPU Efficiency** | High (CTranslate2 optimized) | Very High | Medium |
| **VAD Included** | ✅ Yes (Silero VAD) | ✅ Yes | ❌ No |
| **Multi-language** | 99 languages | 20+ languages | 99 languages |
| **Docker Ready** | ✅ Official Dockerfile | ✅ Community images | ⚠️ Manual setup |
| **API Design** | WebSocket (JSON messages) | WebSocket/gRPC | HTTP POST chunks |
| **License** | MIT | Apache 2.0 | MIT |
| **Maintenance** | Active (Collabora, 2025) | Active | Archived (use SimulStreaming) |
| **Resource Usage** | ~4-8GB VRAM (GPU) / 2-4 CPU cores | ~1-2 CPU cores | ~8-16GB VRAM (GPU) |

**Decision: WhisperLive**

**Justification:**
1. **Streaming-first design:** Built specifically for real-time transcription with WebSocket API
2. **faster-whisper backend:** 4x faster than OpenAI Whisper with same accuracy (CTranslate2 optimization)
3. **Built-in VAD:** Silero VAD reduces unnecessary processing when no speech detected
4. **Production-ready:** Actively maintained by Collabora, Docker support, MIT license
5. **Flexible deployment:** CPU mode for cost, GPU mode for speed (TensorRT/CUDA/OpenVINO)
6. **Language support:** Matches Whisper's 99 languages
7. **Commercial-friendly:** MIT license, no restrictions

**Deployment:**
- **Docker Image:** Custom Dockerfile based on `collabora/whisperlive`
- **Model:** `faster-whisper-large-v3` (best accuracy) or `medium` (balanced)
- **Hardware:**
  - CPU mode: 4 cores, 8GB RAM, ~1-2s latency
  - GPU mode: NVIDIA T4+ (8GB VRAM), ~300-500ms latency

#### Audio Pipeline Configuration
- **Input Format:** 16kHz mono PCM (extracted from LiveKit opus/PCM frames)
- **Chunk Size:** 512-1024 samples (~32-64ms @ 16kHz)
- **Buffer Strategy:** Sliding window with 250ms overlap to avoid word cuts
- **VAD Threshold:** 0.5 (Silero VAD confidence)

---

### 2.5 LLM Service

#### KIMI K2 Integration

**API Details:**
- **Provider:** Moonshot AI
- **Endpoint:** `https://platform.moonshot.ai/v1/chat/completions`
- **Compatibility:** OpenAI API compatible
- **Model:** `kimi-k2-instruct` (general-purpose chat) or `kimi-k2-thinking` (reasoning)
- **License:** Open-source model (Apache 2.0), hosted API (commercial terms)

**Usage Pattern:**
```python
import httpx

async def get_thought_board_update(transcripts: list[dict], context: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://platform.moonshot.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {KIMI_API_KEY}"},
            json={
                "model": "kimi-k2-instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": MEETING_ANALYSIS_PROMPT
                    },
                    {
                        "role": "user",
                        "content": format_transcripts(transcripts)
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2000,
                "stream": False
            },
            timeout=30.0
        )
        return response.json()
```

**Context Management Strategy:**
- **Sliding window:** Keep last 50 transcript segments (~2-5 minutes)
- **Summarization:** Every 100 segments, summarize older context to compress
- **Incremental updates:** Send delta (new transcripts) + current state
- **Token budget:** ~3000 tokens input, ~1000 tokens output per request
- **Rate limiting:** Max 1 request per 5-10 seconds

---

### 2.6 Database

#### PostgreSQL 16+
- **Docker Image:** `postgres:16-alpine`
- *Justification:* Latest stable. Alpine for smaller image. Mature, ACID-compliant, excellent JSON support (for ai_thoughts storage), LISTEN/NOTIFY for real-time events.

#### Connection Pooling
- **PgBouncer** (optional for production)
  - Image: `pgbouncer/pgbouncer:latest`
  - *Justification:* Reduces connection overhead. Essential if scaling backend horizontally.

---

### 2.7 Reverse Proxy & SSL

#### Nginx 1.25+
- **Docker Image:** `nginx:1.25-alpine`
- *Justification:* Industry standard. Handles SSL termination, WebSocket upgrades, static file serving, load balancing.

#### SSL Certificates
- **Let's Encrypt** via **Certbot**
  - *Justification:* Free, automated, trusted CA. Required for WebRTC (HTTPS/WSS).

---

### 2.8 Containerization & Orchestration

#### Docker 24+ & Docker Compose 2.23+
- *Justification:* Standard containerization. Compose simplifies multi-service orchestration for PoC. Easy migration to Kubernetes later.

---

### 2.9 Development Tools

#### Code Quality
- **ESLint** + **Prettier** (frontend)
- **Ruff** (Python linter/formatter, replaces flake8+black, 10-100x faster)
- **mypy** (Python type checking)

#### Testing (for future phases)
- **Pytest** (backend)
- **Vitest** (frontend, Vite-native)

---

## 3. Database Schema

### 3.1 Schema Design Principles

- **Normalization:** 3NF to reduce redundancy
- **Indexes:** On foreign keys, timestamp columns, frequently queried fields
- **Soft Deletes:** `deleted_at` columns for audit trails (not in PoC, but noted for future)
- **UUIDs:** Primary keys as UUIDs for distributed systems (future-proof)
- **Timestamps:** `created_at`, `updated_at` on all tables

### 3.2 Tables

#### Table: `users`

Stores user accounts with authentication credentials.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- bcrypt hash
    full_name VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_admin ON users(is_admin);
```

**Fields:**
- `id`: UUID primary key
- `username`: Unique login identifier
- `email`: Unique email (for future password reset)
- `password_hash`: bcrypt/argon2 hashed password (cost factor 12+)
- `full_name`: Display name
- `is_admin`: Admin flag (grants access to transcript/thought board UI)
- `is_active`: Soft disable account
- `created_at`, `updated_at`: Audit timestamps

**Relationships:**
- One-to-many with `participants`

**Notes:**
- No self-service signup in PoC. Users created via admin script or seed data.
- Future: Add `oauth_provider`, `oauth_id` for SSO.

---

#### Table: `rooms`

Represents meeting rooms.

```sql
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    livekit_room_name VARCHAR(255) UNIQUE NOT NULL, -- Maps to LiveKit room
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'active', -- active, ended, archived
    scheduled_start TIMESTAMP WITH TIME ZONE,
    actual_start TIMESTAMP WITH TIME ZONE,
    actual_end TIMESTAMP WITH TIME ZONE,
    metadata JSONB, -- Extensible storage for future fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_rooms_status ON rooms(status);
CREATE INDEX idx_rooms_livekit_room_name ON rooms(livekit_room_name);
CREATE INDEX idx_rooms_created_by ON rooms(created_by_user_id);
CREATE INDEX idx_rooms_scheduled_start ON rooms(scheduled_start);
```

**Fields:**
- `id`: UUID primary key
- `name`: Human-readable room name ("Team Standup", "Sales Call")
- `livekit_room_name`: Unique identifier passed to LiveKit (e.g., `room_abc123`)
- `created_by_user_id`: User who created the room
- `status`: Lifecycle state (active, ended, archived)
- `scheduled_start`, `actual_start`, `actual_end`: Timing metadata
- `metadata`: JSONB for extensibility (e.g., recording settings, AI config)

**Relationships:**
- One-to-many with `participants`, `transcript_segments`, `ai_thoughts`

---

#### Table: `participants`

Tracks user participation in rooms.

```sql
CREATE TABLE participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    livekit_identity VARCHAR(255) NOT NULL, -- LiveKit participant identity
    display_name VARCHAR(255),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    left_at TIMESTAMP WITH TIME ZONE,
    role VARCHAR(50) DEFAULT 'participant', -- participant, moderator
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(room_id, livekit_identity)
);

-- Indexes
CREATE INDEX idx_participants_room_id ON participants(room_id);
CREATE INDEX idx_participants_user_id ON participants(user_id);
CREATE INDEX idx_participants_livekit_identity ON participants(livekit_identity);
CREATE INDEX idx_participants_joined_at ON participants(joined_at);
```

**Fields:**
- `id`: UUID primary key
- `room_id`: Foreign key to `rooms`
- `user_id`: Foreign key to `users` (nullable for guest support in future)
- `livekit_identity`: LiveKit participant ID (used in tokens, track subscriptions)
- `display_name`: Name shown in UI
- `joined_at`, `left_at`: Session duration
- `role`: Participant role (for future permissions)
- `metadata`: JSONB for extensibility (e.g., device info, network stats)

**Relationships:**
- Many-to-one with `rooms`, `users`
- One-to-many with `transcript_segments`

**Unique Constraint:**
- `(room_id, livekit_identity)`: Prevents duplicate entries

---

#### Table: `transcript_segments`

Stores speech-to-text results per participant.

```sql
CREATE TABLE transcript_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    participant_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    start_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    end_timestamp TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER, -- Milliseconds
    is_final BOOLEAN DEFAULT FALSE, -- Partial vs final transcript
    confidence FLOAT, -- STT confidence score (0.0-1.0)
    language_code VARCHAR(10), -- e.g., "en", "es"
    metadata JSONB, -- STT-specific metadata (e.g., word timings)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_transcript_room_id ON transcript_segments(room_id);
CREATE INDEX idx_transcript_participant_id ON transcript_segments(participant_id);
CREATE INDEX idx_transcript_start_timestamp ON transcript_segments(start_timestamp);
CREATE INDEX idx_transcript_is_final ON transcript_segments(is_final);
```

**Fields:**
- `id`: UUID primary key
- `room_id`: Foreign key to `rooms`
- `participant_id`: Foreign key to `participants`
- `text`: Transcribed text
- `start_timestamp`: When speech started (wall-clock time)
- `end_timestamp`: When speech ended (for final segments)
- `duration_ms`: Speech duration in milliseconds
- `is_final`: `false` for partial results, `true` for final
- `confidence`: STT confidence score (0.0-1.0)
- `language_code`: Detected language (ISO 639-1)
- `metadata`: JSONB for word-level timings, alternatives, etc.

**Relationships:**
- Many-to-one with `rooms`, `participants`

**Indexing Strategy:**
- `(room_id, start_timestamp)`: For fetching transcripts by time range
- `(participant_id, start_timestamp)`: For per-speaker queries

**Notes:**
- Partial results updated in-place or append-only? **Recommendation: Append-only** with `is_final` flag. Frontend deduplicates.
- For production, partition by `room_id` or time for performance.

---

#### Table: `ai_thoughts`

Stores AI-generated insights for the "thought board".

```sql
CREATE TABLE ai_thoughts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    participant_id UUID REFERENCES participants(id) ON DELETE SET NULL, -- Nullable (thought may apply to room, not specific participant)
    thought_type VARCHAR(50) NOT NULL, -- topic, action_item, question, summary, sentiment
    content JSONB NOT NULL, -- Structured thought data
    confidence FLOAT, -- AI confidence score
    source_transcript_ids UUID[], -- Array of transcript segment IDs used
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ai_thoughts_room_id ON ai_thoughts(room_id);
CREATE INDEX idx_ai_thoughts_participant_id ON ai_thoughts(participant_id);
CREATE INDEX idx_ai_thoughts_type ON ai_thoughts(thought_type);
CREATE INDEX idx_ai_thoughts_timestamp ON ai_thoughts(timestamp);
CREATE INDEX idx_ai_thoughts_source_transcripts ON ai_thoughts USING GIN(source_transcript_ids);
```

**Fields:**
- `id`: UUID primary key
- `room_id`: Foreign key to `rooms`
- `participant_id`: Foreign key to `participants` (nullable for room-wide thoughts)
- `thought_type`: Category of insight
  - `topic`: Detected discussion topic
  - `action_item`: Identified action item
  - `question`: Detected question
  - `summary`: Summary of participant's stance
  - `sentiment`: Sentiment analysis
  - `engagement`: Engagement score (future)
- `content`: JSONB with structured data, e.g.:
  ```json
  {
    "title": "Budget Discussion",
    "description": "Team is discussing Q2 budget allocation",
    "keywords": ["budget", "Q2", "allocation"],
    "participants_mentioned": ["user123", "user456"],
    "priority": "high"
  }
  ```
- `confidence`: AI model confidence (0.0-1.0)
- `source_transcript_ids`: Array of `transcript_segments.id` that informed this thought
- `timestamp`: When thought was generated
- `metadata`: Extensible JSONB (model version, prompt used, etc.)

**Relationships:**
- Many-to-one with `rooms`, `participants`

**Indexing:**
- GIN index on `source_transcript_ids` for fast reverse lookup
- Index on `(room_id, timestamp)` for chronological queries

**Example Queries:**
```sql
-- Get all action items for a room
SELECT * FROM ai_thoughts
WHERE room_id = '...' AND thought_type = 'action_item'
ORDER BY timestamp DESC;

-- Get all thoughts referencing a specific transcript
SELECT * FROM ai_thoughts
WHERE '...' = ANY(source_transcript_ids);
```

---

### 3.3 Seed Data (Development/Testing)

```sql
-- Insert admin user (password: "admin123", hashed with bcrypt)
INSERT INTO users (username, email, password_hash, full_name, is_admin) VALUES
('admin', 'admin@example.com', '$2b$12$KIXxLVZ5qZ.eJ9zZ5qZ.eO...', 'Admin User', TRUE);

-- Insert test user (password: "user123")
INSERT INTO users (username, email, password_hash, full_name, is_admin) VALUES
('john', 'john@example.com', '$2b$12$KIXxLVZ5qZ.eJ9zZ5qZ.eO...', 'John Doe', FALSE),
('jane', 'jane@example.com', '$2b$12$KIXxLVZ5qZ.eJ9zZ5qZ.eO...', 'Jane Smith', FALSE);
```

---

### 3.4 Future Schema Extensions

#### For Video Analytics:
```sql
CREATE TABLE video_analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    participant_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- emotion, gaze, posture
    data JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confidence FLOAT
);
```

#### For Audio Analytics:
```sql
CREATE TABLE audio_analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    participant_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- emotion, tone, stress
    data JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confidence FLOAT
);
```

---

## 4. Repository Structure

```
/
├── .env.example              # Environment variable template
├── .gitignore                # Ignore .env, node_modules, __pycache__, etc.
├── docker-compose.yml        # Multi-service orchestration
├── README.md                 # Setup and usage guide
├── ARCHITECTURE.md           # This document
├── LICENSE                   # Project license (e.g., MIT)
│
├── frontend/                 # React + TypeScript frontend
│   ├── .env.example          # Frontend-specific env vars
│   ├── package.json          # NPM dependencies
│   ├── package-lock.json
│   ├── tsconfig.json         # TypeScript config
│   ├── vite.config.ts        # Vite config
│   ├── tailwind.config.js    # TailwindCSS config
│   ├── postcss.config.js     # PostCSS config (for Tailwind)
│   ├── index.html            # HTML entry point
│   ├── Dockerfile            # Multi-stage build for production
│   ├── nginx.conf            # Nginx config for serving SPA
│   │
│   ├── public/               # Static assets
│   │   └── favicon.ico
│   │
│   └── src/
│       ├── main.tsx          # React entry point
│       ├── App.tsx           # Root component
│       ├── vite-env.d.ts     # Vite type definitions
│       │
│       ├── components/       # Reusable UI components
│       │   ├── ui/           # shadcn/ui components (button, modal, etc.)
│       │   ├── VideoGrid.tsx # LiveKit video grid
│       │   ├── TranscriptPanel.tsx
│       │   ├── ThoughtBoard.tsx
│       │   └── ...
│       │
│       ├── pages/            # Route-level pages
│       │   ├── LoginPage.tsx
│       │   ├── MeetingPage.tsx
│       │   └── ...
│       │
│       ├── hooks/            # Custom React hooks
│       │   ├── useAuth.ts
│       │   ├── useLiveKit.ts
│       │   ├── useTranscript.ts
│       │   └── useThoughtBoard.ts
│       │
│       ├── services/         # API clients
│       │   ├── api.ts        # Axios instance with auth
│       │   ├── auth.service.ts
│       │   ├── room.service.ts
│       │   └── socket.service.ts # Socket.IO client
│       │
│       ├── stores/           # Zustand stores
│       │   ├── authStore.ts
│       │   └── roomStore.ts
│       │
│       ├── types/            # TypeScript types
│       │   ├── user.ts
│       │   ├── room.ts
│       │   ├── transcript.ts
│       │   └── thoughtBoard.ts
│       │
│       ├── utils/            # Utility functions
│       │   └── formatters.ts
│       │
│       └── styles/           # Global styles (if needed)
│           └── index.css
│
├── backend/                  # FastAPI Python backend
│   ├── .env.example          # Backend-specific env vars
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile            # Multi-stage build
│   ├── alembic.ini           # Alembic config
│   │
│   ├── alembic/              # Database migrations
│   │   ├── env.py            # Alembic environment (async mode)
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   │
│   └── app/
│       ├── main.py           # FastAPI app entry point
│       ├── config.py         # Pydantic settings (loads .env)
│       ├── dependencies.py   # Dependency injection (DB session, auth)
│       │
│       ├── api/              # API routes
│       │   ├── __init__.py
│       │   ├── auth.py       # POST /api/auth/login, /logout
│       │   ├── rooms.py      # POST /api/rooms/create, /join
│       │   ├── transcripts.py # POST /api/transcripts/segment
│       │   └── thoughts.py   # GET /api/thoughts/{room_id}
│       │
│       ├── models/           # SQLAlchemy models
│       │   ├── __init__.py
│       │   ├── user.py
│       │   ├── room.py
│       │   ├── participant.py
│       │   ├── transcript.py
│       │   └── ai_thought.py
│       │
│       ├── schemas/          # Pydantic schemas (request/response)
│       │   ├── __init__.py
│       │   ├── user.py
│       │   ├── room.py
│       │   ├── transcript.py
│       │   └── thought.py
│       │
│       ├── services/         # Business logic
│       │   ├── __init__.py
│       │   ├── auth_service.py
│       │   ├── livekit_service.py # Generate tokens, manage rooms
│       │   ├── transcript_service.py
│       │   ├── llm_service.py # KIMI K2 integration
│       │   └── websocket_service.py # Broadcast to clients
│       │
│       ├── agents/           # LiveKit agent (audio extraction)
│       │   ├── __init__.py
│       │   ├── meeting_agent.py # LiveKit Agents framework
│       │   └── stt_client.py # WhisperLive WebSocket client
│       │
│       ├── db/               # Database utilities
│       │   ├── __init__.py
│       │   ├── session.py    # Async session factory
│       │   └── base.py       # Declarative base
│       │
│       ├── core/             # Core utilities
│       │   ├── __init__.py
│       │   ├── security.py   # Password hashing, JWT
│       │   └── logging.py    # Logging config
│       │
│       └── utils/
│           └── redis_client.py # Redis pub/sub
│
├── livekit/                  # LiveKit server configuration
│   ├── Dockerfile            # Custom LiveKit server image (if needed)
│   ├── livekit.yaml          # LiveKit server config
│   └── .env.example          # LiveKit env vars
│
├── stt/                      # STT service (WhisperLive)
│   ├── Dockerfile            # WhisperLive Docker build
│   ├── requirements.txt      # Python dependencies
│   ├── config.yaml           # WhisperLive config
│   └── .env.example          # STT env vars
│
├── infra/                    # Infrastructure & deployment
│   ├── nginx/
│   │   ├── Dockerfile
│   │   ├── nginx.conf        # Main config
│   │   ├── ssl/              # SSL certificates (Let's Encrypt)
│   │   └── conf.d/
│   │       └── default.conf  # Site config
│   │
│   ├── postgres/
│   │   ├── Dockerfile        # Custom Postgres image (if needed)
│   │   └── init.sql          # Initialization script (create extensions)
│   │
│   ├── redis/
│   │   └── redis.conf        # Redis config
│   │
│   └── scripts/              # Deployment scripts
│       ├── setup.sh          # Initial setup
│       ├── seed_db.py        # Seed database with test users
│       └── backup_db.sh      # Backup script
│
└── docs/                     # Documentation
    ├── api/                  # API documentation
    │   └── openapi.json      # Auto-generated from FastAPI
    ├── setup.md              # Detailed setup guide
    ├── deployment.md         # Production deployment guide
    └── development.md        # Development workflow
```

---

### 4.1 Dockerfile Examples

#### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 5. Configuration & Environment Design

### 5.1 Root `.env.example`

Place this at repository root. Developers copy to `.env`.

```bash
# =============================================================================
# AI-Enhanced Video Meeting PoC - Environment Configuration
# =============================================================================
# Copy this file to .env and fill in the values
# Do NOT commit .env to version control

# -----------------------------------------------------------------------------
# General
# -----------------------------------------------------------------------------
APP_ENV=development          # development, staging, production
DEBUG=true                   # Enable debug logging
LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR, CRITICAL

# -----------------------------------------------------------------------------
# Frontend
# -----------------------------------------------------------------------------
FRONTEND_PORT=3000           # Port for frontend dev server
VITE_API_BASE_URL=http://localhost:8000/api  # Backend API URL (for frontend)
VITE_WS_URL=ws://localhost:8000              # WebSocket URL (for frontend)
VITE_LIVEKIT_URL=ws://localhost:7880         # LiveKit server URL (for frontend)

# -----------------------------------------------------------------------------
# Backend (FastAPI)
# -----------------------------------------------------------------------------
BACKEND_PORT=8000            # Port for backend server
BACKEND_HOST=0.0.0.0         # Bind address

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:5173  # Comma-separated allowed origins

# -----------------------------------------------------------------------------
# Database (PostgreSQL)
# -----------------------------------------------------------------------------
POSTGRES_HOST=postgres       # Hostname (service name in docker-compose)
POSTGRES_PORT=5432           # PostgreSQL port
POSTGRES_DB=meeting_ai       # Database name
POSTGRES_USER=postgres       # Database user
POSTGRES_PASSWORD=changeme123  # Database password (CHANGE THIS!)

# Constructed database URL (used by backend)
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# -----------------------------------------------------------------------------
# Redis (Message Broker & Cache)
# -----------------------------------------------------------------------------
REDIS_HOST=redis             # Hostname (service name in docker-compose)
REDIS_PORT=6379              # Redis port
REDIS_PASSWORD=              # Redis password (leave empty for no auth in dev)
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/0

# -----------------------------------------------------------------------------
# LiveKit
# -----------------------------------------------------------------------------
LIVEKIT_HOST=livekit         # Hostname (service name in docker-compose)
LIVEKIT_PORT=7880            # WebSocket port (client connections)
LIVEKIT_PORT_HTTP=7881       # HTTP API port (server SDK)
LIVEKIT_URL=ws://${LIVEKIT_HOST}:${LIVEKIT_PORT}  # WebSocket URL
LIVEKIT_API_URL=http://${LIVEKIT_HOST}:${LIVEKIT_PORT_HTTP}  # HTTP API URL

# LiveKit API credentials (generated keys)
LIVEKIT_API_KEY=devkey       # API key (CHANGE THIS!)
LIVEKIT_API_SECRET=secret    # API secret (CHANGE THIS! Use long random string)

# -----------------------------------------------------------------------------
# STT (Speech-To-Text) - WhisperLive
# -----------------------------------------------------------------------------
STT_ENGINE_TYPE=whisperlive  # Engine type (whisperlive, vosk, etc.)
STT_HOST=stt                 # Hostname (service name in docker-compose)
STT_PORT=9090                # WebSocket port
STT_URL=ws://${STT_HOST}:${STT_PORT}  # Full WebSocket URL

# WhisperLive-specific settings
STT_MODEL=large-v3           # Model size: tiny, base, small, medium, large-v3
STT_LANGUAGE=en              # Primary language (auto-detect if empty)
STT_BACKEND=faster_whisper   # Backend: faster_whisper, tensorrt, openvino
STT_DEVICE=cpu               # Device: cpu, cuda
STT_COMPUTE_TYPE=int8        # Compute type: int8, float16, float32

# -----------------------------------------------------------------------------
# LLM (Large Language Model) - KIMI K2
# -----------------------------------------------------------------------------
LLM_PROVIDER=kimi_k2         # Provider name
LLM_API_BASE_URL=https://platform.moonshot.ai/v1  # API base URL
LLM_API_KEY=sk-xxxxxx        # API key (REQUIRED - get from moonshot.ai)
LLM_MODEL=kimi-k2-instruct   # Model: kimi-k2-instruct, kimi-k2-thinking
LLM_TEMPERATURE=0.7          # Sampling temperature (0.0-2.0)
LLM_MAX_TOKENS=2000          # Max tokens per response
LLM_REQUEST_TIMEOUT=30       # Request timeout in seconds

# LLM Rate Limiting
LLM_MIN_REQUEST_INTERVAL=5   # Minimum seconds between LLM requests

# -----------------------------------------------------------------------------
# Authentication & Security
# -----------------------------------------------------------------------------
# JWT Secret (CHANGE THIS! Use: openssl rand -hex 32)
JWT_SECRET=your-secret-key-here-change-this-in-production
JWT_ALGORITHM=HS256          # Algorithm: HS256, RS256
JWT_EXPIRATION_MINUTES=1440  # Token expiration (24 hours)

# Password hashing
PASSWORD_MIN_LENGTH=8        # Minimum password length
BCRYPT_ROUNDS=12             # Bcrypt cost factor (12-14 recommended)

# -----------------------------------------------------------------------------
# Admin User (for initial seed)
# -----------------------------------------------------------------------------
ADMIN_DEFAULT_USERNAME=admin
ADMIN_DEFAULT_PASSWORD=admin123  # CHANGE THIS IMMEDIATELY!
ADMIN_DEFAULT_EMAIL=admin@example.com

# -----------------------------------------------------------------------------
# Nginx (Reverse Proxy)
# -----------------------------------------------------------------------------
NGINX_PORT_HTTP=80           # HTTP port
NGINX_PORT_HTTPS=443         # HTTPS port
DOMAIN=localhost             # Your domain (e.g., meeting.example.com)

# SSL Certificate paths (for Let's Encrypt)
SSL_CERT_PATH=/etc/letsencrypt/live/${DOMAIN}/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/${DOMAIN}/privkey.pem

# -----------------------------------------------------------------------------
# Feature Flags (for future extensions)
# -----------------------------------------------------------------------------
ENABLE_VIDEO_ANALYTICS=false  # Enable video analytics module
ENABLE_AUDIO_ANALYTICS=false  # Enable audio analytics module
ENABLE_RECORDING=false        # Enable meeting recording
```

---

### 5.2 Per-Service `.env.example`

#### `frontend/.env.example`

```bash
# Frontend-specific environment variables
# These are prefixed with VITE_ and injected at build time

VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000
VITE_LIVEKIT_URL=ws://localhost:7880
```

**Usage in React:**
```typescript
// frontend/src/config.ts
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL,
  wsUrl: import.meta.env.VITE_WS_URL,
  liveKitUrl: import.meta.env.VITE_LIVEKIT_URL,
};
```

---

#### `backend/.env.example`

(Mostly duplicates root `.env`, but can be standalone)

```bash
# Backend-specific environment variables
DATABASE_URL=postgresql+asyncpg://postgres:changeme123@postgres:5432/meeting_ai
REDIS_URL=redis://redis:6379/0
LIVEKIT_URL=ws://livekit:7880
LIVEKIT_API_URL=http://livekit:7881
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
STT_URL=ws://stt:9090
LLM_API_BASE_URL=https://platform.moonshot.ai/v1
LLM_API_KEY=sk-xxxxxx
JWT_SECRET=your-secret-key
```

**Usage in Python:**
```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    stt_url: str
    llm_api_base_url: str
    llm_api_key: str
    jwt_secret: str

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

---

### 5.3 Environment Variable Documentation

| Variable | Purpose | Required | Format | Used By | Default |
|----------|---------|----------|--------|---------|---------|
| `APP_ENV` | Deployment environment | No | `development` \| `staging` \| `production` | All services | `development` |
| `DEBUG` | Enable debug mode | No | `true` \| `false` | Backend | `true` |
| `LOG_LEVEL` | Logging verbosity | No | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` | Backend | `INFO` |
| `FRONTEND_PORT` | Frontend dev server port | No | `1-65535` | Frontend (dev only) | `3000` |
| `VITE_API_BASE_URL` | Backend API URL | **Yes** | `http(s)://host:port/api` | Frontend | - |
| `VITE_WS_URL` | Backend WebSocket URL | **Yes** | `ws(s)://host:port` | Frontend | - |
| `VITE_LIVEKIT_URL` | LiveKit server URL | **Yes** | `ws(s)://host:port` | Frontend | - |
| `BACKEND_PORT` | Backend server port | No | `1-65535` | Backend | `8000` |
| `BACKEND_HOST` | Backend bind address | No | IP address | Backend | `0.0.0.0` |
| `CORS_ORIGINS` | Allowed CORS origins | **Yes** | Comma-separated URLs | Backend (`app/main.py` middleware) | - |
| `POSTGRES_HOST` | PostgreSQL hostname | **Yes** | Hostname/IP | Backend | `postgres` |
| `POSTGRES_PORT` | PostgreSQL port | **Yes** | `1-65535` | Backend | `5432` |
| `POSTGRES_DB` | Database name | **Yes** | String | Backend, PostgreSQL container | `meeting_ai` |
| `POSTGRES_USER` | Database user | **Yes** | String | Backend, PostgreSQL container | `postgres` |
| `POSTGRES_PASSWORD` | Database password | **Yes** | String | Backend, PostgreSQL container | - |
| `DATABASE_URL` | Full database connection string | **Yes** | `postgresql+asyncpg://...` | Backend (`app/config.py`, Alembic) | - |
| `REDIS_HOST` | Redis hostname | **Yes** | Hostname/IP | Backend | `redis` |
| `REDIS_PORT` | Redis port | **Yes** | `1-65535` | Backend | `6379` |
| `REDIS_PASSWORD` | Redis password | No | String | Backend, Redis container | (empty) |
| `REDIS_URL` | Full Redis connection string | **Yes** | `redis://...` | Backend (`app/utils/redis_client.py`) | - |
| `LIVEKIT_HOST` | LiveKit hostname | **Yes** | Hostname/IP | Backend | `livekit` |
| `LIVEKIT_PORT` | LiveKit WebSocket port | **Yes** | `1-65535` | Backend, Frontend | `7880` |
| `LIVEKIT_PORT_HTTP` | LiveKit HTTP API port | **Yes** | `1-65535` | Backend | `7881` |
| `LIVEKIT_URL` | LiveKit WebSocket URL | **Yes** | `ws://...` | Frontend | - |
| `LIVEKIT_API_URL` | LiveKit HTTP API URL | **Yes** | `http://...` | Backend (`app/services/livekit_service.py`) | - |
| `LIVEKIT_API_KEY` | LiveKit API key | **Yes** | String | Backend, LiveKit container (`livekit.yaml`) | - |
| `LIVEKIT_API_SECRET` | LiveKit API secret | **Yes** | String (min 32 chars) | Backend, LiveKit container (`livekit.yaml`) | - |
| `STT_ENGINE_TYPE` | STT engine identifier | No | `whisperlive` \| `vosk` | Backend | `whisperlive` |
| `STT_HOST` | STT service hostname | **Yes** | Hostname/IP | Backend | `stt` |
| `STT_PORT` | STT service port | **Yes** | `1-65535` | Backend | `9090` |
| `STT_URL` | STT WebSocket URL | **Yes** | `ws://...` | Backend (`app/agents/stt_client.py`) | - |
| `STT_MODEL` | Whisper model size | No | `tiny` \| `base` \| `small` \| `medium` \| `large-v3` | STT container | `large-v3` |
| `STT_LANGUAGE` | Primary language | No | ISO 639-1 code (`en`, `es`, etc.) | STT container | `en` |
| `STT_BACKEND` | STT backend engine | No | `faster_whisper` \| `tensorrt` \| `openvino` | STT container | `faster_whisper` |
| `STT_DEVICE` | Compute device | No | `cpu` \| `cuda` | STT container | `cpu` |
| `STT_COMPUTE_TYPE` | Precision | No | `int8` \| `float16` \| `float32` | STT container | `int8` |
| `LLM_PROVIDER` | LLM provider name | No | String | Backend | `kimi_k2` |
| `LLM_API_BASE_URL` | LLM API base URL | **Yes** | `https://...` | Backend (`app/services/llm_service.py`) | `https://platform.moonshot.ai/v1` |
| `LLM_API_KEY` | LLM API key | **Yes** | String (starts with `sk-`) | Backend (`app/services/llm_service.py`) | - |
| `LLM_MODEL` | LLM model name | No | `kimi-k2-instruct` \| `kimi-k2-thinking` | Backend | `kimi-k2-instruct` |
| `LLM_TEMPERATURE` | Sampling temperature | No | `0.0-2.0` | Backend | `0.7` |
| `LLM_MAX_TOKENS` | Max tokens per response | No | Integer | Backend | `2000` |
| `LLM_REQUEST_TIMEOUT` | Request timeout (seconds) | No | Integer | Backend | `30` |
| `LLM_MIN_REQUEST_INTERVAL` | Min seconds between requests | No | Integer | Backend | `5` |
| `JWT_SECRET` | JWT signing secret | **Yes** | String (min 32 chars) | Backend (`app/core/security.py`) | - |
| `JWT_ALGORITHM` | JWT algorithm | No | `HS256` \| `RS256` | Backend | `HS256` |
| `JWT_EXPIRATION_MINUTES` | Token expiration | No | Integer | Backend | `1440` |
| `PASSWORD_MIN_LENGTH` | Min password length | No | Integer | Backend | `8` |
| `BCRYPT_ROUNDS` | Bcrypt cost factor | No | `10-14` | Backend | `12` |
| `ADMIN_DEFAULT_USERNAME` | Default admin username | No | String | Seed script (`infra/scripts/seed_db.py`) | `admin` |
| `ADMIN_DEFAULT_PASSWORD` | Default admin password | No | String | Seed script | `admin123` |
| `ADMIN_DEFAULT_EMAIL` | Default admin email | No | String | Seed script | `admin@example.com` |
| `NGINX_PORT_HTTP` | Nginx HTTP port | No | `1-65535` | Nginx container | `80` |
| `NGINX_PORT_HTTPS` | Nginx HTTPS port | No | `1-65535` | Nginx container | `443` |
| `DOMAIN` | Server domain | No | FQDN | Nginx config, SSL certs | `localhost` |
| `SSL_CERT_PATH` | SSL certificate path | No | File path | Nginx config | - |
| `SSL_KEY_PATH` | SSL key path | No | File path | Nginx config | - |
| `ENABLE_VIDEO_ANALYTICS` | Enable video analytics | No | `true` \| `false` | Backend (future) | `false` |
| `ENABLE_AUDIO_ANALYTICS` | Enable audio analytics | No | `true` \| `false` | Backend (future) | `false` |
| `ENABLE_RECORDING` | Enable recording | No | `true` \| `false` | Backend (future) | `false` |

---

### 5.4 Security Notes

- **Never commit `.env` files to Git!** Add to `.gitignore`.
- **Change default passwords immediately** in production.
- **Generate strong secrets:**
  ```bash
  # JWT secret
  openssl rand -hex 32

  # LiveKit API secret
  openssl rand -base64 48
  ```
- **Use environment-specific `.env` files:** `.env.development`, `.env.production`
- **For production:**
  - Use environment variables from cloud provider (AWS Secrets Manager, Azure Key Vault, etc.)
  - Enable HTTPS/WSS (no plain HTTP/WS)
  - Set `DEBUG=false`
  - Use strong `POSTGRES_PASSWORD`, `REDIS_PASSWORD`

---

## 6. README and Setup Flow

### 6.1 README.md Content Outline

```markdown
# AI-Enhanced Video Meeting PoC

Real-time video conferencing with live transcription and AI-powered meeting insights.

## Features

- **WebRTC Video Calls:** Self-hosted LiveKit SFU supporting 2-4 participants
- **Live Transcription:** Per-participant speech-to-text using WhisperLive (open-source)
- **AI Thought Board:** Real-time meeting insights powered by KIMI K2 LLM
  - Detected topics
  - Action items
  - Questions
  - Participant summaries
- **Admin Dashboard:** Transcript and thought board visible to admins during calls
- **Self-Hosted:** Fully open-source stack (LiveKit, WhisperLive, PostgreSQL)

## Tech Stack

- **Frontend:** React + TypeScript + Vite + TailwindCSS
- **Backend:** Python + FastAPI + SQLAlchemy + PostgreSQL
- **WebRTC:** LiveKit (self-hosted SFU)
- **STT:** WhisperLive (faster-whisper backend)
- **LLM:** KIMI K2 (Moonshot AI)
- **Deployment:** Docker + Docker Compose

## Prerequisites

- **Docker** 24+ and **Docker Compose** 2.23+
- **Ubuntu 22.04+** (or similar Linux distro)
- **Hardware:**
  - CPU: 4+ cores
  - RAM: 16GB+ (32GB recommended with GPU)
  - GPU: Optional (NVIDIA T4+ with 8GB VRAM for faster STT)
- **Domain:** (Optional for production) FQDN with DNS pointing to server
- **KIMI K2 API Key:** Get from https://platform.moonshot.ai

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourorg/ai-meeting-poc.git
cd ai-meeting-poc
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and set required values:
# - LIVEKIT_API_KEY and LIVEKIT_API_SECRET (generate random strings)
# - LLM_API_KEY (from Moonshot AI)
# - POSTGRES_PASSWORD (strong password)
# - JWT_SECRET (generate with: openssl rand -hex 32)
# - Change ADMIN_DEFAULT_PASSWORD
nano .env
```

### 3. Generate Secrets

```bash
# Generate JWT secret
openssl rand -hex 32

# Generate LiveKit API secret
openssl rand -base64 48
```

Add these to `.env`.

### 4. Start Services

```bash
# Build and start all containers
docker-compose up -d

# Check logs
docker-compose logs -f
```

Services will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **LiveKit:** ws://localhost:7880

### 5. Run Database Migrations

```bash
# Apply migrations
docker-compose exec backend alembic upgrade head

# Seed database with admin user
docker-compose exec backend python infra/scripts/seed_db.py
```

### 6. Access Application

1. Open http://localhost:3000 in two browser windows
2. **Window 1 (Admin):**
   - Login with username: `admin`, password: `admin123` (or your custom password)
3. **Window 2 (Participant):**
   - Login with username: `john`, password: `user123`
4. In admin window, create a meeting room
5. Join the same room from both windows
6. Start speaking and watch:
   - Transcripts appear in right panel (admin view)
   - AI thought board updates every 5-10 seconds

## Development

### Frontend Development

```bash
cd frontend
npm install
npm run dev  # Starts Vite dev server on :3000
```

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload  # Starts FastAPI on :8000
```

### Database Migrations

```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1
```

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design.

## Troubleshooting

### No audio/video in LiveKit

- Check browser permissions (microphone/camera)
- Verify `LIVEKIT_URL` in frontend `.env` is correct
- Check LiveKit logs: `docker-compose logs livekit`

### Transcription not working

- Check STT service logs: `docker-compose logs stt`
- Verify LiveKit agent is running: `docker-compose logs backend` (look for agent start)
- Check `STT_URL` in backend `.env`

### Thought board not updating

- Check KIMI K2 API key in `.env`
- Check backend logs for LLM errors: `docker-compose logs backend`
- Verify Redis is running: `docker-compose ps redis`

## Production Deployment

See [docs/deployment.md](./docs/deployment.md) for production setup with:
- SSL/TLS certificates (Let's Encrypt)
- Nginx reverse proxy
- Horizontal scaling
- Monitoring & logging

## License

MIT License - see [LICENSE](./LICENSE)

## Contributing

Pull requests welcome! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) first.

## Support

- **Issues:** https://github.com/yourorg/ai-meeting-poc/issues
- **Docs:** https://docs.yourproject.com
```

---

### 6.2 Setup Walkthrough (Step-by-Step)

#### Pre-Requisites Checklist

- [ ] Ubuntu 22.04+ server with SSH access
- [ ] Docker installed (`docker --version` >= 24.0)
- [ ] Docker Compose installed (`docker-compose --version` >= 2.23)
- [ ] Git installed
- [ ] KIMI K2 API key obtained
- [ ] (Production only) Domain name with DNS A record pointing to server IP

#### Step 1: Clone Repository

```bash
cd /home/user
git clone https://github.com/yourorg/ai-meeting-poc.git
cd ai-meeting-poc
```

#### Step 2: Generate Secrets

```bash
# Generate JWT secret
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env.secrets

# Generate LiveKit API key and secret
echo "LIVEKIT_API_KEY=LK$(openssl rand -hex 16)" >> .env.secrets
echo "LIVEKIT_API_SECRET=$(openssl rand -base64 48)" >> .env.secrets

# Generate strong database password
echo "POSTGRES_PASSWORD=$(openssl rand -base64 24)" >> .env.secrets

# View generated secrets
cat .env.secrets
```

#### Step 3: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env
nano .env
```

**Required changes:**
1. Copy secrets from `.env.secrets` into `.env`
2. Set `LLM_API_KEY=sk-your-kimi-k2-key`
3. Change `ADMIN_DEFAULT_PASSWORD` to a strong password
4. (Production) Set `DOMAIN=your-domain.com`
5. (Production) Set `APP_ENV=production` and `DEBUG=false`

#### Step 4: Start Database First

```bash
# Start only PostgreSQL
docker-compose up -d postgres

# Wait 10 seconds for PostgreSQL to initialize
sleep 10

# Check PostgreSQL logs
docker-compose logs postgres
```

#### Step 5: Run Migrations

```bash
# Apply database migrations
docker-compose exec postgres psql -U postgres -d meeting_ai -c "SELECT version();"
docker-compose run --rm backend alembic upgrade head
```

#### Step 6: Seed Database

```bash
# Create admin user and test users
docker-compose run --rm backend python infra/scripts/seed_db.py
```

Expected output:
```
Created user: admin (admin)
Created user: john (user)
Created user: jane (user)
Database seeded successfully!
```

#### Step 7: Start All Services

```bash
# Start all remaining services
docker-compose up -d

# Verify all containers are running
docker-compose ps
```

Expected output:
```
NAME                STATUS
ai-meeting-backend  Up
ai-meeting-frontend Up
ai-meeting-livekit  Up
ai-meeting-postgres Up
ai-meeting-redis    Up
ai-meeting-stt      Up
ai-meeting-nginx    Up
```

#### Step 8: Verify Service Health

```bash
# Check backend health
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Check frontend (should return HTML)
curl http://localhost:3000

# Check LiveKit (should return 404 but service is up)
curl http://localhost:7881/
```

#### Step 9: Test Login

1. Open browser to http://localhost:3000
2. Login with:
   - Username: `admin`
   - Password: `<your ADMIN_DEFAULT_PASSWORD>`
3. Should see dashboard/meeting creation UI

#### Step 10: Test Meeting

1. **Admin window (Chrome):**
   - Login as `admin`
   - Create a room named "Test Meeting"
   - Click "Join"
   - Allow camera/microphone permissions
   - Should see video grid + right panel (transcript/thought board)

2. **Participant window (Firefox/Incognito Chrome):**
   - Login as `john`
   - Join room "Test Meeting"
   - Allow camera/microphone permissions
   - Should see video grid (no right panel)

3. **Test transcription:**
   - Speak in either window
   - Admin should see transcript appear in right panel within 1-2 seconds
   - After 10-15 seconds, thought board should update

#### Step 11: Monitor Logs

```bash
# Tail all logs
docker-compose logs -f

# Tail specific service
docker-compose logs -f backend
docker-compose logs -f stt
```

---

## 7. Implementation Plan and Risks

### 7.1 Prioritized Implementation Plan

#### Phase 1: Core Infrastructure (Week 1)

**Tasks:**
1. **Repository Setup**
   - Initialize Git repo with folder structure
   - Create `.gitignore`, `README.md`, `LICENSE`
   - Set up `docker-compose.yml` skeleton

2. **Database Layer**
   - Write SQLAlchemy models (users, rooms, participants, transcripts, ai_thoughts)
   - Create Alembic migrations
   - Write seed script for test users
   - Test database schema locally

3. **Backend Skeleton**
   - Set up FastAPI app structure
   - Implement Pydantic config (`.env` loading)
   - Create async PostgreSQL session factory
   - Write health check endpoint (`/health`)
   - Dockerize backend

**Deliverable:** Working PostgreSQL + FastAPI with basic CRUD endpoints

**Risks:**
- **Risk:** Async SQLAlchemy setup complexity
  - *Mitigation:* Follow official docs closely, use `asyncpg` driver, test with simple queries
- **Risk:** Docker networking issues (services can't communicate)
  - *Mitigation:* Use Docker Compose networks, test service discovery with `docker-compose exec backend ping postgres`

---

#### Phase 2: Authentication & Room Management (Week 1-2)

**Tasks:**
1. **Authentication**
   - Implement password hashing (bcrypt)
   - Create JWT token generation/validation
   - Write `/api/auth/login` and `/api/auth/me` endpoints
   - Add dependency for `get_current_user`

2. **Room APIs**
   - Create `/api/rooms/create` endpoint (creates DB entry + LiveKit room)
   - Create `/api/rooms/list` endpoint
   - Integrate LiveKit Python SDK for token generation

3. **Frontend Login**
   - Build login page (React component)
   - Create auth service (axios + JWT storage)
   - Implement protected routes (React Router)

**Deliverable:** Users can log in, create rooms, get LiveKit tokens

**Risks:**
- **Risk:** JWT secret management in dev vs prod
  - *Mitigation:* Use `.env` files, document secret generation in README
- **Risk:** LiveKit token generation errors
  - *Mitigation:* Test LiveKit SDK locally first, check LiveKit server logs

---

#### Phase 3: LiveKit Integration & Video UI (Week 2-3)

**Tasks:**
1. **LiveKit Server Setup**
   - Create `livekit.yaml` config
   - Dockerize LiveKit server
   - Test WebRTC connection from browser

2. **Frontend Video UI**
   - Install `@livekit/components-react`
   - Build `MeetingPage.tsx` with `VideoConference` component
   - Connect to LiveKit using token from backend
   - Test 2-participant call

3. **Join Flow**
   - Create `/api/rooms/join` endpoint
   - Insert participant record in DB
   - Frontend calls `/join`, receives token, connects to LiveKit

**Deliverable:** 2 users can join a video call with working audio/video

**Risks:**
- **Risk:** WebRTC doesn't work behind NAT/firewall
  - *Mitigation:* For PoC, test on local network. For production, configure TURN server in `livekit.yaml`
- **Risk:** Browser permissions issues (camera/mic blocked)
  - *Mitigation:* Add clear error messages, guide users to check browser settings

---

#### Phase 4: STT Pipeline (Week 3-4) — **Most Complex**

**Tasks:**
1. **WhisperLive Deployment**
   - Create Dockerfile for WhisperLive
   - Test standalone: send audio via WebSocket, receive transcript
   - Dockerize and add to `docker-compose.yml`

2. **LiveKit Agent for Audio Extraction**
   - Set up LiveKit Agents framework in backend
   - Create `meeting_agent.py` that:
     - Joins room as a participant
     - Subscribes to all audio tracks
     - Buffers audio frames (PCM format)
   - Test agent can receive audio

3. **Audio → STT Streaming**
   - Create `stt_client.py` WebSocket client for WhisperLive
   - Extract audio from LiveKit tracks (convert to 16kHz mono PCM)
   - Send chunks to WhisperLive
   - Receive transcript results
   - Associate transcripts with participant IDs

4. **Transcript Storage & Broadcasting**
   - Create `/api/transcripts/segment` endpoint (internal, called by agent)
   - Save transcript to PostgreSQL
   - Publish event to Redis
   - Broadcast to WebSocket clients (admins only)

5. **Frontend Transcript UI**
   - Build `TranscriptPanel.tsx` component
   - Subscribe to WebSocket events
   - Display per-participant transcripts in real-time

**Deliverable:** Admin sees live transcripts during meeting

**Risks:**
- **Risk:** Audio chunking/buffering latency and jitter
  - *Mitigation:* Use sliding window buffer (250-500ms), test with different chunk sizes
- **Risk:** WhisperLive WebSocket connection drops
  - *Mitigation:* Implement reconnection logic with exponential backoff
- **Risk:** Participant ID mismatch (audio track → transcript)
  - *Mitigation:* Use LiveKit's `participant.identity` consistently across backend and agent
- **Risk:** STT latency too high (>2 seconds)
  - *Mitigation:* Use GPU mode for WhisperLive, tune VAD threshold, use `medium` model instead of `large-v3` if needed
- **Risk:** LiveKit agent doesn't start or crashes
  - *Mitigation:* Add robust error handling, logging, and health checks. Test agent startup independently.

**Critical Path:** This is the hardest part. Allocate extra time (1-2 weeks buffer).

---

#### Phase 5: LLM Integration & Thought Board (Week 5)

**Tasks:**
1. **LLM Service**
   - Create `llm_service.py` with KIMI K2 API client
   - Implement prompt engineering for meeting analysis
   - Test API locally (send sample transcripts, get insights)

2. **Aggregator Service**
   - Create background task that:
     - Monitors new transcript segments (PostgreSQL LISTEN/NOTIFY or polling)
     - Batches transcripts every 5-10 seconds
     - Calls LLM service
     - Parses JSON response (topics, action items, questions, summaries)
     - Saves to `ai_thoughts` table
     - Broadcasts to WebSocket clients

3. **Frontend Thought Board UI**
   - Build `ThoughtBoard.tsx` component
   - Subscribe to WebSocket `thought_board_update` events
   - Display structured insights (topics, action items, etc.)

**Deliverable:** Admin sees AI-generated insights updating in real-time

**Risks:**
- **Risk:** LLM API rate limits or costs
  - *Mitigation:* Implement `LLM_MIN_REQUEST_INTERVAL`, cache responses, monitor usage
- **Risk:** LLM returns malformed JSON
  - *Mitigation:* Use retry logic, validate with Pydantic, have fallback handling
- **Risk:** Context window overflow (too many transcripts)
  - *Mitigation:* Implement sliding window (last 50 segments) + summarization of older context

---

#### Phase 6: WebSocket Communication (Week 5-6)

**Tasks:**
1. **Backend WebSocket Server**
   - Integrate `python-socketio` with FastAPI
   - Create rooms per meeting (Socket.IO rooms)
   - Handle client connections (auth via JWT)
   - Implement Redis pub/sub for broadcasting across multiple backend instances

2. **Frontend WebSocket Client**
   - Create `socket.service.ts` with Socket.IO client
   - Connect on meeting join
   - Subscribe to `transcript_update` and `thought_board_update` events
   - Implement reconnection logic

**Deliverable:** Real-time updates working end-to-end

**Risks:**
- **Risk:** WebSocket connections drop on network issues
  - *Mitigation:* Socket.IO handles auto-reconnection, test with network throttling
- **Risk:** Broadcasting to many clients causes lag
  - *Mitigation:* Use Redis pub/sub, test with 10+ concurrent clients

---

#### Phase 7: Dockerization & Integration Testing (Week 6-7)

**Tasks:**
1. **Dockerize All Services**
   - Frontend multi-stage build (Node → Nginx)
   - Backend multi-stage build
   - STT service Dockerfile
   - Nginx reverse proxy config
   - Finalize `docker-compose.yml`

2. **Integration Testing**
   - Test full flow: login → create room → join → transcripts → thought board
   - Test with 2-4 participants
   - Load test (simulate 10 concurrent meetings)
   - Fix bugs, optimize performance

3. **Documentation**
   - Complete README.md
   - Write setup guide (this document)
   - Document API endpoints (OpenAPI/Swagger)

**Deliverable:** Fully working PoC deployable with `docker-compose up`

**Risks:**
- **Risk:** Docker image sizes too large (slow builds/deployments)
  - *Mitigation:* Use multi-stage builds, Alpine base images, `.dockerignore`
- **Risk:** Services crash on startup (dependency order)
  - *Mitigation:* Use `depends_on` in docker-compose, add health checks

---

#### Phase 8: Polish & Future-Proofing (Week 7-8)

**Tasks:**
1. **UI/UX Polish**
   - Improve error messages
   - Add loading states
   - Responsive design (mobile support)
   - Accessibility (WCAG 2.1 AA)

2. **Logging & Monitoring**
   - Structured logging (JSON format)
   - Centralized logs (optional: ELK stack or Loki)
   - Prometheus metrics (optional)

3. **Security Hardening**
   - Rate limiting (login, API endpoints)
   - Input validation (prevent SQL injection, XSS)
   - HTTPS/WSS in production
   - Helmet.js for frontend security headers

4. **Future Extension Scaffolding**
   - Add placeholder services for video/audio analytics
   - Document extension points in architecture
   - Create feature flags in `.env`

**Deliverable:** Production-ready PoC with documentation for future phases

---

### 7.2 Risk Matrix & Mitigation

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| **STT latency exceeds 2 seconds** | High | Medium | Use GPU, tune model size, optimize chunking, measure latency continuously |
| **LiveKit agent fails to extract audio** | Critical | Low | Test with simple agent first, check LiveKit SDK examples, robust error handling |
| **KIMI K2 API downtime/rate limits** | Medium | Medium | Implement retry logic, cache responses, set min interval, have fallback messages |
| **Database performance bottleneck** | Medium | Low | Use indexes, partition large tables, connection pooling (PgBouncer) |
| **WebSocket connection instability** | Medium | Medium | Use Socket.IO auto-reconnect, implement backoff, test with poor network |
| **Docker networking issues in prod** | Medium | Low | Use host networking for LiveKit (UDP), Nginx reverse proxy for others |
| **SSL certificate management complexity** | Low | Medium | Use Let's Encrypt + Certbot automation, document renewal |
| **Participant ID mismatches** | High | Medium | Use consistent IDs (LiveKit identity), validate at every step, add logging |
| **Out of GPU memory (STT)** | Medium | Low | Start with CPU mode, add GPU only if needed, monitor VRAM usage |
| **LLM prompt not producing useful insights** | Medium | High | Iterate on prompt engineering, A/B test prompts, gather user feedback |

---

### 7.3 Tricky Parts & Gotchas

#### 1. Audio Chunking for STT

**Challenge:** LiveKit provides audio in Opus or PCM frames at variable rates. WhisperLive expects consistent 16kHz mono PCM chunks.

**Solution:**
- Use LiveKit's `AudioFrame` to extract PCM samples
- Resample to 16kHz using `librosa` or `ffmpeg`
- Buffer frames in 0.5-1 second chunks before sending to STT
- Overlap chunks by 250ms to avoid word cuts at boundaries

**Code Sketch:**
```python
from livekit import rtc
import numpy as np

async def on_audio_frame(frame: rtc.AudioFrame, participant_id: str):
    # Convert to numpy array
    samples = np.frombuffer(frame.data, dtype=np.int16)

    # Resample to 16kHz if needed
    if frame.sample_rate != 16000:
        samples = resample(samples, frame.sample_rate, 16000)

    # Add to buffer
    audio_buffer.append(samples)

    # Send chunk every 0.5s
    if len(audio_buffer) >= 8000:  # 0.5s at 16kHz
        chunk = np.concatenate(audio_buffer)
        await stt_client.send(participant_id, chunk)
        audio_buffer = audio_buffer[-4000:]  # Keep 250ms overlap
```

#### 2. LiveKit Agent Lifecycle

**Challenge:** Agent must start when room is created, join as participant, and stop when room ends.

**Solution:**
- Run agent as a long-lived process in backend container
- Use LiveKit webhooks (`room_created`, `room_finished`) to start/stop agents
- Or use LiveKit Agents framework with auto-dispatch

**Code Sketch:**
```python
from livekit import agents

async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    # Subscribe to all audio tracks
    async for track in ctx.room.on_track_subscribed():
        if track.kind == "audio":
            audio_stream = rtc.AudioStream(track)
            async for frame in audio_stream:
                await process_audio(frame, track.participant.identity)
```

#### 3. LLM Context Management

**Challenge:** Sending all transcripts to LLM will exceed token limits.

**Solution:**
- **Sliding window:** Keep last 50 segments (~2-5 minutes)
- **Summarization:** Every 100 segments, call LLM to summarize older context
- **Delta updates:** Send only new transcripts + current thought board state

**Code Sketch:**
```python
async def generate_thoughts(room_id: str):
    recent_transcripts = await get_last_n_transcripts(room_id, 50)
    current_thoughts = await get_current_thoughts(room_id)

    prompt = f"""
    Previous insights:
    {json.dumps(current_thoughts)}

    New transcripts:
    {format_transcripts(recent_transcripts)}

    Generate updated insights (topics, action items, questions, summaries).
    Output as JSON.
    """

    response = await llm_client.chat(prompt)
    return parse_json(response)
```

#### 4. Partial vs Final Transcripts

**Challenge:** STT returns partial results (`is_final=False`) that are later replaced by final results.

**Solution:**
- Store all segments in DB (append-only)
- Frontend deduplicates: show latest partial until final arrives
- Use `transcript_id` or timestamp to match partial/final pairs

**Frontend Logic:**
```typescript
const handleTranscriptUpdate = (segment: TranscriptSegment) => {
  if (segment.is_final) {
    // Replace all partials for this timestamp
    setTranscripts(prev => [
      ...prev.filter(t => t.timestamp !== segment.timestamp),
      segment
    ]);
  } else {
    // Update or append partial
    setTranscripts(prev => {
      const existing = prev.find(t => t.id === segment.id);
      if (existing) {
        return prev.map(t => t.id === segment.id ? segment : t);
      } else {
        return [...prev, segment];
      }
    });
  }
};
```

#### 5. WebSocket Scaling

**Challenge:** Multiple backend instances → need to broadcast to clients connected to different instances.

**Solution:**
- Use **Redis Pub/Sub**
- Backend publishes events to Redis channel
- All backend instances subscribe to channel
- On receiving event, broadcast to local WebSocket clients

**Code Sketch:**
```python
import redis.asyncio as redis

# Publisher
async def broadcast_transcript(room_id: str, transcript: dict):
    await redis_client.publish(
        f"room:{room_id}:transcripts",
        json.dumps(transcript)
    )

# Subscriber (runs in each backend instance)
async def subscribe_to_transcripts():
    pubsub = redis_client.pubsub()
    await pubsub.psubscribe("room:*:transcripts")

    async for message in pubsub.listen():
        room_id = extract_room_id(message['channel'])
        transcript = json.loads(message['data'])

        # Broadcast to local WebSocket clients in this room
        await socketio.emit('transcript_update', transcript, room=room_id)
```

---

### 7.4 Success Criteria

The PoC is considered successful if:

1. ✅ Two users can join a video call with working audio/video
2. ✅ Admin sees per-participant transcripts within 1-2 seconds of speech
3. ✅ Thought board updates with structured insights every 5-15 seconds
4. ✅ System runs stably for 30-minute meeting without crashes
5. ✅ All components are self-hosted (no cloud dependencies except KIMI K2 API)
6. ✅ Deployment is reproducible with `docker-compose up`
7. ✅ Documentation allows a developer to set up the system in <2 hours

---

### 7.5 Next Steps After PoC

Once PoC is validated:

1. **User Feedback:** Test with real users, gather feedback on UI/UX and AI insights quality
2. **Performance Optimization:** Profile bottlenecks, optimize DB queries, add caching
3. **Security Audit:** Penetration testing, code review for vulnerabilities
4. **Scalability:** Move to Kubernetes, add horizontal auto-scaling, CDN for frontend
5. **Video Analytics:** Implement facial expression/gaze/posture detection modules
6. **Audio Analytics:** Add emotion detection, tone analysis, speaking rate metrics
7. **Multimodal AI:** Combine text + audio + video for richer insights
8. **Recording:** Add meeting recording and post-meeting analytics
9. **Self-Service Signup:** Build user registration flow, email verification
10. **Billing:** Integrate payment system if commercializing

---

## Conclusion

This architecture specification provides a **comprehensive, production-minded blueprint** for building an AI-enhanced video meeting PoC. By following this document, a competent engineer can:

- Understand the full system architecture and data flows
- Select and justify every technology choice
- Set up the development environment with clear `.env` configuration
- Deploy all services with Docker Compose
- Implement the system in a logical, phased approach
- Mitigate known risks and handle tricky technical challenges

The design prioritizes:
- **Open-source, self-hosted components** (LiveKit, WhisperLive, PostgreSQL)
- **Commercial-friendly licensing** (Apache 2.0, MIT)
- **Future extensibility** (video/audio analytics, multimodal AI)
- **Production readiness** (proper database schema, authentication, error handling)
- **Developer experience** (clear docs, reproducible setup, minimal friction)

**Total estimated implementation time:** 6-8 weeks for a 2-person team.

**Next action:** Clone the repo structure, set up `.env`, and begin Phase 1 (Core Infrastructure).

---

*End of Architecture Specification*
