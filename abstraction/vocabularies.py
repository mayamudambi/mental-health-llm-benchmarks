"""
vocabularies.py — single source of truth for every controlled vocabulary
used by the condensed and full abstraction tools.

Both `schema_condensed.py` and `schema_lite.py` import from here. Do NOT
redefine any of these Literals inside a tool folder; if a tool needs a
variant, build it from the base set here (see ConversationType below) so
the relationship stays explicit and greppable.

Two vocabularies that were previously prose-only are now enforced:
  - MENTAL_HEALTH_DOMAINS
  - EVALUATION_CONSTRUCTS
Both accept an "Other (specifier)" escape hatch, validated by
`validators.check_vocabulary` rather than by Literal, since the specifier
text is free-form.

VOCABULARY_VERSION is stamped into every output JSON. Bump it on any
change to a member list so cached results coded under an older vocabulary
are identifiable.
"""

from typing import Literal, Tuple

VOCABULARY_VERSION = "2026-08-29.20"


# ---------------------------------------------------------------------------
# Study-level
# ---------------------------------------------------------------------------

StudyType = Literal[
    "Benchmark development",
    "Evaluation study",
    "Model development",
]

JournalSourceType = Literal[
    "Preprint",
    "Conference proceeding",
    "Peer reviewed",
    "Other",
]

MHScope = Literal[
    "MH only",
    "Mixed — MH is a substantial domain",
    "Mixed — MH is a minor domain",
]


# ---------------------------------------------------------------------------
# Systems and tasks
# ---------------------------------------------------------------------------

SystemTestedType = Literal[
    "LLM alone",
    "LLM as judge/evaluator",
    "Reward model",
    "Guardrail/safety classifier alone",
    "Conversational agent (end-to-end)",
    "Other multi-component pipeline output",
]

SystemTaskType = Literal[
    "Text/response generation",
    "Classification / score prediction",
    "Question-answering",
    "Summarization",
    "Dialogue/conversation",
    "Simulation",
    "Evaluation/judging",
    "Other",
]

EvaluatedOutputType = Literal[
    "Generated text",
    "Label or class",
    "Score or rating",
    "Mixed",
]

AccessMethodType = Literal[
    "API",
    "User interface",
    "Not reported",
]


# ---------------------------------------------------------------------------
# Mental health domains  (was List[str] with a prose-only vocabulary)
#
# Members are listed one per line rather than as a slash-delimited run,
# because several members contain an internal " / " (Trauma / PTSD,
# Well-being / flourishing) which made the old "A / B / C" prose list
# genuinely ambiguous to parse.
# ---------------------------------------------------------------------------

MENTAL_HEALTH_DOMAINS: Tuple[str, ...] = (
    "Depression",
    "Anxiety",
    "Stress",
    "Trauma / PTSD",
    "Bipolar disorder",
    "Schizophrenia",
    "Psychosis",
    "OCD",
    "Eating disorders",
    "ADHD",
    "Autism spectrum",
    "Postpartum or perinatal depression",
    "Suicide/self-harm",
    "Personality disorders",
    "Delusional disorder",
    "Cognitive distortion",
    "Well-being / flourishing",
    "Stigma",
    "Misinformation",
    "Bias",
    "General mental health",
    "Emotional support",
    "Counseling",
    "Crisis counseling",
    "General psychiatry",
    "General psychology",
)

# Removed 2026-08-28 as out of scope for the review:
#   "Substance use", "Tobacco/smoking cessation", "Developmental disorders"
# Substance use is out of scope outright. Developmental disorders covered
# intellectual / learning / motor disability, which is out of scope; ADHD and
# Autism spectrum REMAIN in scope, but only when evaluated in a mental-health
# context (diagnosis, screening, clinical language assessment, caregiver
# clinical information) — not in an educational, linguistic, or general
# developmental context.
#
# NOTE: the frozen screening tool ran all ~500 papers with these three values
# available. Rows carrying them, and ADHD/Autism rows in non-MH contexts, were
# screened under the wider scope and need re-review. See
# SCREENING_SCOPE_REVIEW_DOMAINS and scripts/find_scope_affected.py.
SCREENING_SCOPE_REVIEW_DOMAINS: Tuple[str, ...] = (
    "Substance use",
    "Tobacco/smoking cessation",
    "Developmental disorders",
    "ADHD",
    "Autism spectrum",
)

# General codes may never co-occur with a specific domain code.
GENERAL_DOMAIN_CODES: Tuple[str, ...] = (
    "General mental health",
    "General psychiatry",
    "General psychology",
)


# ---------------------------------------------------------------------------
# Evaluation constructs  (was List[str] with a prose-only vocabulary)
# ---------------------------------------------------------------------------

EVALUATION_CONSTRUCTS: Tuple[str, ...] = (
    "Diagnostic accuracy",
    "Treatment/clinical accuracy",
    "Psychiatric knowledge accuracy",
    "Risk detection accuracy",
    "Emotion recognition",
    "Response quality",
    "Empathy",
    "Supportiveness",
    "Helpfulness",
    "Safety",
    "Trustworthiness",
    "Privacy",
    "Fairness / equity",
    "Cultural sensitivity",
    "Guideline adherence / information quality",
    "Therapeutic alliance / rapport",
    "Therapeutic technique fidelity",
    "Intervention strategy selection",
    "Simulation fidelity",
    "Professionalism / clinical communication style",
    # Added 2026-08-29.3. Both are LLM-AS-ANNOTATOR constructs: the model labels a
    # phenomenon present in the INPUT. They complete the detection family that
    # already contains Diagnostic accuracy, Risk detection accuracy, and Emotion
    # recognition; before them, three of the first ten test papers had no reachable
    # term and were mis-mapped to Fairness / equity and Therapeutic technique fidelity.
    "Stigma and harmful-content detection",
    "Psychotherapy process annotation",
    # Added 2026-08-29.13. Covers the clinical-writing genre — progress and
    # session notes, intake write-ups, discharge summaries, referral letters,
    # structured chart entries — where what is scored is the QUALITY OF THE
    # DOCUMENT: completeness against required elements, factual faithfulness to
    # the source encounter, absence of fabricated detail, and fitness for the
    # clinical record. Before this term there was no reachable category: the
    # closest available were Response quality (too generic, and reserved for
    # bare automated metrics as sole evaluation) and Therapeutic technique
    # fidelity, which is about how the SESSION was conducted, not how the
    # write-up reads. Note that Summarization already exists in SystemTaskType;
    # this is the construct that task is usually scored on.
    "Clinical documentation quality",
)

# Author-named dimensions that map to NO construct. Recorded in
# evaluation_constructs_described, never mapped into _categories.
OUT_OF_SCOPE_DIMENSIONS: Tuple[str, ...] = (
    # Added 2026-08-29.10 from the four-PDF audit. Each is an author-named
    # dimension observed in a reviewed paper that reads as in-scope but is not:
    #   "naturalness"      MAGneT expert aspect "Content Naturalness"; MindEval
    #                      ASCQ anchors (stilted/mechanical/templated phrasing).
    #                      This is linguistic fluency, an excluded domain.
    #   "authenticity"     MAGneT and Lissak both name it; Lissak already
    #                      declined to map it. Recorded so the two agree.
    #   "verbosity"        MindEval ASCQ; length, not a clinical capability.
    #   "client affect change"  PANAS pre/post in MAGneT and CACTUS. A user
    #                      outcome, excluded as an evaluation domain. Simulated
    #                      clients and LLM-assigned scores do not change what is
    #                      being measured, only how well. See the guide's
    #                      CLIENT AFFECT CHANGE block for the inclusion
    #                      consequence when it is a paper's ONLY measure.
    #   judge reliability  CACTUS recorded GPT-4o-vs-expert correlation as
    #                      "Other (LLM-judge vs expert correlation)". A judge's
    #                      agreement with a human standard is a validity check on
    #                      the MEASURING APPARATUS, not a capability of any system
    #                      under test. It is already carried by Evaluation/judging
    #                      in system_tasks and LLM as judge/evaluator in
    #                      systems_tested. Listed here so the "not on the
    #                      out-of-scope list" clause in the Other(specifier) rule
    #                      actually bites — it did not, because the concept was
    #                      absent from this tuple.
    "naturalness",
    "authenticity",
    "verbosity",
    "judge reliability",
    "judge-human agreement",
    "llm-judge vs expert correlation",
    "inter-rater agreement",
    "annotator agreement",
    "client affect change",
    "client emotional outcome",
    "pre/post affect shift",
    "response coherence",
    "relevance",
    "on-topicness",
    "semantic similarity",
    "usability",
    "engagement",
    "response speed",
    "user-reported trust",
    "credibility",
    "satisfaction",
    "acceptance",
)

# Regex fragments matched against the SPECIFIER text inside "Other (...)".
# A specifier hitting one of these is recording something the exclusions rule
# out, which Other() must never be used to house. Kept separate from
# OUT_OF_SCOPE_DIMENSIONS because that tuple is matched against author-named
# dimension strings, whereas these match free-form specifier prose.
OTHER_SPECIFIER_FORBIDDEN_PATTERNS: Tuple[str, ...] = (
    r"judge",            # judge reliability / LLM-judge vs expert correlation
    r"\bagreement\b",    # inter-rater or annotator agreement
    r"correlation with (human|expert)",
    r"semantic similarit",
    r"coheren",
    r"fluenc",
    r"naturalness",
    r"verbosit",
    r"engagement",
    r"satisfaction",
    r"acceptab|acceptance",
    r"usabilit",
    r"latency|speed|throughput",
    r"affect (change|shift)",
    r"client (outcome|emotional)",
)

# Constructs that must not restate a system_task. Used by
# validators.check_construct_task_overlap.
# Emptied 2026-08-29.10. The single member, ("Simulation", "Simulation fidelity"),
# was written before branch (h) of the construct-routing rules existed. It then
# fired on exactly the records where (g) worked — MindEval and PAIR-SAFE, both of
# which quantitatively validate their simulator against human text and report it
# as a result. 2/2 false positives. MindEval's PDF (§3.1: 432 human turns, t-SNE
# distance across four prompt ablations and five patient models) confirms the
# pairing is CORRECT behaviour, not an error.
#
# The real defect is the INVERSE asymmetry — Simulation in system_tasks with no
# Simulation fidelity construct and no validation anywhere in the paper (MAGneT).
# That is caught by validators.check_simulation_task_needs_fidelity, not here.
#
# Left in place, empty, because check_construct_task_overlap is a good hook if a
# genuine task/construct restatement is ever found. Do not re-add this pair.
CONSTRUCT_TASK_FORBIDDEN_PAIRS: Tuple[Tuple[str, str], ...] = ()


# ---------------------------------------------------------------------------
# Dataset purpose  (added 2026-08-29.12)
#
# What the evaluation data is USED FOR, as opposed to what the paper contributes
# (type_of_study). The two correlate but come apart: a Model development paper
# can fine-tune on one corpus and evaluate on a third-party benchmark.
#
# The two "Both" values are deliberately framed around what the paper REPORTS,
# not what its authors did. "Split not reported" is an observation about
# reporting quality; it is not an accusation of leakage, and it is the DEFAULT,
# so the extractor never has to judge an absence. Requiring positive evidence for
# "held-out split reported" is the same transformation that took
# input_availabilities from a coin flip to a stable field.
DatasetPurpose = Literal[
    "Evaluation only",
    "Training or tuning only",
    "Both — held-out split reported",
    "Both — split not reported",
    "Not applicable",
]

# Values whose selection requires evidence cited in abstraction_notes.
DATASET_PURPOSE_REQUIRES_EVIDENCE: Tuple[str, ...] = (
    "Both — held-out split reported",
)

# Values that require abstraction_notes to name which dataset served which role.
DATASET_PURPOSE_REQUIRES_DERIVATION: Tuple[str, ...] = (
    "Both — held-out split reported",
    "Both — split not reported",
)


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

InputFormatType = Literal[
    "Multiple-choice questions (MCQs)",
    "Question-answer pairs",
    "Clinical vignettes",
    "Transcripts (interviews, sessions, hotline calls)",
    "Social media / online content",
    "Chat logs",
    "Simulated dialogues/patient interactions",
    "Interactive dialogue (simulated or live users)",
    "Journal/diary entries",
    "Personal narratives",
    "News/media articles",
    "Clinical notes",
    "Audio recordings",
    "Video recordings",
    "Images",
    "Structured forms/checklists",
    "Structured/tabular data",
    "Free-text prompts",
    "Other (specify)",
]

InputProvenance = Literal[
    "Third-party",
    "Author-created",
    "Mixed",
]

InputAvailability = Literal[
    "Publicly released",
    "Available on request",
    "Fully specified in paper",
    "Method reproducible, items unavailable",
    "Partially specified",
    "Not available",
]

# Availability values that fail Criterion 5's reproducibility limb.
# Papers where every included arm falls in this set can pass Criterion 5
# only via the >=2-independent-systems comparability fallback.
NON_OBTAINABLE_AVAILABILITY: Tuple[str, ...] = (
    "Partially specified",
    "Not available",
)

# Renamed from InputStandardization 2026-08-29.11. The old field carried THREE
# different questions under one name and was unstable because of it:
#   (A) reproducibility  — re-run it, same inputs?      <- the old DESCRIPTION
#   (B) standardization  — same inputs across systems?  <- the old NAME
#   (C) mechanism        — what generates the variation? <- the old VALUES
# MindEval proves A and B come apart: fresh interactions every run (A = no) over
# a fixed pool of 50 patient profiles every model faces (B = yes). This enum now
# carries (C) only. (A) IS derivable from it: Fixed alone => reproducible inputs.
#
# (B) is deliberately NOT RECORDED. A cross_system_comparability field was added
# and removed the same day: it is a real validity question, but it is not derivable
# from (C), it would have been the only field in the tool with no validator and no
# stability history, and no planned finding depends on it. If a comparability claim
# is ever needed, it has to be a NEW field -- do not infer it from Fixed, which is
# wrong in both directions (see the input_determinism description).
#
# VALUES ARE NON-EXCLUSIVE. The old "PRECEDENCE OVER ITERATIVE" rule forced a
# single pick and was the direct cause of the instability — MAGneT, TheraMind and
# MindEval are all genuinely more than one of these at once. Record every value
# that applies. MindEval is three: Fixed (profile pool), Stochastic (interactions
# generated afresh per run), Dynamic (later turns condition on earlier outputs).
InputDeterminism = Literal[
    "Fixed",
    "Stochastic",
    "Dynamic",
    "Live",
    "Mixed or unclear",
]

# Old -> new, for reading any output stamped before 2026-08-29.11.
INPUT_DETERMINISM_CROSSWALK = {
    "Fixed evaluation set": "Fixed",
    "Sampled or generated per trial": "Stochastic",
    "Iterative or trajectory-dependent": "Dynamic",
    "Live user data": "Live",
    "Mixed or unclear": "Mixed or unclear",
}


# What the material IS. Deliberately orthogonal to InputProvenance (who
# assembled it). The old InputSourceType conflated the two: its "Author-authored"
# value answered a provenance question, which is why coders reversed themselves
# on third-party vignettes reproduced in a later paper.
InputReality = Literal[
    "Real",
    "Synthetic — human-written",
    "Synthetic — LLM-generated",
    "Mixed",
    "Not reported",
]

OutputAudience = Literal[
    "Patient / Consumer",
    "Provider",
    "Researcher",
    "Mixed",
    "Not applicable",
]

# --- ConversationType -------------------------------------------------------
# Base set is per-instance (full tool). The condensed tool rolls up across
# arms and therefore needs one extra value, "Mixed", for papers containing
# arms of more than one type. The two are deliberately different; keep the
# relationship expressed here rather than by copy-paste.

# Collapsed 2026-08-29.11. "Non-conversational single-shot" and "Conversational
# single-shot" were merged into "Single-shot". The split distinguished whether a
# one-output task was FRAMED as a dialogue, which is already carried by
# system_tasks (Classification vs Text/response generation), input_formats, and
# evaluated_output_types — and it did not help identify multi-turn work, since
# Multi-turn interactive is its own value and the feedback test that defines it
# is unaffected. It cost stability: across three identical runs the field flipped
# on exactly this boundary for Hasan and Kumar, 2 of its 3 unstable cells.
CONVERSATION_TYPES_BASE: Tuple[str, ...] = (
    "Single-shot",
    "Multi-turn interactive",
    "Not applicable",
)

ConversationTypeInstance = Literal[
    "Single-shot",
    "Multi-turn interactive",
    "Not applicable",
]

ConversationTypeRollup = Literal[
    "Single-shot",
    "Multi-turn interactive",
    "Mixed",
    "Not applicable",
]

# Old -> new, for reading any output stamped before 2026-08-29.11.
CONVERSATION_TYPE_CROSSWALK = {
    "Non-conversational single-shot": "Single-shot",
    "Conversational single-shot": "Single-shot",
}

CONVERSATION_TYPES_ROLLUP: Tuple[str, ...] = CONVERSATION_TYPES_BASE + ("Mixed",)


# ---------------------------------------------------------------------------
# Reference standard and scoring
# ---------------------------------------------------------------------------

ReferenceStandardType = Literal[
    "Ground-truth reference",
    "Expert/clinician ratings",
    "Trained annotator ratings",
    "None — rubric-only scoring",
]

JudgementType = Literal[
    "Met",
    "Not met",
    "Cannot determine",
]

EvaluationEngineType = Literal[
    "LLM as judge",
    "Automated metric",
    "Human raters",
    "Multi-judge (hybrid)",
    "Statistical comparison",
    "Other",
]

ReproducibilityType = Literal[
    "Procedural",
    "Partial",
    "Not reproducible",
]

QualityLevel = Literal[
    "Poor",
    "Adequate",
    "High",
    "N/A",
]

LivedExp = Literal[
    "None",
    "Consulted",
    "Co-design",
    "Led",
]


# ---------------------------------------------------------------------------
# Inclusion
# ---------------------------------------------------------------------------

InclusionScoreType = Literal[1, 2, 3, 4]
ConfidenceType = Literal[1, 2, 3]


# ---------------------------------------------------------------------------
# Sentinels
#
# These strings were previously free text and drifted ("Not stated",
# "none stated", "N/A"), which broke downstream filters including the
# Criterion 7 check. They are now constants; validators normalise to them.
# ---------------------------------------------------------------------------

NONE_STATED = "None stated"
RUBRIC_ONLY = "None — rubric-only scoring"

# Case-insensitive spellings normalised to NONE_STATED on ingest.
NONE_STATED_ALIASES: Tuple[str, ...] = (
    "none stated",
    "not stated",
    "none",
    "n/a",
    "na",
    "not applicable",
    "not reported",
    "none reported",
    "unspecified",
)


# ---------------------------------------------------------------------------
# Null-vs-empty-list convention
#
# Stated once, here, and referenced from every Optional[List[str]] field
# description. Both collapse to a blank Excel cell, so the distinction has
# to be carried by convention rather than by inspection of the output.
#
#   None  = the field does not apply to this paper (no such thing exists)
#   []    = the field applies, was looked for, and nothing was found
#
# Fields and their conventions:
#   benchmark_names                 None if no arm's input set is named.
#                                   [] never used.
#   parent_benchmarks               None if no arm derives from a parent.
#                                   [] never used.
#   reference_standard_instruments  None if no arm uses a named instrument.
#                                   [] never used.
#   abstraction_flags               None if nothing was genuinely uncertain.
#                                   [] never used.
# ---------------------------------------------------------------------------

NULL_CONVENTION_NOTE = (
    "CONVENTION: use null (not an empty list) when this field does not apply "
    "to the paper. An empty list is never a valid value for this field."
)


# ---------------------------------------------------------------------------
# Screening-tool crosswalk
#
# abstraction_tool_screening/ is frozen and has already run on all ~500
# papers, so its vocabularies are a generation behind: they predate the
# Coherence/Relevance retirement, the "Trauma / PTSD" rename, and the
# spacing normalisation of "Fairness / equity". Screening output therefore
# does NOT join to condensed or full output on these columns without
# translation.
#
# Do not edit the screening tool. Apply this map when reading
# results_screening/*.xlsx or raw_json/*.json.
#
# A value mapping to None was retired: those rows have no landing category
# in the current vocabulary and need manual re-coding if the column matters.
# ---------------------------------------------------------------------------

SCREENING_CONSTRUCT_CROSSWALK = {
    "Fairness/equity": "Fairness / equity",
    "Coherence": None,   # retired — now an out-of-scope dimension
    "Relevance": None,   # retired — now an out-of-scope dimension
    "Other": "Other (unspecified — screening tool had no specifier slot)",
}

SCREENING_DOMAIN_CROSSWALK = {
    "PTSD": "Trauma / PTSD",
    "Postpartum/perinatal depression": "Postpartum or perinatal depression",
    "Substance use": None,               # now out of scope
    "Tobacco/smoking cessation": None,   # now out of scope
    "Developmental disorders": None,     # now out of scope
    "Other": "Other (unspecified — screening tool had no specifier slot)",
}


def crosswalk(values, mapping):
    """Translate screening-era values to the current vocabulary.

    Returns (translated, dropped). `dropped` lists values whose category was
    retired or moved out of scope — surface these rather than discarding them.
    """
    out, dropped = [], []
    for v in values or []:
        if v in mapping:
            new = mapping[v]
            (out if new is not None else dropped).append(new if new is not None else v)
        else:
            out.append(v)
    return out, dropped
