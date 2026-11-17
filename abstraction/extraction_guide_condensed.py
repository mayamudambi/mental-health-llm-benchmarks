"""
extraction_guide_condensed.py

Field-definition guide for the condensed one-row-per-study abstraction.
"""

EXTRACTION_GUIDE_CONDENSED = """
You are abstracting a research article for a systematic review of LLM
benchmarks in mental health, emotional support, well-being, or developmental
disability applications. Produce ONE row per study — a condensed summary
that aggregates across all evaluation arms/tasks in the paper.

== INCLUDED ARMS ONLY — GLOBAL RULE ==

Every field describes the INCLUDED arms only. An arm excluded at the
relevance gate contributes NOTHING to any field: not its datasets, tasks,
constructs, metrics, models, reference standards, or results. Determine
which arms are included first, then populate every field as if the
excluded arms were not in the paper.

Exceptions — these four fields see the whole paper by design:
  - bibliographic fields (authors, title, year, venue)
  - excluded_content (names the excluded arms and why)
  - mh_scope (the ratio of MH to non-MH content is what it measures)

An arm is excluded when it fails the relevance gate (no generative LLM
output scored) or the mental-health scope gate. Both are per-arm, not
per-paper: a paper qualifies through any one arm, and its other arms
are still excluded.

THIS APPLIES TO GENERAL-DOMAIN BENCHMARK ARMS. The most common way this rule
is broken is a paper that validates its system on a public general-purpose
benchmark (SQuAD, MMLU, a QA set) AND runs a bespoke mental-health evaluation.
The public arm fails the mental-health scope gate — Wikipedia reading
comprehension is not a mental health domain — so it contributes NOTHING:
not its benchmark name, not its metrics, not its constructs, not its
availability. Do not record Response quality because F1/ROUGE/BERTScore were
computed on SQuAD. Do not record the general benchmark in benchmark_names. The
fact that the arm is reproducible and the MH arm is not does not license
borrowing from it.

Worked case: a wellbeing chatbot reports F1/ROUGE-L/BERTScore on SQuAD and a
21-participant Likert study on wellbeing topics. Only the user study is
included. benchmark_names = null, and the constructs come from the Likert
dimensions alone.

== CROSS-CUTTING RULES ==

1. RELEVANCE GATE: only produce a row if the paper (a) evaluates at least
   one generative LLM, AND (b) addresses mental health, emotional support,
   well-being, or developmental disability. If the paper mixes relevant and
   irrelevant content, abstract only the relevant portions and note any
   scope decisions in the summary if consequential.

2. AGGREGATION ACROSS ARMS: when a paper evaluates multiple INCLUDED arms
   (tasks, domains, models, or datasets), DEDUPLICATE values across all
   included arms and list each distinct value ONCE. Do not repeat, do not
   describe per-arm.

3. HIGH-LEVEL DESCRIPTIONS: keep list entries concise — one short phrase per
   item. Substantive detail belongs in the full per-instance abstraction,
   not here.

4. CONTROLLED VOCABULARIES: for system_tasks, mental_health_domains,
   evaluation_constructs, systems_tested, input_formats, and
   conversation_types, always choose from the provided list. Use
   'Other (specifier)' inline only when nothing fits — a wrong specific
   label is worse than Other.

5. Never leave a required field blank. Use empty list [] if a category
   genuinely has no entries. Do not infer facts not stated in the paper.

== STUDY TYPE ==
- Benchmark development: paper BUILDS an evaluation apparatus of its own.
  Judge by what was BUILT, not by naming, release, or full specification.
  Tag Benchmark development when ANY of these apply:
  (a) constructs or curates an ITEM SET with stated selection or generation
      criteria (a new corpus, prompt bank, consultation templates, question
      bank drawn from source texts under stated rules);
  (b) designs an ORIGINAL GRADING INSTRUMENT — a new rubric, autograder, or
      LLM-judge system, including one validated against human raters as
      part of the paper;
  (c) designs an ORIGINAL SCORING PROTOCOL or METRIC VARIANT — a new
      adherence checklist, severity coding scheme, adapted composite metric.
  Naming, public release, and full item specification are NOT required —
  an unnamed, unreleased, partially specified benchmark is still Benchmark
  development.
- Evaluation study: paper applies an EXISTING evaluation apparatus (items
  and scoring both come from prior work). Prompt engineering alone =
  Evaluation study — prompt engineering describes how models were run, not
  whether a benchmark was built.
- Model development: fine-tuning, RLHF, or architectural modification.
  Prompt-only guardrail or classifier systems built on an existing
  generative LLM are NOT Model development — the LLM is unchanged.

PRIORITY RULE — when multiple categories apply, prefer in this order:
  Benchmark development > Model development > Evaluation study

Rationale: priority reflects the durable reusable artifact.

Worked examples:
- SHIELD-style paper: introduces a new benchmark of 100 prompts across 5
  risk categories AND evaluates 5 existing LLMs on it → Benchmark
  development.
- Paper fine-tunes Llama-3 on MH data AND evaluates it on benchmarks →
  Model development.
- Paper evaluates GPT-4 vs Claude on USMLE with no new benchmark and no
  model changes → Evaluation study.
- Paper writes 30 clinical consultation templates against stated inclusion
  criteria, has GPT-4 and Claude complete each one, and scores completions
  with a new 5-point adherence rubric — even without a benchmark name →
  Benchmark development (built both an item set and a rubric).

== BENCHMARK NAMES ==
List only datasets/corpora/exams the system was EVALUATED ON — the inputs
it was scored against, including any benchmark this paper introduces and
runs. Exclude training / fine-tuning corpora, benchmarks cited for
comparison but never run by this paper, and datasets from arms excluded
at the relevance gate (name those in excluded_content). A dataset used
for BOTH training and held-out evaluation IS listed, and the rationale
says so.

NAME THE DATASET ONLY AS THE PAPER NAMES IT. Do not supply a name the
paper does not use, even when the dataset resembles a well-known one you
recognize. If the paper identifies its data only by citation ("the
dataset from [23]", "the work of Rastogi et al."), that is NOT a name —
leave benchmark_names null. Substituting a familiar name for an unnamed
corpus is a fabrication error and is harder to catch than a blank field.

WORK FROM THE ARM LIST, NOT THE DATASET SECTION. Populate this field by
enumerating each arm that passed the gate and asking what its evaluation
items were called. Do not start from the datasets mentioned in the
paper's dataset section and then filter — that path over-collects named
benchmarks from excluded arms and silently omits unnamed ones from
included arms.

NAMED EXAMS COUNT even if the paper doesn't call them "benchmarks":
USMLE, PRITE, MRCPsych, Portuguese National Residency Access Examination
(PNA / Prova Nacional de Acesso), Chinese Medical Licensing Examination,
any national medical licensing / residency / board examination cited by
name and used to score LLM performance. The test is not "does the paper
use the word benchmark" — it's "are the exam questions a named body of
items the LLM was scored on."

SCOPE RESTRICTION — include ONLY benchmarks used in arms that pass the
MH relevance gate. Non-MH benchmarks from arms excluded at the gate do
NOT appear here.
- Example: a paper evaluates on MMLU, MedQA, and PsyQA, but only the
  PsyQA arm is MH-relevant. benchmark_names = ["PsyQA"]. MMLU and MedQA
  do NOT appear.
- LIST EACH BENCHMARK ONCE per paper. A single benchmark spanning
  multiple in-scope arms is one entry, not one per arm.
- Per-benchmark rule: if the same benchmark is used in BOTH an included
  and an excluded arm, it stays.

WORKED EXAMPLE — 13 affective computing tasks; only suicide detection
and well-being (stress) pass the gate. The paper names eight benchmarks
(SemEval-2014/2015, Twitter140, SemEval-2017 Task 5, WASSA-2017 EmoInt,
Toxic Comment Classification Challenge, First Impressions, Sarcasm News
Headlines) — all in excluded arms. The two included arms use corpora
identified only by citation (Desu et al. 2022; Rastogi et al. 2022).
benchmark_names = None. All eight named benchmarks are excluded; both
included benchmarks are unnamed. A populated list here would be wrong
in both directions.

DO NOT include validated clinical or research instruments used as
REFERENCE STANDARDS. C-SSRS, PHQ-9, PHQ-8, GAD-7, CAPS-5, HAM-D, HAMD-17,
MADRS, YMRS, PANSS, WAI, CTRS, MITI, PANAS, and similar go in
reference_standard_instruments, NOT here.

Include a named instrument here ONLY when the scale items are the INPUT
to the LLM. Rule of thumb: does the LLM SEE the scale items?
- Yes → benchmark_names candidate
- No, the scale is only how outputs are graded → reference_standard_instruments

Do NOT include names of models, frameworks, or systems being EVALUATED —
those go in systems_tested. Example: "SAGE" is a framework being evaluated,
not a benchmark. Same for chatbot names (Sarah, BeFreeGPT, ED-LLM, etc.) —
those are systems tested, not benchmarks.

Leave null if the input source is not named — do NOT invent a name.

== PARENT BENCHMARKS ==
Record where a paper's evaluation items came from when they derive from
an earlier public benchmark or corpus. This field is reserved for
EVALUATION ITEM SETS.

THE POSITIVE TEST, APPLIED FIRST. Ask of the scored items: did these
specific pieces of text, audio, or images exist before this paper? If
yes, and they came from a named prior dataset or corpus, that name goes
here. Only then work through the exclusions below.

Most of this section is exclusions, so the field has a strong pull
toward null. Resist it. Run the positive test before reading further,
and populate the field whenever it passes.

WORKED CASES THAT DO POPULATE IT:
- A paper builds a new corpus by SELECTING utterances from an existing
  research dataset and RE-ANNOTATING them with a new taxonomy. The
  utterances are the scored items and they pre-existed.
  parent_benchmarks = the source dataset. Example: 23,930 client
  utterances drawn from a prior counselling corpus and labelled with a
  new resistance taxonomy — the prior corpus is the parent.
- A paper evaluates on a filtered subset of a public benchmark.
- A paper translates or reformats a public benchmark's items.

ANNOTATION IS NOT CREATION. Adding labels, rationales, or a taxonomy to
pre-existing text does not make the items yours. The annotation effort
may be the paper's main contribution and the new corpus may deserve its
own name in benchmark_names — both can be true while parent_benchmarks
still records where the text came from. This is the single most common
way this field is left wrongly null.

BEWARE THE PROVENANCE INTERACTION. Coding input_provenance_types as
Author-created does NOT mean parent_benchmarks is null. Provenance asks
who assembled THIS evaluation set; parent_benchmarks asks where its
items came from. An author-assembled set built from someone else's
corpus is Author-created AND has a parent. Answer the two
independently.

Do NOT include:
- Clinical instruments and frameworks (PHQ-9, GAD-7, C-SSRS, CTRS, MITI,
  DSM-5, Sekhon TFA) — they are reference standards or rubric sources,
  not parent benchmarks. They belong in reference_standard and rubric
  source fields.
- Base models, checkpoints, or training corpora — this field is about
  what the system was tested ON, not what it was built from.
- Related Work citations — a benchmark named only as prior art is not
  a parent. The parent must have contributed actual items.
- Benchmarks the paper's benchmark is merely INSPIRED BY or CONCEPTUALLY
  similar to — hedged language like "starting from corpora such as X,"
  "building on X," "inspired by X," "expanded from X" generally indicates
  a seed relationship rather than a subset. The operative question is
  whether any parent item is scored, unchanged, in the reported results.

MULTI-LEVEL CHAINS: record only the IMMEDIATE parent here, with the
remainder noted in abstraction_notes. Full chains (E-DAIC → DAIC-WOZ →
DAIC; CLPsych 2019 → UMD Reddit Suicidality → Reddit SuicideWatch) can
be reconstructed later by self-joining the field.

DERIVED-FROM vs USED-DIRECTLY: this rule is about GENERATION, not
annotation. Where the parent supplied narrative framings, problem-type
labels, or personas that were then fed to a GENERATOR, and the SCORED
items are the newly generated ones, the derived set is the authors' own
— private and typically unreconstructible without the generation prompt
and any filtering rule. parent_benchmarks stays null.

The distinction is whether the scored text is new:
  Seeds -> generator -> new text is scored        -> no parent
  Existing text selected and re-labelled          -> PARENT
  Existing text filtered, translated, reformatted -> PARENT
If you cannot tell whether the scored items are generated or reused,
populate the field and flag it.

Without these rules, the field fills with "PHQ-9" and stops carrying
information about item reuse.

== JOURNAL/SOURCE ==
For preprints: server name ('arXiv', 'medRxiv', 'bioRxiv', 'PsyArXiv').
For peer-reviewed articles: journal name (e.g. 'JMIR', 'JAMA Psychiatry').
For conference papers: conference name (e.g. 'NeurIPS 2024', 'EMNLP 2023').
Null if unclear.

== JOURNAL SOURCE TYPE ==
IMPORTANT: many arXiv / preprint uploads are actually conference papers.
Before defaulting to Preprint, check for conference signals:
- Author-block or title cites the conference ("To appear at NeurIPS 2024",
  "Accepted at EMNLP 2023", "In Proceedings of ACL 2024")
- Camera-ready formatting (two-column, conference template)
- DOI pointing to a conference proceeding
- Paper title or abstract explicitly names a conference
If ANY conference signal is present → Conference proceeding, not Preprint.

Preprint: arXiv, medRxiv, bioRxiv, PsyArXiv, or other preprint server,
  with NO conference or journal affiliation visible.
Conference proceeding: NeurIPS, EMNLP, ACL, CHI, AMIA, etc. — includes
  conference papers hosted on preprint servers if conference affiliation
  is stated.
Peer reviewed: journal article that went through peer review.
Other: thesis, technical report, book chapter, etc. — include an inline
  specifier when possible.

== MH SCOPE ==
Whether MH is the SOLE focus or one of several domains covered. Populated
after applying the relevance gate.
- MH only: every arm is MH-relevant; no non-MH content excluded at gate.
- Mixed — MH is a substantial domain: paper covers multiple domains AND
  MH is a substantial portion (distinct section, named domain in a multi-
  domain benchmark, ~20-25%+ of results).
- Mixed — MH is a minor domain: paper primarily about non-MH topic
  (general medical exam, multi-domain benchmark) with MH as a small
  subset (e.g. psychiatry as one of five specialties in a residency
  exam).

MH-SMALL-PIECE DECISION RULE — DISAGGREGATION IS THE GATE, NOT SIZE.
For "Mixed — MH is a minor domain" papers:
- INCLUDE when MH-specific results appear separately in any per-domain
  table, figure, subgroup analysis, or domain-stratified test — even
  when the MH subset is small (n=15 questions of 148 is fine).
- EXCLUDE only when the paper reports MH pooled with other domains and
  no MH-specific performance can be extracted from what the paper
  reports.
Worked example: paper evaluates LLMs on 148 questions from a national
medical residency exam covering five specialties including psychiatry
(n=15). If Table 4 reports per-domain accuracy including psychiatry
separately, INCLUDE (mh_scope = Mixed — MH is a minor domain,
mental_health_domains = [General psychiatry]). If only overall accuracy
across all 148 questions is reported, EXCLUDE.

== SYSTEM TASKS (controlled vocabulary) ==

EVALUATION/JUDGING AT STUDY LEVEL. This field aggregates across the paper's
arms, so a paper may legitimately carry Evaluation/judging ALONGSIDE other
tasks. A benchmark paper that scores counsellor LLMs on generated dialogue AND
validates its own LLM judge against human ratings has BOTH Text/response
generation AND Evaluation/judging. Record every task any evaluated system
performs.

Evaluation/judging applies when a JUDGE OR EVALUATOR IS ITSELF EVALUATED —
the paper reports the judge's agreement with human raters, its correlation with
expert scores, or its accuracy against a labelled standard. If an LLM judge is
used only as apparatus and its own quality is never scored, that is methodology:
do NOT record Evaluation/judging, and do NOT list LLM as judge/evaluator in
systems_tested.

The same test governs systems_tested: a judge whose agreement with a human
standard is reported as a result IS a system tested. A judge used unvalidated is
not.

Before extracting system tasks, IDENTIFY the system(s) under evaluation:
the model(s) whose performance the paper measures and reports as results.

Distinguish these from models used in the evaluation METHODOLOGY:
LLM-as-judge, human/LLM annotators, raters, data generators, score assigners.
These methodology roles are part of how the paper measures performance —
they are NOT the systems being evaluated.

System task fields describe ONLY what the system under evaluation does.
Models used as judges, annotators, or data generators must NEVER contribute
task labels to the evaluated system's record. For example, if GPT-4 is
evaluated for diagnostic classification and Claude-3 is used as a judge to
score GPT-4's outputs, only Classification (from GPT-4) goes here — not
Evaluation/judging (from Claude-3's role).

GENERAL EXCLUSIVITY: tag the FEWEST tasks that fully describe what the
evaluated system does across the paper's INCLUDED arms. Do not add a task
that only restates the output format of a task you have already tagged.
If Evaluation/judging applies, it is normally the sole value.

Select all that apply across included arms, deduplicated:

Text/response generation — model produces a free-text reply.

Classification / score prediction — model assigns a categorization OR
predicts a numeric value from a defined output space. Covers both
DISCRETE label/tier assignment scored by exact-match / F1 (severity tier,
diagnosis, risk category) AND CONTINUOUS numeric prediction scored by
RMSE / MAE / CCC / correlation (PHQ-8 continuous 0-24, BFI-10 Likert
items, well-being scale totals). If a paper does both discrete
classification AND continuous score prediction against the same input,
list Classification / score prediction ONCE and describe both outputs
in scoring_procedures.
  EXCLUSION: Do NOT use when the label or score being assigned is a
  JUDGEMENT ABOUT ANOTHER PARTY'S PERFORMANCE (rating a therapist's
  empathy, grading a trainee, scoring another model's reply) — that is
  Evaluation/judging, which takes precedence. Classification means the
  model is labelling the CONTENT of an item (this post shows suicidal
  ideation; this patient's PHQ-8 band is severe), not appraising how
  well someone performed.

Question-answering — model answers a specific factual or clinical question.

Summarization — model condenses a document or session.

Dialogue/conversation — USE ONLY when multi-turn conversational behavior
(turn-taking, context retention, conversation management) is itself what
the reference standard evaluates. A chatbot scored on single responses
to single queries = Text/response generation.

Simulation — model generates a simulated entity. E.g., does an LLM
playing a patient produce responses that correlate with real patient
distributions.

Evaluation/judging — the paper evaluates an LLM's OWN judging behavior:
the model rates, scores, or grades some other agent's output or a
person's performance, and the quality of those ratings is what the
reference standard tests.
  PREEMPTIVE RULE: this value is PREEMPTIVE. When it applies, do NOT
  also tag Classification, Text/response generation, or any other task
  that merely describes the form the judgement takes. A judge always
  emits a label or score; that fact is captured by evaluated_output_type,
  not by a second system_task.
  Do NOT use when a judge model is methodology used to score a
  different evaluated system.

Other — includes agentic task execution / tool use (multi-step planning
workflows where the LLM invokes tools). Use Other with a brief 1-2
sentence description in abstraction_notes explaining the task and why
no other category fits — do not use Other as a default.

OUT OF SCOPE — do NOT record; exclude the paper if this is the only
evaluation:
- Qualitative coding / thematic analysis (inductive code development,
  excerpt extraction with code application, theme synthesis).
- Text / information extraction tasks (pulling entities, spans, structured
  fields from text). These are NLP methodology outside our review's
  clinical-capability scope.

== MENTAL HEALTH DOMAINS (controlled vocabulary) ==
Include a domain ONLY if the paper reports quantitative results for the LLM's
performance in that domain. Do NOT include domains mentioned only in the
Introduction, Related Work, Discussion, or as proposed future applications.

Select all that apply across the paper:
Depression / Anxiety / Stress / Trauma / PTSD / Bipolar disorder / Schizophrenia /
Psychosis / OCD / Eating disorders / ADHD / Autism spectrum /
Postpartum or perinatal depression /
Suicide/self-harm / Personality disorders /
Delusional disorder / Cognitive distortion /
Well-being / flourishing / Stigma / Misinformation / Bias / General mental health / Emotional support /
Counseling / Crisis counseling / General psychiatry / General psychology /
Other (specifier).

OUT OF SCOPE — REMOVED FROM THE VOCABULARY (2026-08-28). Do NOT record
these, not even as 'Other (specifier)':
- Substance use, and tobacco / smoking cessation. Out of scope outright.
- Intellectual, learning, and motor disability; developmental language
  disorder; global developmental delay. The former 'Developmental
  disorders' category covered these and has been removed.
- Neurological disorders (dementia, epilepsy, TBI) as such.
If one of these is the ONLY domain a paper evaluates, the paper fails
the mental-health scope rule and is excluded.

ADHD AND AUTISM IN STIGMA, BIAS, AND MISINFORMATION PAPERS. A paper about
ableist language toward autistic people, autism misinformation, or ADHD stigma
is evaluating how the LLM handles CONTENT ABOUT a condition, not the LLM's
clinical capability regarding that condition. Tag the content domain — Bias,
Stigma, or Misinformation — and do NOT also tag Autism spectrum or ADHD. The
mental-health-context requirement for those two domains means diagnosis,
screening, clinical assessment, risk identification, or clinical information
for caregivers. Detecting ableist Reddit comments is none of those.
Tag Autism spectrum or ADHD alongside Bias only when the paper ALSO reports a
separate clinical-capability result for that condition.

ADHD AND AUTISM SPECTRUM REMAIN IN SCOPE, but only in a MENTAL HEALTH
CONTEXT: diagnosis, screening, clinical assessment, risk identification,
or clinical information for caregivers. They are OUT of scope in an
educational, linguistic, or general-developmental context — an LLM
scored on classroom accommodation planning or on language-sample
analysis is not being evaluated on a mental-health capability. Where the
context is genuinely mixed, tag the domain and flag
mental_health_domains in abstraction_flags.

GENERAL-CODES RULE: use General mental health and General psychology
ONLY when no specific condition or context is identifiable — NEVER
alongside a specific domain code. If Depression is identifiable, tag
Depression alone, not ['Depression', 'General mental health'].

Trauma / PTSD covers PTSD, complex PTSD, acute stress disorder, and
trauma-focused evaluations more broadly.

Distinctions in the split categories:
- General mental health: broad well-being or mental health awareness content,
  not tied to counseling or emotional support specifically.
- Emotional support: acknowledging, validating, or responding to emotional
  distress in a helping capacity.
- Counseling: therapeutic conversation with structured helping intent
  (counselor-client dynamics, motivational interviewing, therapy techniques).
- General psychology: psychology as an academic subject (e.g., psychology
  exams, textbook knowledge assessments), distinct from mental health
  clinical evaluation.

Category mappings for common conditions:
- Stress includes burnout AND Adjustment Disorder.
- Anxiety includes Panic Disorder, Social Anxiety Disorder, GAD.
- Personality disorders: BPD, NPD, cluster-based screening, general PD
  identification. Distinct from personality-test-only studies (Big Five,
  MBTI) which are excluded.
- Well-being / flourishing: subjective well-being, psychological well-being,
  PERMA, Harvard Flourishing Study dimensions, well-being score prediction,
  wellness dimensions.
- Stigma: MH stigma detection, stigma reproduction in LLM outputs,
  stigma-related content classification.
- Misinformation: LLM handling of MH misinformation, myths, and inaccurate
  claims (autism misinformation, misleading treatment claims,
  misinformation detection or reproduction). Distinct from the Guideline
  adherence / information quality CONSTRUCT (LLM's own advice accuracy).
- Bias: LLM reproduction of biased or discriminatory MH-related content
  including ableist language (AUTALIC-style). Distinct from the Fairness /
  equity CONSTRUCT (cross-group performance disparities).
- Cognitive distortion: cognitive-distortion detection (all-or-nothing
  thinking, catastrophizing, mind-reading, personalization) in text — a
  clinical target distinct from Diagnostic accuracy.
- Delusional disorder: DSM-5 Delusional Disorder specifically (one or more
  non-bizarre delusions without broader psychotic-spectrum features).
  Distinct from Psychosis and Schizophrenia. LLM behavior of CONFIRMING a
  delusion is a Safety CONSTRUCT, not a mental_health_domain.

Other: use for specific paradigms without broader clinical grouping —
"Other (loneliness)", "Other (body image)", "Other (grief and
bereavement)", etc.

Multi-domain instruments: when a paper uses an instrument that spans
multiple specific domains (Hamilton Rating Scale covering depression
through mania, YMRS for manic states, mood spectrum diaries,
transdiagnostic scales), tag ALL specific domains the instrument covers
rather than defaulting to General mental health. For HRS: list BOTH
Depression AND Bipolar disorder. Domain tags reflect what the instrument
evaluates, not conclusions about the population — a paper using HRS on an
unspecified mood-disorder cohort still tags both because the instrument
spans both.

OUT OF SCOPE — do NOT record in mental_health_domains, even as
Other-specifier:
- Interpersonal / relationship-focused evaluations: relationships,
  intimacy, parenting, family dynamics.
- Violence and abuse: domestic violence, abuse of adults/children/
  dependents, neglect, child exploitation, abuse/neglect DETECTION,
  grooming and boundary-violation detection.
- Violence PERPETRATION: homicide ideation, violence ideation TOWARD
  OTHERS, threats to others.
- Parent-directed education or pedagogy AS SUCH — parent-education
  workflows where the evaluated construct is caregiver knowledge
  acquisition or general parenting-support information delivery.
- Somatic and physical-health conditions that are not mental health as
  such: somatic symptom disorders / medically unexplained symptoms,
  chronic pain (as physical health), bodily distress disorders (as
  somatic health), elimination disorders (enuresis, encopresis). These
  are physical/somatic health topics excluded because they fall outside
  the mental-health scope, not because they are morally problematic like
  the abuse content above.

CARVE-OUT — AI-safety-in-companion-chatbot papers are IN SCOPE:
The abuse / grooming / boundary-violation exclusion above applies to
detection tasks about HUMAN-TO-HUMAN abuse in existing text data
(annotating chat logs for adult-grooming-a-child, classifying posts
for domestic violence). It does NOT apply to evaluations of whether
AI CHATBOTS exhibit harmful patterns toward their users. Papers
evaluating LLM safety in companion-chatbot / emotional-support
deployments — dependency encouragement, manipulative engagement, social
isolation reinforcement, harmful roleplay — are IN SCOPE. The harm is
about the AI's behavior toward users, not human-to-human dynamics.
Map to mental_health_domains = ['Well-being / flourishing', 'Emotional
support'] and evaluation_constructs = ['Safety', 'Guideline adherence /
information quality'] as appropriate.

CARVE-OUT — LLM DELIVERY OF EVIDENCE-BASED MH INTERVENTIONS to parents
IS IN SCOPE:
The parent-directed exclusion applies to caregiver-education-as-
pedagogy workflows (an LLM teaching parents general facts about child
development as an educational task). It does NOT apply to evaluations
of LLMs delivering evidence-based mental health interventions where
parents happen to be the recipients. Behavioral parent training and
other clinical interventions used to treat diagnosable child
conditions ARE mental health therapy delivery, not parent education.

Signals of the carve-out: LLM evaluated on THERAPY-DELIVERY
capabilities (treatment fidelity to a manualized MH-intervention
protocol, therapeutic alliance, empathy, common therapeutic factors,
therapist-comparison studies). Interventions this covers include
Parent Management Training (PMT), Parent-Child Interaction Therapy
(PCIT), behavioral parent training, family-based therapy for
adolescent MH conditions.

Example: a paper evaluating whether a generative AI conversational
agent can deliver PMT with treatment fidelity comparable to a human
therapist, rated using the Thera-Turing Test framework, is IN SCOPE.
Map to mental_health_domains = ['ADHD'] or ['General psychology'] as appropriate, and evaluation_constructs =
['Therapeutic technique fidelity', 'Therapeutic alliance / rapport',
'Empathy'].

If a study ONLY evaluates out-of-scope domains, exclude it entirely. If
mixed with in-scope domains, tag only the in-scope ones.

EXCLUDE studies that ONLY evaluate personality tests (Big Five, MBTI) or
theory-of-mind tasks. If such a study also has a mental health domain
evaluation, include only the MH domain(s). Personality disorders (clinical
condition category) IS in scope; personality-test-only studies are NOT.

== EVALUATION CONSTRUCTS: DESCRIBED and CATEGORIES ==
Two paired fields:

evaluation_constructs_described (author's language): a list of the
evaluation constructs as the paper's AUTHORS describe them, in their own
words. Short phrases, not overly detailed. Preserves the paper's own
terminology for auditing purposes.
Examples:
- ["Guidance", "Informativeness", "Interpretation", "Empathy",
  "Helpfulness", "Safety"] for a paper naming those six dimensions.
- ["affective attitude", "burden", "ethicality", "coherence (Sekhon TFA)",
  "opportunity cost", "perceived effectiveness", "hallucination extent"]
  for a Sekhon-framework paper.
Do NOT translate to controlled vocabulary here.

evaluation_constructs_categories (controlled vocabulary mapping): the
described constructs mapped to the controlled vocabulary, deduplicated
across INCLUDED arms.

EVIDENCE REQUIREMENT. Every construct listed must correspond to a
reported quantitative result — a metric, rubric dimension, or scored
item set with a number attached. Location doesn't matter; a measurement
must exist. Never derive from Introduction, Related Work, Discussion, or
proposed applications.

TWO CHECKS BEFORE FINALIZING:
(1) Existence — for each construct, state to yourself the specific
result that measures it. If you cannot, drop it.
(2) Mapping — for each result, ask what it actually scores rather than
what its labels are called. Agreement with a clinically-named label set
measures the CHOICE, not the DELIVERY. A results table's caption is not
a construct.

ONE PARADIGM, ONE ENTRY. If two constructs would draw on the same
reported result, at most one is correct.

== ROUTING: DETECTION-OF-CLINICAL-PHENOMENON TASKS ==

The most common mapping failure is a paper where the LLM assigns a label to
something IN THE INPUT — a clinical or psychosocial phenomenon present in text
the model was given — and no controlled term obviously fits. Cognitive-distortion
classification, client-resistance coding, ableist-language detection, and
therapist-behaviour coding all have this shape.

Do NOT reach for the nearest clinical-sounding term. Route by WHAT THE LABEL IS:

(a) The label is a CLINICAL STATE, DIAGNOSIS, or SEVERITY LEVEL of the person
    who produced the input (depressed / not depressed, PHQ-9 band, DSM category,
    remission vs non-remission) → Diagnostic accuracy.

(b) The label is a RISK LEVEL or RISK PRESENCE (suicide risk high/low, self-harm
    intent, crisis escalation) → Risk detection accuracy.

(c) The label is an EMOTION or AFFECTIVE STATE → Emotion recognition.

(d) The label marks text as STIGMATIZING, ABLEIST, DISCRIMINATORY, or as
    MENTAL-HEALTH MISINFORMATION → Stigma and harmful-content detection.

(e) The label is a PSYCHOTHERAPY PROCESS CODE applied to a counsellor's or
    client's behaviour — resistance subtypes, MITI or MISC codes, alliance
    markers, technique labels, change-talk categories →
    Psychotherapy process annotation.

(f) The model WRITES A CLINICAL DOCUMENT about an encounter — progress note,
    intake write-up, discharge or referral summary, SOAP note, treatment plan —
    and the document itself is scored for completeness, faithfulness to the
    source, absence of fabricated detail, or fitness for the record →
    Clinical documentation quality. NOTE this is the one branch here whose
    OBJECT is the model's own output rather than the input; it sits in this
    list because papers reach it from the same summarisation-and-labelling
    territory as (e).

(g) Anything else — a discourse property, a social phenomenon, a content
    property with no home above → Other (specifier), where the specifier names
    the phenomenon in the paper's own terms.

(h) The paper VALIDATES A SIMULATOR — it checks whether an LLM playing a client,
    patient, or user behaves realistically, stays in character, matches the
    clinical profile it was given, or is judged indistinguishable from real
    people → Simulation fidelity.

    This is easy to miss because the simulator is usually built as APPARATUS for
    evaluating something else, so attention goes to the thing being evaluated.
    Ask separately: does the paper report a result about how good the SIMULATOR
    is? If it reports realism ratings, profile-adherence checks, expert
    judgements of whether simulated clients are believable, or agreement between
    simulated and real client behaviour, that is Simulation fidelity and it is
    an additional construct alongside whatever the simulated sessions were used
    to measure.

    NOT Simulation fidelity: merely USING a simulator to generate evaluation
    material, with no reported check on the simulator itself. Then the simulator
    is methodology and belongs in input_reality and system_tasks only.

    A paper that both builds a validated patient simulator AND scores counsellor
    LLMs against it records Simulation fidelity for the first and the
    counselling constructs for the second.

Worked cases:
- Client resistance subtypes in counselling transcripts → Other (client
  resistance detection). NOT Therapeutic technique fidelity: fidelity scores the
  MODEL'S OWN therapeutic conduct against a normative standard, and here the
  model is labelling the CLIENT.
- Anti-autistic ableist language in social media posts → Other (ableist language
  detection). NOT Fairness / equity, which means cross-group PERFORMANCE
  DISPARITY. Measuring agreement with human annotators is detection accuracy,
  however the paper frames the error pattern in its discussion.
- Cognitive distortions per Burns' framework → Diagnostic accuracy IF the paper
  treats the distortion categories as clinical states; otherwise Other
  (cognitive distortion detection). Say which reading you took in
  abstraction_notes.
- Therapist behaviour codes (MITI, MISC) applied by the LLM to human transcripts
  → Other (therapist behaviour coding). Again, the model is coding someone else's
  behaviour, not exhibiting it.

DOWNSTREAM AND APPLICATION ANALYSES ARE NOT CONSTRUCTS. Papers often take a
model's predictions and then correlate them with something else, or run a
human study on top of them. Those results are about the WORLD or about the
HUMANS, not about the model's performance. A construct requires a score of the
MODEL'S OUTPUT against a reference.

Not constructs:
- Correlating model-predicted labels with an outcome measure (e.g. predicted
  resistance proportions correlated with client-reported working alliance).
  That estimates a relationship in the data; the model is the instrument, not
  the object of measurement. Do NOT record Therapeutic alliance / rapport.
- A user study measuring whether humans improved when given model output
  (counsellor response quality before vs after model feedback). That measures
  the humans.
- Prevalence or distribution statistics computed with the model over a new
  corpus.
These belong in evaluation_constructs_described if you want them recorded, and
their statistics do not belong in scoring_procedures, which is for procedures
that score the model.

Test: could this number change if the model got better or worse at its task,
holding the data fixed? If not, it is not a construct.

INTERPRETATION IS NOT MEASUREMENT. A paper may frame a detection result as
evidence of bias, of clinical utility, or of therapeutic insight. That framing
belongs in evaluation_constructs_described. The construct is determined by what
was scored and against what, not by what the authors concluded from it.

== REPRODUCE / PERFORM / DETECT — THE THREE-WAY BIAS BOUNDARY ==

Bias and stigma appear in this literature in three different roles, and they map
to three different places. Decide which the paper measured before mapping
anything.

REPRODUCE — the LLM's own output contains biased, stigmatizing, or ableist
content, and the paper measures how often. The DOMAIN is Bias or Stigma. The
CONSTRUCT is whatever the output was scored for, normally Safety. There is no
"bias construct" for this case; do not reach for Fairness / equity.

PERFORM UNEQUALLY — the same task is run across demographic or clinical
subgroups and the paper reports a PERFORMANCE GAP between them (accuracy by
race, F1 by gender, calibration by age). CONSTRUCT: Fairness / equity. This
requires an actual disaggregated comparison. A paper that discusses bias
without reporting group-stratified results does not qualify.

DETECT — the LLM classifies text it was GIVEN as stigmatizing, ableist,
discriminatory, or as MH misinformation, scored against human labels.
CONSTRUCT: Stigma and harmful-content detection.

Worked case: AUTALIC asks four LLMs to label Reddit sentences as anti-autistic
ableist language and reports macro-F1 against annotator majority vote plus
Cohen's Kappa alignment. That is DETECT. The paper's discussion interprets the
over-classification pattern as model bias, but no group-stratified performance
gap is reported, so Fairness / equity is wrong. Domain: Bias.
mental_health_domains does not also take Autism spectrum — see the stigma and
bias rule in MENTAL HEALTH DOMAINS.

== FIDELITY vs ANNOTATION — WHOSE BEHAVIOUR IS SCORED ==

Therapeutic technique fidelity and Psychotherapy process annotation both involve
psychotherapy taxonomies. The object test separates them cleanly:

THERAPEUTIC TECHNIQUE FIDELITY — the LLM PRODUCES therapeutic output and that
output is judged against a manual or protocol. The model's own conduct is what
gets scored. Example: an LLM counsellor's turns rated with MITI by human coders.

PSYCHOTHERAPY PROCESS ANNOTATION — the LLM LABELS someone else's behaviour
against a psychotherapy taxonomy, and the labels are scored against human
annotation. Example: RECAP classifying client utterances into 13 resistance
subtypes from the PsyFIRE taxonomy, macro-F1 against majority-vote labels from
master's-level annotators.

The same instrument can appear on either side. MITI applied BY the LLM to human
transcripts is annotation; MITI applied TO the LLM's own output is fidelity. Ask
whose behaviour the score is about, not which taxonomy was used.

A paper can have both, in different arms. List both constructs.

== TEST PRECEDENCE — OBJECT TEST WINS ==
Apply the OBJECT TEST first. Only when both candidate categories score the
SAME object does the REFERENCE-STANDARD TEST decide between them. Where the
two tests point different ways, the OBJECT TEST WINS.

Worked case — MITI's Empathy global rating. Object Test: the rating scores a
response, so Empathy. Reference-Standard Test: it comes from a normative
manual, so Therapeutic technique fidelity. Resolution: if the paper reports
that subscale SEPARATELY, the scored object really is the response and the
answer is Empathy. If it is folded into an overall MITI fidelity score, the
scored object is the session rather than any single response, and the answer
is Therapeutic technique fidelity. The same reasoning applies to CTRS
"Collaboration", WAI subscales, and any other clinically-named item embedded
in a fidelity instrument.

CTRS ITEM ROUTING TABLE (added 2026-08-29.10). The rule above says WHETHER a
subscale splits out; it never said WHICH term each one takes, so two records in
one run routed the same instrument differently. Apply this table whenever CTRS
items are reported separately. If the paper reports only aggregates (e.g. one
"general skills" and one "CBT-specific" number), the scored object is the
session and the whole instrument gives Therapeutic technique fidelity — do not
consult the table.

  Understanding                → Empathy
      Scores whether the therapist grasped the client's internal reality and
      reflected it back. This is empathic attunement measured inside a fidelity
      manual, which is exactly the case the paragraph above resolves.
  Interpersonal Effectiveness  → Therapeutic alliance / rapport
      Warmth, genuineness, professional manner. Relational stance, not
      technique. (If the paper ALSO reports a separate professionalism
      dimension, apply DIRECT NAME MATCHES and give that one
      Professionalism / clinical communication style.)
  Collaboration                → Therapeutic alliance / rapport
      Shared agenda and joint work. This is WAI task/goal-agreement territory.
      Where both CTRS Collaboration and WAI are reported, they collapse to ONE
      alliance entry under cap (d) — same term, one entry.
  Guided Discovery             → Therapeutic technique fidelity
  Focus on Key Cognitions      → Therapeutic technique fidelity
  Strategy for Change          → Therapeutic technique fidelity
      The three CBT-specific items. Pure technique.

MODIFIED CTRS. Canonical CTRS (Young & Beck 1980) has 11 items; the 6-item
version above is what the counselling-LLM literature actually uses. Record the
item count used in scoring_procedures, and note any deviation from the canonical
instrument in abstraction_notes — several papers in this corpus use six items
while citing the full scale, and at least one (MAGneT) cites a source that is
not the CTRS at all.

WHY THIS TABLE EXISTS. MAGneT recorded CTRS → fidelity only; CACTUS recorded
CTRS → fidelity + alliance. Both may be correct if MAGneT reports aggregates and
CACTUS reports per item — the separate-reporting rule already permits that
divergence, and it should be confirmed against the tables rather than assumed to
be an error. What was genuinely underspecified is the destination term, which
this table now fixes so the two cannot diverge for any other reason.

== THREE RULES THAT SURVIVE THE DEFINITIONS ==

ONE INSTRUMENT, ONE PARADIGM — WITH A CAP, NOT A FLOOR (revised 2026-08-29).
An instrument's dimensions MAY map to different controlled terms when the paper
reports those dimensions separately and they mean genuinely different things.
Collapsing a ten-dimension rubric to one construct destroys the paper's finding,
and comparability is now carried by primary_construct instead.

What the rule still forbids:

(a) MORE CONSTRUCTS THAN SEPARATELY REPORTED DIMENSIONS. If the paper reports
    six dimension scores, you may record at most six constructs from that
    instrument, and normally fewer since several dimensions usually share a
    term.

(b) SPLITTING AN UNREPORTED DIMENSION. The test is what the paper REPORTS,
    not how the rating was collected. A dimension earns its own construct only
    if a score for that dimension appears in the paper. If raters worked
    through a multi-aspect rubric but only an aggregate is reported, that is
    ONE construct. If a score is reported PER ASPECT — even from a single
    rating session, even pairwise, even as a win/tie/loss percentage — each
    reported aspect is separately mappable, subject to cap (a).

    WORKED EXAMPLE (MAGneT, corrected 2026-08-29.10). Seven psychologists made
    blind pairwise A/B/Tie choices across nine counselling aspects, and the
    paper plots nine separate win rates plus one aggregate. Nine reported
    scores, so up to nine constructs are permitted. An earlier version of this
    rule asserted the opposite from the elicitation format alone and was wrong.
    Do not reinstate a format-based test.

(c) DIMENSIONS NOT REPORTED SEPARATELY. A subscale folded into a composite and
    never reported alone does not earn its own construct.

(d) INFLATING BEYOND THE VOCABULARY'S GRAIN. If three dimensions all map to
    Therapeutic technique fidelity, that is one entry, not three.

So: CTRS, WAI, and PANAS applied to one study give three constructs, one per
instrument. A single 10-question rubric whose questions are individually scored
and reported may give several. A pairwise preference reported per aspect gives
one per reported aspect. Record in abstraction_notes which dimensions drove
which construct whenever you record more than two from one instrument.

(e) MEASURED, NOT MERELY MENTIONED (added 2026-08-29.10). A construct the paper
    states it REMOVED, excluded, or failed to measure is never recorded, no
    matter how prominently the concept appears in surviving rubric text. Read
    the limitations section before mapping. WORKED EXAMPLE: MindEval's rubric
    anchors mention harmful advice and hallucination, but §5 states a Safety
    and Crisis Management axis was built, tested, DROPPED for lack of variation,
    and that self-harm and mandated-reporting scenarios are excluded by design.
    Safety must not appear in that record. Note the removal in abstraction_notes
    — a benchmark that tried and abandoned a construct is a finding.

BARE AUTOMATED METRICS AS SOLE EVALUATION. When the only construct-relevant
evaluation is one or more bare automated metrics against gold responses
(BERTScore, perplexity, ROUGE) with no qualitative dimensions, map to a
SINGLE holistic construct — normally Response quality — rather than
spreading the metrics across stretched near-mappings. BERTScore +
perplexity together is ONE Response quality entry. The metrics belong in
scoring_procedures.

"SOLE" IS EXCLUSIVE, AND IT IS A GATE (sharpened 2026-08-29.10). This rule
fires ONLY when the paper has no qualitative evaluation at all. If the paper
reports ANY human or rubric dimension, the metrics contribute NOTHING to
evaluation_constructs_categories — they are recorded in
evaluation_constructs_described and scoring_procedures and stop there. Bare
similarity is an excluded evaluation domain; this rule is a narrow rescue for
papers that would otherwise have an empty construct list, not a licence to
convert similarity into Response quality alongside real dimensions.

CONTRASTING PAIR, both from the same run. MAGneT reports BERTScore, ROUGE-1,
ROUGE-L and cosine similarity ALONGSIDE CTRS, WAI, PANAS and a nine-aspect
expert battery — correctly mapped none of them. Hasan reports BERTScore F1 and
SBERT cosine ALONGSIDE a five-dimension human battery — and wrongly produced a
Response quality entry from them. Hasan is the error. Same situation, two
answers, because "sole" was not stated as exclusive.

DIRECT NAME MATCHES TAKE PRECEDENCE. When a paper's own dimension name
appears verbatim in the controlled vocabulary AND collides with a default
mapping — e.g. the paper reports both "Guidance" and "Helpfulness" as
separate dimensions, and Guidance normally maps to Helpfulness — map the
direct-name-match dimension to its controlled term first, then find an
alternative mapping for the other. Do not force both into the same term,
and do not remap the direct match to avoid the collision.

SOCIOCULTURAL CONTEXT ROUTES TO CULTURAL SENSITIVITY (added 2026-08-29.10).
A rubric dimension assessing whether the response accounts for family, community,
socioeconomic, racial, ethnic, religious, or identity context maps to Cultural
sensitivity — NOT Helpfulness, and not Response quality. Three papers in one run
handled the same dimension three ways: Lissak's "Personal and Sociocultural
Circumstances" went to Cultural sensitivity (correct); Hasan's "environmental
analysis", defined by that paper as family dynamics, personal circumstances,
economic conditions and social environment, went to Helpfulness (wrong); and
MindEval's Ethical & Professional Conduct anchors, which name cultural
sensitivity and inclusivity verbatim, produced no Cultural sensitivity entry at
all (wrong). Cultural sensitivity does not require the paper to be about culture
— it requires a scored dimension about context.

CLIENT AFFECT CHANGE IS AN EXCLUDED OUTCOME (added 2026-08-29.10, revised same
day). PANAS and similar pre/post measures of the CLIENT's emotional state score
an effect IN THE CLIENT, not a property of the counsellor's response. That is a
user outcome, which the screening criteria exclude as an evaluation domain. It
therefore maps to NO construct: record the measure in
evaluation_constructs_described and scoring_procedures, and stop.

It is NOT Empathy. Empathy is a claim about the response. EVIDENCE: MAGneT
scores WORSE on negative-affect PANAS precisely BECAUSE deeper reflective
exploration raises negative affect. If PANAS measured empathy that result would
be incoherent. Two records in one run (MAGneT, CACTUS) made the Empathy mapping,
so it is systematic, not a slip.

SIMULATION DOES NOT RESCUE IT. In both papers the "client" is an LLM and the
affect score is assigned by a judge LLM reading the transcript, so no real
person experienced anything. That changes the measure's validity, not its
construct. The exclusion is about WHAT is being measured, not how well. A
simulated user outcome is still a user outcome.

INCLUSION CONSEQUENCE. A paper whose ONLY construct-relevant evaluation is
client affect change fails the relevance gate and is excluded. Neither MAGneT
nor CACTUS is affected — both carry CTRS, WAI and expert batteries alongside —
but check this before dropping the construct from a thinner paper.

== THE OBJECT TEST ==
Every construct is scored on either (a) the INPUT the model was given,
or (b) the OUTPUT the model produced. When two categories seem to both
fit, ask which OBJECT is being scored — that resolves most of them.

== THE REFERENCE-STANDARD TEST ==
When two categories score the same object, the reference standard decides.
NORMATIVE source (guideline, manual, practice standard) that says what
SHOULD be done → Guideline adherence or Therapeutic technique fidelity.
Expert judgment or verified fact about what IS true → Psychiatric
knowledge accuracy or Treatment/clinical accuracy. Apply this before
reaching for Other.

== FIVE PROCEDURAL RULES ==

(1) DO NOT ENCODE WHO RATED. Rater identity is captured in
reference_standard_type, not in the construct. A construct does not
change category, and does not fall out of scope, because a client
rather than a clinician produced the rating.

(2) INSTANCE SPLITS ARE NOT CONSTRUCT SPLITS. Two arms differing in
task, input set, reference standard, or scoring procedure become
separate INSTANCES. They may still share the same construct. Do not
create or select a construct because the evaluation setup differs.

(3) GLOBAL EXCLUSIONS. Constructs are CLINICALLY RELEVANT CAPABILITIES,
not properties of the evaluation. Never record as a construct:
statistical or calibration metrics (F1, AUROC, ECE, Brier, reliability
diagrams, coverage), robustness or stability properties, efficiency or
cost, or reproducibility of the evaluation. A construct is listed only
if the paper reports a QUANTITATIVE RESULT for it. Constructs must NOT
duplicate system_tasks.

(4) OUT-OF-SCOPE DIMENSIONS. Some author-named dimensions map to NO
category and are not recorded in evaluation_constructs_categories at
all: response coherence, relevance or on-topicness, semantic similarity,
usability, engagement, response speed, and technology-acceptability
outcomes including user-reported trust, credibility, satisfaction, and
acceptance. Record these in evaluation_constructs_described (it
preserves the paper's own framing) but do NOT map them. A _described
list longer than the _categories list is EXPECTED when out-of-scope
dimensions are present and is NOT an error. If an arm's ONLY scored
dimensions are out of scope, that arm likely fails the relevance gate.

(5) COMPLETENESS IS A SCORING DIMENSION, NOT A CONSTRUCT. Coverage or
completeness measures route by reference standard, exactly like
error-rate measures: against an EXTERNAL, PRE-EXISTING guideline or
manual that specifies required elements → Guideline adherence (a
rubric written for this study does not qualify — see that category's
definition); against the elements a CLINICAL DOCUMENT should contain →
Clinical documentation quality; against an expert ideal
answer or verified fact → Psychiatric knowledge accuracy; framed as
whether the response served the user rather than whether it covered
the material → Helpfulness. Record the coverage metric itself in
scoring_procedures.

== REFERRAL AND ESCALATION — THREE-WAY ROUTING ==
Referral appears under three different framings and they map differently:
- Was the referral or escalation decision clinically CORRECT (right
  service, right urgency, right threshold), judged against clinical
  norms? → Treatment/clinical accuracy.
- Did the model FAIL TO ESCALATE in a crisis, or otherwise cause harm
  by omission? → Safety.
- Was referral information USEFUL and actionable to the user, without a
  correctness or harm judgment? → Helpfulness.
Apply in that order; the first that fits wins.

Select from:
Diagnostic accuracy / Treatment/clinical accuracy /
Psychiatric knowledge accuracy / Risk detection accuracy /
Emotion recognition / Response quality / Empathy / Supportiveness /
Helpfulness / Safety / Trustworthiness / Privacy / Fairness / equity /
Cultural sensitivity / Guideline adherence / information quality /
Therapeutic alliance / rapport / Therapeutic technique fidelity /
Intervention strategy selection / Simulation fidelity /
Professionalism / clinical communication style /
Other (specifier).

== CONSTRUCT DEFINITIONS ==

Diagnostic accuracy — whether the model assigns the correct diagnostic
label, severity tier, or symptom classification to an input case,
transcript, or post, judged against a clinical categorization scheme
or a clinician-assigned label. OBJECT: the model's classification of
the input. INCLUDES severity classification against a clinical scheme
(HRS, MADRS, PHQ-9 severity tiers, YMRS, symptom-severity indices);
condition screening and detection from text. EXCLUDES acute risk
identification (→ Risk detection accuracy) and recommending a course
of care (→ Treatment/clinical accuracy).

Treatment/clinical accuracy — whether the model's clinical
recommendations, management plans, medication advice, and referral or
escalation decisions are correct, judged against clinician expertise
or a documented care standard. OBJECT: the model's proposed action —
DECISION CONTENT. INCLUDES referral and escalation decisions scored
for clinical appropriateness (right service, right urgency, right
threshold). BOUNDARY with Guideline adherence: if the reference
standard is a named guideline document and scoring is conformance to
that document, use Guideline adherence. If the reference is clinician
judgment about the right course of action, use Treatment/clinical
accuracy. BOUNDARY with Therapeutic technique fidelity: this category
is discrete decision content (which treatment, which referral);
fidelity is interactional process (how the session was conducted).
EXCLUDES identifying what the condition is (→ Diagnostic accuracy)
and factual recall unattached to a case (→ Psychiatric knowledge
accuracy).

Psychiatric knowledge accuracy — whether mental health factual content
in the model's output is correct, scored against verified fact, expert
confirmation, or an answer key. Format is irrelevant — exam questions,
free-text explanation, and psychoeducational content all qualify.
OBJECT: the output's factual content. INCLUDES clinical and psychiatric
exams (USMLE, PRITE, MRCPsych) with mental health content, academic
psychology assessments, and factual correctness of information given
to a user (e.g. medication facts, symptom descriptions). An answer key
is a SCORING MECHANISM, not a construct-defining reference. INCLUDES
"hallucination" or fabrication measures framed as factual error. When
framed as harm avoidance instead, use Safety. EXCLUDES conformance to
a normative guideline (→ Guideline adherence) and applied management
of a presented case (→ Treatment/clinical accuracy).

Risk detection accuracy — whether the model identifies ACUTE clinical
risk present in the input: suicidality, self-harm, crisis escalation,
imminent harm, abuse disclosure. OBJECT: the model's judgment about
the input. EXCLUDES severity classification or general symptom
stratification (→ Diagnostic accuracy) and whether the model's own
output is harmful (→ Safety).

Emotion recognition — whether the model correctly classifies or labels
the emotional or affective state expressed in the input — emotion
category, valence, sentiment, affect intensity. OBJECT: the input.
EXCLUDES producing an emotionally attuned response (→ Empathy).

Response quality — RESIDUAL CATEGORY. A holistic or overall quality rating of the model's output where the paper does NOT break the rating into named dimensions. OBJECT: the output, scored as a whole. AN ARITHMETIC MEAN OR COMPOSITE OF DIMENSIONS ALREADY MAPPED IS NOT A DISTINCT RESULT. Papers routinely report six named dimensions and their average; the average is arithmetic, not a separate measurement, and does NOT earn a Response quality entry. Add Response quality alongside specific constructs ONLY when an overall score is separately elicited from raters, or otherwise measured independently of the named dimensions.



Empathy — whether the output conveys understanding of and attunement
to the user's emotional state. OBJECT: the output. INCLUDES empathic
accuracy, emotional reflection, and exploration or interpretation
ratings from empathy frameworks (e.g. EPITOME). EXCLUDES labeling the
emotion in the input (→ Emotion recognition), acknowledging or
validating distress without demonstrated understanding
(→ Supportiveness), and the relational state built across turns
(→ Therapeutic alliance / rapport).

Supportiveness — whether the output acknowledges, validates, and
emotionally supports the user. OBJECT: the output. EXCLUDES
demonstrated understanding of the user's state (→ Empathy) and
practical usefulness (→ Helpfulness). If a paper uses "support" to
mean practical assistance rather than emotional validation, map to
Helpfulness.

Helpfulness — whether the output is practically useful to the user:
actionable guidance, usable suggestions, resolution of the presenting
problem. OBJECT: the output, judged on utility rather than emotional
attunement, factual correctness, or clinical correctness. An author
dimension named "Guidance" maps here unless the paper scores it for
clinical correctness (→ Treatment/clinical accuracy) or for harm
avoidance (→ Safety). See the referral routing rule above.

Safety — whether the model's own output avoids harm: harmful or
dangerous advice, method disclosure, encouragement of self-harm or
disordered eating, failure to escalate or refer in a crisis,
stigmatizing content, inappropriate boundary-crossing. OBJECT: the
output. EXCLUDES identifying risk present in the input (→ Risk
detection accuracy) and clinical correctness of a referral decision
absent a harm framing (→ Treatment/clinical accuracy).
"Hallucination" measures map HERE when framed as harm avoidance, and
to Psychiatric knowledge accuracy when framed as factual error. The
framing decides, not the metric name.

Trustworthiness — whether the output supports warranted reliance:
appropriate expression of uncertainty, acknowledgement of scope
limits, transparency about being an AI system, absence of overclaiming.
OBJECT: the output. EXCLUDES statistical calibration (ECE, Brier
score, reliability diagrams) — those are scoring details belonging in
scoring_procedures; record the underlying task construct instead.
EXCLUDES user-reported trust, credibility, and satisfaction, which are
TECHNOLOGY-ACCEPTABILITY outcomes and out of scope alongside usability
and engagement. This exclusion is about the construct's literature of
origin, not about who supplied the rating.

Privacy — whether the model handles personal or sensitive information
appropriately: avoiding unnecessary disclosure, not reproducing
identifying detail, not eliciting more personal information than the
task requires, appropriate confidentiality behavior. OBJECT: the
output or the model's information-handling behavior. EXCLUDES
system-level data governance, hosting, or compliance arrangements
that are described but not scored.

Fairness / equity — whether model performance or output quality
differs across demographic or social groups (race, ethnicity, gender,
age, socioeconomic status, language, insurance status), or whether
outputs contain bias or stereotyping toward such groups. OBJECT: a
COMPARISON across groups, or a bias score. REQUIRES a reported group
comparison or bias measurement — a single subgroup result with no
comparison is not this construct. Map such studies to the underlying
task construct and capture the group in `population`. EXCLUDES
cultural appropriateness judged within one cultural frame
(→ Cultural sensitivity).

Cultural sensitivity — whether the output is culturally appropriate
and adapted to the cultural or linguistic context: respect for
cultural norms, correct handling of culturally specific idioms of
distress, appropriate localization. OBJECT: the output, judged within
a single cultural frame. REQUIRES that cultural appropriateness is
SCORED. A study conducted in a non-Western setting, or in a language
other than English, is not this construct by virtue of its setting —
record the setting in `population`. EXCLUDES performance disparity
between groups (→ Fairness / equity).

Guideline adherence / information quality — whether the INFORMATIONAL
CONTENT of the output conforms to a named normative source: a
clinical guideline, protocol, or professional practice standard. The
source specifies what SHOULD be said. OBJECT: what was said, compared
against the normative source. INCLUDES completeness against required
elements the source specifies — omitting a mandated element is a
conformance failure. REQUIRES an identifiable normative source.

THE SOURCE MUST BE EXTERNAL TO THE STUDY (added 2026-08-29.18). A
normative source is a published, citable standard that existed before
this paper: a clinical guideline, a professional-body protocol, a
practice standard. A rubric the authors wrote for this study is NOT a
normative source, however carefully designed and however many
clinicians co-designed it. Every rubric specifies required elements —
that is what a rubric is — so treating "scored against a rubric with
required elements" as guideline adherence would attach this construct
to nearly every rubric-scored paper and make the count meaningless.
Same test as reference_standard_instruments: is there a CITATION to a
pre-existing source? If the only standard is the study's own rubric,
this construct does not apply; route by what the dimension MEASURES.

BOUNDARY with Clinical documentation quality — completeness of a
CLINICAL DOCUMENT (SOAP note, intake write-up, discharge summary)
against the elements such a document should contain is Clinical
documentation quality, NOT Guideline adherence. The document's own
required-element list is a documentation standard, not a clinical
guideline about what care to deliver. OBSERVED ERROR: TN-Eval scores
generated therapy notes on completeness, conciseness and faithfulness;
all three are Clinical documentation quality, and the record twice
added Guideline adherence on the reasoning that completeness was
"scored against a rubric specifying required SOAP note elements". That
reasons from HOW the dimension was scored rather than WHAT it
measures. Guideline adherence would apply only if the notes were
additionally checked against, say, published documentation standards
cited as an external source.
General factual correctness with no such source is Psychiatric
knowledge accuracy. BOUNDARY with Therapeutic technique fidelity —
BOTH are normative, so the object decides. Guideline adherence scores
WHAT WAS SAID against a content standard. Technique fidelity scores
HOW THE INTERACTION WAS CONDUCTED against a modality manual or
fidelity instrument. A paper scoring whether advice matched APA or
NICE recommendations is Guideline adherence. A paper scoring a
transcript with MITI, CTRS, or a manual checklist is Technique
fidelity, even though the instrument is equally normative. EXCLUDES
correctness of a clinical decision judged by clinician expertise
rather than document conformance (→ Treatment/clinical accuracy).

Therapeutic alliance / rapport — the RELATIONAL STATE achieved in the
interaction: working alliance, goal and task agreement, bond, trust
and rapport within the therapeutic relationship. OBJECT: the dyad —
a property of the relationship, not of either party's behavior alone.
Typically measured with alliance instruments (WAI, BLRI, SRS) or
rater judgments of the relationship. Rater identity does not affect
eligibility; client-completed, simulated-client-completed, and
observer-rated alliance all map here. BOUNDARY with Therapeutic
technique fidelity: fidelity scores BEHAVIOR against a standard;
alliance scores the STATE achieved. A rubric item for "rapport-building
skills" is fidelity (skill deployment); a WAI bond subscale is alliance
(relational state). The two are empirically dissociable — faithful
technique with weak alliance is a real and reportable finding.
EXCLUDES single-response emotional attunement (→ Empathy) and
warranted reliance on information (→ Trustworthiness).

Therapeutic technique fidelity — whether the model EXECUTES a specified
therapeutic modality correctly: CBT, MI, DBT, ACT, PMT technique use,
adherence to a manual or a prescribed session structure. OBJECT:
INTERACTIONAL PROCESS — how the session was conducted, scored against
a fidelity instrument or manual (MITI, CTRS, manual checklist).
INCLUDES modality-linked strategy choice — selecting the
stage-appropriate technique or therapeutic move — whether scored as
its own dimension or within a fidelity instrument scored as a whole.
BOUNDARY with Guideline adherence: both are normative; this category
scores how the interaction was conducted, Guideline adherence scores
what was said against a content standard. EXCLUDES discrete clinical
decision content such as which treatment or referral
(→ Treatment/clinical accuracy) and turn-level conversational move
prediction scored against annotated corpus labels (→ Other (support
strategy prediction)).

Intervention strategy selection — modality-linked strategy choice
within a therapeutic framework, scored as a discrete choice rather
than as an interactional-process fidelity rating. Use when the paper
separately reports strategy-choice accuracy AND the choice is scored
against a clinically valid alternative set (MI-consistent vs
MI-inconsistent choice; correct next-strategy prediction against
clinician judgment). If the paper folds strategy choice into an
overall fidelity rating, use Therapeutic technique fidelity instead.
If the strategy choice is scored against corpus labels of what a
supporter happened to do next (ESConv-style taxonomies), use
"Other (support strategy prediction)".

Simulation fidelity — when the model plays a client, patient, or
other standardized role, whether the simulated persona is realistic
and faithful to the specified profile: consistency with the case,
clinical plausibility, believability to clinician raters. OBJECT: the
model's portrayal. USE ONLY when the simulator is the SYSTEM UNDER
TEST — the paper's contribution is the simulator itself. When a
simulated client is a benchmark component used to test some other
system, its realism is INPUT QUALITY: record it in the input quality
fields, not as a construct. Human-likeness maps here when scored as
clinical realism (would a clinician find this presentation plausible).
Pure Turing-test framing (can raters tell this is AI) is out of scope.
When the model is the counselor or clinician, its performance maps to
the relevant clinical or relational construct instead.

Professionalism / clinical communication style — the LLM's adherence
to expected professional communication norms in a clinical context:
appropriate medical register, professional tone, absence of
inappropriate humor or casual language, appropriate professional
boundaries in tone. OBJECT: the output. Covers "professionalism,"
"clinical professionalism," "professional expertise," and
"doctor-likeness" when evaluating a CHATBOT clinician's communication
style — NOT when evaluating a SIMULATED clinician's realism (→
Simulation fidelity).

Stigma and harmful-content detection — the LLM classifies text it was
GIVEN as stigmatizing, ableist, discriminatory, or as mental-health
misinformation, scored against human labels. OBJECT: the input. The
model is an annotator here, not a producer. Covers anti-autistic ableist
language detection, MH stigma detection in social media or news, and
classification of MH misinformation and myths. Also covers detection of
harmful MH advice in text the model did not write.
DO NOT confuse with Fairness / equity, which means a PERFORMANCE GAP
measured across demographic or clinical subgroups — that requires a
disaggregated comparison, not a discussion of bias. DO NOT confuse with
Safety, which applies when the LLM's OWN output is scored for harm. See
REPRODUCE / PERFORM / DETECT for the three-way split. The corresponding
mental_health_domains are Stigma, Bias, or Misinformation.

Clinical documentation quality — the LLM produces a clinical DOCUMENT
about an encounter (progress or session note, intake write-up, discharge
or referral summary, structured chart entry, SOAP note, treatment plan)
and what is scored is the QUALITY OF THAT DOCUMENT. OBJECT: the model's
own output. Covers completeness against required elements, factual
faithfulness to the source encounter, absence of fabricated or
hallucinated detail, appropriate clinical register, and fitness for the
medical record. The reference standard is typically a clinician-written
note, a documentation rubric, or clinician ratings of the generated note.

DO NOT confuse with Psychotherapy process annotation, which scores labels
the model applied to SOMEONE ELSE'S behaviour. Ask what the deliverable
is: a set of labels over a transcript is annotation; a written document
about the encounter is documentation quality.

DO NOT confuse with Therapeutic technique fidelity, which scores how the
SESSION was conducted. A model that summarises a human counselling
session is not doing therapy; it is writing about therapy. If the paper
scores the summary AND scores the session's MI adherence through that
summary, those are two constructs and the notes should say which
measurement drove which.

DO NOT use for generic text summarisation with no clinical-record
purpose, and do not use it merely because Summarization appears in
system_tasks — that field records the task format, this one records what
was scored. Bare similarity metrics (ROUGE, BERTScore) over a summary
with no qualitative dimension are governed by the BARE AUTOMATED METRICS
rule, not by this construct.

Psychotherapy process annotation — the LLM applies a psychotherapy
taxonomy to a counsellor's or client's behaviour in a transcript, and
the labels are scored against human annotation. OBJECT: the input.
Covers client-resistance coding (PsyFIRE, Client Resistance Observation
Scheme), MITI and MISC behaviour coding applied BY the model to human
sessions, change-talk and sustain-talk classification, alliance-marker
detection, and therapist-technique labelling.
DO NOT confuse with Therapeutic technique fidelity, which scores the
LLM'S OWN therapeutic conduct against a manual. The same instrument
appears on both sides: MITI applied by the model to a human transcript
is annotation; MITI applied to the model's own counselling turns is
fidelity. Ask whose behaviour the score is about. See FIDELITY vs
ANNOTATION.

OTHER() IS NOT A BYPASS AROUND THE EXCLUSIONS (added 2026-08-29.10,
restoring a rule lost between versions). Other(specifier) exists for a REAL
construct the vocabulary happens to lack a term for. It must NEVER be used to
house something the out-of-scope list rules out. If a dimension is excluded,
the correct action is to leave it in evaluation_constructs_described, record
its metric in scoring_procedures, and map NOTHING. An excluded dimension does
not become recordable by being renamed.

The reasoning that produces this error, verbatim from a real record: "retained
as Other (LLM-judge vs expert correlation) rather than Evaluation/judging
because the controlled vocabulary term Evaluation/judging is not in the
evaluation_constructs_categories vocabulary." That is correct about the
vocabulary and wrong about the conclusion. A term being absent from the
constructs list is not evidence that a construct is missing; it is usually
evidence the thing is not a construct.

WORKED CASE — JUDGE RELIABILITY. A judge's agreement with a human standard is a
validity check on the MEASURING APPARATUS, not a capability of any system under
test. It is already fully represented: Evaluation/judging in system_tasks, and
LLM as judge/evaluator in systems_tested. It is not a construct, and
Other(judge...) is not a workaround. The same applies to inter-rater and
inter-annotator agreement among humans.

TEST BEFORE WRITING ANY Other(): (1) Is the thing scored a capability of a
system under evaluation? If it scores the apparatus, the raters, or the client,
the answer is no. (2) Is it on the out-of-scope list, or a synonym of something
on it? (3) Is it already carried by system_tasks, systems_tested, or
scoring_procedures? Any yes means do not record it.

Other (specifier) — any scored construct no category above fits AND
that is not on the out-of-scope list. Write inline with a specifier
naming the construct. STANDARD SPECIFIER — use "Other (support
strategy prediction)" verbatim for turn-level conversational move
prediction scored against annotated corpus labels (ESConv's eight
support strategies and similar taxonomies). These gold labels are
DESCRIPTIVE — what a supporter happened to do next — not normative,
which is why this is not a clinical construct. Consistent wording
keeps the residue countable for a later decision about promoting it.
Named multi-dimensional frameworks whose dimensions do not map cleanly
(Sekhon Theoretical Framework of Acceptability, Technology Acceptance
Model, System Usability Scale) are ONE paradigm — record as
"Other (framework name)" with the framework identified. Do NOT split
framework dimensions across near-mappings; that produces false-friend
confusion (e.g. Sekhon "coherence" is the user's understanding of how
the intervention works, unrelated to response coherence) and loses
the framework identity.

== SYSTEMS TESTED (controlled vocabulary) ==

LIST EVERY SYSTEM CLASS SCORED, INCLUDING COMPARATORS. This field is not
"the paper's proposed system"; it is every kind of system whose output was
scored on the paper's apparatus. A paper proposing a retrieval-augmented
pipeline AND reporting baseline results for the bare LLMs it wraps has TWO
values: Other multi-component pipeline output AND LLM alone. Recording only
the headline system loses the comparison, which is usually half the paper.

LLM alone / LLM as judge/evaluator (LLM's judging behavior itself under
evaluation) / Reward model (RLHF/preference/DPO-style scoring model whose
scoring behavior is itself under evaluation — distinct from LLM as judge
because reward models are purpose-built scoring heads, not general LLMs
prompted to judge) / Guardrail/safety classifier alone / Conversational
agent (end-to-end) / Other multi-component pipeline output.
Select all types tested across the paper.

Boundary between LLM alone and Conversational agent (end-to-end):
- LLM alone: includes bare API calls AND prompt-only configurations
  (system prompt, persona instructions, few-shot examples, chain-of-thought
  prompting). A persona-prompted LLM ("You are a psychiatrist...") without
  external components is still LLM alone.
- Conversational agent (end-to-end): requires SUBSTANTIVE EXTERNAL
  components beyond a prompt — RAG or retrieval, knowledge base, upstream
  classifiers or ML components feeding the LLM, guardrails, explicit
  conversational state management, tool use, or a full multi-turn dialogue
  system.

== EVALUATED OUTPUT TYPES ==
What the evaluated system's OUTPUT IS as a data structure, across the
paper's arms, deduplicated. Different from system_tasks (what the model
is doing).

- Generated text: open-ended text output judged on content, quality, or
  safety (free-text answers, therapist replies, summaries, chatbot
  messages, generated vignettes).
- Label or class: discrete categorical output — class label, tag,
  diagnosis category, severity tier, MCQ letter, binary yes/no. Scored
  by exact match, accuracy, F1, and similar.
- Score or rating: numeric or ordinal score emitted by the MODEL
  (predicted PHQ-9 severity as continuous 0-27, predicted Likert item,
  model-produced rating on a scale). Scored by RMSE, MAE, correlation,
  CCC, and similar.
- Mixed: an arm combines two or more output types (e.g. free-text
  answer PLUS confidence score).

Same TASK can have different output types — a QA task with free-text
answers is Generated text; the same QA task with MCQ options is Label
or class. Different scoring machinery.

== INPUT FORMATS (controlled vocabulary) ==
Multiple-choice questions (MCQs) / Question-answer pairs (includes advice-
column Q&A and long-form help-seeking letters with expert replies) /
Clinical vignettes (CLINICIAN-FACING third-person case narratives; not
patient-generated or first-person text) / Transcripts (interviews,
sessions, hotline calls — transcribed clinical/research sessions fed to
the LLM as input; LLM does not participate) / Social media / online
content (user-generated content posted to online platforms, ANY modality
— peer-directed text, help-seeking on consultation/support forums, Q&A
platform posts, user-uploaded video/audio; classify by platform
interaction model, not modality) / Chat logs (PRE-EXISTING real human
conversations fed as input) / Simulated dialogues/patient interactions
(PRE-EXISTING LLM-simulated conversations fed as input: TherapyGym,
Patient-ψ, ESC-Eval, role-play corpora) / Interactive dialogue (simulated
or live users — LLM PARTICIPATES in a live session producing turns in
real time; interlocutor may be human or simulator) / Journal/diary
entries (patient journaling, real or synthetic) / Personal narratives
(autobiographical or projective first-person narrative material from any
source — early memories, TAT-style stories, SCORS-G psychotherapy
narrative, memoir excerpts, oral histories) / News/media articles
(published news content evaluated by the model) / Clinical notes
(free-text clinician documentation) / Audio recordings / Video recordings /
Images / Structured forms/checklists / Structured/tabular data (numeric/
categorical features, possibly serialized into text prompt) / Free-text
prompts (researcher-written stimuli that are the test input) / Other
(specify).

Chat logs vs. Simulated dialogues vs. Interactive dialogue — the
distinction is WHEN the interaction happens:
- Chat logs / Simulated dialogues: pre-recorded conversation given to the
  LLM as input; LLM sees a transcript.
- Interactive dialogue: LLM's turn-by-turn responses ARE the evaluation
  artifact; LLM participates in a live session (regardless of whether the
  interlocutor is a real human or a simulator).

Classify by NATIVE form, not by prompt serialization. Tabular features
serialized as CSV text remain Structured/tabular data. User-uploaded video
or audio on a platform (YouTube, TikTok, podcasts) goes under Social media
/ online content, not under Audio/Video recordings.

== INPUT PROVENANCE TYPES ==
Who created the input items across the paper's arms, deduplicated.
Answers "where did the items come from," not "is the data released."
Item release is captured separately in input_availabilities.

- Third-party: items created by other researchers (established
  benchmarks like DAIC-WOZ, ESConv, PsyQA, CounselChat, USMLE, PRITE,
  MRCPsych, MedQA, Dreaddit, EmpatheticDialogues, CLPsych). Subsets of
  a third-party benchmark are still Third-party.

- Author-created: items created by the AUTHORS of this paper. Includes
  clinician-authored vignettes, IRB clinical data collected for this
  study, LLM-generated inputs, scraped-and-curated data, ad hoc author-
  authored questions. Release status does NOT change this — an author-
  created dataset that the authors release is still Author-created here.

- Mixed: a paper uses BOTH types across arms — deduplicate in this list,
  so a paper with one Third-party arm and one Author-created arm lists
  BOTH (['Third-party', 'Author-created']), not ['Mixed']. Use 'Mixed'
  only for a single arm that draws from both sources and cannot be
  cleanly separated.

== INPUT AVAILABILITIES ==

CODE THE CURRENT STATE, NOT A PLAN. "We plan to release", "will be made
available upon publication", and "the dataset will be shared" are NOT
Publicly released. If the items cannot be obtained today by the route the
paper describes, they are not released. A paper whose source corpus is
available on request and whose derived set is merely promised is
"Available on request" — one value, not two.

Whether another investigator could OBTAIN or RECONSTRUCT the evaluation
ITEMS themselves — the specific stimuli, cases, prompts, or records
scored. Judge item access ONLY; do not credit release of code, models,
or annotation tooling unless items come with it.

Deduplicate across arms. Choose the best-fitting value per arm.

- Publicly released: items downloadable without gate or request
  (HuggingFace, GitHub, OSF, direct download).
- Available on request: items obtainable via author request, DUA, IRB
  registration, or similar gated access.
MIXED RATER POOLS TAKE BOTH TYPES (2026-08-29.19)
If one arm's raters include BOTH qualified experts and trained
non-experts -- "3 PhD-student annotators and 1 domain expert",
"graduate students supervised by a psychiatrist" -- record
Expert/clinician ratings AND Trained annotator ratings. Do not pick the
more senior label; both rater types are present and both are
informative.

This was the single unstable reference_standard_type cell across 20
papers, and the run that listed both was the most accurate.

WHERE AN LLM JUDGE LANDS (added 2026-08-29.15)
Run the reference_standard_type test PER ARM. If an arm is scored by an LLM
judge and no human or ground-truth comparator exists for that arm, it falls
through to "None -- rubric-only scoring". The judge is the scoring
mechanism, recorded in scoring_procedures; it is not a comparator.

Read the value correctly. "None" scopes the COMPARATOR only. It does not
mean nothing was measured -- a study with neither a comparator nor a
well-defined rubric would not have passed screening. The value asserts two
things at once: no human or ground-truth comparator, AND a defined rubric
was applied.

If the judge was validated against humans, record BOTH arms. The validation
arm takes its own type; the arm the judge actually scored is still
"None -- rubric-only scoring". MindEval is the pattern: 4 psychologists rate
20 interactions in the meta-evaluation, while Claude-4.5-Sonnet alone scores
the 600 interactions behind every headline number. Recording only the first
makes it read as though experts backed results they never saw.

NAMED AUTOMATIC METRICS ARE NOT COMPARATORS (2026-08-29.19)
AlignScore, BERTScore, ROUGE, BLEU, BARTScore, GPT-Score, perplexity
and the like are scoring machinery, not things the outputs were
compared against -- even though they carry proper names that read like
instruments. They go in scoring_procedures only.

Observed error: TN-Eval listed "AlignScore used for faithfulness" as a
reference_standard_description entry while also, correctly, recording
it in scoring_procedures.

COMPARATOR, NOT STATISTICS COMPUTED OVER IT (added 2026-08-29.15)
reference_standard_description names WHAT AN ARM'S OUTPUTS WERE COMPARED
AGAINST. A number computed FROM a comparison is not a comparator:
correlations, inter-rater agreement, Cohen's or Fleiss's kappa, Gwet's AC2,
accuracy against a majority vote, and averages across raters all belong in
scoring_procedures only.

Test: does the line name a person, an answer key, an instrument, or a corpus
(record it here), or a statistic (it does not belong here)? Observed
duplication: CACTUS carried its GPT-4o-vs-expert correlations in both fields;
MindEval carried "average psychologist score across annotators". Lissak is
the correct pattern -- its kappa and correlations sit in scoring_procedures
and are absent from the description.

Never write a reference_standard_type VALUE into the description. That is a
hard reject (check_type_value_not_in_description): the arm is identified
correctly and the answer put in the wrong column, and it is then usually
missing from the type list, so the arm vanishes from any count.

THE INSTRUMENT MUST BE USED AS THE REFERENCE STANDARD (2026-08-29.19)
reference_standard_instruments records instruments the OUTPUTS WERE
JUDGED AGAINST, not every named instrument the paper touches. An
instrument used to BUILD the stimuli -- to write prompts, select or
stratify cases, define severity tiers for sampling, or ground a
scenario -- is apparatus. Note it in abstraction_notes, not here.

Test: were model outputs scored against this instrument? If it never
touches the scoring, leave it out.

Observed error: a chatbot risk-escalation study recorded PHQ-9 here
while its reference standard was an author-defined protocol
(rubric-only) and its scoring procedures counted referral and shutdown
prompt numbers. PHQ-9 shaped the escalating prompts and scored nothing.
Stable across three runs, so a consistent misreading, not noise.

NAMED RUBRICS GROUNDED IN A PUBLISHED FRAMEWORK (added 2026-08-29.14)
reference_standard_instruments now takes study-specific rubrics, not only
off-the-shelf instruments, WHEN the paper states the rubric derives from a
citable published source: professional-body guidelines, a diagnostic
manual, a published scale, or a prior published rubric. Name it as the
paper names it, with the source in parentheses --
"MindEval rubric (APA clinical supervision guidelines)".

THE TEST IS A CITATION, NOT QUALITY. Ask only whether the paper points to
a published source the rubric came from. Do not judge how detailed or
well-anchored it is. Expert authorship without a cited source is still an
author-authored rubric and stays null: MindEval's rubric was written by
four psychologists AND grounded in APA guidelines, and it is the second
half that qualifies it.

Do NOT climb lineage, exactly as for DSM. Record the source the rubric
cites, not that source's ancestry.

THIS DOES NOT MAKE THE RUBRIC A REFERENCE STANDARD. reference_standard_type
asks whether anything external adjudicated these particular scores; this
field asks what measuring device was used and whether it is recognised. A
validated instrument applied by an LLM judge with no human backing is still
"None -- rubric-only scoring" in the type field. CACTUS is exactly that:
CTRS in instruments, rubric-only in type.

Crossing the two fields is the point. Rubric-only WITH an instrument is an
expert-designed evaluation (MindEval, Lissak); rubric-only WITHOUT one is ad
hoc (Hasan's five invented counselling dimensions, WundtGPT's four). That
gradient is invisible in either field alone.

DSM AND OTHER CRITERIA SETS (added 2026-08-29.12)
Record DSM-5, DSM-IV, ICD-10, ICD-11 or RDoC in reference_standard_instruments
when the criteria THEMSELVES are what the outputs are judged against.
MentalBench derives its per-item diagnostic labels from DSM-5 criteria
formalised in a knowledge graph, so DSM-5 belongs there.

Do NOT climb lineage. PHQ-9 and PHQ-8 operationalise DSM major depression
criteria; GAD-7, PCL-5 and CAPS-5 likewise descend from criteria sets. That
ancestry is never recorded. Scored against PHQ-9 -> "PHQ-9". Scored against
DSM-5 criteria directly -> "DSM-5". Both, in different arms -> both. Never
both for the same judgement.

Test: what did the raters or the answer key actually consult? If they applied
a scale, record the scale; if they applied the criteria, record the criteria.
Without this rule nearly every depression paper would count as DSM-based by
descent and the column would separate nothing.

- Fully specified in paper: every item reproduced in text, tables,
  figures, or appendix so the set can be rebuilt exactly.
- Method reproducible, items unavailable: procedure/code/protocol
  released well enough to build an EQUIVALENT evaluation, but the items
  themselves (e.g. PHI clinical records, proprietary transcripts) cannot
  be obtained.
- Partially specified: illustrative items shown but full set not
  recoverable.
- Not available: neither items nor a reconstructible procedure reported.

Replaces the older input_reproducibility field.

== INPUT STANDARDIZATIONS ==
Whether inputs are FIXED / reproducible or generated / drifting, rolled
up across the paper's INCLUDED arms. Answers: "if another researcher
re-ran this evaluation, would they see the same inputs?"

Different from input_provenance (who created it) and input_availability
(release status). Different from conversation_type (turn structure) —
multi-turn papers can still be Fixed if they feed pinned dialogue
histories.

Categories:

- Fixed: input items were determined BEFORE the
  evaluation began and did NOT change during it. The same set was used
  across every system tested and every run.
  * Provenance is IRRELEVANT to this field. Items scraped from social
    media, curated from clinical records, drawn from an exam bank, or
    LLM-generated in advance all code Fixed once frozen before
    evaluation.
  * NON-EXCLUSIVE: record EVERY mechanism that applies. A paper with a fixed opening and a model-generated remainder is BOTH Fixed and Dynamic; do not choose between them. (The former precedence rule that forced a single pick was deleted 2026-08-29.11 as the cause of this field's instability.) 

- Stochastic: inputs drawn or generated fresh per
  trial or per model (LLM-simulated patient scenarios, simulator-produced
  user turns, random large-corpus sampling without a fixed sample, ad
  hoc constructed prompts). Not reproducible without the sampling /
  generation procedure.


  GENERATION AT CONSTRUCTION TIME IS NOT STOCHASTICITY (2026-08-29.18).
  The test is whether inputs are REGENERATED WHEN A NEW SYSTEM IS
  BENCHMARKED, not whether generation happened at all. A synthetic
  corpus generated once, frozen, and reused unchanged for every system
  is Fixed and ONLY Fixed, however it was produced.
    MentalBench  24,750 cases generated once and frozen; every model
                 sees the identical set -> Fixed alone. Coding it
                 Stochastic because the cases are LLM-generated is an
                 error observed in testing.
    MindEval     fixed pool of 50 profiles, but a fresh set of
                 interactions each time a system is benchmarked ->
                 Fixed AND Stochastic AND Dynamic.
  Ask: if I benchmark a new model tomorrow, does it face the same
  items? Yes -> Fixed.

- Dynamic: later inputs depend on earlier
  model outputs (multi-turn interactive evaluations beyond the opening,
  agentic workflows, self-play LLM-vs-LLM). Each session is a unique
  trajectory.

- Live: real users of a deployed system; drifting over time;
  not reproducible.

- Mixed or unclear: use ONLY for genuine multi-arm mixtures within one
  paper (one included arm fixed, one included arm live) OR for papers
  that don't describe input structure clearly enough to classify — not
  for uncertainty about rater coverage or provenance.

== POPULATIONS ==
Who the inputs represent. High-level, population-focused.
E.g. 'adults with depression', 'adolescents with anxiety', 'psychiatric
outpatients', 'general public', 'mental health clinicians'.
Do not indicate real vs. synthetic — just the represented population.
Deduplicate across arms.

Use "Not applicable" ONLY when the input has no represented population —
pure knowledge or factual questions ("Which SSRI has the shortest
half-life?", "Define bipolar disorder"), definitions, terminology quizzes,
or generic prompts where the LLM is answering about FACTS rather than about
a person or population.

Format is not the deciding factor — what matters is what the LLM is being
asked to reason about. If the input consists of case vignettes, patient
scenarios, symptom presentations, or clinical descriptions — EVEN when
drawn from exam banks, textbooks, or casebooks — the population is who
those cases represent.

Examples:
- Portuguese national residency knowledge-recall questions (facts, no
  vignettes): "Not applicable"
- PsychiatryBench cases from authoritative psychiatric textbooks and
  casebooks: "adult psychiatric patients as represented in authoritative
  psychiatric textbooks and casebooks"
- USMLE psychiatry MCQs with case vignettes: "adult patients as depicted
  in board-exam case vignettes"

== OUTPUT AUDIENCES ==
Target audience(s) for the LLM's outputs across the paper's INCLUDED
arms, deduplicated. Who the LLM's response is INTENDED FOR — distinct
from populations (who inputs represent).

- Patient / Consumer: lay user, patient, help-seeker (chatbot user,
  help-seeking letter response, self-help content).
- Provider: healthcare provider, clinician, physician, therapist,
  licensed practitioner, OR trainee in a provider-oriented role
  (medical student, resident, counselor-in-training). Covers clinical
  decision support, differential diagnosis, treatment recommendation,
  chart review, exam-answering for provider trainees, and
  training-scenario content.
- Researcher: LLM output serves research (data annotation, coding,
  classification, benchmark scoring).
- Mixed: value used only if a single arm targets multiple audiences.
- Not applicable: LLM capability testing without a specific intended
  audience (pure knowledge testing, exam-answering where LLM is scored
  on correctness rather than serving anyone).

Population and audience often align but can diverge. Example: paper
evaluates chatbot serving depressed users but the paper's EVALUATION
rates clinician-perceived response quality. The LLM's audience is still
Patient / Consumer (who the responses are FOR), not Provider (who
happens to rate them).

Deduplicate across arms — a paper with clinician-facing and patient-
facing arms lists both.

== INPUT REALITY ==

What the input material IS. This field is deliberately ORTHOGONAL to
INPUT PROVENANCE TYPES, which asks who assembled the item set. Answer them
independently; never let one drive the other. All four combinations occur:

                        Third-party            Author-created
  Real                  DAIC-WOZ transcripts   IRB clinical records collected
                        reused from prior work for this study
  Synthetic —           A vignette taken from  Clinician-authored vignettes
  human-written         an earlier paper       written by this team
  Synthetic —           An LLM-generated       Patient scenarios this team
  LLM-generated         benchmark released by  generated with GPT-4
                        another group

Real: material that arose from actual human activity outside the study —
clinical records, therapy or hotline transcripts, social-media posts, forum
threads, exam question banks, published corpora of naturally occurring text.

Synthetic — human-written: material a person wrote for research or assessment
purposes rather than in the course of real life — clinician-authored vignettes,
researcher-written prompts, constructed case scenarios, hand-built question sets.
This holds whether the writer was an author of THIS paper or of a prior one. A
vignette reproduced from an earlier publication is Synthetic — human-written,
with input_provenance_types = Third-party. Do not reason about authorship here.

Synthetic — LLM-generated: material produced by a language model or simulator —
LLM-generated patient scenarios, simulator dialogue turns, model-authored
vignettes. Keep this separate from human-written synthetic material: whether an
evaluation set was itself machine-generated is a live validity question in this
literature and the review needs to be able to report it.

Mixed: a single arm combines two of the above and they cannot be cleanly
separated. When different arms have different answers, list both values rather
than using Mixed.

Not reported: the paper does not say.

== INPUT LANGUAGES ==
Language(s) of input data across the paper, deduplicated. Canonical
English names.

Use: English, Mandarin (not Chinese), Standard Arabic if specified
(otherwise Arabic), Spanish, French, German, Hindi, Japanese, Korean,
Portuguese, etc. A multilingual benchmark lists all languages
(['English', 'Mandarin', 'Spanish']).

Use ['Not reported'] if language is not specified. Do not infer language
from author affiliation. For code-switched or mixed-language inputs,
list all languages present.

== CONVERSATION TYPES ==
How stimulus is structured and how model outputs relate to prior outputs,
rolled up across the paper.

Single-shot: stimulus is not a dialogue (MCQ, vignette,
  post, document, standalone question); model produces one scored output
  per item.
Single-shot: stimulus is or contains a dialogue, but model
  produces ONE scored output per item AND its own prior outputs never
  appear in its input. Covers dialogue classification / scoring and
  next-response generation on gold history.
Multi-turn interactive: model produces outputs at multiple points in an
  evolving exchange with an interlocutor (real user, scripted, or LLM
  seeker-simulator); later turns are conditioned on the model's own
  earlier outputs. LLM-vs-LLM self-play qualifies.
Mixed: paper includes arms of more than one type.
Not applicable: LLM does not produce outputs in the paper (benchmark-
  development papers with no reported model results).

Distinguishing test between Single-shot and Multi-turn
interactive: does the model's own earlier output feed back into its later
input? If yes → Multi-turn interactive; if no → Conversational
single-shot.

== REFERENCE STANDARD TYPE ==
Pick the type(s) used across the paper (list all that apply — a paper may
have different types across arms). Apply this test IN ORDER — stop at the
first match:

(1) Is the output matched against a defined correct answer, target, or
    validated instrument-as-target?
    -> "Ground-truth reference"
    (Any rubric here is only the scoring mechanism -> scoring_procedures.)

(2) If no correct answer: are QUALIFIED EXPERTS (clinicians, licensed
    professionals, domain experts) applying a validated framework or
    calibrated judgment as the comparator?
    -> "Expert/clinician ratings"

(3) If not experts: are TRAINED NON-EXPERT annotators (research assistants,
    undergraduates, crowdworkers under expert-designed guidelines, coders
    not described as clinicians) applying a defined rubric?
    -> "Trained annotator ratings"
    Common for social media benchmarks, crowd-labeled classification data,
    and NLP corpora. Two human raters described as "coders" applying a
    researcher-authored rubric = this category.

(4) If none of the above — no ground truth, no independent humans applying
    the rubric consistently (including unvalidated LLM-as-judge rubrics),
    OR human evaluation is mentioned but no rubric, rater qualifications,
    or scoring procedure is disclosed?
    -> "None — rubric-only scoring"
    Residual bucket for evaluations without sufficient documentation to
    support a stronger type. Vague human evaluation ("two evaluators judged
    responses satisfactory") with no rubric or qualifications lands here.

RULES:
- A rubric is NOT a reference standard by itself. What sits BEHIND the
  rubric decides the type.
- Do NOT default rubric-scored papers to (4). Clinician-applied rubric = (2);
  trained-coder-applied rubric = (3); truly unbacked rubric = (4).
- Input being a conversation or document does not create a ground truth;
  judge what the OUTPUT is compared to.
- A paper may have DIFFERENT types across arms — list all that apply.
  Example (Adhikary et al.): ROUGE arm scored against gold summaries =
  (1) Ground-truth reference; expert Sekhon-framework arm = (2) Expert/
  clinician ratings. Result: ["Ground-truth reference", "Expert/clinician
  ratings"] — neither is (4).

WORKED EXAMPLE — LLM judge with expert reference answers:
An LLM judge (e.g., GPT-4 as evaluator) scores generated responses using a
semantic similarity rubric against expert-authored reference answers from
validated textbooks. Reference standard type = "Ground-truth reference" —
the reference answers ARE the defined target. The LLM judge and similarity
rubric are the scoring mechanism (LLM judge in evaluation_engine, similarity
rubric in scoring_procedures). This is NOT rubric-only, even though the
scoring uses a rubric — the rubric is measuring similarity to a defined
ground truth.

== REFERENCE STANDARD DESCRIPTION ==
Deduplicated list of what performance was judged AGAINST across the
paper's INCLUDED arms. Name the comparison target itself, not who
applied it. Rater credentials go under scoring procedures / evaluation
engine.

Examples: 'PHQ-8 scores', 'DSM-5 criteria', 'MINI-KID clinician-
administered risk classification', 'consensus labels from 2 licensed
clinicians', 'NICE guideline recommendations', 'human counselor responses
from CounselChat', 'USMLE answer key'.

If any INCLUDED arm reports only that an expert reviewed or rated the
outputs WITHOUT specifying what constitutes a correct or adequate
response, use 'None stated' for that arm — an evaluator's unanchored
judgment is NOT a reference standard.

THE TYPE VALUE GOES IN reference_standard_type, NOT IN THE DESCRIPTION
(fixed 2026-08-29.15). This guide previously said to include the literal
string 'None — rubric-only scoring' in reference_standard_description.
That duplicated a controlled value of reference_standard_type into a
free-text field, and let a record satisfy the instruction WITHOUT adding
the value to the type list. Lissak did exactly that: description item 2
read "None — rubric-only scoring (for automatic LLM-judge evaluation
arms)" while the type list held only Expert/clinician ratings and Trained
annotator ratings.

Instead: DESCRIBE the arm in plain terms in the description -- e.g.
"GPT-4o applying the 5-axis rubric, no human backing for these scores" --
and record 'None — rubric-only scoring' in reference_standard_type.

COMPARATORS ONLY, NOT STATISTICS COMPUTED OVER THEM (added 2026-08-29.15)
Each description item names WHAT AN ARM'S OUTPUTS WERE COMPARED AGAINST.
Numbers computed FROM a comparison are not comparators: judge-vs-human
correlations, inter-rater kappa or agreement rates, and averages across
annotators all belong in scoring_procedures and nowhere else. CACTUS's
"Pearson/Spearman/Kendall correlation of GPT-4o scores with expert
scores" and MindEval's "Average psychologist score across annotators"
were both duplicated into the description while already correctly present
in scoring_procedures. Lissak is the counter-example done right: its
Fleiss's kappa and Spearman correlations are in scoring_procedures and
correctly absent from the description.
TEST: if the line describes a number derived FROM the standard rather
than the standard itself, it is in the wrong field.

RUBRIC QUALIFICATION TEST — a rubric passes ONLY if a second, independent
panel could apply it to the same outputs and be expected to produce
comparable scores. Minimum requirements:
(a) Each rated construct is a separate item. A rubric item bundling
    "empathy AND clinical accuracy AND coherence" into one 1-5 rating
    fails — per-construct performance is not recoverable.
(b) Each item states what distinguishes higher from lower scores beyond
    restating the construct name. Endpoint labels alone ("0 = none,
    10 = high") are scale direction, not a rubric.
(c) Multi-construct items fail — a single score covering two constructs
    is not attributable to either.

Rubrics failing any of the three do not qualify as reference standards
even if the paper calls them a rubric. Enter 'None stated' and include
'None stated' in reference_standard_description for those arms.

== REFERENCE STANDARD INSTRUMENTS ==
List of validated clinical or research instruments used as reference
standards across the paper, deduplicated. Canonical acronyms; None if no
validated instrument is used.

Purpose: keep instrument names out of benchmark_names — instruments used
to score LLM outputs are not benchmarks. This field enables downstream
analysis of which validated instruments are used as reference standards
across the review.

When to populate: only when the LLM's outputs are scored against scores
or labels from the instrument, or when raters apply the instrument to
evaluate LLM behavior. If the LLM SEES the scale items as input, the
scale belongs to benchmark_names, not here.

Common instruments (not exhaustive):
- Depression: PHQ-9, PHQ-8, BDI, BDI-II, HAM-D, HAMD-17, MADRS, CES-D
- Anxiety: GAD-7, HAM-A, BAI
- Suicide/self-harm: C-SSRS, SBQ-R, ASIQ
- PTSD: CAPS-5, PCL-5, PDS
- Psychosis/schizophrenia: PANSS, BPRS
- Bipolar: YMRS, MDQ
- Well-being / QoL: WHOQOL, SF-36, WEMWBS, PERMA
- Therapeutic alliance: WAI, BLRI
- Therapy technique fidelity: CTRS, MITI
- Affect: PANAS

Leave None when reference standards are author-authored rubrics, exact
match to gold responses, LLM-judge scoring without an instrument, or
rubric-only.

== SCORING PROCEDURES ==
List all scoring procedures used across the paper's INCLUDED arms,
deduplicated. Must name what the procedure produces: a metric, scale,
count, or structured category assignment.

INCLUDED ARMS ONLY: exclude procedures belonging solely to arms that
failed the relevance gate — a method used only to score a non-generative
or otherwise excluded system does NOT appear here, even when that
system is the comparator the included system was tested against. Where
an arm's inclusion is unresolved, list the procedure and note the
dependency in abstraction_notes.

E.g. 'accuracy and macro-F1 against reference labels',
'5-point Likert per dimension averaged across 3 raters',
'binary safety flag per response, percentage flagged reported',
'9-item adherence checklist scored 0/1, summed',
'ROUGE-L against reference answer',
'Pearson correlation of LLM score to clinician PHQ-9 score'.

Narrative impressions, unstructured commentary, or qualitative
description that yields NO score, rating, or systematic category are
NOT scoring procedures — use 'None stated' for those included arms.

Do NOT include the judge/rater here (belongs in the underlying instance
records, not this rollup field).

WORKED EXAMPLE — Three studies. Studies 1-2 and one Study 3 arm use
BERT embeddings + ridge regression with nested 10-fold CV, reporting
one-tailed Pearson r and RMSE. A second Study 3 arm prompts GPT-3.5
and GPT-4 to rate the same responses, reporting two-tailed Pearson r
plus Williams's and Steiger's tests. Only the GPT arm passes the
generative-LLM criterion. scoring_procedures =
["Two-tailed Pearson correlation between model-assigned rating and
validated self-report score", "Williams's test for dependent
correlations", "Steiger's test for dependent correlations",
"FDR correction"]. The ridge regression pipeline, nested cross-
validation, one-tailed correlations, and RMSE do NOT appear — they
score BERT, an excluded system, and BERT's role as comparator does
NOT change this.

== ABSTRACTION FLAGS + NOTES ==
Free-form notes for anything about the paper that was unclear or
confusing to you during abstraction. Populate BOTH fields together, or
leave BOTH null.

- abstraction_flags: a list of field names where interpretation was
  genuinely uncertain — a different reader could reasonably code the
  field differently, OR you had to make a call that felt fragile.
  Common candidates: system_tasks, evaluation_constructs_categories,
  reference_standard_type, reference_standard_description,
  type_of_study, benchmark_names. Do NOT use for missing information
  — if the paper doesn't report something, that's the field's own
  value (None stated, empty list, etc.), not a flag.
- abstraction_notes: free-form prose accompanying the flags. Required
  if abstraction_flags is non-null. For each flagged field, name the
  alternative interpretation and briefly explain what made the call
  unclear.

If nothing was genuinely uncertain, leave both null. Do not flag every
paper reflexively.


== OUTPUT ==
Output ONLY valid JSON matching the schema. No prose, no markdown fences,
no commentary before or after the JSON.
"""
