"""
Vector service — pgvector embedding storage and semantic retrieval.

Uses IBM Granite embeddings (slate-125m-english-rtrvr) via watsonx.ai.
Falls back to zero-vector if watsonx credentials are not configured
(allows local development without IBM credentials).
"""

import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from core.config import settings

logger = structlog.get_logger()

EMBEDDING_DIM = 1536


def _get_embedder():
    """
    Lazily initialise the IBM Granite embedding client.
    Returns None if credentials are not set (dev/test mode).
    """
    if not settings.WATSONX_API_KEY or not settings.WATSONX_PROJECT_ID:
        logger.warning("watsonx credentials not configured — using zero embeddings")
        return None

    try:
        from ibm_watsonx_ai.foundation_models import Embeddings
        from ibm_watsonx_ai.metanames import EmbedTextParamsMetaNames
        from ibm_watsonx_ai import Credentials

        return Embeddings(
            model_id=settings.WATSONX_EMBEDDING_MODEL_ID,
            credentials=Credentials(
                api_key=settings.WATSONX_API_KEY,
                url=settings.WATSONX_URL,
            ),
            project_id=settings.WATSONX_PROJECT_ID,
            params={EmbedTextParamsMetaNames.TRUNCATE_INPUT_TOKENS: 512},
        )
    except Exception as exc:
        logger.error("Failed to initialise Granite embedder", error=str(exc))
        return None


def embed_text(text: str) -> list[float]:
    """
    Generate an embedding vector for the given text using IBM Granite.
    Returns a zero vector of EMBEDDING_DIM if the embedder is unavailable.
    """
    embedder = _get_embedder()
    if embedder is None:
        return [0.0] * EMBEDDING_DIM

    try:
        result = embedder.embed_documents(texts=[text])
        return result[0]
    except Exception as exc:
        logger.error("Embedding failed", error=str(exc))
        return [0.0] * EMBEDDING_DIM


async def upsert_profile_embedding(
    profile_id: uuid.UUID,
    summary_text: str,
    db: AsyncSession,
) -> None:
    """Generate and store the profile embedding in pgvector."""
    vector = embed_text(summary_text)
    vector_str = "[" + ",".join(str(v) for v in vector) + "]"
    await db.execute(
        text(
            "UPDATE profiles SET embedding = :vec WHERE id = :pid"
        ),
        {"vec": vector_str, "pid": str(profile_id)},
    )
    logger.info("Profile embedding stored", profile_id=str(profile_id))


async def find_similar_profiles(
    query_text: str,
    user_id: uuid.UUID,
    db: AsyncSession,
    top_k: int = 5,
) -> list[dict]:
    """
    Retrieve the user's own past profile versions most semantically similar
    to the query text (used for Decision Twin memory retrieval).
    """
    vector = embed_text(query_text)
    vector_str = "[" + ",".join(str(v) for v in vector) + "]"
    result = await db.execute(
        text(
            """
            SELECT id, version, summary_text,
                   1 - (embedding <=> :vec) AS similarity
            FROM profiles
            WHERE user_id = :uid AND embedding IS NOT NULL
            ORDER BY embedding <=> :vec
            LIMIT :k
            """
        ),
        {"vec": vector_str, "uid": str(user_id), "k": top_k},
    )
    return [
        {
            "profile_id": str(row.id),
            "version": row.version,
            "summary": row.summary_text,
            "similarity": round(float(row.similarity), 4),
        }
        for row in result.fetchall()
    ]
