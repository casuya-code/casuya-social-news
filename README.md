# 🏛️ Casuya Social News

Mashine ya Kuandika na Kutengeneza Tamthilia za Habari (Social News Drama Engine) — inayobadilisha habari halisi kuwa tamthilia za sauti zinazoendeshwa na AI.

### Tech Stack

| Component | Technology | Version |
|---|---|---|
| Server | Python + FastAPI | 3.12+ / 0.115+ |
| Database | PostgreSQL + SQLAlchemy | 16+ / 2.0+ |
| Cache | Redis (optional, in-memory fallback) | 7+ |
| Task Queue | Celery + Redis broker | 5.4+ |
| Client | Godot Engine + GDScript | 4.3+ |
| Voice | Google Cloud TTS (default) / ElevenLabs (premium) | — |
| Monitoring | Prometheus + structlog | — |

### Kanuni: "Faili moja = Jukumu moja" (Single Responsibility per File)

Kila faili limeundwa kubeba **kodi kidogo tu** (kwa wastani mistari 30–150), ili:
- Kurekebisha kosa moja kusiguse mifumo mingine.
- Wanadeveloper wengi waweze kufanya kazi kwa wakati mmoja bila migongano ya Git.
- AI (Claude/GPT) iweze kusoma na kuhariri faili moja bila kuchanganyikiwa na muktadha mkubwa.

---

## 🌳 Muundo Mkuu (Top-Level)

```
casuya-social-news/
├── server-python/          # SEVA YA CLOUD (Ubongo)
├── client-godot/           # APLIKESHONI YA SIMU (Mwili)
├── shared/                 # Vitu vinavyotumika pande zote mbili
├── infra/                  # DevOps, deployment, monitoring
├── docs/                   # Nyaraka za mradi
└── tools/                  # Scripts za msaada (build, seed, test)
```

---

## 1️⃣ Server-Python/ — Seva ya Cloud (Ubongo wa Mfumo)

```
server-python/
│
├── config/
│   ├── settings.py                 # Env vars, constants
│   └── logging_config.py           # Usanidi wa logs
│
├── scraper/                        # 📰 Ukusanyaji wa Habari
│   ├── news_fetcher.py             # Inavuta habari mbichi (RSS/API)
│   ├── slang_detector.py           # Kipengele #26: Slang Dictionary Layer
│   └── source_registry.py          # Orodha ya vyanzo vya habari
│
├── nlp/                            # 🗣️ Uchambuzi wa Lugha na Uandishi
│   ├── contextualizer.py           # Kipengele #24: Habari → Tamthilia
│   ├── narrative_matrix.py         # Kipengele #1: Methali/Nahau prompts
│   ├── emotion_tagger.py           # Kipengele #2: [anacheka_kwa_dharau] tags
│   ├── overlap_cue_generator.py    # Kipengele #6: Mazungumzo yanayoingiliana
│   └── prompt_templates/
│       ├── asubuhi_prompt.txt
│       ├── mchana_prompt.txt
│       └── usiku_prompt.txt
│
├── memory/                         # 🧠 Kumbukumbu ya Wahusika
│   ├── vector_store.py             # Muunganiko wa Vector DB
│   ├── character_memory.py         # Kipengele #25: Stochastic Character Memory
│   └── mood_state.py               # Kipengele #22: Diurnal Mood Drift
│
├── ai_director/                    # 🎬 "Ubongo" wa Maamuzi
│   ├── utility_ai.py               # Kipengele #16: Behavior Trees / Scoring
│   ├── behavior_scorer.py          # Alama za "kucheka" vs "kuhuzunika" n.k.
│   └── script_writer.py            # Inaunganisha nlp/ + memory/ → JSON script
│
├── voice/                          # 🎙️ Sauti (Google Cloud / ElevenLabs)
│   ├── tts_provider.py             # Abstract interface — switch providers via config
│   ├── google_cloud_client.py      # Default: $4/1M chars, 4M free/mo
│   ├── elevenlabs_client.py        # Premium: $50/1M chars, best quality
│   ├── voice_stability_engine.py   # Kipengele #4: Vocal Micro-Tremor
│   ├── emotion_carryover.py        # Kipengele #5: Emotional Voice Carry-Over
│   └── voice_profiles.json         # Sauti za kila mhusika
│
├── weather_sync/                   # 🌦️ Muktadha wa Mazingira
│   ├── geo_clock.py                # Kipengele #14: Muda wa Ulimwengu
│   └── meteorological_feed.py      # Kipengele #30: Hali ya Hewa
│
├── economy/                        # 💰 Mapato
│   ├── product_placement.py        # Kipengele #34: Automated Product Placement
│   └── fan_lore_voting.py          # Kipengele #35: Community Lore-Baking
│
├── api/                            # 🌐 Njia za Mawasiliano na Client
│   ├── websocket_server.py         # Delta updates kwa Godot client
│   ├── delta_compressor.py         # Kipengele #27: Delta Compression
│   └── routes/
│       ├── v1/
│       │   ├── script_routes.py    # POST /api/v1/scripts/generate
│       │   ├── voice_routes.py     # POST /api/v1/voice/synthesize
│       │   └── economy_routes.py   # POST /api/v1/economy/vote
│       └── health.py              # GET /api/v1/health
│
├── cache/
│   └── redis_client.py             # Redis caching (news 15min, vectors 1hr, scripts 24hr)
│
├── storage/                        # 📁 File storage (local dev: ./storage/, prod: S3)
│   ├── audio/                      # Generated .mp3 files (auto-purged after 24h)
│   └── scripts/                    # Generated script JSONs (compressed to summary, then deleted)
│
├── queue/
│   └── task_queue.py               # Celery — async voice gen, scraping, script writing
│
├── middleware/
│   ├── auth.py                     # JWT authentication (24hr expiry, refresh flow)
│   └── rate_limiter.py             # 60 req/min per IP, 5 req/min voice generation
│
├── security/
│   ├── api_key_auth.py             # API key auth — client sends X-API-Key header
│   └── input_validator.py          # Pydantic models for all request bodies
│
├── monitoring/
│   ├── circuit_breaker.py          # Wrap TTS provider — open after 5 failures, half-open 60s
│   ├── metrics.py                  # Prometheus counters/histograms
│   └── health_check.py             # GET /api/v1/health — DB, Redis, TTS provider status
│
├── database/
│   ├── models.py                   # SQLAlchemy models
│   └── migrations/
│
└── main.py                         # Entry point (FastAPI app)
```

---

## 2️⃣ Client-Godot/ — Aplikeshoni ya Simu (Mwili wa Mfumo)

```
client-godot/
│
├── autoload/                       # Singletons (Global)
│   ├── NetworkManager.gd           # Kupokea Delta data kutoka server
│   ├── LocalCache.gd               # Kipengele #27: Local caching
│   └── SceneDirector.gd            # Anaunganisha mifumo yote kwa tukio moja
│
├── camera/                         # 🎥 Cinematography
│   ├── ProceduralCamera.gd         # Kipengele #12: Kamera ya Kisanii
│   ├── BeatTracker.gd              # Kipengele #13: Cinematic Beat Tracking
│   └── ShotComposer.gd             # Close-up / Wide shot logic
│
├── facial/                         # 😐 Uso na Macho
│   ├── LipsyncController.gd        # Kipengele #7: Adaptive Lipsync
│   ├── PhonemeAnalyzer.gd          # Kipengele #8: Dynamic Phoneme Extraction
│   ├── EyeGazeSystem.gd            # Kipengele #9: Micro-Expressions & Eye Gaze
│   ├── CognitiveEyeDart.gd         # Kipengele #10: Eye-Darting (kufikiri)
│   └── BlinkReflex.gd              # Kipengele #11: Sensory Blink Reflex
│
├── animation/                      # 🚶 Miendo ya Mwili
│   ├── ProceduralLocomotion.gd     # Kipengele #17: IK-based Locomotion
│   ├── IdleGenerator.gd            # Kipengele #18: Procedural Idle
│   ├── GaitBiomechanics.gd         # Kipengele #19: Umri → Mwendo
│   ├── CulturalGestures.gd         # Kipengele #20: Ishara za Kiafrika
│   └── ProximityShader.gd          # Kipengele #21: Dynamic Proximity
│
├── audio/                          # 🔊 Sauti za Mazingira
│   ├── SpatialAudioManager.gd      # Kipengele #32: Spatial Procedural Audio
│   ├── AcousticOcclusion.gd        # Kipengele #33: Mwangwi wa Sauti
│   └── OverlapSpeechPlayer.gd      # Kipengele #6 (upande wa client)
│
├── environment/                    # 🌅 Mazingira
│   ├── LightBaker.gd               # Kipengele #29: Stylized Visual Baking
│   ├── WeatherShader.gd            # Kipengele #30: Dynamic Weather
│   └── CrowdGenerator.gd           # Kipengele #31: Autonomous Crowd
│
├── characters/                     # 👤 Wahusika
│   ├── CharacterController.gd      # Muunganiko wa mifumo yote ya mhusika
│   ├── TextureSwapper.gd           # Kipengele #23: Dynamic Texture Swapping
│   └── ClothWearAlgorithm.gd       # Kipengele #28: Mavazi Yanayozeeka
│
├── ui/
│   ├── VotingPanel.gd              # Kipengele #35: Fan voting UI
│   ├── LoadingScreen.gd            # Progress bar + estimated time
│   ├── ErrorDisplay.gd             # Toast notifications — network errors, auto-dismiss 5s
│   ├── ToastNotification.gd        # Non-blocking alerts
│   └── SettingsPanel.gd            # Audio quality, notifications, data usage toggle
│
├── network/
│   ├── RetryHandler.gd             # Auto-retry with backoff, manual retry after 3 failures
│   └── OfflineDetector.gd          # Connectivity detection, "cached stories available" banner
│
├── data/
│   ├── character_registry.tres
│   └── scene_registry.tres
│
└── project.godot
```

---

## 3️⃣ Shared/ — Inayotumika Pande Zote Mbili

```
shared/
├── schemas/
│   ├── script_schema.json          # Muundo wa JSON kati ya server na client
│   ├── emotion_tags.json           # Orodha rasmi ya [anacheka_kwa_dharau] n.k.
│   ├── api_response.json           # Standard error/success response format
│   └── character_id_map.json
└── docs/
    └── data_contract.md            # Mkataba wa data kati ya Python na Godot
```

---

## 4️⃣ Infra/ — DevOps

```
infra/
├── docker/
│   ├── Dockerfile.server
│   └── docker-compose.yml
├── deployment/
│   ├── hetzner_setup.sh
│   └── nginx.conf
└── monitoring/
    ├── prometheus.yml              # Prometheus scrape config
    └── alert_rules.yml             # Alerts: disk >80%, API errors >5%, TTS provider down
```

---

## 5️⃣ Docs/ — Nyaraka

```
docs/
├── MASTER_BLUEPRINT.md             # Blueprint kuu ya mradi
├── BUDGET_PLAN.md                  # Mpango wa bajeti
└── ONBOARDING_DEVELOPER.md         # Mwongozo kwa developers wapya
```

---

## 6️⃣ Tools/ — Scripts za Msaada

```
tools/
├── seed_test_characters.py
├── run_local_dev.sh
└── generate_voice_sample.py
```

---

## ✅ Faida za Muundo Huu

| Faida | Maelezo |
|---|---|
| **Urekebishaji rahisi** | Kila kipengele (1–35) kina faili lake maalum — ukigundua tatizo la "Blink Reflex" unaenda moja kwa moja `facial/BlinkReflex.gd` |
| **Kazi ya pamoja** | Developer mmoja anaweza kufanyia kazi `voice/` huku mwingine akifanyia `camera/` bila migongano |
| **AI-friendly** | Ukimwomba Claude/GPT arekebishe kipengele kimoja, unamtumia faili moja tu (mistari <150) badala ya kumpa hati nzima |
| **Upimaji (Testing)** | Kila moduli inaweza kupimwa (unit test) peke yake |
| **Uwekaji wa toleo (Versioning)** | Git diffs zinabaki wazi na fupi — hakuna faili kubwa la mistari 2000+ |

---

## ⚙️ Mahitaji ya Uendeshaji (Operational Requirements)

### Kasi (Speed)

| Mahitaji | Utendaji |
|---|---|
| **Redis caching** | `cache/redis_client.py` — habari mbichi (TTL 15min), vector za wahusika (TTL 1hr), script zilizotolewa (TTL 24hr) |
| **Async task queue** | `queue/task_queue.py` — Celery kwa sauti, scraper, script writing — usisubiri API response |
| **Database indexing** | Indexes kwenye `news_articles(source, published_at)`, `characters(id, mood_state)`, `scripts(created_at)` |
| **Connection pooling** | SQLAlchemy `pool_size=20, max_overflow=10` |
| **Response compression** | gzip middleware kwenye FastAPI |
| **CDN** | `.mp3` za sauti zinatumwa kupitia Cloudflare/CloudFront, si kutoka VPS moja kwa moja |

### Usalama (Security)

| Mahitaji | Utendaji |
|---|---|
| **API key auth** | `security/api_key_auth.py` — client sends `X-API-Key` header, validated per-request |
| **JWT authentication** | `middleware/auth.py` — FastAPI dependency, token expires 24hr, refresh flow |
| **Rate limiting** | `middleware/rate_limiter.py` — 60 req/min kwa IP, 5 req/min kwa sauti |
| **Input validation** | `security/input_validator.py` — Pydantic models kwa kila request body |
| **Secrets management** | `.env` file + `python-dotenv`, usijweke kombe, revake API keys kila robo mwaka |
| **WebSocket auth** | Validate API key on WS connect, reject unauthorized |
| **HTTPS** | nginx terminate TLS, forwarded kwa FastAPI kwenye localhost |

### Uendeshaji (Reliability)

| Mahitaji | Utendaji |
|---|---|
| **Circuit breaker** | `monitoring/circuit_breaker.py` — funga baada ya makosa 5, fungua nusu baada ya 60s |
| **Retry + backoff** | Exponential retry (1s, 2s, 4s) kwa external APIs, max 3 attempts |
| **Graceful degradation** | Kama AI down → tumia script iliyohifadhiwa au onyesha "Huduma haipatikani kwa muda" |
| **Health check** | `GET /api/v1/health` — hali ya DB, Redis, TTS provider |
| **Graceful shutdown** | Shibisha SIGTERM, drainage WebSocket connections, fungua DB pools |

### Kukataza Madhara (Bug Handling)

| Mahitaji | Utendaji |
|---|---|
| **Structured logging** | JSON logs — request ID, timestamp, module, severity |
| **Error boundaries** | Kila moduli inashika makosa yake, inarudisha typed error responses |
| **Log rotation** | 48hrs live, compress older, delete baada ya siku 7 |

### Error Code Taxonomy

| Code | Module | Description |
|---|---|---|
| `E1001` | nlp | Script generation failed |
| `E1002` | nlp | Emotion tagging failed |
| `E1003` | nlp | Contextualizer timeout |
| `E2001` | voice | TTS provider API down |
| `E2002` | voice | TTS provider quota exceeded |
| `E2003` | voice | Audio file write failed |
| `E3001` | cache | Redis unavailable (fallback to in-memory) |
| `E3002` | database | Connection pool exhausted |
| `E3003` | database | Migration required |
| `E4001` | auth | Invalid API key |
| `E4002` | auth | JWT expired |
| `E4003` | rate_limit | Rate limit exceeded |
| `E5001` | scraper | News source unavailable |
| `E5002` | scraper | Rate limited by news source |

### Logging Format

```json
{
  "timestamp": "2026-08-13T20:45:00Z",
  "level": "error",
  "request_id": "req_abc123",
  "module": "voice",
  "error_code": "E2001",
  "message": "TTS provider API timeout after 30s",
  "traceback": "..."
}
```

### Data Retention

| Data Type | Retention | Action |
|---|---|---|
| Raw news articles | 24 hours | Delete after script generated or after 48h regardless |
| Generated .mp3 files | 24 hours | Delete after client downloads |
| Full script JSON | 24 hours | Compress to 1-line summary, delete original |
| Character vectors | Indefinite | Keep (small, high value) |
| Mood state values | Indefinite | Keep (few numbers per character) |
| Logs | 48 hours live, 7 days compressed | Auto-delete after 7 days |

### API Cost Controls

| API | Monthly Budget | Action When Hit |
|---|---|---|
| Google Cloud TTS | $0 (4M free chars/mo covers 5+ months) | Fall back to ElevenLabs or cached audio |
| ElevenLabs (optional) | $50 USD | Pause voice generation, serve cached audio |
| OpenAI | $5 USD | Fall back to template-based script generation |
| News API | Free tier | Rotate sources, respect rate limits |

---

## ⚡ Usambazaji wa Wakati Halisi (Real-Time Architecture)

### Real-Time Pipeline

```
News Feed → Scraper → NLP → Script → Voice → Client
   0s        +30s     +10s   +15s    +5s     +2s
   └────────────────────────────────────────────┘
              Target: <60 seconds total
```

| Stage | Latency Target | Implementation |
|---|---|---|
| News detection | 0-30s | RSS webhook / 30s polling |
| Script generation | +10-15s | GPT-4o-mini (fast) |
| Voice synthesis | +5-10s | Google Cloud TTS (streaming) |
| Client delivery | +1-2s | WebSocket push |
| **Total** | **<60s** | |

### Speed Optimization

| Tier | When | Strategy |
|---|---|---|
| **Tier 1: Breaking news** | First 5 min | Fast models (GPT-4o-mini, Google Cloud), no caching, priority queue |
| **Tier 2: Recent news** | 5-60 min | Cache check first, fall back to generation, normal queue |
| **Tier 3: Archive** | 1+ hour | Cache only, serve pre-generated content, background queue |

| Optimization | How |
|---|---|
| **Streaming voice** | Google Cloud TTS streams audio chunks, client plays while downloading |
| **Parallel generation** | Generate character voices in parallel (3 characters × 5s = 5s total, not 15s) |
| **Pre-generation** | Predict high-demand stories, generate during off-peak hours |
| **Delta compression** | Only send changed parts of script to client, not full JSON |
| **Connection pooling** | Reuse HTTP connections to APIs, don't reconnect per request |

### Quality vs Speed Tradeoffs

| Priority | Script Model | Voice Model | Latency | Quality | Cost/1K stories |
|---|---|---|---|---|---|
| **Speed first** | GPT-4o-mini | Google Cloud Standard | ~30s | Good | $3 |
| **Balanced** | GPT-4o-mini | Google Cloud WaveNet | ~40s | High | $16 |
| **Quality first** | GPT-4o | ElevenLabs Flash | ~50s | Highest | $50+ |

### Caching Strategy for Real-Time

| Layer | What | TTL | Hit Rate Target |
|---|---|---|---|
| **L1: In-memory** | Current story being discussed | 0 (active) | 100% |
| **L2: Redis** | Recent stories (last 24h) | 1 hour | 80% |
| **L3: Database** | Story summaries + character memory | Indefinite | 95% |
| **L4: CDN** | Audio files | 24 hours | 70% |

### Queue Management for Real-Time

| Queue | Priority | Workers | Use Case |
|---|---|---|---|
| **critical** | High | 2 | Breaking news (first 5 min) |
| **default** | Normal | 4 | Recent news (5-60 min) |
| **bulk** | Low | 2 | Archive content, batch generation |
| **voice** | Separate | 3 | Voice synthesis (CPU-intensive) |

| Metric | Alert Threshold |
|---|---|
| Queue depth | > 50 jobs pending |
| Worker CPU | > 80% sustained |
| Job latency | > 30s average |
| Failure rate | > 5% of jobs |

### TTS Provider Comparison

| Provider | $/1M chars | Free Tier | Quality | Voice Cloning | Best For |
|---|---|---|---|---|---|
| **Google Cloud** | $4 | 4M chars/mo | Good | No | Budget, multilingual |
| **ElevenLabs** | $50-100 | 10K chars/mo | Highest | Yes | Premium content |

**At 10 stories/day (750K chars/mo):**
- Google Cloud: **$3/mo** (or free for 5+ months)
- ElevenLabs: **$37.50-75/mo**

**Recommendation:** Start with Google Cloud (free tier covers prototyping). Upgrade to ElevenLabs only if voice quality feedback demands it.

---

## 📱 Mahitaji ya Mteja (Client Requirements)

### UI/UX

| Mahitaji | Utendaji |
|---|---|
| **Loading states** | `LoadingScreen.gd` — progress bar + muda wa makadirio kwa utengenezaji wa sauti |
| **Error display** | `ErrorDisplay.gd` — toast notifications kwa makosa ya mtandao, auto-dismiss baada ya 5s |
| **Retry UX** | `RetryHandler.gd` — retry moja kwa moja na kiashiria, kitufe cha retry baada ya mapinduzi 3 |
| **Offline mode** | `OfflineDetector.gd` — Gundua muunganisho, onyesha bango "Nje ya mtandao — hadithi zilizohifadhiwa zinapatikana" |
| **Offline cache** | Max 100MB local storage, LRU eviction, cache last 10 stories + their audio |
| **Settings** | `SettingsPanel.gd` — ubora wa sauti, mapendeleo ya arifa, toggle ya matumizi ya data |
| **Keyboard navigation** | VIPengele vyote vya UI vinaweza kufikiwa, tab order imewekwa, escape funga modals |
| **Accessibility** | Custom screen reader helpers via platform APIs, toggle ya high-contrast, min touch target 44x44px |

### Ubora wa Simu (Mobile Responsiveness)

| Mahitaji | Utendaji |
|---|---|
| **Viewport** | Godot `display/size` inakubaliana na resolution ya kifaa, jaribio katika 360px, 768px, 1024px |
| **Touch gestures** | Custom swipe recognizer via `InputEventScreenDrag`, pinch zoom via `InputEventScreenTouch` |
| **Battery optimization** | Android: use `OS.request_permissions()` + battery API plugin; iOS: use `ProcessInfo.processInfo.isLowPowerModeEnabled`; reduce to 30fps when battery <20% |
| **Data saving** | Toggle kupunguza ubora wa sauti (64kbps vs 128kbps), ruka ushirikiano wa hali ya hewa |
| **Adaptive quality** | Gundua uwezo wa kifaa kiotomatiki, punguza msongamano / misuli kwenye vifaa vya chini |
| **Camera controls** | IMU-based tilt requires gyroscope plugin + `OS.request_permissions()`; fallback to touch-drag |

---

## 🎯 MVP (Minimum Viable Product)

Kabla ya kujenga kila kipengele (1–35), fanya kazi hii kwanza:

| Step | File | Description |
|---|---|---|
| 1 | `shared/schemas/script_schema.json` | Define JSON contract between server and client |
| 2 | `server-python/nlp/contextualizer.py` | Habari → Script (mock LLM first, real later) |
| 3 | `server-python/voice/tts_provider.py` | Script → Audio (auto-selects Google Cloud or ElevenLabs) |
| 4 | `server-python/api/routes/v1/script_routes.py` | `POST /api/v1/scripts/generate` endpoint |
| 5 | `client-godot/autoload/NetworkManager.gd` | Fetch script + audio from server |

**MVP demo flow:**
1. User taps "Generate Story" on phone
2. Client sends request to server
3. Server fetches news → generates script → generates voice → returns JSON + audio URL
4. Client plays audio with basic lip-sync

Hii inatosha kuonyesha mfumo unafanya kazi. Kisha ongeza camera, animation, caching, n.k.

---

## 🚀 Kuanza (Quick Start)

1. Clone repo na weka `.env` file:
   ```bash
   git clone <repo-url>
   cd casuya-social-news/server-python
   cp .env.example .env   # Jaza API keys zako
   ```
2. Anzisha PostgreSQL na Redis:
   ```bash
   docker compose -f ../infra/docker/docker-compose.yml up -d
   ```
3. Weka Google Cloud credentials (default TTS provider):
   ```bash
   # Option A: gcloud CLI (recommended)
   gcloud auth application-default login

   # Option B: Service account key
   # Set GOOGLE_APPLICATION_CREDENTIALS in .env
   ```
4. Funga dependencies na endesha migration:
   ```bash
   pip install -r requirements.txt
   alembic upgrade head
   ```
5. Endesha server (port 8000):
   ```bash
   uvicorn main:app --reload --port 8000
   ```
6. Fungua `client-godot/project.godot` kwenye Godot 4.3+.
7. Seeda wahusika wa majaribio:
   ```bash
   python tools/seed_test_characters.py
   ```

API inapatikana kwenye: `http://localhost:8000/api/v1/health`

---

## 📌 Hatua Inayofuata

1. `server-python/nlp/contextualizer.py` — Habari → Tamthilia (Kipengele #24)
2. `client-godot/camera/ProceduralCamera.gd` — Kamera ya Kisanii (Kipengele #12)
3. `shared/schemas/script_schema.json` — Mkataba wa data kati ya server na client (msingi wa vyote)

Pendekezo: Anza na **#3 (script_schema.json)** kwa sababu ndiyo msingi unaounganisha Python na Godot — bila hiyo, mifumo mingine haiwezi "kuongea" vizuri.
