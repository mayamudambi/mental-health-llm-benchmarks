"""Benchmark-level schema: one row per (study, benchmark).

Each arm inherits EVERY field and validator of the condensed StudyRollup, so a
row is directly comparable with the study-level sheet, and adds:
  * benchmark / scored / scored_notes   -- the row key and a gate for listed-but-not-scored artifacts
  * the benchmark-level factual fields (models_tested ... scoring_reproducibility_notes)
  * optionally, the Poor/Adequate/High component ratings (--with-quality-ratings)

The guide text for the added fields lives HERE (BENCHMARK_FIELDS_GUIDE) rather than
being spliced from the lite guide. Everything is phrased per BENCHMARK: the unit of
extraction is the benchmark. No dependency on schema_lite.py / extraction_guide_lite.py.
"""
import re
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator

import validators as _v
from schema_condensed import StudyRollup
from vocabularies import (AccessMethodType, JudgementType, ReproducibilityType, LivedExp, QualityLevel,
                          NONE_STATED, RUBRIC_ONLY)

AUTOMATED_SENTINEL = "Not applicable — automated metric"
SINGLE_RATER_SENTINEL = "Not reported — single rater, IRR not possible"
UNNAMED = "[unnamed]"

INPUT_MODALITIES = ("text", "audio", "video", "image", "multimodal (text+audio)",
                    "multimodal (text+video)", "multimodal (text+image)", "other")

ENGINE_PREFIXES = ("LLM as judge (", "Automated metric (", "Human raters (",
                   "Multi-judge (hybrid; ", "Statistical comparison (", "Other (")
AUTOMATED_ENGINE_PREFIXES = ("Automated metric (", "Statistical comparison (")


class ModelEntry(BaseModel):
    name: str = Field(..., description=(
        "Model name as given in the paper. Generative LLMs only — omit logistic regression, SVMs, "
        "fine-tuned encoders (BERT-family), rule-based systems, and any judge / simulator model."))
    role: Optional[Literal["Baseline/comparator"]] = Field(None, description=(
        "'Baseline/comparator' only if this generative LLM is a comparison point rather than a primary "
        "evaluation focus. Null if it is a primary subject of evaluation."))


# ---------------------------------------------------------------------------
# Guide text for the added fields. Written per benchmark. Appended to the system
# prompt by abstract_benchmarks.build_system_prompt.
# ---------------------------------------------------------------------------
BENCHMARK_FIELDS_GUIDE = """
== BENCHMARK-LEVEL FIELDS ==
Every field below describes the evaluation of THIS BENCHMARK only. If the paper scores this
benchmark under more than one reference standard or scoring procedure (e.g. BERTScore against
gold responses AND a clinician rubric on the same outputs), describe ALL of them in the prose
fields and rate the enum fields (judgement, reproducibility, quality) on the WEAKEST procedure
that carries a headline claim — the same rollup rule the study-level guide uses. Never describe
an attribute of another benchmark in this row.

SCORED and SCORED_NOTES
scored=true only if the paper reports a generative LLM's result on this benchmark AND that result
is MH-disaggregated (the MH-scope gate applies per benchmark). A dataset used only for training,
listed in a table without results, or reported only as part of an aggregate over non-MH data is
scored=false. When scored=false: scored_notes gives the reason in one sentence, models_tested is
[], n_test_cases is null (the only number available is usually a training-set size — do not record
it), evaluation_engine is 'Other (not scored)', and the remaining fields describe what the paper
says about the artifact as best you can. Do NOT put 'not scored' in abstraction_notes; scored_notes
is the only place for it.

MODELS TESTED
List ONLY generative LLMs whose output on THIS benchmark is scored. Omit non-generative models,
LLMs used only as judges, raters, user simulators or data generators, and models mentioned in
related work. role='Baseline/comparator' only for a generative LLM serving as a comparison point.
Collapse prompt variants, checkpoints and decoding settings of one model into one entry.

ACCESS METHOD
API / User interface / Not reported. Categories only. A locally-run open-weights model is API.

INPUT MODALITY
All modalities of this benchmark's items, lowercase, from: text / audio / video / image /
multimodal (text+audio) / multimodal (text+video) / multimodal (text+image) / other. Classify by
the native form of the items even if transcribed before model input.

N TEST CASES
Number of distinct items on this benchmark that the model is scored on. NOT number of models,
participants, raters, dialogue turns, or the size of a training split. If a test split is used,
record the split size and say so in n_test_cases_notes ('test set only — 20% of 1,250'). If the
paper scores a sample of the benchmark, record the sample size and note the full size. Null if not
reported; do not estimate and do not copy a headline dataset size that was not what was scored.

INPUT SOURCE/GROUNDING
WHERE this benchmark's items came from and whether they were validated — no content or format
description (that is input_formats / input_reality). Start with a category: clinician-authored /
psychiatric textbooks or guidelines / real clinical data / social media (real, uncurated) /
LLM-generated / researcher-authored / validated instrument / unstated. Then: who authored or
validated the items and whether that validation was independent of the authors. Combine
categories when needed. E.g. 'Clinician-authored, single psychiatrist, not independently
validated'; 'Real clinical data — de-identified outpatient transcripts, single centre 2018-2021,
no representativeness check'; 'LLM-generated (GPT-4) from DSM-5 criteria, every item reviewed by
two clinicians'. For a third-party benchmark, describe its ORIGINAL construction as this paper
reports it; if this paper says nothing about it, write 'Third-party benchmark; construction not
described in this paper'.

LIVED-EXPERIENCE ROLES (input_lived_experience_role, scoring_lived_experience_role)
None / Consulted / Co-design / Led. Above 'None' ONLY when people identified by the paper as
having lived experience of a mental-health condition (service users, peer-support workers,
patient advisory groups) were explicitly involved in DESIGNING or VALIDATING the items (input)
or the scoring criteria (scoring). People who merely SUPPLIED data (posted online, took part as
participants, were the patients in the transcripts) are NOT involved in design — that is 'None'.
Clinicians never count here regardless of their own history unless the paper says so. Consulted:
feedback or review. Co-design: shared authorship of items or criteria. Led: lived-experience
contributors directed the design. If the paper is silent, 'None'.

PROMPT VARIATION TESTING
Was robustness to prompt rewording, paraphrase, template change or ordering tested ON THIS
BENCHMARK, and what was found? One sentence naming the manipulation and the reported effect.
Zero- vs few-shot and chain-of-thought comparisons count. Temperature sweeps and different models
do NOT count. 'Not reported' if absent.

REFERENCE STANDARD JUDGEMENT
- Met: an external comparison target is named AND applied — an answer key, expert labels,
  instrument scores, or a rubric that passes the qualification test in the REFERENCE STANDARD
  DESCRIPTION section.
- Not met: outputs judged only by evaluator impression with no stated basis ('experts rated the
  responses', no rubric, no criteria, no reference), OR the evaluators also constructed the
  stimuli (scoring not independent of the material). When Not met, reference_standard_description
  must contain 'None stated' for that procedure (never the rubric-only type value — that goes in
  reference_standard_type only, per the REFERENCE STANDARD DESCRIPTION section).
- Cannot determine: a standard is implied but not described well enough to identify.
This judges legitimacy, not rigour. A single-clinician DSM-5 label with no verification is Met;
its rigour is captured by the quality rating.

SCORING PROCEDURE JUDGEMENT
- Met: a specified operation produces a numeric score, ordinal rating or systematic category,
  applied uniformly across this benchmark's items and reported (per item or aggregate).
- Not met: narrative description with no quantification, OR a scheme is named but results are not
  reported. When Not met, scoring_procedures may still describe the scheme.
- Cannot determine: results are quantified but the procedure producing them is not described.
Met is incompatible with scoring_procedures = 'None stated'.

EVALUATION ENGINE
Who or what produces the scores on this benchmark. EXACTLY one prefix with a specifier in
parentheses — the string must start with one of these and end with ')':
  'LLM as judge (model name)'                  e.g. 'LLM as judge (GPT-4o)'
  'Automated metric (metric family)'           e.g. 'Automated metric (accuracy, macro-F1)'
  'Human raters (count + type)'                e.g. 'Human raters (3 licensed psychiatrists)'
  'Multi-judge (hybrid; composition)'          e.g. 'Multi-judge (hybrid; GPT-4o + 2 clinicians)'
  'Statistical comparison (test name)'         e.g. 'Statistical comparison (Pearson r vs clinician PHQ-9)'
  'Other (specifier)'
If more than one engine scores this benchmark, use 'Multi-judge (hybrid; ...)' and list them.
Systems under evaluation never appear here, even if they act as judges: an LLM whose judging is
itself being tested belongs in models_tested. If scored=false, use 'Other (not scored)'.

RUBRIC SOURCE/GROUNDING
WHERE the scoring criteria came from and whether validated. If the engine is an automated metric
or a statistical comparison with no rubric, write EXACTLY 'Not applicable — automated metric' and
nothing else. Otherwise name the instrument or framework, who designed the dimensions, and the
validation status. E.g. 'CARE measure (Mercer et al., 2004), items unmodified'; 'Clinician-informed
— two psychiatrists drafted dimensions, no independent review'; 'Authored for this study — no
clinical grounding cited'; 'Mixed: safety dimension from C-SSRS; 4 remaining dimensions authored
for this study'. 'Not reported' is not an option here: an undisclosed rubric is 'Authored for this
study — not disclosed'.

JUDGE VALIDATION / RELIABILITY
How the judge's reliability was established on this benchmark. Automated metric or statistical
comparison: EXACTLY 'Not applicable — automated metric'. LLM judge: agreement with human/expert
ratings (κ, ICC, r, accuracy vs humans) as reported, or 'Not reported'. Human raters with ≥2
raters: IRR statistic as reported, or 'Not reported'. Exactly one human rater: EXACTLY
'Not reported — single rater, IRR not possible'. Internal consistency of a judge with itself
(self-agreement across runs) is not validation; report it but label it as consistency.

SCORING REPRODUCIBILITY and NOTES
Scoped to the SCORING SETUP only (rubric text, judge prompt, parsing rules, engine config) — not
to item availability, which is input_availabilities.
- Procedural: rubric, judge prompt and parsing rules fully disclosed and usable.
- Partial: some scoring materials disclosed but meaningful gaps remain.
- Not reproducible: rubric, judge prompt or configuration undisclosed or irrecoverable.
An exact-match or standard automated metric with the metric named is Procedural. An LLM judge whose
prompt is described in prose but not quoted is Partial. scoring_reproducibility_notes is ALWAYS
required: what is available, what is missing, why the rating. A Procedural rating with notes that
describe something missing is a contradiction and will be flagged.
"""

BENCHMARK_QUALITY_GUIDE = """
== INPUT QUALITY RATING (this benchmark) ==
Four components (High / Adequate / Poor / N/A):
A. Source category — provenance of the items.
B. Independent validation — items checked by someone other than their creators.
C. Informant involvement — clinical/domain expertise in creation or annotation.
D. Lived-experience involvement — people with the relevant condition.
Combination (ENFORCED by a validator — compute it, do not estimate it):
  Poor  if any of A/B/C is Poor.
  High  if A is High or Adequate AND B is High AND C is High (D is a bonus).
  Adequate otherwise.
Floors: proxy/self-labelled data → A Poor. LLM-generated without human verification → A Poor;
with expert verification of every item → A Adequate max.
Justification: score A/B/C/D individually and state the rule or floor applied.

== REFERENCE STANDARD QUALITY RATING (this benchmark) ==
EXACTLY 'N/A' when this benchmark's ONLY reference_standard_type is 'None — rubric-only scoring';
never 'N/A' otherwise (if a rubric-only procedure sits alongside a real standard, rate the real one).
Rate on: (1) anchoring to clinical frameworks, validated instruments or actual clinical
assessment; (2) authorship by clinical experts or trained annotators with expert adjudication;
(3) independent verification reported (pre-existing validated instruments carry external
validation weight); (4) construct match.
High: all four. Adequate: most met, minor gaps. Poor: one or more substantially unmet.
Floors: proxy/self-derived labels → Poor; unacknowledged construct mismatch → Poor.
Ceilings: no verification AND not a validated instrument → Adequate max; single rater, no
adjudication, no external validation → Adequate max.
Justification must address all four criteria.

== SCORING QUALITY RATING (this benchmark) ==
Four components (High / Adequate / Poor / N/A):
A. Metric-task fit. B. Judge/scoring validation against expert judgment (consistency ≠ validity —
caps B at Adequate; N/A for exact match against unambiguous ground truth). C. Transparency of
scoring materials (undisclosed = absent). D. Output-variability handling (N/A if output is
unambiguous and fully parseable).
Overall: weakest element drives it. High: A, B, C High and D High or N/A. Adequate: A ≥ Adequate,
B and C Adequate, D may be Adequate. Poor: A Poor; or B Poor where the task requires judgement;
or C Poor. Floors: judge circularity (the judge is the model under test or its own family) →
Adequate max, or Poor if config undisclosed; unvalidated automated scoring for safety-critical
claims → Poor; semantic-similarity-only scoring of clinical reasoning → Poor.
Justification: score A/B/C/D and state the rule or floor applied.
"""


class BenchmarkArm(StudyRollup):
    benchmark: str = Field(..., description=(
        "The benchmark this row describes. Copied EXACTLY from the BENCHMARK LIST in the user "
        "message. '[unnamed]' only when the list says so."))
    scored: bool = Field(..., description=(
        "True if the paper reports an MH-disaggregated result of a generative LLM on THIS benchmark. "
        "False if the benchmark is only mentioned, used for training, or listed without results."))
    scored_notes: Optional[str] = Field(None, description=(
        "Required when scored=false: one sentence saying why (training-only, listed without results, "
        "no MH-disaggregated result). Null when scored=true."))

    models_tested: List[ModelEntry] = Field(..., description=(
        "Generative LLMs scored on THIS benchmark. [] when scored=false. See BENCHMARK-LEVEL FIELDS."))
    input_modality: List[str] = Field(..., description=(
        "Modalities of this benchmark's items, lowercase: text / audio / video / image / "
        "multimodal (text+audio) / multimodal (text+video) / multimodal (text+image) / other."))
    n_test_cases: Optional[int] = Field(None, description=(
        "Distinct items on this benchmark the model is scored on. Null if not reported or scored=false."))
    n_test_cases_notes: Optional[str] = Field(None, description=(
        "Qualifier if ambiguous (test split, sample of a larger set). Null if unambiguous."))
    access_method: AccessMethodType = Field(..., description="API / User interface / Not reported.")
    input_source_grounding: str = Field(..., description=(
        "Category + who authored/validated the items + whether independent. No content/format description."))
    input_lived_experience_role: LivedExp = Field(..., description=(
        "None / Consulted / Co-design / Led — lived-experience involvement in item design or validation."))
    prompt_variation_testing: str = Field(..., description=(
        "Prompt-robustness testing on this benchmark and its effect, or 'Not reported'."))
    reference_standard_judgement: JudgementType = Field(..., description="Met / Not met / Cannot determine.")
    evaluation_engine: str = Field(..., description=(
        "'<prefix> (specifier)' with prefix one of: LLM as judge / Automated metric / Human raters / "
        "Multi-judge (hybrid; ...) / Statistical comparison / Other."))
    rubric_source_grounding: str = Field(..., description=(
        "Where the scoring criteria came from and validation status, or EXACTLY "
        "'Not applicable — automated metric'."))
    scoring_lived_experience_role: LivedExp = Field(..., description=(
        "None / Consulted / Co-design / Led — lived-experience involvement in scoring design or validation."))
    judge_validation_reliability: str = Field(..., description=(
        "Judge reliability evidence, 'Not reported', 'Not applicable — automated metric', or "
        "'Not reported — single rater, IRR not possible'."))
    scoring_procedure_judgement: JudgementType = Field(..., description="Met / Not met / Cannot determine.")
    scoring_reproducibility: ReproducibilityType = Field(..., description="Procedural / Partial / Not reproducible.")
    scoring_reproducibility_notes: str = Field(..., description=(
        "Always required — what scoring materials are available, what is missing, why the rating."))

    # ------------------------------------------------------------------
    @model_validator(mode="after")
    def _arm_consistency(self) -> "BenchmarkArm":
        # --- row key ---
        if self.benchmark != UNNAMED and self.benchmark_names != [self.benchmark]:
            raise ValueError(f"benchmark_names must be exactly [{self.benchmark!r}] on this arm; "
                             f"got {self.benchmark_names!r}")
        if self.parent_benchmarks and self.benchmark in self.parent_benchmarks:
            raise ValueError(f"{self.benchmark!r} cannot be its own parent")

        # --- scored gate (hard: notes; soft: models / n) ---
        if not self.scored and not (self.scored_notes or "").strip():
            raise ValueError("scored=false requires scored_notes (one sentence: why not scored)")
        if self.scored and (self.scored_notes or "").strip():
            raise ValueError("scored_notes must be null when scored=true")
        if self.scored != bool(self.models_tested):
            _v.add_flag(self, "scored",
                        f"scored={self.scored} but models_tested={[m.name for m in self.models_tested]!r}; "
                        "scored=true needs at least one generative LLM with a result on this benchmark, "
                        "scored=false needs [].")
        if not self.scored and self.n_test_cases is not None:
            _v.add_flag(self, "n_test_cases", "n_test_cases is set on an unscored benchmark — this is "
                        "usually a training-set size. Leave null unless the paper reports the scored set.")

        # --- input modality vocabulary (normalise, then check) ---
        self.input_modality = [re.sub(r"\s+", " ", m).strip().lower() for m in self.input_modality]
        bad = [m for m in self.input_modality if m not in INPUT_MODALITIES]
        if bad:
            raise ValueError(f"input_modality values not in vocabulary: {bad}; allowed {list(INPUT_MODALITIES)}")

        # --- evaluation engine prefix ---
        eng = self.evaluation_engine.strip()
        if not eng.startswith(ENGINE_PREFIXES) or not eng.endswith(")"):
            raise ValueError(f"evaluation_engine must be '<prefix> (specifier)' with prefix in "
                             f"{[p.rstrip(' (;') for p in ENGINE_PREFIXES]}; got {eng!r}")
        automated = eng.startswith(AUTOMATED_ENGINE_PREFIXES)

        # --- automated ⇔ rubric / judge sentinels ---
        rubric_na = self.rubric_source_grounding.strip() == AUTOMATED_SENTINEL
        judge_na = self.judge_validation_reliability.strip() == AUTOMATED_SENTINEL
        if automated and not (rubric_na and judge_na):
            raise ValueError(f"evaluation_engine {eng!r} is automated/statistical, so rubric_source_grounding "
                             f"and judge_validation_reliability must both be exactly {AUTOMATED_SENTINEL!r}")
        if not automated and (rubric_na or judge_na) and self.scored:
            raise ValueError(f"evaluation_engine {eng!r} involves a judge, but rubric_source_grounding / "
                             f"judge_validation_reliability say {AUTOMATED_SENTINEL!r}")
        if _v._norm(self.rubric_source_grounding) in {_v._norm(a) for a in ("not reported", "n/a", "none")}:
            raise ValueError("rubric_source_grounding may not be 'Not reported' — an undisclosed rubric is "
                             "'Authored for this study — not disclosed'")
        m = re.match(r"Human raters \((\d+)\b", eng)
        if m and int(m.group(1)) == 1 and self.judge_validation_reliability.strip() != SINGLE_RATER_SENTINEL:
            _v.add_flag(self, "judge_validation_reliability",
                        f"single human rater — judge_validation_reliability should be {SINGLE_RATER_SENTINEL!r}")
        if m and int(m.group(1)) > 1 and self.judge_validation_reliability.strip() == SINGLE_RATER_SENTINEL:
            raise ValueError("single-rater sentinel used with more than one human rater")

        # --- judgement coherence ---
        descs = [_v._norm(d) for d in (self.reference_standard_description or [])]
        rs_types = list(self.reference_standard_type or [])
        if self.reference_standard_judgement == "Not met" and _v._norm(NONE_STATED) not in descs \
                and RUBRIC_ONLY not in rs_types:
            _v.add_flag(self, "reference_standard_judgement",
                        "'Not met' but every reference_standard_description names a real standard and no "
                        "type is rubric-only. Not met means unanchored evaluator judgement or a rubric failing "
                        "the qualification test — one description entry should read 'None stated'.")
        procs = [_v._norm(s) for s in (self.scoring_procedures or [])]
        if self.scoring_procedure_judgement == "Met" and procs and all(p == _v._norm(NONE_STATED) for p in procs):
            raise ValueError("scoring_procedure_judgement=Met is incompatible with scoring_procedures='None stated'")
        if rs_types and all(t == RUBRIC_ONLY for t in rs_types) and automated:
            _v.add_flag(self, "evaluation_engine",
                        "reference_standard_type is rubric-only but the engine is an automated metric — "
                        "an automated metric compares to a reference, so one of the two is wrong.")

        # --- reproducibility ⇔ notes ---
        notes = self.scoring_reproducibility_notes.lower()
        if self.scoring_reproducibility == "Procedural" and re.search(
                r"not (quoted|stated|disclosed|released|reported|provided|given)|missing|unclear|undisclosed", notes):
            _v.add_flag(self, "scoring_reproducibility",
                        "rated Procedural but scoring_reproducibility_notes describes a gap")
        if self.scoring_reproducibility == "Not reproducible" and re.search(
                r"fully (reproduced|disclosed|provided)|appendix|supplement", notes) and \
                not re.search(r"\bnot\b|\bno\b|missing", notes):
            _v.add_flag(self, "scoring_reproducibility",
                        "rated Not reproducible but notes describe materials as available")

        # --- drop the low-precision parent flag: at 5x the rows it is noise ---
        self._drop_auto_flag("parent_benchmarks", "author-assembled set of REAL material")
        _v.check_flags_notes_paired(self)
        return self

    def _drop_auto_flag(self, field: str, marker: str) -> None:
        notes = self.abstraction_notes or ""
        if field not in (self.abstraction_flags or []) or marker not in notes:
            return
        parts = [p for p in notes.split(" | ") if marker not in p]
        self.abstraction_notes = " | ".join(parts) or None
        flags = [f for f in (self.abstraction_flags or []) if f != field]
        self.abstraction_flags = flags or None


class BenchmarkArmWithQuality(BenchmarkArm):
    """Adds the Poor/Adequate/High component ratings. No stability history:
    run three times on a subset before trusting them."""
    input_quality_source: QualityLevel = Field(..., description="Component A — source category.")
    input_quality_validation: QualityLevel = Field(..., description="Component B — independent validation.")
    input_quality_informants: QualityLevel = Field(..., description="Component C — informant involvement.")
    input_quality_lived_experience: QualityLevel = Field(..., description="Component D — lived-experience involvement.")
    input_quality_overall: QualityLevel = Field(..., description="Computed from A/B/C by the rule in the guide; enforced.")
    input_quality_justification: str = Field(..., description="Score A/B/C/D individually and state the rule or floor.")
    reference_standard_quality: QualityLevel = Field(..., description="'N/A' iff the only reference_standard_type is rubric-only.")
    reference_standard_quality_justification: str = Field(..., description="Address all four criteria.")
    scoring_quality_metric_fit: QualityLevel = Field(..., description="Component A — metric-task fit.")
    scoring_quality_validation: QualityLevel = Field(..., description="Component B — validation vs expert judgement.")
    scoring_quality_transparency: QualityLevel = Field(..., description="Component C — transparency.")
    scoring_quality_variability: QualityLevel = Field(..., description="Component D — output-variability handling.")
    scoring_quality_overall: QualityLevel = Field(..., description="Weakest element drives it; floors in the guide.")
    scoring_quality_justification: str = Field(..., description="Score A/B/C/D and state the rule or floor.")

    @model_validator(mode="after")
    def _quality_arithmetic(self) -> "BenchmarkArmWithQuality":
        A, B, C = self.input_quality_source, self.input_quality_validation, self.input_quality_informants
        if "Poor" in (A, B, C):
            exp = "Poor"
        elif A in ("High", "Adequate") and B == "High" and C == "High":
            exp = "High"
        else:
            exp = "Adequate"
        if self.input_quality_overall != exp:
            raise ValueError(f"input_quality_overall must be {exp!r} given A={A}, B={B}, C={C} "
                             f"(got {self.input_quality_overall!r})")

        rs_types = list(self.reference_standard_type or [])
        rubric_only = bool(rs_types) and all(t == RUBRIC_ONLY for t in rs_types)
        if rubric_only and self.reference_standard_quality != "N/A":
            raise ValueError("reference_standard_quality must be 'N/A' when reference_standard_type is rubric-only")
        if not rubric_only and self.reference_standard_quality == "N/A":
            raise ValueError("reference_standard_quality 'N/A' is only valid for rubric-only reference standards")

        sa, sb, sc = self.scoring_quality_metric_fit, self.scoring_quality_validation, self.scoring_quality_transparency
        if "Poor" in (sa, sc) and self.scoring_quality_overall != "Poor":
            raise ValueError("scoring_quality_overall must be Poor when metric fit or transparency is Poor")
        if self.scoring_quality_overall == "High" and not (sa == sb == sc == "High"):
            raise ValueError("scoring_quality_overall High requires A, B and C all High")
        if self.evaluation_engine.startswith("LLM as judge (") and self.scoring_quality_overall == "High":
            judge = self.evaluation_engine[len("LLM as judge ("):-1].lower().split()
            if judge and any(judge[0] in m.name.lower() for m in self.models_tested):
                _v.add_flag(self, "scoring_quality_overall",
                            "judge appears to share a family with a model under test — circularity caps at Adequate")
        return self


class BenchmarkRollup(BaseModel):
    arms: List[BenchmarkArm] = Field(..., description="Exactly one arm per benchmark in the BENCHMARK LIST, in the same order.")

    @model_validator(mode="after")
    def _unique(self) -> "BenchmarkRollup":
        names = [a.benchmark for a in self.arms]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate benchmark rows: {names}")
        return self


class BenchmarkRollupWithQuality(BaseModel):
    arms: List[BenchmarkArmWithQuality] = Field(..., description="Exactly one arm per benchmark in the BENCHMARK LIST, in the same order.")

    @model_validator(mode="after")
    def _unique(self) -> "BenchmarkRollupWithQuality":
        names = [a.benchmark for a in self.arms]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate benchmark rows: {names}")
        return self


# Paper-level: copied from the reviewed study sheet, never re-asked.
PAPER_LEVEL_FIELDS = ["authors", "title", "type_of_study", "publication_year", "journal_source", "journal_source_type"]

# Re-extracted per benchmark but ALSO kept from the study row as <field>_study for comparison.
STUDY_COMPARISON_FIELDS = ["mh_scope", "systems_tested", "dataset_purpose"]

# Re-extracted per benchmark. Everything not here and not paper-level is also per benchmark
# (the StudyRollup fields all describe the arm); this list is what the README documents.
ARM_ONLY_FIELDS = [
    "mh_scope", "systems_tested", "dataset_purpose",
    "system_tasks", "mental_health_domains", "evaluation_constructs_described",
    "evaluation_constructs_categories", "primary_construct", "evaluated_output_types",
    "input_formats", "input_provenance_types", "input_availabilities", "input_determinism",
    "parent_benchmarks", "populations", "output_audiences", "input_reality", "input_languages",
    "conversation_types", "reference_standard_type", "reference_standard_description",
    "reference_standard_instruments", "scoring_procedures",
]

# Multi-select fields whose arm values must be a SUBSET of the study row's values
# (a benchmark can be narrower than the paper, never wider). Checked in flatten_arm.
SUBSET_CHECK_FIELDS = [
    "systems_tested", "system_tasks", "mental_health_domains", "evaluation_constructs_categories",
    "evaluated_output_types", "input_formats", "input_provenance_types", "input_availabilities",
    "input_determinism", "output_audiences", "input_reality", "input_languages", "reference_standard_type",
]
