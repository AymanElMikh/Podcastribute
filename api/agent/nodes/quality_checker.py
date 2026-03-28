"""LangGraph node: lightweight quality gate before marking episode ready.

Verifies minimum content requirements are met and emits a warning event
if quality thresholds are not satisfied (without blocking completion).
"""

import structlog

from api.agent.state import PodcastState

log = structlog.get_logger(__name__)

_MIN_TWITTER_TWEETS: int = 5
_MIN_BLOG_WORDS: int = 400
_MIN_SUCCESSFUL_FORMATS: int = 6
_TOTAL_FORMATS: int = 8


async def quality_checker(state: PodcastState) -> dict:
    """Check generated content meets minimum quality thresholds.

    Validates:
    - Twitter thread has >= 5 tweets
    - Blog post has >= 400 words
    - At least 6 of 8 formats generated successfully

    Emits a warning SSE event if quality is low but does not block completion.

    Args:
        state: Current pipeline state with populated content_pack.

    Returns:
        Dict with updated "status" key.
    """
    pack = state.get("content_pack") or {}
    episode_id = state.get("episode_id", "")
    issues: list[str] = []

    # Count successful formats (no "error" key or content is not None)
    success_count = sum(
        1 for v in pack.values() if not (isinstance(v, dict) and v.get("error"))
    )
    if success_count < _MIN_SUCCESSFUL_FORMATS:
        issues.append(
            f"only {success_count}/{_TOTAL_FORMATS} formats generated successfully"
        )

    # Twitter thread length check
    twitter = pack.get("twitter", {})
    thread = twitter.get("main_thread") or []
    if isinstance(thread, list) and len(thread) < _MIN_TWITTER_TWEETS:
        issues.append(f"twitter thread has {len(thread)} tweets (min {_MIN_TWITTER_TWEETS})")

    # Blog post word count check
    blog = pack.get("blog_post", {})
    body = blog.get("body") or ""
    word_count = len(body.split()) if body else 0
    if word_count < _MIN_BLOG_WORDS:
        issues.append(f"blog post has {word_count} words (min {_MIN_BLOG_WORDS})")

    if issues:
        log.warning(
            "quality_check_failed",
            episode_id=episode_id,
            issues=issues,
        )
    else:
        log.info("quality_check_passed", episode_id=episode_id, formats=success_count)

    return {"status": "ready"}
