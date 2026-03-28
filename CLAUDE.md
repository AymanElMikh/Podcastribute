# PodcastAI — Agent Build Instructions
# ══════════════════════════════════════════════════════════════════
# Project  : AI Podcast Repurposing Engine (SaaS)
# Stack    : FastAPI · LangGraph · Celery · Whisper · Next.js 14
#            PostgreSQL · Redis · Stripe · Docker · Nginx
# VPS path : /opt/projects/podcastai
# Domain   : podcast.yourdomain.com
# Pricing  : Starter $49 · Creator $149 · Studio $399/mo
# ══════════════════════════════════════════════════════════════════

You are a senior full-stack AI engineer building PodcastAI — a SaaS
that turns podcast episodes into 8 content formats automatically.

The core insight: podcasters need content that sounds like THEM,
not generic AI output. The voice fingerprint is the product's moat.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## BEFORE EVERY ACTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Read build_status.json — know the current phase
2. Work ONLY on the current phase — nothing else
3. All tests must pass before marking a phase complete
4. Update build_status.json after completing each phase

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## ARCHITECTURE RULES — NON-NEGOTIABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Code quality:
  - Type hints on EVERY function and class attribute
  - Docstrings on EVERY class and public method
  - Pydantic models for ALL request/response/config shapes
  - Named constants — never magic strings or numbers inline
  - structlog for all logging — never bare print()
  - No hardcoded credentials — Pydantic Settings only

Architecture:
  - Generators use Protocol (typing) — not ABC
  - All LLM calls go through the LLM gateway at GATEWAY_URL
  - Audio processing is ALWAYS in Celery worker — never in FastAPI request
  - Content generation is ALWAYS async with asyncio.gather
  - SSE progress events emitted at every meaningful state transition
  - Stripe webhook validates signature — never trust raw payload

Processing flow:
  1. FastAPI receives upload → saves file → enqueues Celery task → returns 202
  2. Celery worker runs the full LangGraph pipeline
  3. Every node emits SSE events via Redis pub/sub
  4. Frontend EventSource consumes the stream live
  5. On completion: save to PostgreSQL, notify via SSE "content_ready"

Security:
  - Stripe webhook: always verify with stripe.Webhook.construct_event()
  - File uploads: validate MIME type + size before saving
  - User isolation: every DB query filters by user_id from JWT
  - Audio files: stored in /uploads/{user_id}/{episode_id}/ — never flat

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## ENVIRONMENT VARIABLES (define in config.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  GATEWAY_URL              # http://gateway.yourdomain.com
  DATABASE_URL             # postgresql+asyncpg://...
  REDIS_URL                # redis://redis:6379
  CELERY_BROKER_URL        # redis://redis:6379/1
  STRIPE_SECRET_KEY
  STRIPE_WEBHOOK_SECRET
  STRIPE_PRICE_STARTER     # price_xxx
  STRIPE_PRICE_CREATOR     # price_xxx
  STRIPE_PRICE_STUDIO      # price_xxx
  WHISPER_MODEL            # base | small | medium (default: small)
  UPLOADS_DIR              # /uploads
  MAX_UPLOAD_MB            # 500
  JWT_SECRET_KEY
  JWT_ALGORITHM            # HS256
  ENVIRONMENT              # development | production

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## DATABASE SCHEMA — define all models before writing any business logic
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

users:
  id UUID PK, email TEXT UNIQUE, hashed_password TEXT,
  stripe_customer_id TEXT, plan TEXT (starter|creator|studio|free),
  episodes_this_month INT DEFAULT 0,
  plan_reset_at TIMESTAMP, created_at TIMESTAMP

voice_profiles:
  id UUID PK, user_id UUID FK → users,
  vocabulary_level TEXT, sentence_style TEXT, humor_level TEXT,
  twitter_style TEXT, linkedin_style TEXT,
  signature_phrases JSONB, topics JSONB,
  words_to_avoid JSONB, tone_adjectives JSONB,
  calibration_samples_count INT, created_at TIMESTAMP, updated_at TIMESTAMP

episodes:
  id UUID PK, user_id UUID FK → users,
  title TEXT, source_type TEXT (upload|youtube|rss),
  source_url TEXT, audio_path TEXT,
  duration_seconds INT, transcript TEXT,
  status TEXT (queued|transcribing|detecting|generating|ready|error),
  error_message TEXT, processing_started_at TIMESTAMP,
  processing_completed_at TIMESTAMP, created_at TIMESTAMP

moments:
  id UUID PK, episode_id UUID FK → episodes,
  start_time TEXT, end_time TEXT, text TEXT,
  moment_type TEXT, shareability_score FLOAT,
  one_line_hook TEXT, position INT

content_packs:
  id UUID PK, episode_id UUID FK → episodes,
  twitter_thread JSONB, twitter_hooks JSONB, twitter_listen_tweet TEXT,
  linkedin_post TEXT, linkedin_carousel_outline JSONB,
  newsletter_section TEXT, newsletter_subject_lines JSONB,
  short_video_scripts JSONB,
  blog_post_title TEXT, blog_post_body TEXT, blog_post_meta TEXT,
  youtube_description TEXT, youtube_chapters JSONB,
  quote_cards JSONB,
  email_sequence JSONB,
  created_at TIMESTAMP

publish_logs:
  id UUID PK, episode_id UUID FK, platform TEXT,
  content_type TEXT, status TEXT (sent|failed|scheduled),
  scheduled_at TIMESTAMP, sent_at TIMESTAMP, error TEXT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## BUILD PHASES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

╔══════════════════════════════════════════════════════════════════╗
║  PHASE 1 — Scaffold, models, config                            ║
╚══════════════════════════════════════════════════════════════════╝

Create full directory structure with empty modules + docstrings.
Define ALL Pydantic models completely. Define ALL SQLAlchemy models.
No business logic yet — structure only.

Directory structure to create:
  api/__init__.py, api/main.py, api/config.py, api/dependencies.py
  api/ingestion/__init__.py, api/ingestion/audio_processor.py
  api/ingestion/youtube_downloader.py, api/ingestion/rss_parser.py
  api/ingestion/diarizer.py
  api/agent/__init__.py, api/agent/graph.py, api/agent/state.py
  api/agent/nodes/__init__.py, api/agent/nodes/moment_detector.py
  api/agent/nodes/content_factory.py, api/agent/nodes/quality_checker.py
  api/generators/__init__.py, api/generators/base.py
  api/generators/twitter.py, api/generators/linkedin.py
  api/generators/newsletter.py, api/generators/short_video.py
  api/generators/blog_post.py, api/generators/youtube_description.py
  api/generators/quote_cards.py, api/generators/email_sequence.py
  api/voice/__init__.py, api/voice/fingerprint.py
  api/publisher/__init__.py, api/publisher/buffer_client.py
  api/publisher/beehiiv_client.py, api/publisher/linkedin_client.py
  api/models/__init__.py, api/models/episode.py
  api/models/content.py, api/models/voice.py, api/models/user.py
  api/db/__init__.py, api/db/models.py, api/db/session.py
  api/v1/__init__.py, api/v1/auth.py, api/v1/episodes.py
  api/v1/content.py, api/v1/publish.py, api/v1/voice.py
  api/v1/billing.py, api/v1/stream.py
  api/streaming.py
  worker/__init__.py, worker/celery_app.py, worker/tasks.py
  tests/__init__.py, tests/conftest.py
  pyproject.toml, .env.example, .gitignore, Makefile

PodcastState TypedDict (api/agent/state.py):
  session_id: str
  user_id: str
  episode_id: str
  source_type: str                    # upload | youtube | rss
  audio_path: str
  transcript: str
  speaker_segments: list[dict]        # [{speaker, start, end, text}]
  voice_profile: dict                 # VoiceProfile as dict
  moments: list[dict]                 # detected moments
  content_pack: dict                  # all generated content
  status: str
  error: str | None

ContentGenerator Protocol (api/generators/base.py):
  class ContentGenerator(Protocol):
      async def generate(self, moments, transcript, voice) -> dict: ...
      @property
      def format_name(self) -> str: ...

Makefile targets:
  dev        → docker compose up --build
  down       → docker compose down
  test       → pytest tests/ -v
  worker     → celery -A worker.celery_app worker --loglevel=info
  lint       → ruff check api/ tests/ worker/
  migrate    → alembic upgrade head
  shell      → docker compose exec api bash

Phase complete when:
  - python -c "from api.main import app" imports without error
  - python -c "from api.agent.state import PodcastState" passes
  - make lint passes

╔══════════════════════════════════════════════════════════════════╗
║  PHASE 2 — Auth + user management                              ║
╚══════════════════════════════════════════════════════════════════╝

Implement full auth system before any feature work.

api/v1/auth.py:
  POST /v1/auth/register    → create user, hash password (bcrypt)
  POST /v1/auth/login       → verify, return JWT access token
  GET  /v1/auth/me          → return current user from JWT

JWT:
  - HS256 signing with JWT_SECRET_KEY
  - Payload: {sub: user_id, email, plan, exp}
  - 30 day expiry for access token
  - FastAPI dependency: get_current_user(token: str = Depends(oauth2_scheme))

Plan limits enforcement — dependency:
  async def require_plan(min_plan: str):
      # checks user.plan against hierarchy: free < starter < creator < studio
      # raises 403 with upgrade message if plan insufficient

Episode quota enforcement — dependency:
  async def check_episode_quota(user, db):
      # resets counter if plan_reset_at has passed
      # raises 429 with quota message if at limit
      # limits: free=1 trial, starter=4, creator=15, studio=unlimited

Tests (tests/test_auth.py):
  - register creates user with hashed password
  - login returns valid JWT
  - invalid password returns 401
  - expired token returns 401
  - plan check blocks insufficient tier

Phase complete when: all auth tests pass

╔══════════════════════════════════════════════════════════════════╗
║  PHASE 3 — Ingestion pipeline                                  ║
╚══════════════════════════════════════════════════════════════════╝

Three ingestion paths: file upload, YouTube URL, RSS feed.
All paths converge on a local audio file + transcript.

api/ingestion/audio_processor.py:
  class AudioProcessor:
    async def transcribe(audio_path: str) -> TranscriptResult
      - run whisper via subprocess: whisper {path} --model small --output_format json
      - parse output JSON → transcript text + word-level timestamps
      - return TranscriptResult(text, segments, duration_seconds, language)

    async def convert_to_wav(input_path: str) -> str
      - ffmpeg -i {input} -ar 16000 -ac 1 {output.wav}
      - returns output path
      - required for Whisper accuracy

api/ingestion/youtube_downloader.py:
  class YouTubeDownloader:
    async def download(url: str, output_dir: str) -> str
      - yt-dlp --format bestaudio --extract-audio
      - --audio-format mp3 --audio-quality 5
      - validates URL is a real YouTube URL before downloading
      - returns path to downloaded file
      - raises DownloadError on failure

api/ingestion/rss_parser.py:
  class RSSParser:
    async def get_latest_episode(feed_url: str) -> RSSEpisode
      - fetch RSS feed with httpx
      - parse with feedparser
      - find most recent episode with enclosure (audio URL)
      - download audio with httpx streaming to temp file
      - return RSSEpisode(title, audio_path, published_at, episode_url)

    async def list_episodes(feed_url: str, limit=10) -> list[RSSEpisode]
      - same but returns list for user to choose

api/v1/episodes.py:
  POST /v1/episodes/upload    — multipart file upload
    - validate: MIME in [audio/mpeg, audio/wav, audio/mp4, audio/x-m4a]
    - validate: size <= MAX_UPLOAD_MB
    - save to uploads/{user_id}/{episode_id}/{filename}
    - create Episode record (status=queued)
    - enqueue Celery task: process_episode.delay(episode_id)
    - return 202 {episode_id, status: "queued"}

  POST /v1/episodes/youtube   — {url: str}
  POST /v1/episodes/rss       — {feed_url: str, episode_index: 0}
  GET  /v1/episodes           — list user's episodes (paginated)
  GET  /v1/episodes/{id}      — episode detail + status

worker/tasks.py:
  @celery_app.task
  def process_episode(episode_id: str):
    # runs the full LangGraph pipeline synchronously in Celery worker
    asyncio.run(_run_pipeline(episode_id))

  async def _run_pipeline(episode_id: str):
    # 1. load episode from DB
    # 2. convert audio to WAV if needed
    # 3. transcribe with Whisper
    # 4. load user's voice profile from DB
    # 5. invoke research_graph with initial state
    # 6. save results to DB
    # 7. update episode status

Tests (tests/test_ingestion.py):
  - transcribe() returns TranscriptResult with text and segments
  - youtube download validates URL format
  - upload rejects non-audio MIME types
  - upload rejects files over size limit

Phase complete when: can upload a short MP3 and get a transcript in DB

╔══════════════════════════════════════════════════════════════════╗
║  PHASE 4 — Voice fingerprint builder                           ║
╚══════════════════════════════════════════════════════════════════╝

The core differentiator. Build before any content generation.

api/voice/fingerprint.py:
  FINGERPRINT_PROMPT = """
  Analyze these content samples from a podcaster. Extract their voice profile.
  Return ONLY valid JSON:
  {
    "vocabulary_level": "casual|professional|academic|technical",
    "sentence_style": "short_punchy|conversational|detailed|storytelling",
    "humor_level": "none|dry|occasional|frequent",
    "twitter_style": "thread_storyteller|hot_take|educator|question_asker",
    "linkedin_style": "personal_story|industry_insight|contrarian|practical_tips",
    "signature_phrases": ["phrases they use repeatedly"],
    "topics_they_care_about": ["recurring themes"],
    "what_they_never_say": ["jargon and words to avoid"],
    "tone_adjectives": ["three words describing their voice"],
    "default_cta_style": "soft_invite|direct_ask|community_focused|value_first"
  }
  """

  class VoiceFingerprintBuilder:
    async def build_from_transcripts(
        self, transcripts: list[str]
    ) -> VoiceProfile
      - combine up to 5 transcripts (truncate to 6000 chars total)
      - call gateway with strategy="quality" (needs best model)
      - parse JSON → VoiceProfile
      - fallback to default profile if parsing fails

    async def build_from_social_posts(
        self, posts: list[str]
    ) -> VoiceProfile
      - same but with social media samples
      - adjust prompt to mention posts are from social media

    async def refine(
        self, existing: VoiceProfile, feedback: str
    ) -> VoiceProfile
      - user says "I never use corporate buzzwords" or "make it more casual"
      - refines specific fields based on feedback

api/v1/voice.py:
  POST /v1/voice/calibrate/transcripts  — {transcripts: list[str]}
  POST /v1/voice/calibrate/posts        — {posts: list[str]}
  POST /v1/voice/calibrate/episodes     — uses user's past episodes
  PUT  /v1/voice/refine                 — {feedback: str}
  GET  /v1/voice                        — get current voice profile
  PUT  /v1/voice                        — manual override of profile fields

Onboarding flow:
  - New user sees voice calibration as step 1 before first upload
  - Option A: paste 5 existing social posts (fastest)
  - Option B: upload 2-3 past episode audio files
  - Option C: skip (use balanced default profile, less personalized)
  - Profile is saved to voice_profiles table
  - Can be updated anytime in settings

Tests (tests/test_voice.py):
  - build_from_transcripts returns valid VoiceProfile
  - handles gateway failure with default profile fallback
  - refine() updates only the fields mentioned in feedback
  - empty samples list returns default profile

Phase complete when: voice calibration flow works end to end

╔══════════════════════════════════════════════════════════════════╗
║  PHASE 5 — Moment detection agent                              ║
╚══════════════════════════════════════════════════════════════════╝

api/agent/nodes/moment_detector.py:

  MOMENT_TYPES = [
    "strong_opinion", "surprising_statistic", "actionable_advice",
    "personal_story", "contrarian_take", "quotable_one_liner",
    "debate_moment", "prediction", "definition", "case_study"
  ]

  DETECTOR_PROMPT = """
  Analyze this podcast transcript segment. Find the best moments for content repurposing.
  Voice profile of this podcaster: {voice_profile_summary}

  For each strong moment, evaluate:
  - Standalone value (0-1): understood without full episode context?
  - Emotional resonance (0-1): does it provoke a reaction?
  - Shareability (0-1): would someone forward this?
  - Type: one of {moment_types}

  Return JSON array (top moments only, minimum score 0.6):
  [{{"start_time":"MM:SS","end_time":"MM:SS","text":"exact quote",
    "type":"moment_type","shareability_score":0.0-1.0,
    "one_line_hook":"what makes this worth sharing"}}]
  """

  async def moment_detector(state: PodcastState) -> dict:
    1. chunk transcript into 500-word overlapping segments
    2. score each chunk in parallel (asyncio.gather)
    3. deduplicate overlapping moments (same start_time)
    4. rank by shareability_score descending
    5. take top 10
    6. ensure diversity: at least 3 different moment_types represented
    7. emit event: moments_detected with count
    8. return {"moments": top_10}

  Chunking strategy:
    - 500 words per chunk with 50-word overlap
    - overlap prevents missing moments that span chunk boundaries
    - include timestamp markers in each chunk

Tests (tests/test_moment_detector.py):
  - detects moments from a sample transcript
  - returns max 10 moments
  - ensures diversity of moment types
  - handles transcript with no strong moments gracefully

Phase complete when: moment detector returns ranked moments from a real transcript

╔══════════════════════════════════════════════════════════════════╗
║  PHASE 6 — All 8 content generators                            ║
╚══════════════════════════════════════════════════════════════════╝

Implement all generators. Each follows the same pattern:
  - System prompt embeds voice profile fields
  - User prompt provides moments + context
  - Returns typed Pydantic model
  - Handles gateway errors gracefully

Generator 1 — api/generators/twitter.py:
  Output: {
    main_thread: list[str]            # 8-12 tweets, numbered
    standalone_hooks: list[str]       # 3 single viral tweets
    listen_tweet: str                 # drives episode plays
  }
  Rules: no corporate language, each tweet under 280 chars,
         thread should tell a story not just list points,
         first tweet is the hook (no "🧵 Thread:" prefix)

Generator 2 — api/generators/linkedin.py:
  Output: {
    post: str                         # 150-300 words
    carousel_outline: list[str]       # 7 slide titles for Canva
    post_hooks: list[str]             # 3 alternative opening lines
  }
  Rules: LinkedIn rewards vulnerability + specificity,
         no buzzwords, end with a genuine question,
         carousel should be a standalone lesson

Generator 3 — api/generators/newsletter.py:
  Output: {
    section_title: str
    section_body: str                 # 200-400 words
    subject_lines: list[str]          # 5 options A/B/C/D/E
    preview_text: str                 # email preview line
  }
  Rules: conversational not formal, section should feel
         like a letter not an article, subject lines
         should be curiosity-driven not clickbait

Generator 4 — api/generators/short_video.py:
  Output: {
    clips: list[{
      start_time: str
      end_time: str
      hook: str                       # first 3 seconds spoken text
      script_note: str                # what to show on screen
      platform: str                   # tiktok|reels|shorts
    }]
  }
  Rules: hook must be the strongest moment, script notes
         help editor know what text overlay to add,
         clips should be 45-90 seconds

Generator 5 — api/generators/blog_post.py:
  Output: {
    title: str                        # SEO-optimized H1
    meta_description: str             # 155 chars
    outline: list[str]                # H2 section headings
    body: str                         # 800-1200 words markdown
    internal_link_suggestions: list[str]
    target_keywords: list[str]
  }
  Rules: blog post should add context beyond the episode,
         not just a transcript, optimize for search intent,
         every section should be skimmable

Generator 6 — api/generators/youtube_description.py:
  Output: {
    description: str                  # first 150 chars are critical
    chapters: list[{time: str, title: str}]
    tags: list[str]                   # 15 tags
    end_screen_script: str            # what to say in last 20 seconds
  }
  Rules: first line hooks the viewer, chapters improve
         watch time, tags mix specific and broad

Generator 7 — api/generators/quote_cards.py:
  Output: {
    quotes: list[{
      text: str                       # under 140 chars
      attribution: str                # "— [Host Name], Episode Title"
      background_suggestion: str      # color/style recommendation
      caption: str                    # social caption for the image post
    }]
  }
  Rules: quotes should be self-contained insights,
         grammatically correct as standalone,
         no context-dependent references

Generator 8 — api/generators/email_sequence.py:
  Output: {
    emails: list[{
      subject: str
      preview_text: str
      body: str                       # 100-200 words each
      send_day: int                   # 0, 2, 5
      purpose: str                    # announce|insight|cta
    }]
  }
  Rules: email 0 = episode announcement, email 2 = best insight
         from episode, email 5 = CTA based on episode topic

All generators share this gateway call pattern:
  async def _call_gateway(
      self, system: str, user: str, strategy: str = "balanced"
  ) -> str:
      async with httpx.AsyncClient(timeout=60.0) as client:
          r = await client.post(
              f"{settings.GATEWAY_URL}/v1/chat/completions",
              json={
                  "messages": [
                      {"role": "system", "content": system},
                      {"role": "user", "content": user}
                  ],
                  "strategy": strategy,
                  "max_tokens": 2000,
              }
          )
          r.raise_for_status()
          return r.json()["choices"][0]["message"]["content"]

Tests (tests/test_generators.py):
  - each generator returns correctly structured output
  - mock gateway with realistic responses
  - voice profile fields appear in prompt (test via mock call_args)
  - graceful error: gateway failure returns empty content not crash

Phase complete when: all 8 generators pass their tests

╔══════════════════════════════════════════════════════════════════╗
║  PHASE 7 — Content factory + LangGraph graph                   ║
╚══════════════════════════════════════════════════════════════════╝

Wire everything into the LangGraph pipeline.

api/agent/nodes/content_factory.py:
  async def content_factory(state: PodcastState) -> dict:
    voice = VoiceProfile(**state["voice_profile"])
    moments = state["moments"]
    transcript = state["transcript"]

    await emit_event(state["session_id"], "generating_content", {
        "formats": 8, "message": "Generating all content formats..."
    })

    results = await asyncio.gather(
        TwitterGenerator(voice).generate(moments, transcript),
        LinkedInGenerator(voice).generate(moments, transcript),
        NewsletterGenerator(voice).generate(moments, transcript),
        ShortVideoGenerator(voice).generate(moments, transcript),
        BlogPostGenerator(voice).generate(moments, transcript),
        YouTubeDescriptionGenerator(voice).generate(moments, transcript),
        QuoteCardGenerator(voice).generate(moments, transcript),
        EmailSequenceGenerator(voice).generate(moments, transcript),
        return_exceptions=True,
    )

    names = [
        "twitter","linkedin","newsletter","short_video",
        "blog_post","youtube","quote_cards","email_sequence"
    ]
    pack = {}
    success_count = 0
    for name, result in zip(names, results):
        if isinstance(result, Exception):
            pack[name] = {"error": str(result), "content": None}
            log.warning("generator_failed", format=name, error=str(result))
        else:
            pack[name] = result.model_dump()
            success_count += 1

    await emit_event(state["session_id"], "content_ready", {
        "formats_generated": success_count,
        "episode_id": state["episode_id"]
    })
    return {"content_pack": pack, "status": "ready"}

api/agent/nodes/quality_checker.py:
  async def quality_checker(state: PodcastState) -> dict:
    # lightweight check before marking ready:
    # - twitter thread has >= 5 tweets
    # - blog post has >= 400 words
    # - at least 6 of 8 formats generated successfully
    # if quality too low: emit warning event, still return ready
    pass

api/agent/graph.py:
  def build_podcast_graph() -> CompiledGraph:
    graph = StateGraph(PodcastState)
    graph.add_node("moment_detector", moment_detector)
    graph.add_node("content_factory", content_factory)
    graph.add_node("quality_checker", quality_checker)
    graph.add_edge(START, "moment_detector")
    graph.add_edge("moment_detector", "content_factory")
    graph.add_edge("content_factory", "quality_checker")
    graph.add_edge("quality_checker", END)
    return graph.compile()

  podcast_graph = build_podcast_graph()  # compiled once at import

Tests (tests/test_graph.py):
  - full graph runs with mocked generators
  - failed generator does not stop the pipeline
  - content_ready event emitted on completion
  - state contains all 8 format keys after run

Phase complete when: full graph integration test passes

╔══════════════════════════════════════════════════════════════════╗
║  PHASE 8 — SSE streaming + progress events                     ║
╚══════════════════════════════════════════════════════════════════╝

api/streaming.py:
  CHANNEL = "podcast:{session_id}"
  EVENT_TTL = 7200  # 2 hours

  EVENT_TYPES = {
    "upload_received":     "Episode received, preparing...",
    "transcription_start": "Transcribing audio...",
    "transcription_done":  "Transcription complete ({duration})",
    "moments_detected":    "Found {count} great moments",
    "generating_content":  "Generating {formats} content formats...",
    "content_ready":       "All content ready for review!",
    "error":               "Processing failed: {message}",
  }

  async def emit_event(redis, session_id, type, data=None):
    event = {
        "type": type,
        "data": data or {},
        "label": EVENT_TYPES.get(type, type),
        "timestamp": datetime.utcnow().isoformat(),
    }
    await redis.publish(f"podcast:{session_id}", json.dumps(event))

  async def event_stream(redis, session_id) -> AsyncIterator[str]:
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"podcast:{session_id}")
    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            data = message["data"].decode()
            yield f"data: {data}\n\n"
            event = json.loads(data)
            if event["type"] in ("content_ready", "error"):
                break
    finally:
        await pubsub.unsubscribe()
        await pubsub.aclose()

api/v1/stream.py:
  GET /v1/stream/{episode_id}:
    - verify episode belongs to current user
    - return StreamingResponse(event_stream(...))
    - headers: Cache-Control: no-cache, X-Accel-Buffering: no

Phase complete when:
  - upload an episode → SSE stream shows progress events
  - frontend EventSource receives events live

╔══════════════════════════════════════════════════════════════════╗
║  PHASE 9 — Review dashboard + content editing (Next.js)        ║
╚══════════════════════════════════════════════════════════════════╝

frontend/app/content/[id]/page.tsx:
  Layout: two-column on desktop, stacked on mobile
  Left sidebar: format selector (Twitter, LinkedIn, Newsletter, etc.)
  Main area: the selected content, editable inline
  Right sidebar: episode info + publish queue

Components to build:

  ContentEditor.tsx:
    - renders content for selected format
    - inline editing with contentEditable or textarea
    - "Reset to original" button per format
    - character count for Twitter tweets (280 limit, red if over)
    - word count for blog/newsletter
    - saves edits to local state (not API until Publish)

  FormatNav.tsx:
    - tabs or sidebar list of 8 formats
    - badge showing "ready" or "error" per format
    - click to switch active format
    - "Approve all" button marks all formats as reviewed

  PublishQueue.tsx:
    - "Publish now" → immediate API call to /v1/publish
    - "Schedule" → date/time picker → schedules via Buffer API
    - "Copy" → clipboard, no API needed
    - shows platform logo (Twitter, LinkedIn, etc.)
    - success/error feedback per platform

  ProcessingProgress.tsx (used during processing):
    - EventSource connection to /v1/stream/{episode_id}
    - animated step indicators as events arrive
    - estimated time remaining (calibrate from avg processing time)
    - redirects to content view when content_ready fires

Pages:
  /dashboard           → episode list, usage meter, upgrade CTA
  /upload              → upload zone + YouTube URL + RSS
  /content/[id]        → review + edit + publish
  /settings            → voice calibration + platform connections + billing
  /onboarding          → 3-step: voice calibration → first upload → review

Phase complete when: full review flow works — upload, watch progress, review, copy

╔══════════════════════════════════════════════════════════════════╗
║  PHASE 10 — Platform publisher integrations                    ║
╚══════════════════════════════════════════════════════════════════╝

Implement direct publish to platforms.
Copy-to-clipboard works already (no API). This phase adds direct publish.

api/publisher/buffer_client.py:
  class BufferClient:
    POST https://api.bufferapp.com/1/updates/create.json
    - schedules Twitter, LinkedIn posts via Buffer
    - user connects Buffer in settings (OAuth flow)
    - store encrypted Buffer access token per user

api/publisher/beehiiv_client.py:
  class BeehiivClient:
    POST https://api.beehiiv.com/v2/publications/{pub_id}/posts
    - creates newsletter draft with generated content
    - user connects Beehiiv in settings (API key)

api/publisher/linkedin_client.py:
  class LinkedInClient:
    POST https://api.linkedin.com/v2/ugcPosts
    - direct LinkedIn post (no Buffer needed)
    - OAuth 2.0 flow for LinkedIn connection

api/v1/publish.py:
  POST /v1/publish:
    body: {
      episode_id: str,
      platforms: list[str],       # ["twitter", "linkedin", "newsletter"]
      content_overrides: dict,    # edited content to publish instead of original
      schedule_at: datetime | None
    }
    - check user plan allows this platform
    - call appropriate publisher client
    - log to publish_logs table
    - return {platform: status} dict

  GET /v1/publish/{episode_id}:
    - list all publish logs for this episode

Phase complete when: can publish to at least one platform directly

╔══════════════════════════════════════════════════════════════════╗
║  PHASE 11 — Stripe billing                                     ║
╚══════════════════════════════════════════════════════════════════╝

api/v1/billing.py:

  POST /v1/billing/checkout:
    - create Stripe Checkout Session
    - price_id from plan requested (starter|creator|studio)
    - success_url: /settings?upgraded=true
    - cancel_url: /settings
    - attach metadata: {user_id}

  POST /v1/billing/portal:
    - create Stripe Customer Portal session
    - for managing/cancelling subscription

  POST /v1/billing/webhook:
    - verify signature: stripe.Webhook.construct_event()
    - handle events:
        checkout.session.completed → update user.plan, user.stripe_customer_id
        customer.subscription.updated → update user.plan
        customer.subscription.deleted → downgrade to free
        invoice.payment_failed → send email warning (future)

  GET /v1/billing/usage:
    - return {episodes_this_month, limit, plan, reset_at}

Plan enforcement:
  - Episode upload checks quota before accepting file
  - Plan limits: free=1(trial), starter=4, creator=15, studio=unlimited
  - Monthly reset: check plan_reset_at, reset counter if month has passed

Pricing page (frontend/app/pricing/page.tsx):
  - Three cards: Starter, Creator, Studio
  - Highlight Creator as "Most popular"
  - "Start free" → free trial (1 episode, no card)
  - "Start plan" → Stripe Checkout

Phase complete when:
  - Checkout flow works in test mode
  - Webhook updates user.plan correctly
  - Episode upload blocked when quota exceeded

╔══════════════════════════════════════════════════════════════════╗
║  PHASE 12 — Docker + Nginx + CI/CD                             ║
╚══════════════════════════════════════════════════════════════════╝

docker/Dockerfile.api:
  FROM python:3.12-slim AS builder
  ... standard multi-stage pattern
  non-root user (app, uid 1000)
  HEALTHCHECK: curl -f http://localhost:8002/v1/health
  CMD: uvicorn api.main:app --host 0.0.0.0 --port 8002 --workers 2

docker/Dockerfile.worker:
  FROM python:3.12-slim
  # same deps as api
  CMD: celery -A worker.celery_app worker --concurrency=2 --loglevel=info

docker/Dockerfile.frontend:
  FROM node:20-alpine AS builder + runner (standalone output)
  CMD: node server.js (port 3001)

docker/docker-compose.yml:
  services: api, worker, frontend, redis, postgres
  All on podcast-net bridge network
  Volumes: pg-data, redis-data, uploads-data

nginx/podcast.conf:
  listen 443 ssl http2;
  server_name podcast.yourdomain.com;
  client_max_body_size 500M;          # large audio uploads
  proxy_request_buffering off;        # stream upload to API

  location / → frontend :3001
  location /v1/ → api :8002 with proxy_buffering off, timeout 600s
  HTTP → HTTPS redirect

.github/workflows/deploy.yml:
  jobs: test-api, test-frontend, build (2 images), deploy (SSH to VPS)
  environment: production (requires approval)
  deploy: pull both images, docker compose up api worker frontend

Phase complete when: full stack deploys to VPS, health check passes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SESSION COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"Build phase {N}"      → implement exactly that phase, nothing more
"Status"               → read build_status.json, show progress table
"Run tests"            → run pytest and show results
"Fix: {description}"   → fix a specific issue in current phase
"Review phase {N}"     → review code quality, suggest improvements