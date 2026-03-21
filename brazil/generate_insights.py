"""
Generate editorial "insight pills" from Brazil AI-jobs data.

Pipeline:
  1. Load data.json + summary.json
  2. Run pure-Python analysis functions per template
  3. Call LLM for editorial prose (Portuguese)
  4. Write insights.json

Uses the same OpenRouter pattern as score_br.py.
Model: google/gemini-2.5-flash (cheap, good Portuguese).

Usage:
    OPENROUTER_API_KEY=... python brazil/generate_insights.py
"""

import hashlib
import json
import os
import sys
from datetime import date

import httpx

from insight_templates import get_templates

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"

DATA_PATH = "brazil/site/data.json"
SUMMARY_PATH = "brazil/site/summary.json"
OUTPUT_PATH = "brazil/site/insights.json"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def data_hash(findings):
    """Hash the findings dict to detect data changes for caching."""
    raw = json.dumps(findings, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode()).hexdigest()


def load_existing_insights():
    """Load existing insights.json for cache comparison."""
    if not os.path.exists(OUTPUT_PATH):
        return {}
    try:
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            existing = json.load(f)
        return {item["id"]: item for item in existing}
    except (json.JSONDecodeError, KeyError):
        return {}


def call_llm(findings, prompt_template):
    """Call OpenRouter LLM to generate editorial prose from pre-computed findings."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("  ⚠ No OPENROUTER_API_KEY — using placeholder text")
        return {
            "title": f"Insight: {findings.get('headline_stat', '?')}",
            "subtitle": findings.get("headline_label", ""),
            "body": "<p>Artigo será gerado quando a chave de API estiver configurada.</p>",
        }

    # Format prompt with findings details (default missing keys to "N/D")
    class DefaultDict(dict):
        def __missing__(self, key):
            return "N/D"
    prompt = prompt_template.format_map(DefaultDict(findings.get("details", {})))

    client = httpx.Client()
    response = client.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Você é um jornalista de dados brasileiro premiado. "
                        "Escreva em português claro e direto. "
                        "Não invente dados. Use APENAS os números fornecidos. "
                        "Retorne APENAS JSON válido, sem markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        },
        timeout=60,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]

    # Strip markdown code fences if present
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    return json.loads(content)


def main():
    print("Loading data...")
    data = load_json(DATA_PATH)
    summary = load_json(SUMMARY_PATH)

    templates = get_templates()
    existing = load_existing_insights()
    insights = []

    for tmpl in templates:
        print(f"\n── {tmpl['id']} ──")

        # Step 1: Pure Python analysis
        findings = tmpl["analysis_fn"](data, summary)
        current_hash = data_hash(findings)
        print(f"  headline: {findings['headline_stat']} — {findings['headline_label']}")

        # Step 2: Check cache (skip placeholders even if hash matches)
        cached = existing.get(tmpl["id"])
        is_placeholder = cached and "chave de API" in (cached.get("body_html") or "")
        if cached and cached.get("data_hash") == current_hash and not is_placeholder:
            print("  ✓ cached (data unchanged)")
            insights.append(cached)
            continue
        if is_placeholder:
            print("  ↻ regenerating (was placeholder)")

        # Step 3: LLM call for editorial prose
        print("  → calling LLM...")
        try:
            prose = call_llm(findings, tmpl["prompt_template"])
        except Exception as e:
            print(f"  ✗ LLM error: {e}")
            # Keep existing placeholder or create one
            if cached:
                insights.append(cached)
            continue
        print(f"  title: {prose.get('title', '?')}")

        insights.append({
            "id": tmpl["id"],
            "category": tmpl["category"],
            "title": prose["title"],
            "subtitle": prose.get("subtitle", ""),
            "body_html": prose.get("body", ""),
            "headline_stat": findings["headline_stat"],
            "headline_label": findings["headline_label"],
            "chart": {"type": tmpl["chart_type"], "data": findings["chart_data"]},
            "generated_at": date.today().isoformat(),
            "tags": tmpl["tags"],
            "data_hash": current_hash,
        })

    # Write output
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(insights, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Wrote {len(insights)} insights to {OUTPUT_PATH}")


if __name__ == "__main__":
    # Allow running from repo root
    if os.path.exists("brazil") and not os.path.exists("insight_templates.py"):
        sys.path.insert(0, "brazil")
    main()
