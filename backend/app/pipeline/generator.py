"""Answer generator — supports NVIDIA (free) and Anthropic providers.

Provider is selected via LLM_PROVIDER in .env:
  "nvidia"    → meta/llama-3.3-70b-instruct via integrate.api.nvidia.com (free tier)
  "anthropic" → claude-sonnet-4-6 via api.anthropic.com

Both stream tokens identically so the chat API doesn't care which is active.

The citation-enforcing system prompt is the most important piece of prompt
engineering in this system. It instructs the model to:
  - Only use the provided context passages
  - Cite every claim with [n]
  - Never give legal advice
"""

import logging
from collections.abc import AsyncIterator

from app.config import settings
from app.pipeline.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert guide to Irish public services and EU regulations applicable in Ireland.

Your job is to help people understand their rights, entitlements, and obligations by explaining official rules in plain English.

RULES YOU MUST FOLLOW:
1. Answer using ONLY the context passages provided. Every factual claim must be cited with [n] where n is the passage number.
2. If the context does not contain enough information to answer the question fully, say so explicitly. Never invent, guess, or extrapolate.
3. Clearly distinguish between:
   - Legal requirements ("You must...", "The law requires...")
   - Administrative procedures ("To apply, you need to...")
   - User options ("You may choose to...")
4. Do NOT give legal advice. You are an informational guide, not a solicitor. If the question requires professional legal or tax advice, say so.
5. Write in plain English. Aim for clarity — imagine explaining to a friend, not writing a legal document.
6. End every response with: "⚠️ This is informational guidance, not legal or professional advice."

FORMAT:
- Use short paragraphs
- Use bullet points for lists of requirements or steps
- Use [1], [2], [3] inline citations immediately after each factual claim"""


def _build_context_block(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        # Use the wider parent window if available (v0.3 hierarchical chunking)
        context = chunk.parent_content or chunk.content
        parts.append(f"[{i}] SOURCE: {chunk.title}\nURL: {chunk.url}\n\n{context}")
    return "\n\n---\n\n".join(parts)


async def _generate_nvidia(question: str, chunks: list[RetrievedChunk]) -> AsyncIterator[str]:
    """Stream via NVIDIA's OpenAI-compatible API (free tier)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=settings.nvidia_api_key,
    )

    context_block = _build_context_block(chunks)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Context passages:\n\n{context_block}\n\n---\n\n"
                f"Question: {question}\n\n"
                f"Please answer based solely on the context passages above, citing each claim with [n]."
            ),
        },
    ]

    stream = await client.chat.completions.create(
        model=settings.nvidia_model,
        messages=messages,  # type: ignore[arg-type]
        max_tokens=1500,
        temperature=0.1,  # low temperature = more factual, less creative
        stream=True,
    )

    async for chunk in stream:
        if not chunk.choices:
            continue
        content = chunk.choices[0].delta.content
        if content:
            yield content


async def _generate_anthropic(question: str, chunks: list[RetrievedChunk]) -> AsyncIterator[str]:
    """Stream via Anthropic Claude (fallback)."""
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    context_block = _build_context_block(chunks)

    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Context passages:\n\n{context_block}\n\n---\n\n"
                    f"Question: {question}\n\nCite each claim with [n]."
                ),
            }
        ],
    ) as stream:
        async for token in stream.text_stream:
            yield token


async def generate(question: str, chunks: list[RetrievedChunk]) -> AsyncIterator[str]:
    """Route to the configured LLM provider and stream the answer."""
    if not chunks:
        yield (
            "I wasn't able to find relevant information in my knowledge base for that question. "
            "Please try rephrasing, or visit citizensinformation.ie directly."
        )
        return

    logger.info(
        "Generating via %s for: %s...", settings.llm_provider, question[:60]
    )

    if settings.llm_provider == "nvidia":
        if not settings.nvidia_api_key:
            yield "Error: NVIDIA_API_KEY is not set in .env. Add it and restart the backend."
            return
        async for token in _generate_nvidia(question, chunks):
            yield token
    else:
        if not settings.anthropic_api_key:
            yield "Error: ANTHROPIC_API_KEY is not set in .env. Add it and restart the backend."
            return
        async for token in _generate_anthropic(question, chunks):
            yield token
