# Benchmark Quality Rating Checklist (v6.1)

**How to use.** For each criterion, answer the questions in order; the first "yes" gives the step code. **Once any criterion is Poor, stop** — leave the rest of that dimension blank. Otherwise code every criterion. The workbook computes the dimension totals.

**What you are rating.** *Items*: what the model is given. *Reference standard*: what outputs are compared with (labels, answer key, human ratings). *Scoring*: how the comparison becomes a number. Pre-labeled items: the text or question is Inputs, the label is Reference standard. Tags that categorize items (topic, competency, difficulty) are item metadata, not the reference standard.

**Headline only.** Rate the procedure(s) whose results the paper presents as benchmark results — in the abstract, the main results tables or figures, or as a stated research question. If two such procedures exist, rate the weaker. A judge, panel, or metric used only in a secondary analysis (a sampled error analysis, a case study, an appendix-only check) does not drive a rating. Narrative or purely descriptive "qualitative evaluations" are out of scope.

**Evidence = this report only.** Rate on what the report says, including its summary of a cited source paper. Do not consult the source paper or fill gaps from what you know about a dataset.

**Three kinds of "no."** *NA* — the criterion does not apply. *NR* — the criterion applies but the report says nothing that answers it; choose NR only when nothing in the report bears on the question (a partial description is rated on what it says). *Poor* — the report states something deficient, or (IA1, RD1 for own labels, SA1, SB1) is silent where silence itself is the deficiency.

**Reformatted vs generated.** Third-party data the authors only reformat (templated, chunked, truncated, translated) is still third-party. Third-party data used as a **seed** to make new items (LLM-simulated dialogues from real profiles) is author-created.

**LLM-as-judge / LLM-as-instrument studies** (the paper measures how well an LLM rates or scores): the LLM measured is the system under test; the reference standard is the human ratings or diagnoses it is compared with; scoring is the statistical comparison (SA0). This holds even when the paper calls the LLM a "judge" or "annotator": if the paper's question is how well the LLM rates, the LLM is the system under test and its agreement with humans is the result, not a judge-validation statistic (EPITOME as used by Lee 2026).

---

## INPUTS

### IA. Validation — was the item set independently checked before use?
*Look for:* "Quality control", "Expert review", "reviewed by", "two annotators", "kappa", "panel".

| Step | Question | If yes |
|------|------|------|
| IA0 | Third-party benchmark whose validation this report does not describe — and the items are neither a validated published instrument nor an official examination? The items are scored as they came (or only reformatted: templated, chunked, translated), not generated from them. | **NA** — stop |
| IA1 | Author-created or LLM-generated items with no review described? This includes new items **generated from** third-party material used as a seed (LLM conversations built from real posts or profiles; vignettes written from records) when no review of the generated items is described. Filtering or screening items by rules — even rules built from a hand-annotated sample — is not a review of the items; a review means people read the items against criteria. | **Poor** — stop |
| IA2 | Reviewed by two or more reviewers with agreement reported; **or** by reviewers outside the author team (independent panel, examination board); **or** a validated published instrument with cited psychometrics (RMET, LEAS, PHQ-9 items)? | **High** — stop |
| IA3 | Otherwise — review by the author team (including clinician co-authors) without agreement statistics; a single reviewer; a spot-check Generated items reviewed on a sample only: IA2 if the reviewed sample is the benchmark itself (the items scored are the ones reviewed, with agreement reported); otherwise a sampled or spot review is IA3, and a review of the seeds rather than the generated items is no review (IA1). | **Adequate** |

*A documented read-through of every item by qualified reviewers counts, whatever its stated purpose (two psychiatrists tagging each question's competency → IA2). It does not validate the answer key — that is RD.*

### IB. Informants — who created the items?
*Who wrote or assembled the items, not who labeled them (labelers → RA).*

| Step | Question | If yes |
|------|------|------|
| IB0 | No human created the items (LLM-generated)? | **NA** — stop |
| IB1 | Created by named domain experts — a stated profession is enough ("psychiatrists", "licensed psychologists"); exam boards and instrument developers count? | **High** — stop |
| IB2 | Crowdworkers, students, research team, authors without a stated domain background; "experts" or "annotators" not characterized; the public or service users whose own words are the items (social media posts); filmmakers or other non-expert originators of found material | **Adequate** |
| IB-NR | Otherwise — the report says nothing about who wrote or assembled the items (a dataset cited by name only) | **NR** |

*"Created" covers producing and compiling: if either is a named expert body, IB1; otherwise IB2. If the report names the source platform or population, the creators are known (IB2), not NR. Labelers' credentials do not set IB (CRADLE BENCH: clinicians labeled, authors collected from Reddit → IB2). An LLM that only elicits human responses (a chatbot interviewer) does not create them — the people who answered do (participants' answers → IB2). When the items are conversations between people and a chatbot, rate the people who took part (IB2, or IB1 if clinicians); the chatbot's turns do not change IB. If the chatbot in the conversation is the model being evaluated, the items are the human side only.*

### IC. Source — what kind of material are the items?

| Step | Question | If yes |
|------|------|------|
| IC1 | Real material from the target setting — clinical interviews, health records, clinician notes, items from an **official** licensing or board examination, items of a validated instrument, published expert case material? | **High** — stop |
| IC2 | Otherwise — social media or forum posts; crowdworker or participant role-play; conversations collected outside a clinical setting (including clinicians or students acting as patients); **mock or preparatory** exam items; expert-written vignettes; LLM-generated items | **Adequate** |

---

## REFERENCE STANDARD

**R0 is pre-specified in the workbook**, with a one-line description of the standard to rate. The rule: did a person, exam board, or validated instrument decide the correct answer or label before the model was scored? Yes → R0-applies. Outputs judged only at scoring time by an LLM, classifier, or rule — even an LLM following a human-written rubric → R0-NA (the judge is rated under SA). Human raters applying a rubric to each output **is** a reference standard. Labels made by an LLM *before* scoring and then used as the "ground truth" (e.g. GPT-4o-assigned severity labels) are also a reference standard: R0-applies, then RA1. If you think the pre-specified standard is wrong, change R0 and say why in Notes.

*Look for:* "Ground truth", "Labels", "Annotation", "Human evaluation"; instrument names (PHQ-9, HAM-D, C-SSRS, CTRS, MITI); "diagnosed by", "annotated by", "majority vote", "kappa", "subreddit". This dimension is about the labels, not the medium: social-media or synthetic text is rated under IC and must not lower these ratings.

### RA. Authorship — who produced the labels or ratings?

| Step | Question | If yes |
|------|------|------|
| RA1 | Labels inherited from subreddit membership, hashtags, or a self-declared diagnosis with no per-item human labeling (proxy labels); or produced by an LLM? | **Poor** — stop |
| RA2 | Produced by qualified experts (clinicians, licensed professionals, domain experts), the instrument's developers, or an examination authority? | **High** — stop |
| RA3 | Trained non-expert annotators (research assistants, students, crowdworkers, "coders"); "experts" or "annotators" of unstated qualification; the authors themselves for items they made | **Adequate** |
| RA-NR | Otherwise — the report never mentions that anyone labeled the items ("posts are split into three classes"; a dataset cited by name; a target variable named with no account of how it was recorded) | **NR** |

*Recorded values: a target supplied with a dataset counts as an answer key or recorded value only if the report says what recorded it (an exam key, a named instrument score, a chart diagnosis); if only the variable is named ("stress-resilience index"), RA, RB and RD are not reported.*

*RA3 needs some mention of the people who labeled; if no one is mentioned, RA-NR. Do not infer labelers from the existence of labels, and do not infer proxy labels from a subreddit source unless the report says the labels came from it. Posts collected from a topic subreddit and then labeled per post by annotators are not proxy. Translating, cleaning, or filtering posts is not labeling them: if the class still comes from the source, RA1 (BSMDD).*

### RB. Anchoring — what is the standard based on?

| Step | Question | If yes |
|------|------|------|
| RB1 | No framework, instrument, or clinical assessment behind the labels, **and** the label scheme is unrelated to the construct the benchmark claims to test? | **Poor** — stop |
| RB2 | A **named** published instrument, clinical framework, or guideline (C-SSRS, IMCS, NBCC outline, national diagnostic guideline); an actual clinical assessment or recorded clinical outcome; an examination or item-bank answer key? | **High** — stop |
| RB3 | A rubric, taxonomy, or label scheme the authors wrote — including one designed with clinicians and "grounded in" a cited framework (MindEval, MindGuard); a validated **self-report** instrument | **Adequate** |
| RB-NR | Otherwise — categories listed or implied but no basis given. Dimension names alone ("empathy, relevance, safety") with no anchors, definitions or scoring guidance are RB-NR, not RB3. | **NR** |

*A scheme needs content a second rater could apply: named dimensions with anchors, definitions, or an appendix rubric are RB3 (MindEval, MindGuard); dimension names alone, with no description of what the scale points mean, are RB-NR (Saha 2026: four dimensions rated 1–5 by one psychologist). Citing a framework as inspiration does not make the scheme that framework. Who designed or applied the scheme is RA, not RB.*

### RC. Construct match — does the label measure what the benchmark claims to test?

| Step | Question | If yes |
|------|------|------|
| RC1 | The label records a different construct and the paper does not acknowledge the gap (content-safety category used for clinical appropriateness; stress labels for a depression benchmark)? | **Poor** — stop |
| RC2 | The label is the construct itself (PHQ-9 total for severity; clinician diagnosis for diagnosis; exam key for knowledge; the task's own category — crisis type for crisis detection)? | **High** — stop |
| RC3 | A coarser, finer, or screening version of the construct (binarized severity; a screener for a diagnosis; annotators inferring an instrument score from free text), or an acknowledged mismatch | **Adequate** |
| RC-NR | Otherwise — the report does not say what the labels record | **NR** |

### RD. Verification — were the labels checked?

| Step | Question | If yes |
|------|------|------|
| RD1 | A reported check found faulty labels, or a reported agreement statistic is below 0.20; **or** the labels are the authors' own and the report says nothing about what they are based on and nothing about whether they were checked? | **Poor** — stop |
| RD2 | Inter-rater agreement reported (overall or median value); adjudication or consensus among two or more qualified raters (even without a statistic); a pre-existing validated instrument; a prospective structured clinical assessment; an official examination? | **High** — stop |
| RD3 | Single rater without adjudication; verification described but short of RD2 (spot checks, informal review of some items) | **Adequate** |
| RD-NR | Otherwise — a third-party standard with no verification described | **NR** |

*NR is for third-party standards this report does not describe; for the authors' own labels, silence about both basis and checking is Poor (RD1), as for IA1. Pilot double-annotation with agreement, then single annotation with adjudication of flagged items, is RD2. Agreement must be on the labels used as the standard — all of them or a reliability subset of them. A κ from a training or calibration exercise on other material is rater qualification, not verification: RD3 if a single coder then labelled each item. If the report does not say what the κ was computed on, treat it as computed on the task (RD2). Spot checks and informal looks at a sample are RD3; a reliability subset with a reported statistic is RD2.*

---

## SCORING

### SA. Judge validation — if a human, LLM, or classifier judges outputs, was the judge checked?
*Look for:* "Human evaluation", "LLM-as-judge", "inter-rater reliability", κ, α, ICC, r, ρ, "percent agreement". Note which model judges and which models are evaluated.

| Step | Question | If yes |
|------|------|------|
| SA0 | No judgment layer in the headline procedure — exact match, accuracy, F1, MAE, κ, correlation, or similarity against a fixed reference; or the judge is the system under test? | **NA** — stop |
| SA1 | A judgment layer (LLM judge, human rubric raters, or a learned classifier/reward model) with **nothing** reported about its agreement with human judgment on these outputs; **or** reported agreement below 0.70 (median across dimensions); **or** percent agreement or a match rate only; **or** an unvalidated judge scoring a safety-critical claim? Reliability reported for the rubric or classifier in prior work does not count. | **Poor** — stop |
| SA2 | The judge is a model under test or shares its model family (GPT-4 judging GPT-4o), or its score was a training signal for a system under test? | **Adequate** — stop (Poor if the judge configuration is undisclosed) |
| SA3 | Agreement with **expert** raters on these outputs of **0.90 or more** on a chance-corrected or correlation statistic (κ, α, AC, ICC, r, ρ), median across dimensions? | **High** — stop |
| SA4 | Otherwise — agreement with expert raters of 0.70–0.89; agreement ≥ 0.70 with non-expert humans; a published classifier with agreement ≥ 0.70 checked on these outputs | **Adequate** |

*Agreement reported for dataset construction or label annotation (the reference standard) does not count toward SA, even if the same people were involved. If two judgment layers both carry headline results, rate the weaker.*

### SB. Transparency — could someone reproduce the scoring?
*Item or dataset availability does not belong here.*

| Step | Question | If yes |
|------|------|------|
| SB1 | A rubric or judge prompt that is neither reproduced nor described (dimensions named without anchors; "an LLM judge rated the responses" with no prompt), or the rule for turning outputs into scores is missing? | **Poor** — stop |
| SB2 | Everything the headline procedure **actually uses** is reproduced in the paper, appendix, or a repository the report says holds it: the metric; for free-text outputs, the rule for extracting the answer; for a rubric or judge, the rubric text or judge prompt; aggregation? | **High** — stop |
| SB3 | Otherwise — a rubric or prompt described in prose or partly shown; a manual cited but not reproduced; metric named but extraction rule not | **Adequate** |

*Ask first: what does this paper's scoring consist of? It only has to reproduce the materials its procedure has. Accuracy against an exam key with the prompt quoted is SB2. A repository counts only for the materials the report says it holds; "code is available" does not cover a judge prompt or scoring rule the report does not mention. Raters do not open repositories. Constrained-choice responses, classifier heads, and numeric predictions need no extraction rule. An extraction rule counts as given when the paper says what it is (eg, "regular expressions matching yes/no"; "keyword matching on the disorder name"); the pattern itself need not be shown. If free-text outputs were mapped to labels or numbers and the paper does not say how, SB3.*

### SC. Metric fit — does the metric measure the construct claimed?

| Step | Question | If yes |
|------|------|------|
| SC1 | A text-similarity metric (BLEU, ROUGE, METEOR, BERTScore, cosine) is the **only** headline scoring of clinical reasoning or response quality? | **Poor** — stop |
| SC2 | The headline metric fits the task — exact match, accuracy, F1, κ, or MAE for labeling; MAE or correlation for ordinal or continuous targets; rubric ratings by qualified raters on named dimensions for response quality; any new metric fully defined? | **High** — stop |
| SC3 | Otherwise — a reasonable but imperfect proxy | **Adequate** |

*A similarity metric reported alongside an appropriate headline metric does not lower the rating.*

---

## Worked examples
- **CAMS as used by Yang 2023.** Dataset named, cited, 626 Reddit posts, six cause labels; nothing else. IA0, IB2, IC2 → Adequate. RA-NR, RB-NR, RC2, RD-NR → NR. SA0, SB2, SC2 → High.
- **Taiwan psychiatry licensing exam (Chang 2024).** Official exam: IA2, IB1, IC1. Key: RA2, RB2, RC2, RD2. Accuracy with prompt and statistics stated: SA0, SB2, SC2. High / High / High.
- **CounselingBench (Nguyen 2024).** Mock-exam MCQs: IA2 (two psychiatrists read every item, tiebreak), IB2 (compiled from prep sites), IC2. Prep-site answer key: RA3, RB2 (NBCC outline), RC2, RD-NR. Competency tags are metadata; reasoning-chain ROUGE is secondary. Adequate / Adequate / High.
- **DFEW as used by Le 2025.** "Movie clips annotated with seven emotions", cited. IA0, IB2, IC2. RA-NR, RB-NR, RC2, RD-NR → NR. UAR/WAR, splits and code → High.
- **LifeSnaps as used by Kim 2024.** Prompts templated from third-party sensor records → still third-party: IA0, IB2, IC2. Targets named with no account of how recorded → RA-NR, RB-NR, RD-NR → NR. MAE/accuracy with templates described, but free-text outputs parsed to numbers by a rule that is not shown ("code available" does not cover it) → SB3 → Adequate.
- **Feng 2025.** GPT-4o generates dialogues from ESConv seeds, no review → IA1, IB0, IC2 → Poor. Human IM coders: RA2, RB2 (IMCS), RC2, RD2 → High (κ reported for the coder pairs; if a paper says such a κ came only from training material, RD3). GPT-4o supervisor unvalidated on these outputs → SA1 → Poor.
- **Olufadewa 2025.** Headline is accuracy against PHQ-9 severity labels; the "qualitative" panel is out of scope. IA3, IB2 (research team made the prompts), IC2 → Adequate. RA2, RB2, RC3 (annotator-inferred instrument score), RD3 → Adequate. SA0, SB2, SC2 → High.
- **Jin 2026 (BDI-FS-GPT).** LLM-as-instrument study. IA2, IB1, IC1 → High. RA2, RB2 (national guideline), RC2, RD3 (single psychiatrist) → Adequate. SA0, SB3 (mapping rules not reproduced), SC2 → Adequate.
- **Aremu 2024.** Author-curated true/false items: IA1 → Poor. "We curated a dataset" — RA3, RB-NR, RC2, RD1 (own labels, no basis, no check) → Poor. Accuracy: SA0, SB3 (free-text chatbot answers, mapping rule not stated), SC2 → Adequate.
- **BSMDD (Chowdhury 2024).** Depressive = r/depression + r/SuicideWatch, non-depressive = Sentiment140; seven annotators reach consensus on the *translation* → RA1 → Poor.
- **MindEval (Pombal 2025).** Four clinical psychologists rate 20 interactions with author-written, APA-grounded guidelines; Kendall τ reported. RA2, RB3, RC2, RD2 → Adequate.

## Recording
Per dimension, enter each step code; the workbook computes the total. Use Notes for an R0 override or anything you had to decide. A benchmark proposed with **no model evaluation** has no scoring procedure: enter SA0, leave SB and SC blank (scoring total = NA) and write "not evaluated" in Notes.
