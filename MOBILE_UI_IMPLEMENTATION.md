# Mobile UI Implementation & Next Steps

## Completed: Mobile Responsive UI Styling

### Theme Implementation
- **File**: `client-godot/ui/theme/casuya_theme.tres`
- Modern theme with somaapp.ke-inspired styling
- Clean button styles with 12px rounded corners
- Cyan/blue color palette (0.2, 0.7, 0.9) for modern African aesthetic
- Hover and pressed states for better interactivity
- Consistent spacing and padding throughout
- Panel styles with subtle shadows

### Scene Updates

#### Main Scene (`client-godot/scenes/main.tscn`)
- Applied modern theme to all UI elements
- Increased touch targets: buttons now 70x52px (mobile-friendly)
- Improved spacing: 8-12px separation between elements
- Rounded corners on panels (12-16px radius)
- Cleaner borders and modern color scheme
- Larger fonts for better readability:
  - Title: 24px
  - Dialogue: 22px
  - Status labels: 13-14px

#### Settings Scene (`client-godot/scenes/settings.tscn`)
- Applied consistent modern theme
- Touch targets increased to 48px height
- Better spacing (16px separation)
- Modern color scheme matching main scene
- Improved label font sizes (14px)

#### Operator Scene (`client-godot/scenes/operator.tscn`)
- Applied modern theme throughout
- Touch targets increased to 48px height
- Improved spacing (10px separation)
- Cleaner panel styling with rounded corners
- Consistent font sizing improvements

### Mobile Responsiveness Features
- **Viewport**: Configured at 360x640 (mobile portrait)
- **Stretch mode**: Set to "canvas_items" for proper scaling
- **Touch targets**: All buttons now 48-52px height (meets mobile standards)
- **Spacing**: Generous padding for easy touch interaction
- **Typography**: Larger, more readable fonts
- **Colors**: High contrast with modern cyan/blue accents

---

## Remaining: To See Full Project Reality

### 1. Server Setup & Configuration

#### Environment Variables
Configure `server-python/.env` with:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/casuya_db

# Cache (optional)
REDIS_URL=redis://localhost:6379/0

# TTS Provider (choose one)
GOOGLE_CLOUD_TTS_API_KEY=your_google_cloud_key
# or
ELEVENLABS_API_KEY=your_elevenlabs_key

# News API
NEWS_API_KEY=your_news_api_key

# Weather API (optional)
OPENWEATHER_API_KEY=your_openweather_key

# API Key for Godot Client
API_KEY=your_secure_api_key
```

#### Database Setup
```bash
# Install PostgreSQL 16+
# Create database
createdb casuya_db

# Run migrations
cd server-python
alembic upgrade head
```

#### Install Dependencies
```bash
cd server-python
pip install -r requirements.txt
```

### 2. TTS Provider Setup

#### Option A: Google Cloud TTS (Free Tier)
- Create Google Cloud project
- Enable Text-to-Speech API
- Create service account and download JSON key
- Set `GOOGLE_CLOUD_TTS_API_KEY` in .env
- Free tier: 4M characters/month (covers 5+ months)

#### Option B: ElevenLabs (Premium)
- Create ElevenLabs account
- Get API key from dashboard
- Set `ELEVENLABS_API_KEY` in .env
- Cost: $37.50-75/month at 10 stories/day

#### Testing TTS
```bash
cd server-python
python -c "from voice.tts_provider import get_tts_provider; print(get_tts_provider())"
```

### 3. News Source Configuration

#### Option A: News API (Production)
- Sign up at https://newsapi.org
- Get API key
- Configure Swahili news sources in `scraper/news_api_client.py`
- Set `NEWS_API_KEY` in .env

#### Option B: Mock Feed (Development)
- Already configured in `scraper/mock_feed.py`
- No API key required
- Rotates through sample Swahili headlines

### 4. Build & Deploy Client

#### Prerequisites
- Install Godot Engine 4.7.1
- Download export templates for target platforms

#### Export to Mobile
```bash
# Using Godot Editor:
# 1. Open project.godot
# 2. Project > Export
# 3. Add export preset (Android/iOS)
# 4. Configure signing certificates
# 5. Export project
```

#### Export to Web
```bash
# In Godot Editor:
# 1. Project > Export
# 2. Add Web preset
# 3. Export to client-godot/build/web/
```

### 5. Testing the Full Pipeline

#### Start the Server
```bash
cd server-python
python main.py
```

Server will:
- Start FastAPI on http://localhost:8000
- Initialize database connections
- Start background scheduler for story generation
- Begin WebSocket server at `/api/v1/ws`

#### Run the Client
```bash
# Option 1: Godot Editor
# Open project.godot and press F5

# Option 2: Exported build
# Run the exported executable
```

#### Test Flow
1. Client connects to server via WebSocket
2. Server fetches latest news
3. NLP generates dramatic script from news
4. TTS synthesizes audio for each character
5. Client receives script + audio URLs
6. Audio plays with character dialogue
7. User can vote on story direction
8. Next story generated based on community pulse

### 6. Production Deployment (Optional)

#### Docker Setup
```bash
cd infra/docker
docker-compose up -d
```

#### Nginx Configuration
- Configure reverse proxy in `infra/deployment/nginx.conf`
- Set up SSL/TLS certificates
- Configure domain and routing

#### Cloud Deployment (Hetzner)
```bash
# Run setup script
bash infra/deployment/hetzner_setup.sh
```

#### Monitoring
- Prometheus metrics available at `/metrics`
- Configure alerts in `infra/monitoring/alert_rules.yml`
- Health check endpoint: `GET /api/v1/health`

---

## Quick Start Guide (Development)

### Minimal Setup (Mock Mode)
```bash
# 1. Start server with mock providers
cd server-python
cp .env.example .env
# Edit .env: set SCHEDULER_BACKEND=inprocess, use mock providers
python main.py

# 2. Run client in Godot Editor
# Open client-godot/project.godot
# Press F5 to run
```

### Full Setup (Production Mode)
```bash
# 1. Configure all API keys in server-python/.env
# 2. Set up PostgreSQL database
# 3. Install Redis (optional but recommended)
# 4. Start server
cd server-python
python main.py

# 5. Export and run client
# See section 4 above
```

---

## Troubleshooting

### Common Issues

**Server won't start**
- Check .env file exists and has required variables
- Verify PostgreSQL is running and accessible
- Check port 8000 is not in use

**Client can't connect**
- Verify server is running
- Check API_KEY matches between client and server
- Verify network connectivity

**No audio playing**
- Check TTS provider API key is valid
- Verify audio files are being generated in storage
- Check client audio settings in Settings panel

**News not updating**
- Verify NEWS_API_KEY is valid (if using News API)
- Check scheduler is running in server logs
- Try manual refresh via API: `POST /api/v1/news/refresh`

---

## Architecture Overview

### Tech Stack
- **Server**: Python 3.12+ / FastAPI
- **Database**: PostgreSQL 16+ / SQLAlchemy 2.0+
- **Cache**: Redis 7+ (optional)
- **Task Queue**: Celery 5.4+ (optional)
- **Client**: Godot Engine 4.7+ / GDScript
- **Voice**: Google Cloud TTS / ElevenLabs
- **Monitoring**: Prometheus / structlog

### Data Flow
```
News Feed → Scraper → NLP → Script → TTS → WebSocket → Client
   0s        +30s    +10s   +15s    +5s     +2s
   └──────────────────────────────────────────────┘
                    Target: <60s total
```

### Key Components
- **Scraper**: Fetches and deduplicates news
- **NLP**: Converts news to dramatic scripts with character dialogue
- **TTS**: Synthesizes character voices
- **WebSocket**: Real-time updates to clients
- **Economy**: Community voting system
- **Weather Sync**: Environmental mood bias

---

## Next Steps After UI Completion

1. **Configure backend services** (API keys, database)
2. **Test server locally** with mock providers
3. **Test client-server connection**
4. **Configure real TTS provider** for voice synthesis
5. **Export to target platform** (mobile/web)
6. **Deploy to production** (optional)

The UI is now mobile-ready with modern styling. The remaining work is primarily backend configuration and deployment.
