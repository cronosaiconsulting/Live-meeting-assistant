# AI-Enhanced Video Meeting PoC

> **Real-time video conferencing with live transcription and AI-powered meeting insights**

A proof-of-concept system that combines WebRTC video calls with streaming speech-to-text transcription and LLM-powered "thought board" analysis, all running on self-hosted, open-source infrastructure.

## ✨ Features

- 🎥 **WebRTC Video Calls** – Self-hosted LiveKit SFU supporting 2-4 participants
- 🎙️ **Live Transcription** – Per-participant speech-to-text using WhisperLive (open-source)
- 🤖 **AI Thought Board** – Real-time meeting insights powered by KIMI K2 LLM
  - Detected topics and themes
  - Identified action items
  - Highlighted questions
  - Participant stance summaries
- 👔 **Admin Dashboard** – Transcript and thought board visible to meeting admins
- 🔒 **Self-Hosted** – Fully open-source stack with commercial-friendly licenses

## 🏗️ Architecture

**Full system design, tech stack justifications, database schema, and implementation plan:**
📖 **[Read the complete Architecture Specification →](./ARCHITECTURE.md)**

### High-Level Stack

```
┌─────────────────────────────────────────────────┐
│  Frontend: React + TypeScript + Vite           │
│  Styling: TailwindCSS + shadcn/ui              │
│  WebRTC: LiveKit JS SDK                        │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  Backend: Python + FastAPI                     │
│  Database: PostgreSQL + SQLAlchemy (async)     │
│  Cache/PubSub: Redis                           │
│  WebSocket: Socket.IO                          │
└─────────────────┬───────────────────────────────┘
                  │
    ┌─────────────┼─────────────┬─────────────┐
    │             │             │             │
┌───▼────┐  ┌─────▼──────┐  ┌──▼──────┐  ┌──▼──────┐
│LiveKit │  │ WhisperLive│  │ KIMI K2 │  │  Redis  │
│  SFU   │  │ (STT/ASR)  │  │  (LLM)  │  │ Pub/Sub │
└────────┘  └────────────┘  └─────────┘  └─────────┘
```

### Key Technologies

| Component | Technology | License |
|-----------|-----------|---------|
| **WebRTC SFU** | LiveKit v1.7+ | Apache 2.0 ✅ |
| **STT Engine** | WhisperLive (faster-whisper) | MIT ✅ |
| **LLM** | KIMI K2 (Moonshot AI) | Apache 2.0 ✅ |
| **Backend** | FastAPI + Python 3.11 | MIT ✅ |
| **Frontend** | React 18 + TypeScript + Vite | MIT ✅ |
| **Database** | PostgreSQL 16 | PostgreSQL License ✅ |
| **Cache/Queue** | Redis 7 | BSD-3-Clause ✅ |

All components use permissive licenses allowing commercial SaaS deployment.

## 🚀 Quick Start

### Prerequisites

- **Docker** 24+ and **Docker Compose** 2.23+
- **Ubuntu 22.04+** (or similar Linux distro)
- **Hardware:** 4+ CPU cores, 16GB RAM (32GB for GPU)
- **KIMI K2 API Key** from [platform.moonshot.ai](https://platform.moonshot.ai)

### 1️⃣ Clone Repository

```bash
git clone https://github.com/yourorg/ai-meeting-poc.git
cd ai-meeting-poc
```

### 2️⃣ Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Generate secrets
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env.secrets
echo "LIVEKIT_API_KEY=LK$(openssl rand -hex 16)" >> .env.secrets
echo "LIVEKIT_API_SECRET=$(openssl rand -base64 48)" >> .env.secrets
echo "POSTGRES_PASSWORD=$(openssl rand -base64 24)" >> .env.secrets

# View generated secrets
cat .env.secrets
```

**Edit `.env` and set:**
- Copy secrets from `.env.secrets`
- Set `LLM_API_KEY=sk-your-kimi-k2-key` (get from [Moonshot AI](https://platform.moonshot.ai))
- Change `ADMIN_DEFAULT_PASSWORD` to a strong password

### 3️⃣ Start Services

```bash
# Build and start all containers
docker-compose up -d

# Wait for services to initialize (~30 seconds)
docker-compose logs -f
```

### 4️⃣ Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Seed with admin user and test users
docker-compose exec backend python infra/scripts/seed_db.py
```

### 5️⃣ Access Application

Open **http://localhost:3000** in your browser.

**Test Credentials:**
- **Admin:** `admin` / `<your ADMIN_DEFAULT_PASSWORD>`
- **User 1:** `john` / `user123`
- **User 2:** `jane` / `user123`

### 6️⃣ Test Meeting

1. **Window 1 (Admin):**
   - Login as `admin`
   - Create a meeting room
   - Join the room
   - Allow camera/microphone permissions
   - You should see video grid + **right panel** (transcript + thought board)

2. **Window 2 (Participant):**
   - Open incognito/different browser
   - Login as `john`
   - Join the same room
   - You should see video grid (no admin panels)

3. **Speak in either window:**
   - Admin should see **live transcripts** appear within 1-2 seconds
   - After 10-15 seconds, **thought board** should update with AI insights

## 📊 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | React app (meeting UI) |
| **Backend API** | http://localhost:8000 | FastAPI REST API |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger docs |
| **LiveKit** | ws://localhost:7880 | WebRTC server (internal) |
| **PostgreSQL** | localhost:5432 | Database (internal) |
| **Redis** | localhost:6379 | Cache/pub-sub (internal) |
| **STT Service** | ws://localhost:9090 | WhisperLive (internal) |

## 🧪 Development

### Frontend Development

```bash
cd frontend
npm install
npm run dev  # Vite dev server on :3000
```

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload  # FastAPI on :8000
```

### Database Migrations

```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback one version
docker-compose exec backend alembic downgrade -1
```

## 🏗️ Project Structure

```
/
├── .env.example              # Environment configuration template
├── docker-compose.yml        # Multi-service orchestration
├── ARCHITECTURE.md           # Detailed architecture specification
├── README.md                 # This file
│
├── frontend/                 # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/       # UI components
│   │   ├── pages/            # Route pages
│   │   ├── services/         # API clients
│   │   └── stores/           # State management (Zustand)
│   └── package.json
│
├── backend/                  # FastAPI + Python
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── agents/           # LiveKit agent (audio extraction)
│   ├── alembic/              # Database migrations
│   └── requirements.txt
│
├── livekit/                  # LiveKit server config
│   └── livekit.yaml
│
├── stt/                      # WhisperLive STT service
│   ├── Dockerfile
│   └── requirements.txt
│
└── infra/                    # Infrastructure & deployment
    ├── nginx/                # Reverse proxy config
    ├── postgres/             # PostgreSQL init scripts
    └── scripts/              # Deployment scripts
```

## 🔍 Troubleshooting

### No audio/video in LiveKit
- Check browser permissions (microphone/camera)
- Verify `VITE_LIVEKIT_URL` in frontend `.env`
- Check LiveKit logs: `docker-compose logs livekit`

### Transcription not working
- Check STT service logs: `docker-compose logs stt`
- Verify LiveKit agent is running: `docker-compose logs backend`
- Check `STT_URL` in backend `.env`

### Thought board not updating
- Verify KIMI K2 API key is correct
- Check backend logs for errors: `docker-compose logs backend | grep -i llm`
- Ensure Redis is running: `docker-compose ps redis`

### Container fails to start
```bash
# Check container logs
docker-compose logs <service-name>

# Restart specific service
docker-compose restart <service-name>

# Rebuild and restart
docker-compose up -d --build <service-name>
```

## 📚 Documentation

- **[Architecture Specification](./ARCHITECTURE.md)** – Complete system design, tech stack, database schema, implementation plan
- **[API Documentation](http://localhost:8000/docs)** – Interactive Swagger/OpenAPI docs (when backend is running)
- **Setup Guide** – See [docs/setup.md](./docs/setup.md) (detailed installation)
- **Deployment Guide** – See [docs/deployment.md](./docs/deployment.md) (production deployment)

## 🚧 Implementation Status

**Current Phase:** PoC Design & Specification ✅

**Completed:**
- [x] Architecture design
- [x] Tech stack selection and justification
- [x] Database schema design
- [x] Environment configuration system
- [x] Docker Compose orchestration
- [x] Repository structure
- [x] Documentation

**Next Steps:**
1. Implement database models and migrations
2. Build FastAPI backend skeleton
3. Integrate LiveKit server
4. Deploy WhisperLive STT service
5. Implement LiveKit agent for audio extraction
6. Build React frontend with LiveKit components
7. Connect STT pipeline (audio → WhisperLive → backend → frontend)
8. Integrate KIMI K2 LLM for thought board
9. End-to-end testing
10. Production deployment guides

**Estimated Implementation Time:** 6-8 weeks (2-person team)

## 🔮 Future Extensions

The architecture is designed to support:

- **Video Analytics:** Facial expressions, gaze tracking, engagement scoring
- **Audio Analytics:** Emotion detection, prosody analysis, voice stress
- **Multimodal AI:** Combined text + audio + video reasoning
- **Meeting Recording:** Save and replay meetings with AI summaries
- **Advanced Insights:** Speaker diarization, topic segmentation, sentiment trends

See [ARCHITECTURE.md § Extension Points](./ARCHITECTURE.md#13-future-extension-points) for integration details.

## 📄 License

MIT License – see [LICENSE](./LICENSE)

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 💬 Support

- **Issues:** [GitHub Issues](https://github.com/yourorg/ai-meeting-poc/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourorg/ai-meeting-poc/discussions)
- **Documentation:** [Full Architecture Spec](./ARCHITECTURE.md)

## 🙏 Acknowledgments

Built with:
- [LiveKit](https://livekit.io) – Open-source WebRTC infrastructure
- [WhisperLive](https://github.com/collabora/WhisperLive) – Real-time Whisper transcription by Collabora
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) – Optimized Whisper implementation
- [KIMI K2](https://github.com/MoonshotAI/Kimi-K2) – Open-source LLM by Moonshot AI
- [FastAPI](https://fastapi.tiangolo.com) – Modern async Python framework
- [React](https://react.dev) – UI component library

---

**Ready to build the future of AI-enhanced meetings? 🚀**

Start by reading the [complete architecture specification](./ARCHITECTURE.md).