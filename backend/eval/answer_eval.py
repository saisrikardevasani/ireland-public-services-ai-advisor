"""Answer evaluation — measures faithfulness and key-fact coverage.

Two metrics:

1. KEY-FACT COVERAGE (deterministic, free):
   For each gold Q&A pair, check that every key_fact string appears
   somewhere in the generated answer. Fast substring match — no LLM.

2. FAITHFULNESS (LLM-as-judge):
   Ask the LLM: "Given only these context passages, does this answer
   contain any claims not supported by the context?"
   Score: 0.0 (hallucinated) → 1.0 (fully grounded).

   This is the same concept as RAGAS faithfulness, implemented directly
   so you can see exactly how it works. RAGAS is a wrapper around this
   same idea.

Usage:
    python eval/answer_eval.py                  # all 30 questions
    python eval/answer_eval.py --sample 5       # quick 5-question smoke test
    python eval/answer_eval.py --fail-below 0.70
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database import AsyncSessionLocal
from app.pipeline.generator import generate
from app.pipeline.retrieval import retrieve

logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")

GOLD_PATH = Path(__file__).parent / "gold_qa.json"
DEFAULT_FAIL_BELOW = 0.70

FAITHFULNESS_PROMPT = """You are an evaluation assistant. Your job is to check whether an AI answer is faithful to the provided context.

CONTEXT PASSAGES:
{context}

QUESTION:
{question}

ANSWER:
{answer}

TASK:
Rate the faithfulness of the answer on a scale from 0.0 to 1.0:
- 1.0 = every claim in the answer is directly supported by the context passages
- 0.5 = most claims are supported, but there is at least one claim not in the context
- 0.0 = the answer contains significant claims not supported by the context

Respond with ONLY a JSON object in this format:
{{"score": 0.9, "reason": "one sentence explaining your rating"}}"""


async def _collect_stream(gen) -> str:
    tokens = []
    async for token in gen:
        tokens.append(token)
    return "".join(tokens)


async def _judge_faithfulness(question: str, context: str, answer: str) -> dict:
    import asyncio
    from openai import AsyncOpenAI, RateLimitError

    client = AsyncOpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=settings.nvidia_api_key,
    )
    prompt = FAITHFULNESS_PROMPT.format(
        context=context, question=question, answer=answer
    )

    for attempt in range(4):
        try:
            response = await client.chat.completions.create(
                model=settings.nvidia_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.0,
                stream=False,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw)
        except RateLimitError:
            wait = 10 * (2 ** attempt)
            print(f"    Rate limit hit — waiting {wait}s before retry {attempt + 1}/3...")
            await asyncio.sleep(wait)
        except json.JSONDecodeError:
            return {"score": 0.5, "reason": f"Could not parse judge response: {raw[:100]}"}

    return {"score": 0.5, "reason": "Rate limit retries exhausted"}


def _key_fact_coverage(answer: str, key_facts: list[str]) -> float:
    answer_lower = answer.lower()
    hits = sum(1 for fact in key_facts if fact.lower() in answer_lower)
    return hits / len(key_facts) if key_facts else 1.0


async def evaluate(sample: int | None = None) -> dict:
    gold = json.loads(GOLD_PATH.read_text())
    if sample:
        gold = gold[:sample]

    import asyncio

    results = []
    async with AsyncSessionLocal() as session:
        for i, item in enumerate(gold, 1):
            print(f"  [{i}/{len(gold)}] {item['id']}: {item['question'][:60]}...")

            chunks = await retrieve(session, item["question"])
            context_text = "\n\n---\n\n".join(
                f"[{j+1}] {c.title}\n{c.content}" for j, c in enumerate(chunks)
            )

            answer = await _collect_stream(generate(item["question"], chunks))

            coverage = _key_fact_coverage(answer, item["key_facts"])
            faithfulness = await _judge_faithfulness(item["question"], context_text, answer)

            # Pace requests to stay under NVIDIA free-tier rate limits
            await asyncio.sleep(3)

            results.append(
                {
                    "id": item["id"],
                    "question": item["question"],
                    "answer_preview": answer[:200],
                    "key_fact_coverage": coverage,
                    "key_facts": item["key_facts"],
                    "faithfulness_score": faithfulness.get("score", 0.5),
                    "faithfulness_reason": faithfulness.get("reason", ""),
                }
            )

    avg_faithfulness = sum(r["faithfulness_score"] for r in results) / len(results)
    avg_coverage = sum(r["key_fact_coverage"] for r in results) / len(results)

    return {
        "avg_faithfulness": avg_faithfulness,
        "avg_key_fact_coverage": avg_coverage,
        "total": len(results),
        "results": results,
    }


def print_report(report: dict) -> None:
    print(f"\n{'='*60}")
    print("  ANSWER EVAL")
    print(f"{'='*60}")
    print(f"  Faithfulness (LLM-as-judge):  {report['avg_faithfulness']:.2f} / 1.0")
    print(f"  Key-fact coverage:            {report['avg_key_fact_coverage']:.1%}")
    print(f"  Questions evaluated:          {report['total']}")
    print(f"{'='*60}\n")

    low = [r for r in report["results"] if r["faithfulness_score"] < 0.7]
    if low:
        print(f"  LOW FAITHFULNESS ({len(low)} questions):")
        for r in low:
            print(f"  [{r['id']}] score={r['faithfulness_score']:.2f} — {r['faithfulness_reason']}")
            print(f"         Q: {r['question'][:70]}")
            print()

    miss_coverage = [r for r in report["results"] if r["key_fact_coverage"] < 1.0]
    if miss_coverage:
        print(f"  INCOMPLETE KEY-FACT COVERAGE ({len(miss_coverage)} questions):")
        for r in miss_coverage:
            print(
                f"  [{r['id']}] coverage={r['key_fact_coverage']:.0%} "
                f"facts={r['key_facts']}"
            )
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Answer faithfulness eval")
    parser.add_argument("--sample", type=int, default=None, help="Evaluate only first N questions")
    parser.add_argument("--fail-below", type=float, default=DEFAULT_FAIL_BELOW)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    print("\nRunning answer eval (calls LLM for each question)...")
    report = asyncio.run(evaluate(args.sample))

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)

    if report["avg_faithfulness"] < args.fail_below:
        print(
            f"  FAIL: Faithfulness {report['avg_faithfulness']:.2f} "
            f"< threshold {args.fail_below:.2f}"
        )
        sys.exit(1)
    else:
        print(
            f"  PASS: Faithfulness {report['avg_faithfulness']:.2f} "
            f">= threshold {args.fail_below:.2f}"
        )


if __name__ == "__main__":
    main()
