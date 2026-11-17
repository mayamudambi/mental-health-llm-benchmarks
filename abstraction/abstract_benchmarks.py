"""Benchmark-level abstraction: one row per (study, benchmark).

Reuses the condensed guide, vocabulary and validators. For every study in
manifest.json it asks Claude for one arm per named benchmark; every study NOT in
the manifest has its study-level row copied (benchmark = its single name or
'[unnamed]'). Paper-level fields always come from the reviewed study sheet.

Usage:
  python abstract_benchmarks.py --sheet abstraction_condensed_cleaned.xlsx \
      --manifest manifest.json --pdf-dir pdfs/ --output-dir results_benchmark/ \
      [--with-quality-ratings] [--backend api|bedrock] [--limit N] [--refresh-stale]

Output:
  results_benchmark/raw_json/<stem>.json      one file per extracted study
  results_benchmark/benchmark_long.xlsx       every study expanded to benchmark rows
"""
import argparse, base64, hashlib, json, logging, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import anthropic
from anthropic import Anthropic, AnthropicBedrock
import pandas as pd
from pydantic import ValidationError

from extraction_guide_condensed import EXTRACTION_GUIDE_CONDENSED
from vocabularies import VOCABULARY_VERSION
from schema_condensed import StudyRollup
from schema_benchmark import (BenchmarkRollup, BenchmarkRollupWithQuality, BENCHMARK_FIELDS_GUIDE,
                              BENCHMARK_QUALITY_GUIDE, PAPER_LEVEL_FIELDS, STUDY_COMPARISON_FIELDS,
                              SUBSET_CHECK_FIELDS, UNNAMED)
from abstract_articles_condensed import (flatten as flatten_study, MODEL_API, MODEL_BEDROCK_DEFAULT,
                                         MAX_RETRIES, RETRY_DELAY_SECONDS, DEFAULT_TEMPERATURE)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("bench")

# The condensed runner's MAX_TOKENS (4000) is sized for ONE StudyRollup. Each arm is a full
# StudyRollup plus ~17 fields (~2-3k tokens), so size per benchmark with a generous floor.
TOKENS_PER_ARM = 3500
MIN_MAX_TOKENS = 16000
MAX_MAX_TOKENS = 64000


def _sha(t: str) -> str: return hashlib.sha256(t.encode()).hexdigest()[:16]


BENCHMARK_SUPPLEMENT = """
== BENCHMARK-LEVEL MODE ==
The unit of extraction is the BENCHMARK. Instead of one study-level row, return one ARM per
benchmark in the BENCHMARK LIST supplied in the user message, in the same order, under the key
"arms". Wherever the guide above says "arm" or "the paper", read it for this benchmark only.

Rules for each arm:
1. "benchmark" is copied EXACTLY from the list. Do not rename, merge or split entries.
   benchmark_names on the arm is the single-item list [benchmark] (null if benchmark is '[unnamed]').
2. PAPER-LEVEL FIELDS are given to you in the user message (authors, title, type_of_study,
   publication_year, journal_source, journal_source_type). Copy them verbatim onto every arm; they
   are not re-derived and will be overwritten from the reviewed sheet regardless.
3. EVERY OTHER FIELD describes THIS BENCHMARK only: its tasks, constructs, domains, inputs,
   population, languages, reference standard and scoring. This includes mh_scope, systems_tested and
   dataset_purpose, which vary by benchmark (a training-only corpus is 'Training or tuning only'; the
   held-out benchmark is 'Evaluation only'; a benchmark scoring the judge is 'LLM as judge/evaluator').
   Multi-select fields (domains, languages, formats, tasks, constructs...) list ONLY the values
   that apply to this benchmark's items and scoring — never the union across the paper. A
   benchmark's values are a subset of the paper's, never wider.
4. "scored" and "scored_notes" follow the BENCHMARK-LEVEL FIELDS section. The MH-scope gate is
   applied per benchmark: a benchmark with no MH-disaggregated generative-LLM result is scored=false.
5. parent_benchmarks follows the PARENT BENCHMARKS section for this artifact alone. A benchmark is
   never its own parent.
6. If the paper introduces its own artifact AND evaluates on existing ones, the paper's own artifact
   is one arm and each existing benchmark is another. type_of_study is paper-level (rule 2).
7. The benchmark-level fields (models_tested ... scoring_reproducibility_notes, and the quality
   ratings if present) are governed by the BENCHMARK-LEVEL FIELDS section below. 'Not reported' is
   the correct answer when the paper is silent — do not infer from study quality.
8. abstraction_flags / abstraction_notes keep their study-level meaning (genuine interpretive
   uncertainty, both or neither). 'not scored' never goes there — it goes in scored_notes.
"""


def build_system_prompt(schema_json: str, with_quality: bool) -> str:
    quality = BENCHMARK_QUALITY_GUIDE if with_quality else ""
    return f"""{EXTRACTION_GUIDE_CONDENSED}
{BENCHMARK_SUPPLEMENT}
{BENCHMARK_FIELDS_GUIDE}
{quality}
== OUTPUT SCHEMA ==
Return JSON that validates against this JSON Schema. Match field names exactly.

{schema_json}

Read the attached PDF and produce the benchmark-level abstraction (one arm per listed benchmark).
Output ONLY the JSON object — no preamble, no markdown fences, no trailing commentary."""


def provenance(model, system_prompt, temperature, schema_cls, with_quality):
    return {"model": model, "temperature": temperature, "vocabulary_version": VOCABULARY_VERSION,
            "guide_sha": _sha(EXTRACTION_GUIDE_CONDENSED),
            "schema_sha": _sha(json.dumps(schema_cls.model_json_schema(), sort_keys=True)),
            "system_prompt_sha": _sha(system_prompt), "mode": "benchmark-level",
            "with_quality_ratings": with_quality,
            "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


STALE_KEYS = ("vocabulary_version", "guide_sha", "schema_sha", "system_prompt_sha", "model", "mode", "with_quality_ratings")


def stale_reasons(cached, current) -> List[str]:
    prev = cached.get("_provenance")
    if not prev: return ["no provenance"]
    return [k for k in STALE_KEYS if prev.get(k) != current[k]]


def paper_level_block(study_row: Dict[str, Any]) -> str:
    lines = ["PAPER-LEVEL FIELDS (copy verbatim onto every arm):"]
    for k in PAPER_LEVEL_FIELDS:
        v = study_row.get(k)
        if isinstance(v, float) and pd.isna(v): v = None
        lines.append(f"  {k}: {json.dumps(v, ensure_ascii=False)}")
    return "\n".join(lines)


def extract_one(client, model, pdf_path: Path, benchmarks: List[str], study_row: Dict[str, Any],
                system_prompt: str, temperature: float, schema_cls):
    b64 = base64.standard_b64encode(pdf_path.read_bytes()).decode()
    listing = ("BENCHMARK LIST (one arm each, this order):\n"
               + "\n".join(f"{i+1}. {b}" for i, b in enumerate(benchmarks))
               + "\n\n" + paper_level_block(study_row))
    max_tokens = min(MAX_MAX_TOKENS, max(MIN_MAX_TOKENS, TOKENS_PER_ARM * len(benchmarks)))
    correction = None; last_error = None; last_parsed = None
    for attempt in range(1, MAX_RETRIES + 1):
        content: List[Dict[str, Any]] = [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64}},
            {"type": "text", "text": listing},
        ]
        if correction:
            content.append({"type": "text", "text": "Your previous attempt was rejected. Fix ONLY what the error describes and return the corrected JSON object.\n\n" + correction})
        try:
            resp = client.messages.create(model=model, max_tokens=max_tokens, temperature=temperature,
                                          system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
                                          messages=[{"role": "user", "content": content}])
            if resp.stop_reason == "max_tokens":
                # Retrying the same call cannot help; bump once, then give up.
                if max_tokens < MAX_MAX_TOKENS:
                    max_tokens = min(MAX_MAX_TOKENS, max_tokens * 2)
                    logger.warning("%s -- truncated at max_tokens; retrying with %d", pdf_path.name, max_tokens)
                    continue
                raise RuntimeError(f"response truncated at max_tokens={max_tokens} (MAX_MAX_TOKENS reached)")
            raw = "".join(b.text for b in resp.content if b.type == "text").strip()
            if raw.startswith("```"):
                raw = raw.strip("`"); raw = raw[4:].strip() if raw.lower().startswith("json") else raw
            parsed = json.loads(raw); last_parsed = parsed
            validated = schema_cls.model_validate(parsed)
            got = [a.benchmark for a in validated.arms]
            if got != benchmarks:
                raise ValidationError.from_exception_data("BenchmarkRollup", [{"type": "value_error", "loc": ("arms",),
                    "input": got, "ctx": {"error": f"arms must be exactly {benchmarks} in order; got {got}"}}])
            u = resp.usage
            logger.info("%s -- ok %d arms (in=%s cache_read=%s out=%s)", pdf_path.name, len(got),
                        getattr(u, "input_tokens", "?"), getattr(u, "cache_read_input_tokens", 0), getattr(u, "output_tokens", "?"))
            return validated.model_dump()
        except ValidationError as e:
            last_error = f"Validation error on attempt {attempt}: {e}"; correction = str(e)
        except json.JSONDecodeError as e:
            last_error = f"JSON parse error on attempt {attempt}: {e}"; correction = f"The response was not valid JSON: {e}. Return one JSON object only."
        except anthropic.APIError as e:
            last_error = f"{e} (attempt {attempt})"; correction = None
        logger.warning("%s -- %s", pdf_path.name, last_error)
        if attempt < MAX_RETRIES: time.sleep(RETRY_DELAY_SECONDS * attempt)
    if last_parsed is not None and isinstance(last_parsed.get("arms"), list):
        for arm in last_parsed["arms"]:
            if not isinstance(arm, dict): continue
            arm["abstraction_notes"] = ((arm.get("abstraction_notes") or "") + f"\n\nAUTO-FLAG: best-effort save — validation failed after {MAX_RETRIES} attempts: {last_error}").strip()
            arm["abstraction_flags"] = list(arm.get("abstraction_flags") or []) + ["BEST-EFFORT: validation failed"]
            arm["scored"] = None  # keep best-effort rows out of Benchmark_counts
        last_parsed["_best_effort"] = True
        logger.warning("%s -- saving best-effort result", pdf_path.name)
        return last_parsed
    raise RuntimeError(last_error or "Unknown failure")


EXTRA = ["scored", "scored_notes", "models_tested", "input_modality", "n_test_cases", "n_test_cases_notes",
         "access_method", "input_source_grounding", "input_lived_experience_role", "prompt_variation_testing",
         "reference_standard_judgement", "evaluation_engine", "rubric_source_grounding",
         "scoring_lived_experience_role", "judge_validation_reliability", "scoring_procedure_judgement",
         "scoring_reproducibility", "scoring_reproducibility_notes",
         "input_quality_source", "input_quality_validation", "input_quality_informants", "input_quality_lived_experience",
         "input_quality_overall", "input_quality_justification", "reference_standard_quality",
         "reference_standard_quality_justification", "scoring_quality_metric_fit", "scoring_quality_validation",
         "scoring_quality_transparency", "scoring_quality_variability", "scoring_quality_overall", "scoring_quality_justification"]

REVIEW_COLS = ["wider_than_study", "changed_vs_study"]


def _split(v) -> set:
    if v is None or (isinstance(v, float) and pd.isna(v)): return set()
    if isinstance(v, list): return {str(x).strip() for x in v}
    return {t.strip() for t in str(v).split(";") if t.strip()}


def flatten_arm(study_id: str, arm: Dict[str, Any], prov: Dict[str, Any], study_row: Dict[str, Any]) -> Dict[str, Any]:
    arm = dict(arm); arm["_provenance"] = prov
    for k in StudyRollup.model_fields:  # best-effort dicts may lack keys flatten() indexes directly
        arm.setdefault(k, None)
    row = flatten_study(study_id, arm)
    for k in PAPER_LEVEL_FIELDS:
        row[k] = study_row.get(k)
    for k in STUDY_COMPARISON_FIELDS:
        row[f"{k}_study"] = study_row.get(k)
    row["benchmark"] = arm.get("benchmark", "[UNKNOWN]")
    row["row_source"] = "benchmark-level extraction" + (" (best-effort)" if "BEST-EFFORT: validation failed" in (arm.get("abstraction_flags") or []) else "")
    for k in EXTRA: row[k] = arm.get(k)
    row["models_tested"] = "; ".join(
        f"{m.get('name')} ({m['role']})" if m.get("role") else str(m.get("name"))
        for m in (arm.get("models_tested") or []) if isinstance(m, dict)) or None
    row["input_modality"] = "; ".join(arm.get("input_modality") or []) or None

    # README sanity check 1, in code: an arm may be narrower than the study row, never wider.
    wider, changed = [], []
    for k in SUBSET_CHECK_FIELDS:
        a, s = _split(arm.get(k)), _split(study_row.get(k))
        if not s: continue
        extra = a - s
        if extra: wider.append(f"{k}={sorted(extra)}")
    for k in ("mh_scope", "dataset_purpose", "primary_construct", "conversation_types"):
        a, s = arm.get(k), study_row.get(k)
        if a is not None and s is not None and not (isinstance(s, float) and pd.isna(s)) and str(a) != str(s):
            changed.append(f"{k}: {s!r} -> {a!r}")
    row["wider_than_study"] = "; ".join(wider) or None
    row["changed_vs_study"] = "; ".join(changed) or None
    return row


def copied_row(sid: str, r: Dict[str, Any], benchmark: str, source: str) -> Dict[str, Any]:
    row = dict(r); row["benchmark"] = benchmark; row["row_source"] = source
    for k in STUDY_COMPARISON_FIELDS: row[f"{k}_study"] = r.get(k)
    for k in EXTRA + REVIEW_COLS: row.setdefault(k, None)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--pdf-dir", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--with-quality-ratings", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="extract at most N studies this run; the rest are copied, not dropped")
    ap.add_argument("--backend", choices=["api", "bedrock"], default="api")
    ap.add_argument("--aws-region", default=os.environ.get("AWS_REGION", "us-east-1"))
    ap.add_argument("--bedrock-model-id", default=MODEL_BEDROCK_DEFAULT)
    ap.add_argument("--refresh-stale", action="store_true", help="re-extract cached results whose provenance differs")
    ap.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    a = ap.parse_args()

    schema_cls = BenchmarkRollupWithQuality if a.with_quality_ratings else BenchmarkRollup
    sysp = build_system_prompt(json.dumps(schema_cls.model_json_schema(), indent=2), a.with_quality_ratings)
    if a.backend == "bedrock":
        client = AnthropicBedrock(aws_region=a.aws_region); model = a.bedrock_model_id
    else:
        client = Anthropic(); model = MODEL_API
    prov = provenance(model, sysp, a.temperature, schema_cls, a.with_quality_ratings)

    df = pd.read_excel(a.sheet, sheet_name="Studies")
    studies = {r["study_id"]: r for r in df.to_dict("records")}
    manifest = json.loads(a.manifest.read_text(encoding="utf-8"))
    unknown = set(manifest) - set(studies)
    if unknown: logger.error("manifest lists %d study_ids not in the sheet: %s", len(unknown), sorted(unknown)[:5])
    raw_dir = a.output_dir / "raw_json"; raw_dir.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    done = 0; n_copied = 0; n_fallback = 0
    for sid, r in studies.items():
        m = manifest.get(sid)
        if not m:
            names = _split(r.get("benchmark_names"))
            bench = next(iter(names)) if len(names) == 1 else (UNNAMED if not names else "; ".join(sorted(names)))
            rows.append(copied_row(sid, r, bench, "study-level row (single benchmark)")); n_copied += 1
            continue

        fallback_reason = None
        if not m.get("pdf"):
            fallback_reason = "no PDF"
        elif a.limit and done >= a.limit and not (raw_dir / (Path(m["pdf"]).stem + ".json")).exists():
            fallback_reason = "--limit reached"

        result = None
        if fallback_reason is None:
            pdf = a.pdf_dir / m["pdf"]; out = raw_dir / (pdf.stem + ".json")
            if out.exists():
                cached = json.loads(out.read_text(encoding="utf-8")); reasons = stale_reasons(cached, prov)
                if reasons and a.refresh_stale:
                    logger.info("%s -- stale (%s), re-extracting", sid, ",".join(reasons))
                elif reasons:
                    logger.warning("%s -- using STALE cache (%s); pass --refresh-stale to redo", sid, ",".join(reasons))
                    result = cached
                else:
                    result = cached
            if result is None:
                try:
                    result = extract_one(client, model, pdf, m["benchmarks"], r, sysp, a.temperature, schema_cls)
                    result["_provenance"] = prov
                    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"); done += 1
                except Exception as e:
                    logger.error("%s -- FAILED: %s", sid, e); fallback_reason = f"extraction failed: {e}"

        if result is None:
            # Never drop a study: keep the study row so the long table still covers every study.
            rows.append(copied_row(sid, r, "; ".join(m["benchmarks"]),
                                   f"study-level row (multi-benchmark, NOT expanded: {fallback_reason})"))
            n_fallback += 1; logger.warning("%s -- copied unexpanded (%s)", sid, fallback_reason)
            continue
        for arm in result["arms"]:
            if isinstance(arm, dict):
                rows.append(flatten_arm(sid, arm, result.get("_provenance", prov), r))

    long = pd.DataFrame(rows)
    front = ["study_id", "benchmark", "scored", "row_source", "wider_than_study", "changed_vs_study"]
    long = long[front + [c for c in long.columns if c not in front]]
    xlsx = a.output_dir / "benchmark_long.xlsx"
    scored_mask = (long["scored"] != False) & (long["benchmark"] != UNNAMED) & \
                  (~long["row_source"].str.contains("NOT expanded|best-effort", regex=True))
    with pd.ExcelWriter(xlsx, engine="openpyxl") as w:
        long.to_excel(w, sheet_name="Study_x_Benchmark", index=False)
        long[scored_mask].groupby("benchmark").size().rename("n_studies_scored").reset_index() \
            .sort_values("n_studies_scored", ascending=False).to_excel(w, sheet_name="Benchmark_counts", index=False)
        review = long[long["wider_than_study"].notna() | long["changed_vs_study"].notna() |
                      long["row_source"].str.contains("NOT expanded|best-effort", regex=True)]
        review[front + ["abstraction_flags", "abstraction_notes"]].to_excel(w, sheet_name="Review", index=False)
    logger.info("wrote %s: %d rows / %d studies (%d extracted this run, %d copied single-benchmark, %d copied unexpanded)",
                xlsx, len(long), long.study_id.nunique(), done, n_copied, n_fallback)
    if long.study_id.nunique() != len(studies):
        logger.error("study count mismatch: sheet has %d, long table has %d", len(studies), long.study_id.nunique())


if __name__ == "__main__":
    main()
