#!/usr/bin/env python3
"""
abstract_articles_condensed.py

Condensed one-row-per-study abstraction. Runs on PDFs directly (no
prerequisite full abstraction). Aggregates across all evaluation arms
in each paper into a single row with controlled-vocabulary lists.

Supports two backends:

1. Direct Anthropic API (default):
    export ANTHROPIC_API_KEY=sk-ant-...
    python abstract_articles_condensed.py --input-dir ./articles --output-dir ./results_condensed

2. Amazon Bedrock:
    export AWS_ACCESS_KEY_ID=...
    export AWS_SECRET_ACCESS_KEY=...
    export AWS_REGION=us-east-1
    python abstract_articles_condensed.py --input-dir ./articles --output-dir ./results_condensed --backend bedrock

Output:
    results_condensed/raw_json/<filename>.json   # one file per article (resumable)
    results_condensed/errors.log                  # failures with reason
    results_condensed/abstraction_condensed.xlsx  # one sheet "Studies", one row per paper

The guide and schema go in a cached system prompt. They are byte-identical
across every call, so after the first article they are read from cache and
only the PDF is charged at full input rate.

Every output JSON carries a `_provenance` block recording the model, the
vocabulary version, and hashes of the exact guide and schema used. Cached
results produced under different rules are detected and reported, and
re-extracted with --refresh-stale. This replaces the manual "remember to
delete raw_json/ after a schema change" step.
"""

import argparse
import base64
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import anthropic
from anthropic import Anthropic, AnthropicBedrock
import pandas as pd
from pydantic import ValidationError

from schema_condensed import StudyRollup
from extraction_guide_condensed import EXTRACTION_GUIDE_CONDENSED
from vocabularies import VOCABULARY_VERSION

MODEL_API = "claude-sonnet-4-6"
MODEL_BEDROCK_DEFAULT = "global.anthropic.claude-sonnet-4-6-v1"

# Raised from 2000. A multi-arm paper with populated abstraction_notes and
# several long list fields runs past 2000, and a truncated response was
# indistinguishable from malformed JSON — it burned all three retries and the
# paper went to errors.log without anyone knowing why.
MAX_TOKENS = 4000

# Deterministic by default. The previous default of 1.0 made the extraction
# non-reproducible, which is both a data-quality problem and something you
# cannot honestly describe in a Methods section.
DEFAULT_TEMPERATURE = 0.0

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def build_system_prompt(schema_json: str) -> str:
    """The stable, cacheable prefix: guide + schema + output instruction."""
    return f"""{EXTRACTION_GUIDE_CONDENSED}

== OUTPUT SCHEMA ==
Return JSON that validates against this JSON Schema. Match field names exactly.

{schema_json}

Read the attached PDF and produce the condensed one-row abstraction.
Output ONLY the JSON object — no preamble, no markdown fences, no trailing commentary."""


def provenance(model: str, system_prompt: str, temperature: float) -> Dict[str, Any]:
    return {
        "model": model,
        "temperature": temperature,
        "vocabulary_version": VOCABULARY_VERSION,
        "guide_sha": _sha(EXTRACTION_GUIDE_CONDENSED),
        "schema_sha": _sha(json.dumps(StudyRollup.model_json_schema(), sort_keys=True)),
        "system_prompt_sha": _sha(system_prompt),
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def is_stale(cached: Dict[str, Any], current: Dict[str, Any]) -> bool:
    """True if a cached result was produced under different rules."""
    prev = cached.get("_provenance")
    if not prev:
        return True  # pre-provenance output; rules unknown
    return any(prev.get(k) != current[k]
               for k in ("vocabulary_version", "guide_sha", "schema_sha", "model"))


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def extract_one(
    client: Union[Anthropic, AnthropicBedrock],
    model: str,
    pdf_path: Path,
    system_prompt: str,
    temperature: float,
) -> Dict[str, Any]:
    """Call Claude on a single PDF, return parsed+validated dict. Raises on failure."""
    pdf_bytes = pdf_path.read_bytes()
    b64_data = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    # Correction is fed into the next attempt. Retrying an identical prompt
    # after a validation failure only re-rolls the dice; telling the model
    # what was wrong lets it fix the specific field.
    correction: Optional[str] = None
    last_error = None
    last_parsed: Optional[Dict[str, Any]] = None  # last successful JSON parse, even if validation failed

    for attempt in range(1, MAX_RETRIES + 1):
        user_content: List[Dict[str, Any]] = [{
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf", "data": b64_data},
        }]
        if correction:
            user_content.append({
                "type": "text",
                "text": ("Your previous attempt was rejected. Fix ONLY what the error "
                         "describes and return the corrected JSON object.\n\n" + correction),
            })

        try:
            response = client.messages.create(
                model=model,
                max_tokens=MAX_TOKENS,
                temperature=temperature,
                system=[{
                    "type": "text",
                    "text": system_prompt,
                    # Byte-identical across all 500 calls.
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=[{"role": "user", "content": user_content}],
            )

            if response.stop_reason == "max_tokens":
                # Distinguish truncation from malformed output; previously this
                # surfaced only as an opaque JSONDecodeError.
                raise ValueError(
                    f"response truncated at max_tokens={MAX_TOKENS}; raise MAX_TOKENS"
                )

            raw_text = "".join(b.text for b in response.content if b.type == "text").strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.strip("`")
                if raw_text.lower().startswith("json"):
                    raw_text = raw_text[4:].strip()

            parsed = json.loads(raw_text)
            last_parsed = parsed  # save before validation so best-effort is available
            validated = StudyRollup.model_validate(parsed)

            u = response.usage
            logger.info("%s -- ok (in=%s cache_read=%s cache_write=%s out=%s)",
                        pdf_path.name,
                        getattr(u, "input_tokens", "?"),
                        getattr(u, "cache_read_input_tokens", 0),
                        getattr(u, "cache_creation_input_tokens", 0),
                        getattr(u, "output_tokens", "?"))
            return validated.model_dump()

        except ValidationError as e:
            last_error = f"Validation error on attempt {attempt}: {e}"
            correction = str(e)
            logger.warning("%s -- %s", pdf_path.name, last_error)
        except json.JSONDecodeError as e:
            last_error = f"JSON parse error on attempt {attempt}: {e}"
            correction = f"The response was not valid JSON: {e}. Return one JSON object only."
            logger.warning("%s -- %s", pdf_path.name, last_error)
        except ValueError as e:
            last_error = f"{e} (attempt {attempt})"
            correction = None
            logger.warning("%s -- %s", pdf_path.name, last_error)
        except anthropic.APIError as e:
            last_error = f"API error on attempt {attempt}: {e}"
            correction = None
            logger.warning("%s -- %s", pdf_path.name, last_error)

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS * attempt)

    if last_parsed is not None:
        # All retries exhausted but we have a structurally valid JSON response.
        # Save it as best-effort so the paper appears in the output for human
        # review rather than being silently dropped. The validation error is
        # recorded in abstraction_notes with an AUTO-FLAG prefix so it is
        # visually distinct from the model's own uncertainty notes.
        error_note = f"AUTO-FLAG: best-effort save — validation failed after {MAX_RETRIES} attempts: {last_error}"
        existing_notes = last_parsed.get("abstraction_notes") or ""
        last_parsed["abstraction_notes"] = (
            (existing_notes + "\n\n" + error_note).strip() if existing_notes else error_note
        )
        flags = list(last_parsed.get("abstraction_flags") or [])
        flags.append("BEST-EFFORT: validation failed")
        last_parsed["abstraction_flags"] = flags
        logger.warning("%s -- saving best-effort result despite validation failure", pdf_path.name)
        return last_parsed

    raise RuntimeError(last_error or "Unknown failure")


# ---------------------------------------------------------------------------
# Flatten
# ---------------------------------------------------------------------------

def flatten(study_id: str, r: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten the validated JSON into a spreadsheet row.

    List fields are joined with "; ". No vocabulary member contains a
    semicolon, so the join is lossless — do NOT change this delimiter to
    "/" or "," without re-checking, since several members contain both.
    """
    def join(v):
        if v is None:
            return None
        if isinstance(v, list):
            return "; ".join(v) if v else None
        return v

    prov = r.get("_provenance") or {}

    return {
        "study_id":                       study_id,
        "authors":                        r.get("authors"),
        "title":                          r.get("title"),
        "benchmark_names":                join(r.get("benchmark_names")),
        "type_of_study":                  r.get("type_of_study"),
        "mh_scope":                       r.get("mh_scope"),
        "publication_year":               r.get("publication_year"),
        "journal_source":                 r.get("journal_source"),
        "journal_source_type":            r.get("journal_source_type"),
        "system_tasks":                   join(r.get("system_tasks")),
        "mental_health_domains":          join(r.get("mental_health_domains")),
        "evaluation_constructs_described":  join(r.get("evaluation_constructs_described")),
        "evaluation_constructs_categories": join(r.get("evaluation_constructs_categories")),
        "primary_construct":              r.get("primary_construct"),
        "systems_tested":                 join(r.get("systems_tested")),
        "evaluated_output_types":         join(r.get("evaluated_output_types")),
        "input_formats":                  join(r.get("input_formats")),
        "input_provenance_types":         join(r.get("input_provenance_types")),
        "input_availabilities":           join(r.get("input_availabilities")),
        "input_determinism":              join(r.get("input_determinism")),
        "parent_benchmarks":              join(r.get("parent_benchmarks") or []),
        "populations":                    join(r.get("populations")),
        "output_audiences":               join(r.get("output_audiences")),
        "input_reality":                  join(r.get("input_reality")),
        "input_languages":                join(r.get("input_languages")),
        "conversation_types":             r.get("conversation_types"),
        "dataset_purpose":                r.get("dataset_purpose"),
        "reference_standard_type":        join(r["reference_standard_type"]),
        "reference_standard_description": join(r["reference_standard_description"]),
        "reference_standard_instruments": join(r["reference_standard_instruments"] or []),
        "scoring_procedures":             join(r["scoring_procedures"]),
        "abstraction_flags":              join(r.get("abstraction_flags") or []),
        "abstraction_notes":              r.get("abstraction_notes"),
        # Machine-detected inconsistencies carry an AUTO-FLAG: prefix, so they
        # separate cleanly from the model's own self-reported uncertainty.
        "auto_flagged":                   "AUTO-FLAG:" in (r.get("abstraction_notes") or ""),
        "vocabulary_version":             prov.get("vocabulary_version"),
        "guide_sha":                      prov.get("guide_sha"),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Condensed one-row-per-study abstraction of mental-health LLM benchmark articles.")
    parser.add_argument("--input-dir", required=True, type=Path, help="Folder of PDF articles.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Folder to write results to.")
    parser.add_argument("--limit", type=int, default=None, help="Optional cap on PDFs to process.")
    parser.add_argument("--backend", choices=["api", "bedrock"], default="api",
                        help="'api' uses Anthropic API (needs ANTHROPIC_API_KEY). 'bedrock' uses AWS Bedrock. Default: api.")
    parser.add_argument("--aws-region", default=os.environ.get("AWS_REGION", "us-east-1"),
                        help="AWS region for Bedrock. Ignored if --backend api.")
    parser.add_argument("--bedrock-model-id", default=MODEL_BEDROCK_DEFAULT,
                        help=f"Bedrock inference profile ID. Default: {MODEL_BEDROCK_DEFAULT}.")
    parser.add_argument("--refresh-stale", action="store_true",
                        help="Re-extract cached papers whose provenance does not match the current guide/schema/vocabulary. Without this they are reported but reused.")
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE,
                        help=f"Sampling temperature. Default {DEFAULT_TEMPERATURE} (deterministic). Use >0 only for reliability testing.")
    args = parser.parse_args()

    raw_json_dir = args.output_dir / "raw_json"
    raw_json_dir.mkdir(parents=True, exist_ok=True)
    error_log_path = args.output_dir / "errors.log"

    pdf_paths = sorted(args.input_dir.glob("*.pdf"))
    if args.limit:
        pdf_paths = pdf_paths[: args.limit]
    if not pdf_paths:
        logger.error("No PDFs found in %s", args.input_dir)
        sys.exit(1)

    if args.backend == "bedrock":
        client = AnthropicBedrock(aws_region=args.aws_region)
        model = args.bedrock_model_id
        logger.info("Using Bedrock backend, region=%s, model=%s", args.aws_region, model)
    else:
        client = Anthropic()
        model = MODEL_API
        logger.info("Using direct Anthropic API, model=%s", model)

    schema_json = json.dumps(StudyRollup.model_json_schema(), indent=2)
    system_prompt = build_system_prompt(schema_json)
    prov = provenance(model, system_prompt, args.temperature)
    logger.info("Vocabulary %s | guide %s | schema %s | temperature %s",
                prov["vocabulary_version"], prov["guide_sha"], prov["schema_sha"], args.temperature)

    rows: List[Dict[str, Any]] = []
    n_new = n_cached = n_failed = n_stale = 0

    with open(error_log_path, "a") as error_log:
        for pdf_path in pdf_paths:
            study_id = pdf_path.stem
            cached_path = raw_json_dir / f"{study_id}.json"

            result = None
            if cached_path.exists():
                cached = json.loads(cached_path.read_text())
                if is_stale(cached, prov):
                    n_stale += 1
                    if args.refresh_stale:
                        logger.info("Re-extracting %s (cached under different rules)", study_id)
                    else:
                        p = cached.get("_provenance") or {}
                        logger.warning(
                            "%s was extracted under DIFFERENT rules (vocab=%s guide=%s). "
                            "Reusing it. Run with --refresh-stale to re-extract.",
                            study_id, p.get("vocabulary_version", "unknown"),
                            p.get("guide_sha", "unknown"))
                        result, n_cached = cached, n_cached + 1
                else:
                    result, n_cached = cached, n_cached + 1

            if result is None:
                logger.info("Processing %s ...", study_id)
                try:
                    result = extract_one(client, model, pdf_path, system_prompt, args.temperature)
                    result["_provenance"] = prov
                    cached_path.write_text(json.dumps(result, indent=2))
                    n_new += 1
                except Exception as e:
                    n_failed += 1
                    msg = f"{study_id}: FAILED -- {e}"
                    logger.error(msg)
                    error_log.write(msg + "\n")
                    continue

            rows.append(flatten(study_id, result))

    df = pd.DataFrame(rows)
    excel_path = args.output_dir / "abstraction_condensed.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Studies", index=False)

    n_auto = int(df["auto_flagged"].sum()) if len(df) and "auto_flagged" in df else 0
    logger.info("Done. %d newly extracted, %d from cache, %d failed.", n_new, n_cached, n_failed)
    if n_stale and not args.refresh_stale:
        logger.warning("%d cached paper(s) were extracted under different rules and are NOT "
                       "comparable to the rest. Re-run with --refresh-stale.", n_stale)
    if n_auto:
        logger.info("%d row(s) carry an automatic consistency flag — filter on auto_flagged "
                    "in the spreadsheet and review those first.", n_auto)
    logger.info("Results: %s", excel_path)
    if n_failed:
        logger.info("See %s for failure details.", error_log_path)


if __name__ == "__main__":
    main()
