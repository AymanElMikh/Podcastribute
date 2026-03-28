# PodcastAI — Learning Agent Instructions
# ══════════════════════════════════════════════════════════════════
# Reads the production code built by CLAUDE.md and extracts
# interview-ready learning concepts from it — grounded in real code.
# ══════════════════════════════════════════════════════════════════

You are a senior educator. Read the production code built by the
builder agent (CLAUDE.md) in this repository. Extract teachable
concepts grounded in the actual code — not invented abstractions.

Same rules as llm-gateway/LEARN.md: always read build_status.json
first, only teach from completed phases, never repeat concepts
already in learned_concepts.json.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## CATEGORIES FOR THIS PROJECT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  python_core         — Protocol, TypedDict, asyncio patterns
  fastapi             — file uploads, multipart, JWT auth, Depends
  async_python        — asyncio.gather, Celery, parallel generation
  langgraph           — linear graph, state, node design
  ai_patterns         — voice fingerprint, moment detection, content factory
  databases           — SQLAlchemy async, Alembic, JSONB columns
  devops              — Celery worker Dockerfile, multi-service Compose
  testing             — mocking httpx, mocking Celery, file upload tests
  saas_patterns       — Stripe billing, plan enforcement, quota tracking
  nextjs              — SSE EventSource, file upload UX, streaming progress

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## FULL CONCEPT INVENTORY — 80+ CONCEPTS ACROSS 12 PHASES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Use the 5-layer framework from llm-gateway/LEARN.md on every concept:
  Layer 1: what the code IS
  Layer 2: WHY it's written this way
  Layer 3: what was DECIDED and why
  Layer 4: how to TEST it
  Layer 5: the INTERVIEW TRAP hiding in it

─────────────────────────────────────────────────
PHASE 1 — Scaffold  (7 concepts)
─────────────────────────────────────────────────
python_core:
  P01  ContentGenerator Protocol — why Protocol over ABC for generators
       source: api/generators/base.py → class ContentGenerator(Protocol)
       trap: can you isinstance() check a Protocol without runtime_checkable?

  P02  PodcastState as TypedDict — nested dict vs dataclass for graph state
       source: api/agent/state.py → class PodcastState(TypedDict)
       trap: what happens if you try to use a method on a TypedDict?

  P03  Pydantic Settings with multiple env sources
       source: api/config.py → class Settings(BaseSettings)
       trap: what's the precedence when .env file and os.environ both set a var?

fastapi:
  P04  FastAPI app factory pattern — why create_app() not module-level app
       source: api/main.py → def create_app() → FastAPI(...)
       trap: what breaks if you create two FastAPI instances in tests?

saas_patterns:
  P05  Plan hierarchy enforcement — dependency injection for access control
       source: api/dependencies.py → require_plan()
       trap: how do you test a route that requires plan="creator"?

  P06  Monthly quota reset pattern — comparing timestamps not counters
       source: api/dependencies.py → check_episode_quota()
       trap: what happens at midnight on reset day in a different timezone?

databases:
  P07  JSONB column in PostgreSQL — when to use JSONB vs separate table
       source: api/db/models.py → content_packs.twitter_thread JSONB
       trap: can you query inside a JSONB column? What's the cost?

─────────────────────────────────────────────────
PHASE 2 — Auth  (6 concepts)
─────────────────────────────────────────────────
fastapi:
  P08  JWT with FastAPI — oauth2_scheme, Depends, decode + verify
       source: api/v1/auth.py → get_current_user dependency
       trap: what's the difference between authentication and authorization?

  P09  bcrypt password hashing — work factor, timing attacks
       source: api/v1/auth.py → bcrypt.hashpw / bcrypt.checkpw
       trap: why is bcrypt.checkpw() safe against timing attacks?

  P10  HTTPException with WWW-Authenticate header — 401 vs 403
       source: api/v1/auth.py → raise HTTPException(401, headers=...)
       trap: when should you return 401 vs 403?

testing:
  P11  Testing protected routes — dependency_overrides for auth
       source: tests/test_auth.py → app.dependency_overrides[get_current_user]
       trap: what if you forget to clear dependency_overrides after test?

saas_patterns:
  P12  Stripe customer ID lifecycle — create on first payment not on signup
       source: api/db/models.py → stripe_customer_id nullable
       trap: what if you create a Stripe customer on signup but they never pay?

  P13  JWT payload design for SaaS — what to include, what to avoid
       source: api/v1/auth.py → payload: {sub, email, plan, exp}
       trap: if plan changes, old JWT still has old plan — how do you handle this?

─────────────────────────────────────────────────
PHASE 3 — Ingestion  (9 concepts)
─────────────────────────────────────────────────
async_python:
  P14  subprocess for CPU-heavy tools (Whisper) — asyncio.create_subprocess_exec
       source: api/ingestion/audio_processor.py → asyncio.create_subprocess_exec
       trap: if you use subprocess.run() in an async function, what blocks?

  P15  Celery for long-running background tasks
       source: worker/celery_app.py → @celery_app.task
       layer 1: Celery worker runs in separate process from FastAPI
       trap: can a Celery task be async? What's the pattern?

  P16  asyncio.run() inside a synchronous Celery task
       source: worker/tasks.py → asyncio.run(_run_pipeline(episode_id))
       trap: what happens if you call asyncio.run() inside a running event loop?

  P17  FastAPI file upload — UploadFile, multipart/form-data
       source: api/v1/episodes.py → async def upload(file: UploadFile)
       trap: UploadFile is a SpooledTemporaryFile — when does it hit disk?

fastapi:
  P18  202 Accepted — the correct status for async task submission
       source: api/v1/episodes.py → return JSONResponse(status_code=202, ...)
       layer 2: 202 tells client "I got it, I'm working on it"
       trap: what's the difference between 200, 201, and 202?

  P19  File validation before saving — MIME type + size guard
       source: api/v1/episodes.py → validate_audio_file()
       trap: can you trust the Content-Type header from the browser?

production_patterns:
  P20  Streaming file download with httpx — don't load 200MB into memory
       source: api/ingestion/rss_parser.py → client.stream("GET", url)
       trap: what happens if you use client.get() on a 500MB file?

  P21  Path isolation per user — uploads/{user_id}/{episode_id}/
       source: api/ingestion/audio_processor.py → build_upload_path()
       trap: what's the security risk of a flat uploads/ directory?

devops:
  P22  Celery worker as a separate Docker service
       source: docker/Dockerfile.worker → CMD celery ... worker
       layer 2: API and worker share code but run in separate containers
       trap: what happens if the worker crashes mid-transcription?

─────────────────────────────────────────────────
PHASE 4 — Voice Fingerprint  (6 concepts)
─────────────────────────────────────────────────
ai_patterns:
  P23  Voice fingerprint as a structured LLM output
       source: api/voice/fingerprint.py → FINGERPRINT_PROMPT
       layer 1: prompt enforces JSON schema, parse into Pydantic model
       trap: what do you do when the LLM returns valid JSON with wrong fields?

  P24  Graceful fallback to default profile
       source: api/voice/fingerprint.py → except JSONDecodeError: return default
       layer 2: one failed calibration shouldn't block the user's first upload
       trap: how do you tell the user their calibration failed without alarming them?

  P25  Injecting voice profile into every generator prompt
       source: api/generators/twitter.py → system.format(voice_profile=...)
       layer 3: why format() at call time, not at class instantiation?
       trap: what's the prompt injection risk when voice profile contains user text?

python_core:
  P26  strategy="quality" vs "balanced" — choosing LLM tier per task
       source: api/voice/fingerprint.py → strategy="quality"
       layer 3: fingerprint runs once, costs more but matters most — use best model
       generators run for every episode — use balanced to control costs

testing:
  P27  Testing LLM-dependent code — mock at the HTTP layer
       source: tests/test_voice.py → respx.mock for gateway calls
       trap: should you test with a real LLM in CI? Why or why not?

  P28  Asserting prompt content in tests — checking call_args
       source: tests/test_voice.py → mock.call_args[1]["json"]["messages"]
       layer 1: check that the right system prompt was sent
       trap: what's the difference between assert_called_once and assert_called_once_with?

─────────────────────────────────────────────────
PHASE 5 — Moment Detection  (6 concepts)
─────────────────────────────────────────────────
ai_patterns:
  P29  Chunking strategy for long transcripts — overlapping windows
       source: api/agent/nodes/moment_detector.py → chunk_transcript()
       layer 1: 500-word chunks with 50-word overlap
       trap: why is overlap necessary? What moment does it prevent you from missing?

  P30  Parallel scoring of transcript chunks
       source: api/agent/nodes/moment_detector.py → asyncio.gather(*tasks)
       layer 2: process all chunks at once instead of one-by-one
       trap: if one chunk fails, do you lose all results? Use return_exceptions=True

  P31  Moment diversity enforcement — not just top scores
       source: api/agent/nodes/moment_detector.py → ensure_type_diversity()
       layer 3: top 10 by score would all be "strong_opinion" — boring
       trap: how do you enforce diversity without hurting quality?

  P32  Self-assessed confidence scores — LLM rates its own output
       source: api/agent/nodes/moment_detector.py → shareability_score: float
       layer 5: LLM confidence scores are not calibrated probabilities
       trap: when should you trust LLM self-scores and when should you not?

langgraph:
  P33  Linear graph — no conditional edges needed
       source: api/agent/graph.py → all add_edge, no add_conditional_edges
       layer 3: podcast repurposing is deterministic — no branching needed
       contrast with research agent which has a loop

  P34  Compiling graph once at module import
       source: api/agent/graph.py → podcast_graph = build_podcast_graph()
       layer 1: compile() is expensive — do it once, not per request
       trap: is a compiled LangGraph graph thread-safe?

─────────────────────────────────────────────────
PHASE 6 — Content Generators  (8 concepts)
─────────────────────────────────────────────────
ai_patterns:
  P35  System prompt templating with voice profile fields
       source: api/generators/twitter.py → TWITTER_SYSTEM.format(...)
       layer 3: why format() not f-string? Because prompt is a module constant

  P36  Output format contracts — JSON-only prompts
       source: api/generators/twitter.py → "Return ONLY valid JSON"
       trap: what's the failure rate of JSON-only prompts? How do you handle it?

  P37  Tweet character limit enforcement — validation after generation
       source: api/generators/twitter.py → validate_tweet_length()
       layer 2: LLM doesn't count characters accurately — validate after
       trap: does len() correctly count Twitter's character limit?

  P38  Format-specific prompt design — LinkedIn vs Twitter voice
       source: generators/twitter.py vs generators/linkedin.py
       layer 3: same voice profile, completely different prompt rules per platform

python_core:
  P39  Protocol for generators — structural duck typing
       source: api/generators/base.py → class ContentGenerator(Protocol)
       layer 2: all generators have generate() — Protocol enforces this statically

async_python:
  P40  httpx.AsyncClient timeout strategy for LLM calls
       source: api/generators/base.py → timeout=60.0 in AsyncClient
       trap: what's the right timeout for a generator that produces 1500 tokens?

testing:
  P41  Mock call_args to test prompt content
       source: tests/test_generators.py → assert voice fields in prompt
       layer 1: verify the generator actually uses the voice profile

  P42  Parametrize generators — test all 8 with one test function
       source: tests/test_generators.py → @pytest.mark.parametrize("generator_class")
       layer 2: DRY — all generators have the same interface

─────────────────────────────────────────────────
PHASE 7 — Content Factory  (7 concepts)
─────────────────────────────────────────────────
async_python:
  P43  asyncio.gather with return_exceptions=True — fault-tolerant parallel
       source: api/agent/nodes/content_factory.py → gather(*tasks, return_exceptions=True)
       layer 1: one failed generator doesn't kill the whole content pack
       trap: how do you distinguish a real result from an Exception in the results list?

  P44  Parallel vs sequential LLM calls — cost vs latency tradeoff
       source: api/agent/nodes/content_factory.py
       layer 3: 8 sequential calls = 8 minutes. 8 parallel = 90 seconds.
       trap: what's the risk of 8 parallel gateway calls on rate limits?

ai_patterns:
  P45  Content pack as a flat dict — not nested model
       source: api/agent/nodes/content_factory.py → pack[name] = result.model_dump()
       layer 3: JSONB storage requires serializable dict, not Pydantic objects

  P46  Partial success strategy — 6/8 formats is still a success
       source: api/agent/nodes/content_factory.py → success_count check
       layer 2: user gets 6 formats now and can retry failed ones
       trap: what's the minimum acceptable number of formats?

langgraph:
  P47  Node returning partial state — not full AgentState
       source: api/agent/nodes/content_factory.py → return {"content_pack": pack}
       layer 1: LangGraph merges partial returns into full state
       trap: what happens if you accidentally return a field that conflicts?

testing:
  P48  Integration testing a LangGraph graph — mock every node
       source: tests/test_graph.py → patch each node function
       layer 2: test the graph wiring, not the node logic (that's in unit tests)

  P49  Asserting SSE events in graph tests
       source: tests/test_graph.py → mock Redis publish, assert call_count
       trap: how do you assert events were emitted in correct order?

─────────────────────────────────────────────────
PHASE 8 — SSE Streaming  (5 concepts)
─────────────────────────────────────────────────
async_python:
  P50  Redis pub/sub in async Python — publish from worker, subscribe in API
       source: api/streaming.py → redis.publish / pubsub.listen()
       trap: Celery worker is synchronous — how do you publish to Redis from it?

  P51  AsyncIterator as StreamingResponse source
       source: api/streaming.py → async def event_stream() → AsyncIterator[str]
       layer 1: FastAPI StreamingResponse wraps the generator

fastapi:
  P52  SSE format — "data: {json}\n\n" — why two newlines
       source: api/streaming.py → yield f"data: {data}\n\n"
       trap: what does the browser EventSource do with a single \n?

nextjs:
  P53  EventSource API — browser-native SSE client
       source: frontend/components/ProcessingProgress.tsx
       layer 1: EventSource reconnects automatically — sometimes a problem
       trap: how do you prevent EventSource from reconnecting after "done" event?

  P54  Cleanup of EventSource in React useEffect
       source: frontend/components/ProcessingProgress.tsx → return () => es.close()
       trap: what happens if you forget the cleanup function?

─────────────────────────────────────────────────
PHASE 9 — Next.js Dashboard  (6 concepts)
─────────────────────────────────────────────────
nextjs:
  P55  File upload with progress in Next.js — XMLHttpRequest vs fetch
       source: frontend/components/UploadZone.tsx
       layer 1: fetch() doesn't support upload progress — use XHR or axios
       trap: how do you show upload progress percentage with the Fetch API?

  P56  Drag-and-drop file upload — DataTransfer API
       source: frontend/components/UploadZone.tsx → onDrop handler
       trap: how do you prevent the browser from opening the file on drop?

  P57  Inline contentEditable editing — controlled vs uncontrolled
       source: frontend/components/ContentEditor.tsx
       layer 3: why contentEditable here instead of textarea?
       trap: how do you get the text content from a contentEditable div?

  P58  Next.js App Router — server vs client components for streaming
       source: frontend/app/content/[id]/page.tsx
       layer 3: page is server component, EventStream is client component
       trap: can you use EventSource in a server component?

  P59  Clipboard API — navigator.clipboard.writeText()
       source: frontend/components/PublishQueue.tsx → copy button
       trap: does clipboard API work in non-HTTPS context?

  P60  Optimistic UI — show "published" before API confirms
       source: frontend/components/PublishQueue.tsx
       layer 3: feels faster, but needs rollback on failure

─────────────────────────────────────────────────
PHASE 10 — Publisher Integrations  (5 concepts)
─────────────────────────────────────────────────
production_patterns:
  P61  OAuth token storage — encrypt at rest in DB
       source: api/publisher/buffer_client.py → encrypted_token field
       trap: what's wrong with storing OAuth tokens in plaintext?

  P62  Per-platform error handling — publish failure is not a fatal error
       source: api/v1/publish.py → return {platform: status} per platform
       layer 2: one platform failing should not stop others

  P63  Idempotency in publish — prevent double-posting
       source: api/v1/publish.py → check publish_logs before sending
       trap: what's the race condition risk if user clicks Publish twice?

  P64  Buffer API rate limits — one post per second
       source: api/publisher/buffer_client.py → asyncio.sleep between calls
       trap: what's the correct approach when you hit a rate limit?

testing:
  P65  Testing OAuth flows — mock the token exchange
       source: tests/test_publisher.py → respx.mock for platform APIs
       layer 2: never use real platform API tokens in CI

─────────────────────────────────────────────────
PHASE 11 — Stripe Billing  (8 concepts)
─────────────────────────────────────────────────
saas_patterns:
  P66  Stripe Checkout vs Stripe Elements — which to use when
       source: api/v1/billing.py → create_checkout_session()
       layer 3: Checkout = hosted page (easier, less control). Elements = custom UI.
       trap: Checkout redirects away from your site — test the return URL carefully

  P67  Stripe webhook signature verification — the critical security step
       source: api/v1/billing.py → stripe.Webhook.construct_event()
       layer 1: verify webhook came from Stripe, not an attacker
       trap: what happens if you return 200 to a failed webhook?

  P68  Stripe event idempotency — process each event exactly once
       source: api/v1/billing.py → check event already processed
       trap: Stripe retries webhooks on failure — your handler must be idempotent

  P69  Subscription lifecycle — which events to handle
       source: api/v1/billing.py → checkout.session.completed, subscription events
       layer 2: at minimum handle: completed, updated, deleted, payment_failed
       trap: what happens if you only handle checkout.session.completed?

  P70  Downgrade logic — what happens to their data on cancellation
       source: api/v1/billing.py → on subscription.deleted: plan = "free"
       layer 3: design decision — keep their episodes? Limit access? Block entirely?

  P71  Stripe test mode vs live mode — environment separation
       source: api/config.py → STRIPE_SECRET_KEY starts with sk_test_ or sk_live_
       trap: how do you prevent accidentally charging real cards in development?

  P72  Episode quota as a rate limiting pattern
       source: api/dependencies.py → check_episode_quota()
       layer 2: quota is a usage-based limit, not a feature flag
       trap: what's the UX when a user hits their quota mid-month?

  P73  Stripe Customer Portal — let Stripe handle subscription management
       source: api/v1/billing.py → create_portal_session()
       layer 3: don't build your own cancellation/upgrade UI — Stripe does it better

─────────────────────────────────────────────────
PHASE 12 — Docker + Deploy  (7 concepts)
─────────────────────────────────────────────────
devops:
  P74  Three Dockerfiles — api, worker, frontend — shared code, different entrypoints
       source: docker/Dockerfile.api vs docker/Dockerfile.worker
       layer 2: same Python code, different CMD. Worker doesn't need uvicorn.
       trap: if you update a dependency, do you need to rebuild both images?

  P75  Celery worker concurrency — how many tasks run in parallel
       source: docker/Dockerfile.worker → --concurrency=2
       layer 3: transcription is CPU-bound, not I/O-bound
       trap: what's the right concurrency for CPU-bound vs I/O-bound Celery tasks?

  P76  client_max_body_size in Nginx for large file uploads
       source: nginx/podcast.conf → client_max_body_size 500M
       trap: what error does the client see if this is too small?

  P77  proxy_request_buffering off — stream upload to API directly
       source: nginx/podcast.conf → proxy_request_buffering off
       layer 1: without this, Nginx buffers the entire 200MB before forwarding
       trap: what's the memory impact of buffering large uploads at Nginx?

  P78  Upload volume mount — persist audio files across container restarts
       source: docker/docker-compose.yml → uploads-data volume
       trap: what happens to uploaded files if you don't mount a volume?

  P79  Celery task result backend — Redis vs PostgreSQL
       source: worker/celery_app.py → result_backend = REDIS_URL
       layer 3: we use Redis for results because we don't need long-term task history
       trap: what happens to task results if Redis restarts without persistence?

  P80  Health check for worker — Celery inspect ping
       source: docker/docker-compose.yml → healthcheck for worker service
       layer 1: docker can't HTTP-check a Celery worker — use celery inspect ping

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## README.md FORMAT (per concept)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# {Concept Title}

## Where This Appears
File: `{exact path}`
Reference: `{function or class name}`

(exact code snippet — 5-15 lines from the real file)

## Interview Question
## Short Answer (30 seconds)
## Deep Explanation
## Why the Builder Used This Here
## Common Mistakes
## Interview Trap
## Related Concepts in This Project

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## demo.py FORMAT (per concept)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
Concept : {Title}
Source  : {file path in podcastai}
Run     : python demo.py
Deps    : {list or 'none'}
"""
# 1. concept in isolation
# 2. gateway pattern mirrored from production
# 3. wrong way vs correct way
# 4. edge case / interview trap

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SESSION COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"Learn phase {N}"              → extract 5 concepts from that phase
"Learn phase {N} — more"       → 5 more concepts from same phase
"Learn phase {N} — {layer}"    → focus on syntax|pattern|tradeoffs|testing|traps
"Learn phase {N} — {category}" → focus on one category
"Learn concept P{number}"      → generate that specific concept
"What can I learn from phase {N}?" → show full inventory, mark covered/uncovered
"Concept map"                  → full coverage table across all phases
"Deep dive — {slug}"           → regenerate with more depth
"Review {slug}"                → quiz mode