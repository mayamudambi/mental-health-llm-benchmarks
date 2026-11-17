"""
schema_condensed.py

Condensed one-row-per-study abstraction. Aggregates across all evaluation
arms/tasks in a paper into single fields at the study level.

Controlled vocabularies match the full (per-instance) schema so that
condensed and full outputs can be filtered/joined with the same categories.
No quality ratings — those are per-instance judgments and don't aggregate.
"""

from __future__ import annotations

import os as _os, sys as _sys
# vocabularies.py and validators.py live at the PROJECT ROOT, one level above this
# tool folder. Make them importable no matter which directory the runner is
# launched from.
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

import validators as _v
from vocabularies import (
    VOCABULARY_VERSION,
    NULL_CONVENTION_NOTE,
    NONE_STATED,
    RUBRIC_ONLY,
    EVALUATION_CONSTRUCTS,
    MENTAL_HEALTH_DOMAINS,
    StudyType,
    SystemTestedType,
    SystemTaskType,
    InputFormatType,
    ConversationTypeRollup as ConversationType,
    InputProvenance,
    InputAvailability,
    InputDeterminism,
    DatasetPurpose,
    EvaluatedOutputType,
    JudgementType,
    InclusionScoreType,
    ConfidenceType,
    JournalSourceType,
    OutputAudience,
    MHScope,
    InputReality,
    ReferenceStandardType,
)

__all__ = ["StudyRollup", "VOCABULARY_VERSION"]



class StudyRollup(BaseModel):
    """
    One row per study. All list-valued fields aggregate across evaluation
    arms/tasks in the paper — deduplicate, do not repeat.
    """
    authors: str = Field(..., description="Author list as given on the paper.")
    title: str = Field(..., description="Exact paper title.")
    benchmark_names: Optional[List[str]] = Field(
        None,
        description=(
            "Named benchmark(s), dataset(s), corpus(es), or exam(s) that the LLM was "
            "EVALUATED ON in arms that pass the MH relevance gate. "
            "EVALUATION-ONLY RULE: include ONLY datasets/corpora/exams used as evaluation "
            "material — the inputs the LLM was scored on. Do NOT include training corpora, "
            "fine-tuning datasets, RLHF preference datasets, or datasets mentioned only in "
            "the model's provenance. E.g. a paper that fine-tunes on ESConv and evaluates "
            "on PsyQA lists ['PsyQA'], not ['ESConv', 'PsyQA']. "
            "NAME AS THE PAPER NAMES IT: transcribe the name exactly as it appears in this "
            "paper's methods section. Do NOT supply familiar canonical names for corpora "
            "the paper describes without naming. If the paper says 'we sampled 100 posts "
            "from a Reddit mental-health forum' without naming the corpus, leave that "
            "unnamed (do not tag as 'Reddit MH corpus' or similar). If the paper names it "
            "'MHRedditSet-v2', use exactly that. "
            "WORK FROM THE ARM LIST, NOT THE DATASET SECTION: enumerate the evaluation arms "
            "first (task × input × reference standard × scoring), then list the named "
            "benchmark used in each in-scope arm. Do not scrape the dataset section for "
            "names — some named datasets there may belong only to training or excluded "
            "arms. Named exams count: USMLE, PRITE, MRCPsych, Portuguese National "
            "Residency Access Examination (PNA), Chinese Medical Licensing Examination "
            "count even when the paper does not say 'benchmark.' "
            "SCOPE RESTRICTION: include ONLY benchmarks used in arms that pass the MH "
            "relevance gate. Non-MH benchmarks from arms excluded at the gate do NOT "
            "appear here. A paper evaluating on MMLU + MedQA + PsyQA where only PsyQA is "
            "MH-relevant lists only ['PsyQA']. Per-benchmark rule: if the same benchmark "
            "appears in BOTH an included and an excluded arm, it stays. "
            "LIST EACH BENCHMARK ONCE per paper regardless of how many in-scope arms use it. "
            "WORKED EXAMPLE: a paper with 8 named benchmarks used across 13 arms where "
            "3 arms are MH-relevant and use 2 of the 8 benchmarks — list those 2 "
            "benchmarks, once each. "
            "DO NOT include validated clinical or research instruments used as REFERENCE "
            "STANDARDS (C-SSRS, PHQ-9, PHQ-8, GAD-7, CAPS-5, HAM-D, HAMD-17, MADRS, YMRS, "
            "PANSS, WAI, CTRS, MITI, PANAS, etc.). Those go in reference_standard_instruments, "
            "not here. Include a named instrument here ONLY when the scale items are the "
            "INPUT to the LLM. Rule of thumb: does the LLM SEE the scale items? If yes → "
            "benchmark_names candidate; if no (scale is only how outputs are graded) → "
            "reference_standard_instruments. "
            "Do NOT include the name of the model, framework, or system being EVALUATED — "
            "that goes in systems_tested / models_tested. E.g. 'SAGE' is a framework being "
            "evaluated, not a benchmark. Same for chatbot names (Sarah, BeFreeGPT, etc.). "
            "BUT: 'FRAMEWORK' IS NOT A CARVE-OUT (clarified 2026-08-29.10). This exclusion is "
            "about the OBJECT OF EVALUATION, not the word the paper uses. Ask which side of the "
            "test the named thing sits on. If it is a system being SCORED, exclude it. If it is "
            "the apparatus DOING the scoring and it owns a named, fixed input set, it is a "
            "benchmark and belongs here — even when the paper calls it a framework, a harness, a "
            "pipeline, or an environment, and even when it holds no static transcripts. WORKED "
            "EXAMPLE: MindEval calls itself 'a framework' in its abstract and was wrongly left "
            "null. It names itself in its title, lists 'MindEval (ours)' in a table of benchmarks, "
            "and owns a fixed set of 50 patient profiles against which every system under test is "
            "run. benchmark_names = ['MindEval']. A benchmark whose fixed component is the "
            "stimulus generator rather than the stimuli is still a benchmark. "
            "COROLLARY: if the paper introduces a named evaluation artefact at all — which "
            "type_of_study = 'Benchmark development' asserts — this field cannot be null. "
            "Leave null if the input source is not named — do NOT invent a name."
            "CONVENTION: use null (not an empty list) when this field does not apply to the paper. An "
            "empty list is never a valid value for this field."
        ),
    )
    type_of_study: StudyType = Field(
        ...,
        description=(
            "Benchmark development: paper BUILDS an evaluation apparatus of its own. "
            "Judge by what was BUILT, not by whether the artifact is named, released, or "
            "fully specified. Tag Benchmark development when ANY of these apply: "
            "(a) constructs or curates an ITEM SET with stated selection or generation "
            "criteria; (b) designs an ORIGINAL GRADING INSTRUMENT — a new rubric, "
            "autograder, or LLM-judge system, including one validated against human "
            "raters as part of the paper; (c) designs an ORIGINAL SCORING PROTOCOL or "
            "METRIC VARIANT — a new adherence checklist, severity coding scheme, or "
            "adapted composite metric. Naming, release, and full specification are NOT "
            "required. "
            "Evaluation study: paper evaluates existing models on existing benchmarks / "
            "instruments / protocols without building any of the three above. Prompt "
            "engineering alone = Evaluation study. "
            "Model development: fine-tuning, RLHF, or architectural modification. "
            "Prompt-only guardrail / classifier systems built on an existing generative "
            "LLM are NOT Model development. "
            "PRIORITY RULE — when multiple categories apply, prefer: Benchmark "
            "development > Model development > Evaluation study. A paper that both "
            "develops a benchmark AND evaluates existing models on it (SHIELD-style: "
            "new benchmark + baseline rates on 5 LLMs) → Benchmark development. A "
            "paper that fine-tunes a model AND evaluates it → Model development. Only "
            "papers with no new benchmark and no model changes are Evaluation study. "
            "WORKED EXAMPLE: a paper writes 30 clinical consultation templates against "
            "stated inclusion criteria, has GPT-4 and Claude complete each one, and "
            "scores completions with a new 5-point adherence rubric. Even without a "
            "benchmark name → Benchmark development."
        ),
    )
    mh_scope: MHScope = Field(
        ...,
        description=(
            "Whether mental health is the SOLE focus of the paper or one of several "
            "domains covered. Populated after applying the relevance gate. "
            "MH only: every arm is MH-relevant; no non-MH content was excluded at the "
            "gate. Typical of dedicated MH benchmark papers, MH-specific chatbot "
            "evaluations. "
            "Mixed — MH is a substantial domain: the paper covers multiple domains "
            "(general medicine including MH, multi-specialty clinical evaluations, "
            "broad LLM benchmarks with MH as one section) AND MH is a substantial "
            "portion — a distinct section, a named domain, ~20-25%+ of results. "
            "Mixed — MH is a minor domain: paper primarily about a non-MH topic "
            "(general medical exam, multi-domain benchmark) with MH as a small subset. "
            "Included only when results are disaggregated for the MH subset."
        ),
    )
    publication_year: Optional[int] = Field(None, description="Year the paper was published.")
    journal_source: Optional[str] = Field(
        None,
        description=(
            "Publication venue. For preprints, use the server name: 'arXiv', 'medRxiv', "
            "'bioRxiv', 'PsyArXiv'. For peer-reviewed articles, the journal name. "
            "For conference papers, the conference name (e.g., 'NeurIPS 2024', 'EMNLP 2023'). "
            "Null if unclear."
        ),
    )
    journal_source_type: JournalSourceType = Field(
        ...,
        description=(
            "Category of publication venue. "
            "IMPORTANT: many arXiv / preprint uploads are actually conference papers. "
            "Before defaulting to Preprint, check for conference signals — author-block "
            "cites the conference ('To appear at NeurIPS 2024', 'Accepted at EMNLP 2023'), "
            "camera-ready formatting, DOI pointing to a conference, or paper explicitly "
            "names a conference. If ANY conference signal is present → Conference "
            "proceeding, not Preprint. Preprint is ONLY for uploads with no evidence of "
            "formal venue publication. "
            "Preprint: arXiv, medRxiv, bioRxiv, PsyArXiv, or other preprint server, with "
            "NO conference or journal affiliation visible. "
            "Conference proceeding: NeurIPS, EMNLP, ACL, CHI, AMIA, etc. — includes "
            "conference papers hosted on preprint servers if conference affiliation is "
            "stated. "
            "Peer reviewed: journal article that went through peer review. "
            "Other: thesis, technical report, book chapter, etc. — include a brief inline "
            "specifier when possible."
        ),
    )
    system_tasks: List[SystemTaskType] = Field(
        ...,
        description=(
            "System tasks performed by the SYSTEM UNDER EVALUATION — the model(s) whose "
            "performance the paper measures and reports as results. "
            "IMPORTANT: distinguish evaluated systems from models used in the evaluation "
            "methodology (LLM-as-judge, annotators, raters, data generators, score assigners). "
            "System tasks describe ONLY what the evaluated system does. Never include tasks "
            "performed by judge/annotator models — those methodology roles do not contribute "
            "task labels to the evaluated system's record. "
            "TAG THE FEWEST TASKS across the paper (deduplicated) that fully describe what "
            "the evaluated systems are doing. Do not add tags for peripheral behaviors. "
            "MCQ vs CLASSIFICATION — THE POSED-QUESTION TEST (added 2026-08-29.10). Multiple-"
            "choice answering is ALWAYS 'Question-answering', never 'Classification / score "
            "prediction', regardless of subject matter. If the item presents the model with a "
            "QUESTION plus a fixed set of candidate answers, it is Question-answering. If the "
            "model is handed MATERIAL and asked to assign a label or score from a schema it "
            "was told about but that is not offered as options on the item, it is "
            "Classification / score prediction. Format, not topic: a diagnostic MCQ over a "
            "clinical vignette is still Question-answering, because the model picks among "
            "presented options. WORKED PAIR: MAGneT scores CounselingBench MCQs -> "
            "Question-answering (correct). MentalBench asks 'What is the most likely "
            "diagnosis? A/B/C/D' over a vignette -> Question-answering (was coded "
            "Classification; this is the corrected value). CONTRAST, both stay Classification: "
            "WundtGPT assigns one of nine emotion labels to an utterance with no options "
            "presented; Kumar assigns MITI Likert scores to a summary. Those are the "
            "LLM-as-annotator family, which the constructs vocabulary already treats "
            "separately (Psychotherapy process annotation, Stigma and harmful-content "
            "detection). RATIONALE: MCQ answering is common in this corpus, so splitting it "
            "across two codes empties both columns; reserving Classification for "
            "annotation-of-material makes the field separate two genuinely different setups. "
            "The MCQ format itself is already carried by input_formats. "
            "Classification / score prediction: covers both DISCRETE label/tier assignment "
            "scored by exact-match / F1 (severity tier, diagnosis, risk category) AND "
            "CONTINUOUS numeric prediction scored by RMSE / MAE / CCC / correlation (PHQ-8 "
            "continuous 0-24, BFI-10 Likert items, well-being scale totals). Both go here — "
            "record the discrete-vs-continuous distinction and specific scoring metric in "
            "scoring_procedures. If a paper does both on the same input, list Classification "
            "/ score prediction once. "
            "EXCLUSION: Classification / score prediction does NOT cover judgment-about-"
            "another-party's-performance. When the evaluated system is asked to grade, "
            "rate, judge, or score another system's or a human's output, that is "
            "Evaluation/judging. Classification is about assigning a label to an input; "
            "Evaluation/judging is about assessing a performance. "
            "Evaluation/judging: the evaluated system is being scored on how well it grades, "
            "rates, or assesses another party's outputs (LLM-as-judge validation studies, "
            "autograder evaluations). Do NOT tag when a judge is used only as evaluation "
            "methodology to score another system's outputs. "
            "PREEMPTION IS PER-SYSTEM, NOT PER-STUDY: when Evaluation/judging applies to "
            "a system, do not also tag Classification / score prediction or Text/response "
            "generation FOR THAT SAME SYSTEM'S ROLE — a judge emitting an integer rubric "
            "rating is Evaluation/judging alone. But this field aggregates across the "
            "paper's arms, so a STUDY may carry Evaluation/judging ALONGSIDE other tasks "
            "performed by DIFFERENT systems: a paper that scores counsellor LLMs on "
            "generated dialogue AND validates its own LLM judge against human ratings has "
            "BOTH Text/response generation AND Evaluation/judging. Record every task any "
            "evaluated system performs. "
            "WHEN DOES A JUDGE COUNT AT ALL: only when the judge is ITSELF EVALUATED — the "
            "paper reports its agreement with human raters, its correlation with expert "
            "scores, or its accuracy against a labelled standard. An LLM judge used purely "
            "as apparatus, whose own quality is never scored, is methodology: do NOT record "
            "Evaluation/judging and do NOT list 'LLM as judge/evaluator' in systems_tested. "
            "Other includes agentic task execution / tool use (multi-step planning "
            "workflows). Use Other with a brief 1-2 sentence description in "
            "abstraction_notes explaining the task and why no other category fits — do not "
            "use Other as a default. "
            "OUT OF SCOPE — do NOT record: qualitative coding / thematic analysis "
            "(inductive code development, excerpt extraction, theme synthesis); text / "
            "information extraction tasks (pulling entities, spans, structured fields from "
            "text). These are qualitative research or NLP methodology outside our review's "
            "clinical-capability scope. If a paper's only evaluation is qualitative coding "
            "or text extraction, exclude the paper. "
            "Select all that apply across the paper, deduplicated."
        ),
    )
    mental_health_domains: List[str] = Field(
        ...,
        description=(
            "Mental health domain(s) the LLM is EVALUATED on, deduplicated. The vocabulary is "
            "enforced: any value outside it, other than an inline 'Other (specifier)', is rejected. "
            "Include a domain ONLY if the paper reports quantitative results for the LLM's "
            "performance in that domain — never from the Introduction, Related Work, Discussion, or "
            "proposed future applications. GENERAL-CODES RULE: 'General mental health' and 'General "
            "psychology' are for use ONLY when no specific condition or context is identifiable, and "
            "NEVER alongside a specific domain code. Category boundaries, multi-domain-instrument "
            "handling, and the construct-versus-domain distinctions (Misinformation vs Guideline "
            "adherence; Bias vs Fairness / equity; Cognitive distortion vs Diagnostic accuracy; "
            "Delusional disorder vs LLM delusion confirmation) are in the MENTAL HEALTH DOMAINS "
            "section of the extraction guide."
        ),
    )
    evaluation_constructs_described: List[str] = Field(
        ...,
        description=(
            "Evaluation constructs AS DESCRIBED BY THE AUTHORS in their own words — "
            "dimensions or criteria they name in the paper. Short phrases, not overly "
            "detailed. Paired with evaluation_constructs_categories (the controlled "
            "vocabulary mapping) to let reviewers audit categorization decisions. "
            "E.g. ['Guidance', 'Informativeness', 'Interpretation', 'Empathy', "
            "'Helpfulness', 'Safety']; ['affective attitude', 'burden', 'ethicality', "
            "'coherence (Sekhon TFA)', 'opportunity cost', 'perceived effectiveness', "
            "'hallucination extent']. Preserve the paper's own terminology — do not "
            "translate to controlled vocabulary here. Deduplicate across arms."
        ),
    )
    evaluation_constructs_categories: List[str] = Field(
        ...,
        description=(
            "Evaluation construct(s) the paper REPORTS QUANTITATIVE RESULTS FOR, mapped to the "
            "controlled vocabulary. The vocabulary is enforced: any value outside it, other than an "
            "inline 'Other (specifier)', is rejected. FULL DEFINITIONS, the Object Test, the "
            "Reference-Standard Test, the five procedural rules, and the referral routing rule are in "
            "the EVALUATION CONSTRUCTS section of the extraction guide. Apply them there; this "
            "description states only the invariants. (1) EVIDENCE. Every construct must correspond to "
            "a reported quantitative result. Terminology in the title, abstract, taxonomy, Related "
            "Work, or Discussion is not evidence of measurement. (2) TEST PRECEDENCE. Apply the "
            "OBJECT TEST first — is the construct scored on the INPUT the model was given, or the "
            "OUTPUT it produced? Only when both candidates score the same object does the "
            "REFERENCE-STANDARD TEST decide. Where the two tests point different ways, the OBJECT "
            "TEST WINS. Worked case: MITI's Empathy global rating scores the output (Object Test → "
            "Empathy) but comes from a normative manual (Reference-Standard Test → Therapeutic "
            "technique fidelity). Object Test wins only if the paper reports that subscale "
            "SEPARATELY; if it is folded into an overall MITI fidelity score, the scored object is "
            "the session, not the response, and the answer is Therapeutic technique fidelity. (3) ONE "
            "PARADIGM, ONE ENTRY. If two constructs would draw on the same reported result, at most "
            "one is correct. (4) ONE INSTRUMENT, ONE CONSTRUCT. Each validated instrument is one "
            "paradigm mapped to a single construct — its closest controlled term, or 'Other "
            "(instrument name)'. Do NOT split an instrument's subscales into separate constructs, and "
            "do NOT collapse multiple distinct instruments into one best-fit entry. A paper using "
            "CTRS, WAI, and PANAS yields THREE constructs, one per instrument — not eleven subscale "
            "entries and not one list. (5) BARE AUTOMATED METRICS. When the only construct-relevant "
            "evaluation is one or more bare automated metrics against gold responses (BERTScore, "
            "perplexity, ROUGE) with no qualitative dimensions, map to a SINGLE holistic construct, "
            "normally Response quality — not several stretched near-mappings. The metrics belong in "
            "scoring_procedures. (6) DIRECT NAME MATCHES TAKE PRECEDENCE. When a paper's own "
            "dimension name appears verbatim in the vocabulary and collides with a default mapping — "
            "the paper reports both 'Guidance' and 'Helpfulness' as separate dimensions, and Guidance "
            "normally maps to Helpfulness — map the direct match first, then find an alternative for "
            "the other. Do not force both into one term. (7) RESPONSE QUALITY IS RESIDUAL. Use it for "
            "a holistic rating the paper does NOT break into named dimensions. An ARITHMETIC MEAN OR "
            "COMPOSITE OF DIMENSIONS ALREADY MAPPED IS NOT A DISTINCT RESULT — do not add Response "
            "quality for it. Add it alongside specific constructs only when an overall score is "
            "separately elicited from raters or otherwise measured independently of the named "
            "dimensions. (8) EXCLUSIONS. Never record statistical or calibration metrics (F1, AUROC, "
            "ECE, Brier, coverage), robustness, efficiency, reproducibility, or judge-reliability "
            "metrics. Constructs must not duplicate system_tasks. Out-of-scope author dimensions "
            "(response coherence, relevance, semantic similarity, usability, engagement, response "
            "speed, user-reported trust / credibility / satisfaction / acceptance) go in "
            "evaluation_constructs_described and are NOT mapped here — a _described list longer than "
            "this one is expected and is not an error."
        ),
    )
    primary_construct: str = Field(
        ...,
        description=(
            "THE SINGLE construct this paper is primarily about — the one a reader scanning the "
            "corpus would say the paper measures. Analysis runs on this column; "
            "evaluation_constructs_categories keeps the full detail. MUST be one of the values in "
            "evaluation_constructs_categories. If that list has one entry, this is that entry. "
            "SELECTION ORDER, applied in sequence until one rule decides: (1) HEADLINE RESULT. The "
            "construct behind the finding the abstract leads with, or the result reported first in "
            "the results section. THE HEADLINE IS THE NUMBER REPORTED, NOT THE FRAMING THAT "
            "MOTIVATES IT (added 2026-08-29.10). Titles, motivations and contribution claims are "
            "not results. If the reported headline is a COMPOSITE of several dimensions, the "
            "primary is what that composite measures, and a construct carried by only one "
            "sub-dimension can never be primary. WORKED EXAMPLE: Hasan is titled and motivated "
            "around culturally-grounded knowledge, but cultural appropriateness is one "
            "parenthetical qualifier inside one of five human dimensions, and the headline number "
            "is the five-dimension mean improving under KG grounding. Cultural sensitivity belongs "
            "in the categories list; it is NOT the primary. (2) ANCHORING INSTRUMENT. If one validated instrument anchors the "
            "evaluation, take the construct that instrument maps to — CTRS or MITI anchoring a "
            "counselling evaluation gives Therapeutic technique fidelity even when secondary "
            "dimensions map elsewhere. (3) WEIGHT OF EVIDENCE. The construct with the most separately "
            "reported quantitative results behind it. (4) SPECIFICITY. Never choose 'Response "
            "quality' or an 'Other (specifier)' entry when a specific named construct is available; "
            "residual and catch-all terms lose to named ones. If two constructs remain genuinely tied "
            "after all four rules, pick either, flag primary_construct in abstraction_flags, and name "
            "the alternative in abstraction_notes."
        ),
    )
    systems_tested: List[SystemTestedType] = Field(
        ...,
        description="All system-tested types evaluated across the paper, deduplicated.",
    )
    evaluated_output_types: List[EvaluatedOutputType] = Field(
        ...,
        description=(
            "All evaluated-output types across the paper's arms, deduplicated. What the "
            "evaluated system OUTPUTS: Generated text (open-ended text judged on content/"
            "quality/safety), Label or class (discrete categorical output scored by exact "
            "match / F1 / accuracy), Score or rating (numeric or ordinal score emitted by "
            "the model, scored by RMSE / MAE / correlation), Mixed (arm combines two or "
            "more output types). Different from system_tasks — a QA task can be Generated "
            "text (free-text answers) or Label or class (MCQ options) with different "
            "scoring machinery."
        ),
    )
    input_formats: List[InputFormatType] = Field(
        ...,
        description=(
            "All input formats used across the paper, deduplicated. Classify by NATIVE form, "
            "not by prompt serialization. Use 'Other (specify)' rather than the nearest-sounding "
            "category."
        ),
    )
    input_provenance_types: List[InputProvenance] = Field(
        ...,
        description=(
            "WHO ASSEMBLED the input item set, deduplicated across the paper. This is one of two "
            "orthogonal questions about the inputs; the other is input_reality, which asks what the "
            "material IS. Answer them independently — all four combinations occur, and neither answer "
            "constrains the other. Third-party: items assembled by other researchers — established "
            "benchmarks, published datasets, prior-work corpora (DAIC-WOZ, ESConv, PsyQA, "
            "CounselChat, USMLE, PRITE, MRCPsych, MedQA, Dreaddit, EmpatheticDialogues, CLPsych). A "
            "subset of a third-party benchmark is still Third-party, and so is a vignette reproduced "
            "from an earlier paper. Author-created: items assembled by the AUTHORS of this paper — "
            "vignettes they wrote, IRB data they collected, inputs they generated with an LLM, data "
            "they scraped and curated, questions they wrote ad hoc. Release status does not change "
            "this: an author-created dataset the authors release is still Author-created. Mixed: use "
            "ONLY for a single arm drawing from both sources inseparably. A paper with one "
            "Third-party arm and one Author-created arm lists BOTH values, not Mixed. Item release is "
            "a separate question again, captured in input_availabilities."
        ),
    )
    input_availabilities: List[InputAvailability] = Field(
        ...,
        description=(
            "Whether another investigator could obtain or reconstruct the evaluation "
            "ITEMS themselves, deduplicated across arms. Judge item access only. "
            "Publicly released: items downloadable without gate or request. "
            "Available on request: items obtainable via author request, DUA, IRB "
            "registration. "
            "Fully specified in paper: every item reproduced in text, tables, figures, "
            "or appendix. "
            "Method reproducible, items unavailable: procedure released but items "
            "themselves (e.g. PHI clinical records, proprietary transcripts) cannot be "
            "obtained. "
            "Partially specified: illustrative items shown but full set not recoverable. "
            "Not available: neither items nor reconstructible procedure reported. "
            "DEFAULT AND EVIDENCE RULE (added 2026-08-29.11). 'Not available' is the "
            "DEFAULT. Silence is not availability: if the paper contains no repository "
            "link, no data-availability statement, and no sentence offering the items, the "
            "answer is 'Not available' and no inference is permitted from the fact that "
            "the authors seem cooperative, the data seem shareable, or similar work is "
            "usually released. ANY value other than 'Not available' requires POSITIVE "
            "EVIDENCE quoted or cited in abstraction_notes — a URL, a named repository, a "
            "data-availability section, or the sentence offering access. In particular "
            "'Available on request' requires the paper to actually SAY the items are "
            "available on request; it is not the polite default for unreleased data. "
            "WHY: across three identical runs this field flipped Hasan between 'Available "
            "on request' and 'Not available', and the Hasan paper says nothing whatever "
            "about availability — the non-default value was invented, not read. "
            "Replaces the older input_reproducibility field."
        ),
    )
    input_determinism: List[InputDeterminism] = Field(
        ...,
        description=(
            "WHAT GENERATES THE VARIATION in the evaluation inputs, deduplicated across "
            "the paper's INCLUDED arms. Renamed from input_standardizations 2026-08-29.11 "
            "because that name asked a DIFFERENT question (whether all systems face the "
            "same inputs). That question is NOT recorded by this tool — see the note at "
            "the end of this description. "
            "VALUES ARE NON-EXCLUSIVE — record every mechanism that applies. The former "
            "'PRECEDENCE OVER ITERATIVE' rule, which forced a single pick, is DELETED: it "
            "was the direct cause of this field's instability, because simulation papers "
            "are genuinely several of these at once. "
            "Fixed: items are determined BEFORE the evaluation begins and do not change "
            "during it. Provenance is irrelevant (third-party, author-created and mixed "
            "sources can all be Fixed). Prompt variants over a fixed item set are still "
            "Fixed. Single-system papers can be Fixed. "
            "Stochastic: inputs are drawn or generated fresh per trial or per run — "
            "GENERATION AT CONSTRUCTION TIME IS NOT STOCHASTICITY (added 2026-08-29.18). "
            "The test is whether inputs are REGENERATED WHEN A NEW SYSTEM IS BENCHMARKED, "
            "not whether generation happened at all. A synthetic corpus that was generated "
            "once, frozen, and reused unchanged for every system is Fixed and ONLY Fixed, "
            "however it was produced. CONTRAST: MentalBench generated 24,750 cases once and "
            "froze them — every model sees the identical set — so it is Fixed alone; coding "
            "it Stochastic because the cases are LLM-generated is an error observed in "
            "testing. MindEval keeps a fixed pool of 50 patient profiles but generates a "
            "fresh set of interactions each time a system is benchmarked, so it is Fixed AND "
            "Stochastic AND Dynamic. Ask: if I benchmark a new model tomorrow, does it face "
            "the same items? Yes -> Fixed. "
            "LLM-generated scenarios, random corpus sampling without a pinned sample, ad "
            "hoc constructed prompts. "
            "Dynamic: later inputs depend on the model's OWN earlier outputs — multi-turn "
            "interactive beyond the opening, agentic loops, self-play. "
            "Live: inputs come from real users of a deployed system and drift outside the "
            "investigators' control. "
            "Mixed or unclear: the paper does not report enough to tell. Use sparingly; it "
            "is not a substitute for listing two applicable values. "
            "WORKED EXAMPLE (MindEval) — THREE values, all true: Fixed (a pinned pool of 50 "
            "patient profiles, reused for every system), Stochastic (a fresh set of "
            "interactions is generated each time a system is benchmarked), Dynamic (within "
            "an interaction, later turns condition on earlier ones). Under the old "
            "precedence rule the extractor had to choose one, and chose differently on "
            "different runs. "
            "WHAT THIS FIELD DOES AND DOES NOT SUPPORT. Fixed ALONE implies the inputs are "
            "reproducible across runs — that inference is safe. Fixed does NOT imply the "
            "compared systems were scored on the SAME items, and this tool does not record "
            "that. Systems may be scored on different subsets, on model-specific prompt "
            "variants over one item set (still coded Fixed), or in separate arms this "
            "rollup collapses; and single-system papers can be Fixed with no comparison at "
            "all. Conversely not-Fixed does not imply the systems faced different items — "
            "MindEval regenerates every interaction yet every system faces the identical "
            "pool of 50 profiles. Do not use this field to support a claim about "
            "cross-system comparability in either direction."
        ),
    )
    parent_benchmarks: Optional[List[str]] = Field(
        None,
        description=(
            "Names of pre-existing EVALUATION BENCHMARKS (item sets) that any benchmark "
            "in this paper reuses as a composite or derivation, deduplicated across the "
            "paper. Populated ONLY when a benchmark used in an in-scope arm derives from "
            "or composites items drawn from another named evaluation benchmark. Direct "
            "reuse of an existing benchmark (or a subset of one) leaves this None. "
            "RESERVED FOR EVALUATION ITEM SETS. Do NOT include: "
            "(a) validated clinical instruments (PHQ-9, GAD-7, C-SSRS, WAI, CTRS, etc.) — "
            "these are scoring instruments or reference standards, not parent benchmarks; "
            "(b) diagnostic taxonomies or classification systems (DSM-5, ICD-10, ICD-11, "
            "RDoC) — these are frameworks the benchmark is built AGAINST, not parents; "
            "(c) evaluation frameworks or theoretical models (Sekhon TFA, TAM, SUS, HBM, "
            "Bloom's taxonomy) — these are rubric frameworks, not item sources; "
            "(d) base foundation models, checkpoints, or training corpora — those belong "
            "in models_tested or in the model's provenance section, not here; "
            "(e) benchmarks cited only in Related Work or Discussion as comparisons — "
            "the parent must have actually contributed items to this paper's benchmark; "
            "(f) benchmarks the paper's benchmark is merely INSPIRED BY or CONCEPTUALLY "
            "similar to — the parent must have contributed actual items. "
            "MULTI-LEVEL CHAINS: if benchmark A derives from B which derives from C, "
            "list only IMMEDIATE parent B here. Note the deeper chain in abstraction_notes. "
            "DERIVED-FROM vs USED-DIRECTLY: language matters. 'Composed of items sampled "
            "from X' or 'Built by adapting items from X' → X is a parent. 'Uses X' or "
            "'Evaluated on X' with no modification → X IS the input, not a parent (goes "
            "in benchmark_names, not parent_benchmarks). Hedged language like 'inspired by' "
            "or 'similar to' → NOT a parent. "
            "Use canonical names to enable cross-study aggregation (SafetyBench, TrustGPT, "
            "MedSafetyBench, DAIC-WOZ, ESConv, PsyQA, CounselChat, USMLE question banks, "
            "etc.). "
            "SEEDED GENERATION IS DERIVATION (added 2026-08-29.10). When this paper's items are "
            "GENERATED from seeds, profiles, cases or prompts taken from another named benchmark, "
            "that benchmark is a parent, even though every resulting item is new text. The test is "
            "item-level traceability: can each new item be traced back to a specific item in the "
            "source set? WORKED EXAMPLE: MAGneT generates synthetic counselling sessions from 150 "
            "client intake profiles taken from CACTUS, each session anchored to one profile — "
            "CACTUS is a parent AND, being an evaluation set the study involves, also belongs in "
            "benchmark_names. CONTRASTING NON-EXAMPLES: MindEval's attribute pool is 'inspired by' "
            "Patient-psi with no items carried over (parent = None, per the hedged-language rule "
            "above); MentalBench builds MentalKG from DSM-5 text, which is a taxonomy and is "
            "excluded by (b) above (parent = None). "
            "Example: XTRUST-MH is a composite of SafetyBench + TrustGPT + MedSafetyBench "
            "→ parent_benchmarks = ['SafetyBench', 'TrustGPT', 'MedSafetyBench']; "
            "input_provenance_types still includes 'Author-created' because the composite "
            "is new."
            "CONVENTION: use null (not an empty list) when this field does not apply to the paper. An "
            "empty list is never a valid value for this field."
        ),
    )
    populations: List[str] = Field(
        ...,
        description=(
            "All populations the inputs represent across the paper, deduplicated. "
            "High-level, population-focused. E.g. 'adults with depression', "
            "'psychiatric outpatients', 'mental health clinicians', 'general public'. "
            "Do not indicate real vs. synthetic. "
            "Use 'Not applicable' ONLY when the input has no represented population — pure "
            "knowledge or factual questions ('Which SSRI has the shortest half-life?', "
            "'Define bipolar disorder'), definitions, terminology quizzes, or generic prompts "
            "where the LLM is answering about FACTS rather than about a person or population. "
            "Format is not the deciding factor — what matters is what the LLM is being asked "
            "to reason about. If the input consists of case vignettes, patient scenarios, "
            "symptom presentations, or clinical descriptions — EVEN when drawn from exam "
            "banks, textbooks, or casebooks — the population is who those cases represent "
            "(e.g., 'adult psychiatric patients as depicted in authoritative textbooks and "
            "casebooks', 'adolescents with anxiety presenting to primary care')."
        ),
    )
    output_audiences: List[OutputAudience] = Field(
        ...,
        description=(
            "All target audiences for the LLM's outputs across the paper, deduplicated. "
            "Who the LLM's response is INTENDED FOR — distinct from populations (who "
            "inputs represent). "
            "Patient / Consumer: lay user, patient, help-seeker, general consumer "
            "(chatbot user, help-seeking letter response, self-help content). "
            "Provider: healthcare provider, clinician, physician, therapist, licensed "
            "practitioner, OR trainee in a provider-oriented role (medical student, "
            "resident, counselor-in-training). Covers clinical decision support, "
            "differential diagnosis, treatment recommendation, chart review, exam-"
            "answering for provider trainees, and training-scenario content. "
            "Researcher: LLM output serves research (data annotation, coding, "
            "classification, benchmark scoring). "
            "Mixed: use as a value only if a single arm targets multiple audiences. "
            "Not applicable: LLM capability testing without a specific intended audience "
            "(pure knowledge testing, exam-answering scored on correctness). "
            "Deduplicate across arms — a paper with provider-facing and patient-facing "
            "arms lists both."
        ),
    )
    input_reality: List[InputReality] = Field(
        ...,
        description=(
            "What the input material IS, deduplicated across the paper. This field asks about the"
            "NATURE OF THE DATA and is deliberately orthogonal to input_provenance_types, which asks"
            "WHO ASSEMBLED IT. The two answers are independent: authors can assemble real data"
            "(Author-created + Real), and a third-party benchmark can consist of LLM-generated"
            "vignettes (Third-party + Synthetic — LLM-generated). Never reason about authorship here."
            "Real: material that arose from actual human activity outside the study — clinical"
            "records, therapy or hotline transcripts, social-media posts, forum threads, exam"
            "question banks, published corpora of naturally occurring text. Synthetic — human-"
            "written: material a person wrote for research or assessment purposes rather than in the"
            "course of real life — clinician-authored vignettes, researcher-written prompts,"
            "constructed case scenarios, hand-built question sets. This applies whether the person"
            "who wrote it was an author of this paper or of a prior one; a vignette taken from an"
            "earlier publication and reproduced here is Synthetic — human-written, with"
            "input_provenance_types = Third-party. Synthetic — LLM-generated: material produced by a"
            "language model or simulator — LLM-generated patient scenarios, simulator dialogue turns,"
            "model-authored vignettes. Mixed: a single arm combines two of the above and they cannot"
            "be cleanly separated. Use separate list entries, not Mixed, when different arms have"
            "different answers. Not reported: the paper does not say."
        ),
    )
    input_languages: List[str] = Field(
        ...,
        description=(
            "Language(s) of input data across the paper, deduplicated. Canonical English "
            "names: English, Mandarin (not Chinese), Standard Arabic if specified "
            "(otherwise Arabic), Spanish, French, German, Hindi, Japanese, Korean, "
            "Portuguese, etc. A multilingual benchmark lists all languages. Use "
            "['Not reported'] if language is not specified. Do not infer language from "
            "author affiliation."
        ),
    )
    conversation_types: ConversationType = Field(
        ...,
        description=(
            "How stimulus is structured and how model outputs relate to prior outputs, "
            "rolled up across the paper. "
            "Single-shot: the model produces ONE scored output per item AND its own prior "
            "outputs never appear in its input. Covers non-dialogue stimuli (MCQ, "
            "vignette, post, document, standalone question) AND dialogue stimuli where "
            "the model answers once (dialogue classification / scoring, next-response "
            "generation on gold history). Whether the stimulus is a dialogue does NOT "
            "matter here — that is carried by input_formats and system_tasks. "
            "Multi-turn interactive: model produces outputs at multiple points in an "
            "evolving exchange; later turns are conditioned on the model's own earlier "
            "outputs (with real users, scripted interlocutors, or LLM seeker-simulators; "
            "LLM-vs-LLM self-play qualifies). "
            "Mixed: paper includes arms of more than one type. "
            "Not applicable: LLM does not produce outputs in the paper (e.g. benchmark-"
            "only papers with no reported model results). "
            "Distinguishing test between Single-shot and Multi-turn "
            "interactive: does the model's own earlier output feed back into its later "
            "input? If yes → Multi-turn interactive; if no → Single-shot."
        ),
    )
    dataset_purpose: DatasetPurpose = Field(
        ...,
        description=(
            "What the paper's evaluation data is USED FOR, rolled up across the study. "
            "Distinct from type_of_study, which records what the paper contributes; this "
            "field records what the data does. A Model development paper can fine-tune on "
            "one corpus and evaluate on a third-party benchmark, and an Evaluation study "
            "can build data it only ever scores against. "
            "'Evaluation only': the data exists to score systems and is never used to "
            "update model weights. "
            "'Training or tuning only': the data is used to fine-tune, distil, RLHF, or "
            "continue-pretrain a model, and no arm scores systems on it. TRAINING IS "
            "BROADER THAN FINE-TUNING — distillation, preference tuning and continued "
            "pretraining all count. "
            "'Both — held-out split reported': some data trains and some evaluates, AND the "
            "paper describes a held-out split, test set, or other separation. "
            "'Both — split not reported': some data trains and some evaluates, and the "
            "paper does not describe a separation. "
            "'Not applicable': no evaluation data in the paper (e.g. position or survey "
            "papers). "
            "FEW-SHOT EXEMPLARS ARE NOT TRAINING. Items placed in a prompt as examples are "
            "prompt construction, not weight updates. MindEval draws 5 annotated "
            "interactions as judge exemplars and is 'Evaluation only'. In-context learning, "
            "retrieval augmentation and RAG corpora are likewise NOT training. "
            "DEFAULT AND EVIDENCE RULE. Between the two 'Both' values the default is 'split "
            "not reported'. Choosing 'held-out split reported' requires POSITIVE EVIDENCE "
            "quoted or cited in abstraction_notes — the sentence naming the split, the test "
            "set, or the separation. Do NOT infer a split from the fact that splitting is "
            "normal practice, that the authors are careful, or that results look clean. "
            "This value is a claim about what the paper REPORTS, not about what the authors "
            "did; 'split not reported' is a reporting-quality observation, not an "
            "accusation of leakage. "
            "DERIVATION REQUIRED FOR EITHER 'Both' VALUE: name in abstraction_notes which "
            "dataset served which purpose. MAGneT is the pattern — its own generated "
            "sessions train Llama-3-8B, CounselingBench evaluates it."
        ),
    )
    reference_standard_type: List[ReferenceStandardType] = Field(
        ...,
        description=(
            "Type(s) of reference standard used across the paper. A paper may have DIFFERENT "
            "types across arms — list all that apply, deduplicated. "
            ""
            "Pick per arm by applying this test IN ORDER — stop at the first match: "
            ""
            "AN LLM APPLYING A RUBRIC IS NEVER THE REFERENCE STANDARD (added 2026-08-29.15). "
            "Run the test below per ARM. If an arm is scored by an LLM judge and no human "
            "or ground-truth comparator exists FOR THAT ARM, it falls through to (4) and the "
            "arm is 'None — rubric-only scoring'. The judge is the scoring mechanism and "
            "belongs in scoring_procedures; it is not a comparator. "
            "READ THE VALUE CORRECTLY: 'None' scopes the COMPARATOR only. It does not mean "
            "nothing was measured — a study with neither a comparator nor a well-defined "
            "rubric would not have passed screening. The value asserts two things at once: "
            "no human or ground-truth comparator, AND a defined rubric was applied. "
            "IF THE JUDGE WAS VALIDATED AGAINST HUMANS, RECORD BOTH ARMS. The validation "
            "arm takes its own type from the test below; the benchmarking arm the judge "
            "actually scored is still 'None — rubric-only scoring'. MindEval is the "
            "pattern: 4 psychologists rate 20 interactions in the meta-evaluation "
            "(Expert/clinician ratings) while Claude-4.5-Sonnet alone scores the 600 "
            "interactions behind every headline number (None — rubric-only scoring). "
            "Recording only the first makes it read as though experts backed results they "
            "never saw. CACTUS is the same shape. "
            "(1) Is the output matched against a defined correct answer, target, or validated "
            "instrument-as-target? -> 'Ground-truth reference'. Any rubric here is only the "
            "scoring mechanism (goes in scoring_procedures). "
            ""
            "(2) If no correct answer: are QUALIFIED EXPERTS (clinicians, licensed "
            "professionals, domain experts) applying a validated framework or calibrated "
            "judgment as the comparator? -> 'Expert/clinician ratings'. "
            ""
            "AN LLM APPLYING A RUBRIC IS NEVER THE REFERENCE STANDARD (added 2026-08-29.15). "
            "A judge model is not an expert, not a trained annotator, and not a correct "
            "answer, so an LLM-scored arm falls through every step to 'None — rubric-only "
            "scoring'. Apply the test PER ARM and list every arm's result: a paper whose "
            "headline results are LLM-judged but which separately has humans rate a subset "
            "carries BOTH 'None — rubric-only scoring' and 'Expert/clinician ratings'. "
            "MindEval is exactly this: 4 psychologists rate 20 interactions in its "
            "meta-evaluation, while all 12 models in the main results are scored by "
            "Claude-4.5-Sonnet alone. Recording only the expert arm reads as though experts "
            "backed the headline numbers. "
            "READ THE VALUE NAME CAREFULLY. 'None — rubric-only scoring' does NOT mean the "
            "LLM is the standard, and does NOT mean no scoring happened. It records two "
            "things at once: (a) NO human or ground-truth comparator adjudicated these "
            "particular scores, and (b) a well-defined rubric WAS applied. Both halves "
            "matter — (b) is what keeps such a study inside the review's inclusion "
            "criteria, which require either a reference standard or a well-defined rubric. "
            "An arm with neither is not includable. "
            "MIXED RATER POOLS TAKE BOTH TYPES (added 2026-08-29.19). If one arm's raters "
            "include BOTH qualified experts and trained non-experts — '3 PhD-student "
            "annotators and 1 domain expert', 'graduate students supervised by a "
            "psychiatrist' — record Expert/clinician ratings AND Trained annotator ratings. "
            "Do not pick the more senior label; both rater types are present and both are "
            "informative. This was the single unstable reference_standard_type cell across 20 "
            "papers, and the run that listed both was the most accurate. "
            "(3) If not experts: are TRAINED NON-EXPERT annotators (research assistants, "
            "undergraduates, crowdworkers under expert-designed guidelines, coders not "
            "described as clinicians) applying a defined rubric? -> 'Trained annotator ratings'. "
            "Common for social media benchmarks, crowd-labeled data, NLP corpora. "
            ""
            "(4) If none of the above — no ground truth, no independent humans applying the "
            "rubric consistently (including unvalidated LLM-as-judge rubrics), OR human "
            "evaluation is mentioned but no rubric, rater qualifications, or scoring "
            "procedure is disclosed? -> 'None — rubric-only scoring'. This category is the "
            "residual bucket — vague human evaluation ('two evaluators judged responses "
            "satisfactory') with no rubric or qualifications lands here, not in (2) or (3). "
            ""
            "RULES: A rubric is NOT a reference standard by itself — what sits BEHIND it "
            "decides the type. Do NOT default rubric-scored papers to (4): clinician-applied "
            "rubric = (2); trained-coder-applied rubric = (3). Input being a conversation or "
            "document does not create a ground truth — judge what the OUTPUT is compared to. "
            ""
            "Example (Adhikary et al.): ROUGE arm scored against gold summaries = (1); "
            "expert Sekhon-framework arm = (2). Result: ['Ground-truth reference', "
            "'Expert/clinician ratings']. "
            ""
            "Example (LLM judge + expert reference): LLM judge scores generated responses via "
            "similarity rubric against expert-authored reference answers from validated "
            "textbooks. Type = 'Ground-truth reference' — the reference answers are the target. "
            "The LLM judge and similarity rubric are scoring mechanism, not the reference."
        ),
    )
    reference_standard_description: List[str] = Field(
        ...,
        description=(
            "COMPARATOR, NOT STATISTICS COMPUTED OVER IT (added 2026-08-29.15). Each entry "
            "names WHAT AN ARM'S OUTPUTS WERE COMPARED AGAINST. A number computed FROM a "
            "comparison is not a comparator: correlations (Pearson, Spearman, Kendall), "
            "inter-rater agreement, Cohen's or Fleiss's kappa, Gwet's AC2, accuracy against "
            "a majority vote, and averages across raters all belong in scoring_procedures "
            "ONLY. NAMED AUTOMATIC METRICS ARE ALSO NOT COMPARATORS (added 2026-08-29.19): "
            "AlignScore, BERTScore, ROUGE, BLEU, BARTScore, GPT-Score, perplexity and the "
            "like are scoring machinery, not things the outputs were compared against, even "
            "though they carry proper names that read like instruments. OBSERVED ERROR: "
            "TN-Eval listed 'AlignScore used for faithfulness' as a description entry while "
            "also, correctly, recording it in scoring_procedures. "
            "Test: does the line name a person, an answer key, an instrument, or a "
            "corpus (comparator, record it here), or a statistic (does not belong here)? "
            "OBSERVED DUPLICATION: CACTUS carried 'Pearson/Spearman/Kendall correlation of "
            "GPT-4o scores with expert scores' in BOTH fields, and MindEval carried 'average "
            "psychologist score across annotators'. Lissak is the correct pattern — its "
            "kappa and correlations sit in scoring_procedures and are absent here. "
            "All reference standards used across the paper's INCLUDED arms, deduplicated. "
            "High-level descriptions of the label/score types. "
            "E.g. 'Clinician-assigned PHQ-9 scores', 'DSM-5 diagnostic labels', "
            "'Expert consensus ratings', 'Board-exam answer key', 'Gold summaries'. "
            "THE TYPE VALUE GOES IN reference_standard_type, NOT HERE (fixed 2026-08-29.15). "
            "This field previously instructed 'include exactly None — rubric-only scoring' "
            "in the description list, which duplicated a controlled value of "
            "reference_standard_type into a free-text field and let a record satisfy the "
            "instruction WITHOUT adding the value to the type list. Lissak did exactly "
            "that: description item 2 read 'None — rubric-only scoring (for automatic "
            "LLM-judge evaluation arms)' while the type list held only Expert/clinician "
            "and Trained annotator. Instead, DESCRIBE the arm in plain terms — e.g. "
            "'GPT-4o applying the 5-axis rubric, no human backing for these scores' — and "
            "record 'None — rubric-only scoring' in reference_standard_type. "
            "COMPARATORS ONLY, NOT STATISTICS COMPUTED OVER THEM (added 2026-08-29.15). "
            "Each item names WHAT AN ARM'S OUTPUTS WERE COMPARED AGAINST. Numbers computed "
            "FROM a comparison are not comparators: correlations between a judge and human "
            "raters, inter-rater kappa or agreement rates, and averages across annotators "
            "all belong in scoring_procedures and nowhere else. Two live cases, both "
            "duplicated into the wrong field while already correctly present in "
            "scoring_procedures: CACTUS's 'Pearson/Spearman/Kendall correlation of GPT-4o "
            "scores with expert scores' and MindEval's 'Average psychologist score across "
            "annotators'. Lissak is the counter-example done right — its Fleiss's kappa and "
            "Spearman correlations appear in scoring_procedures and are correctly absent "
            "here. TEST: if the line describes a number derived FROM the standard rather "
            "than the standard itself, it is in the wrong field. "
            "RUBRIC QUALIFICATION TEST — when a reference standard is a rubric (i.e. "
            "'None — rubric-only scoring' would be entered), the rubric must pass ALL of: "
            "(a) Independent-panel test: a second, independent panel of raters given the "
            "rubric plus the outputs could produce comparable scores. Rubrics relying on "
            "the original raters' shared unstated understanding fail. "
            "(b) One-construct-per-item test: each rated construct is its own scored item. "
            "A rubric item bundling 'empathy AND clinical accuracy AND coherence' into one "
            "1-5 rating fails — per-construct performance is not recoverable. "
            "(c) Higher-vs-lower test: each item explicitly states what distinguishes a "
            "higher score from a lower score. Numeric anchors alone (1-5 Likert with "
            "endpoints 'poor' and 'excellent') are NOT a rubric. "
            "If the rubric fails any of the three, do NOT list it here — enter 'None "
            "stated'."
            "SENTINEL: when nothing qualifies, use the exact string 'None stated'. Variants ('Not "
            "stated', 'N/A', 'none') are normalised on ingest but should not be produced."
        ),
    )
    # NOTE (2026-08-29.15): the comparator-vs-statistic boundary is stated in the
    # reference_standard_description field above.
    reference_standard_instruments: Optional[List[str]] = Field(
        None,
        description=(
            "Named validated clinical or research instruments, AND named study-specific rubrics that derive from a citable published framework, used as reference standards "
            "across the paper, deduplicated. Instruments like C-SSRS, PHQ-9, PHQ-8, GAD-7, "
            "CAPS-5, HAM-D, MADRS, YMRS, PANSS, WAI, CTRS, MITI, PANAS. "
            "PURPOSE: keep instrument names out of benchmark_names — instruments used to "
            "score LLM outputs are not benchmarks. This field enables downstream analysis "
            "of which validated instruments are used as reference standards across the "
            "review, separately from benchmark inputs. "
            "WHEN TO POPULATE: only when the LLM's outputs are scored against scores or "
            "labels from the instrument, or when raters apply the instrument to evaluate "
            "LLM behavior. If the LLM SEES the scale items as input, the scale belongs to "
            "benchmark_names, not here. "
            "DIAGNOSTIC CRITERIA SETS COUNT, BUT DO NOT CLIMB LINEAGE (added 2026-08-29.12). "
            "Record DSM-5 (or DSM-IV, ICD-10, ICD-11, RDoC) here when the criteria "
            "THEMSELVES are the standard the outputs are judged against — MentalBench "
            "derives its per-item diagnostic labels from DSM-5 criteria formalised in a "
            "knowledge graph, so DSM-5 belongs here. "
            "But record ONLY the standard actually applied. Most named instruments "
            "descend from a criteria set — PHQ-9 and PHQ-8 operationalise DSM major "
            "depression criteria, GAD-7 the GAD criteria, PCL-5 the PTSD criteria, CAPS-5 "
            "likewise — and that ancestry is NEVER recorded. A paper scoring against PHQ-9 "
            "gets 'PHQ-9' and NOT 'DSM-5'. A paper scoring against DSM-5 criteria "
            "directly gets 'DSM-5'. A paper doing both gets both, one for each arm. "
            "TEST: what did the raters or the answer key actually consult? If they applied "
            "a scale, record the scale. If they applied the criteria, record the criteria. "
            "Never both for the same judgement. "
            "This keeps the downstream count of DSM-grounded studies meaningful: without "
            "the rule, nearly every depression paper would count as DSM-based by descent, "
            "and the column would separate nothing. "
            "NAMED RUBRICS GROUNDED IN A PUBLISHED FRAMEWORK ALSO COUNT (widened 2026-08-29.14). "
            "Record a study-specific rubric here when the paper states it DERIVES FROM a "
            "citable published source — professional-body guidelines, a diagnostic manual, "
            "a published scale, or a prior published rubric. Name it as the paper names it "
            "with the source in parentheses: 'MindEval rubric (APA clinical supervision "
            "guidelines)'. MindEval and Lissak both qualify; both were previously null. "
            "THE TEST IS A CITATION, NOT QUALITY. Ask only whether the paper points to a "
            "published source the rubric came from. Do not judge how good, how detailed, "
            "or how well-anchored the rubric is, and do not credit a rubric merely because "
            "clinicians helped write it — expert authorship without a cited source is "
            "still an author-authored rubric. "
            "DO NOT CLIMB LINEAGE, exactly as for DSM above. Record the source the rubric "
            "actually cites, not that source's ancestry. "
            "WHY THIS FIELD IS WIDER THAN IT LOOKS. Populating it does NOT make the rubric "
            "a reference standard. reference_standard_type asks whether anything external "
            "adjudicated these particular scores; this field asks what measuring device was "
            "used and whether it is a recognised one. A validated instrument applied by an "
            "LLM judge with no human backing is still 'None — rubric-only scoring' in the "
            "type field — CACTUS is exactly that. Crossing the two fields is what "
            "distinguishes an expert-designed rubric-only evaluation (MindEval, Lissak) "
            "from an ad hoc one (Hasan, WundtGPT), which is otherwise invisible. "
            "THE INSTRUMENT MUST BE USED AS THE REFERENCE STANDARD (added 2026-08-29.19). This "
            "field records instruments the OUTPUTS WERE JUDGED AGAINST, not every named "
            "instrument the paper touches. An instrument used to BUILD the stimuli — to write "
            "prompts, select or stratify cases, define severity tiers for sampling, or ground "
            "a scenario — is apparatus and does NOT belong here; note it in abstraction_notes "
            "instead. TEST: were model outputs scored against this instrument? If it never "
            "touches the scoring, leave it out. OBSERVED ERROR: a chatbot risk-escalation "
            "study recorded PHQ-9 here while its reference standard was an author-defined "
            "protocol (rubric-only) and its scoring procedures counted referral and shutdown "
            "prompt numbers — PHQ-9 shaped the escalating prompts and scored nothing. Stable "
            "across three runs, so a consistent misreading rather than noise. "
            "LEAVE None when the reference standard is exact match to gold responses, or an "
            "author-authored rubric with NO cited published source. Hasan's five counselling "
            "dimensions and WundtGPT's four dimensions are invented for those papers and "
            "stay null — that is the contrast the cross-tab depends on."
            "CONVENTION: use null (not an empty list) when this field does not apply to the paper. An "
            "empty list is never a valid value for this field."
        ),
    )
    scoring_procedures: List[str] = Field(
        ...,
        description=(
            "All scoring procedures used across the paper's INCLUDED arms, deduplicated. "
            "High-level descriptions of the measurement operation and its OUTPUT (metric, "
            "scale, count, or structured category). "
            "INCLUDED ARMS ONLY: exclude scoring procedures belonging solely to arms that "
            "failed the MH relevance gate. If a procedure is used in both an included and "
            "an excluded arm, it stays (via its use in the included arm). "
            "E.g. 'accuracy and macro-F1 against reference labels', "
            "'5-point Likert per dimension, averaged across 3 raters', "
            "'binary safety flag per response, percentage flagged reported', "
            "'ROUGE-L against reference answer'. "
            "Include exactly 'None stated' if an included arm uses no scoring procedure. "
            "WORKED EXAMPLE: a paper has 3 arms — Arm 1 evaluates BERT vs GPT-4 on a "
            "generic sentiment task (excluded, not MH); Arm 2 evaluates GPT-4 on PsyQA "
            "with ROUGE-L against reference answers (MH-relevant); Arm 3 evaluates GPT-4 "
            "on a depression severity task with accuracy against clinician-labeled "
            "severity tiers (MH-relevant). scoring_procedures lists only ['ROUGE-L "
            "against reference answers', 'Accuracy against clinician-labeled severity "
            "tiers']. Arm 1's scoring does not appear."
            "SENTINEL: when nothing qualifies, use the exact string 'None stated'. Variants ('Not "
            "stated', 'N/A', 'none') are normalised on ingest but should not be produced."
        ),
    )
    abstraction_flags: Optional[List[str]] = Field(
        None,
        description=(
            "Free-form list of field names where interpretation was genuinely uncertain — "
            "a different reader could reasonably code the field differently, or something "
            "about the paper was confusing to the abstractor. NOT for missing information "
            "(use the field's own value for that). Common candidates: system_tasks, "
            "evaluation_constructs_categories, reference_standard_type, reference_standard_"
            "description, type_of_study, benchmark_names. Null if no genuine ambiguity."
            "CONVENTION: use null (not an empty list) when this field does not apply to the paper. An "
            "empty list is never a valid value for this field."
        ),
    )
    abstraction_notes: Optional[str] = Field(
        None,
        description=(
            "Free-form prose notes accompanying abstraction_flags. Required if "
            "abstraction_flags is non-null; for each flagged field, name the alternative "
            "interpretation and briefly explain what made the call unclear. Null if "
            "abstraction_flags is null."
        ),
    )

    # ---------------------------------------------------------------------
    # Consistency enforcement
    #
    # Vocabulary membership is a HARD reject (the value is unusable as data
    # and the runner will retry with the error fed back). Everything else is
    # a SOFT flag appended to abstraction_flags/abstraction_notes, following
    # the pattern established by _enforce_rubric_only_consistency in the
    # full schema: never discard a record you can instead mark for review.
    # ---------------------------------------------------------------------

    @field_validator("primary_construct")
    @classmethod
    def _v_primary(cls, v: str) -> str:
        return _v.check_vocabulary([v], EVALUATION_CONSTRUCTS, "primary_construct",
                                   allow_other=True)[0]

    @field_validator("evaluation_constructs_categories")
    @classmethod
    def _v_constructs(cls, v: List[str]) -> List[str]:
        return _v.check_vocabulary(
            v, EVALUATION_CONSTRUCTS, "evaluation_constructs_categories", allow_other=True
        )

    @field_validator("mental_health_domains")
    @classmethod
    def _v_domains(cls, v: List[str]) -> List[str]:
        return _v.check_vocabulary(
            v, MENTAL_HEALTH_DOMAINS, "mental_health_domains", allow_other=True
        )

    @field_validator("reference_standard_description", "scoring_procedures")
    @classmethod
    def _v_none_stated(cls, v: List[str]) -> List[str]:
        return _v.normalise_none_stated(v)

    @field_validator("benchmark_names", "parent_benchmarks", "reference_standard_instruments",
                     "abstraction_flags")
    @classmethod
    def _v_no_empty_list(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        # Convention: null means "does not apply"; [] is never valid here.
        return None if v == [] else v

    @model_validator(mode="after")
    def _enforce_consistency(self) -> "StudyRollup":
        # --- hard rejects (raise; runner feeds the message back on retry) ---
        _v.check_other_requires_notes(self, self.system_tasks, "system_tasks")
        _v.check_other_specifier_not_excluded(self, self.evaluation_constructs_categories)
        _v.check_type_value_not_in_description(
            self, self.reference_standard_description, self.reference_standard_type,
        )
        _v.check_dataset_purpose_derivation(self, self.dataset_purpose, self.abstraction_notes)
        _v.check_availability_non_default_has_evidence(
            self, self.input_availabilities, self.abstraction_notes,
        )
        _v.check_simulator_validation_implies_fidelity(
            self, self.system_tasks, self.evaluation_constructs_categories,
            self.scoring_procedures, self.reference_standard_description,
        )

        # --- within-field exclusivity ---
        _v.check_general_domain_codes(self, self.mental_health_domains, "mental_health_domains")
        # Evaluation/judging preemption is NOT applied here — see the validator
        # docstring. A study-level record aggregates arms, and a paper that
        # evaluates a responder and validates its judge has both tasks.

        # --- cross-field disjointness ---
        _v.check_disjoint(
            self, self.benchmark_names, self.reference_standard_instruments,
            "benchmark_names", "reference_standard_instruments",
            "A named instrument belongs in benchmark_names only when the LLM SAW the scale "
            "items as input; otherwise it is a reference standard. If the override applies, "
            "say so explicitly in abstraction_notes.",
        )
        _v.check_disjoint(
            self, self.benchmark_names, list(self.systems_tested),
            "benchmark_names", "systems_tested",
            "A framework or chatbot being evaluated is a system tested, not a benchmark.",
        )
        _v.check_disjoint(
            self, self.parent_benchmarks, self.benchmark_names,
            "parent_benchmarks", "benchmark_names",
            "Direct reuse of a benchmark populates benchmark_names only. parent_benchmarks "
            "is for a distinct derived set whose items came from the parent.",
        )
        _v.check_construct_task_overlap(
            self, self.system_tasks, self.evaluation_constructs_categories
        )

        _v.check_primary_in_categories(
            self, self.primary_construct, self.evaluation_constructs_categories
        )

        # --- logical implication ---
        _v.check_categories_not_longer_than_described(
            self, self.evaluation_constructs_described, self.evaluation_constructs_categories
        )
        _v.check_live_data_not_released(self, self.input_determinism, self.input_availabilities)




        # --- new 2026-08-29.10, from the four-PDF audit ---
        _v.check_simulation_task_needs_fidelity(
            self, self.system_tasks, self.evaluation_constructs_categories,
            self.abstraction_notes,
        )
        _v.check_thirdparty_inputs_have_named_benchmark(
            self, self.input_provenance_types, self.benchmark_names,
        )
        _v.check_benchmark_development_names_a_benchmark(
            self, self.type_of_study, self.benchmark_names,
        )

        _v.check_authored_real_corpus_has_parent(
            self, self.benchmark_names, self.input_provenance_types,
            self.input_reality, self.parent_benchmarks,
        )

        # --- pairing (last, so auto-flags above satisfy it rather than trip it) ---
        _v.check_flags_notes_paired(self)
        return self
