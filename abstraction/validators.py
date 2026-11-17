"""
validators.py — shared consistency checks for the condensed and full
abstraction tools.

Two enforcement modes, deliberately kept distinct:

  HARD REJECT  — raises ValueError, so the runner retries the call with the
                 error text fed back. Reserved for cases where the output is
                 unusable as data: an off-vocabulary category, or a rule the
                 guide states as an invariant with no legitimate exception.

  SOFT FLAG    — appends to abstraction_flags / abstraction_notes and lets
                 the record through. Used wherever a violation is more likely
                 to mean "this paper is odd" than "the model erred". Follows
                 the pattern already established by
                 _enforce_rubric_only_consistency in schema_lite.py: never
                 discard a record you can instead mark for human review.

Every soft flag is prefixed with "AUTO-FLAG:" so downstream analysis can
separate machine-detected inconsistencies from the model's own
self-reported uncertainty.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, List, Optional, Sequence, Tuple

import vocabularies as V

OTHER_PATTERN = re.compile(r"^Other \(.+\)$")
AUTO_PREFIX = "AUTO-FLAG: "


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().casefold()


def _set(values: Optional[Iterable[str]]) -> set:
    return {_norm(v) for v in (values or [])}


def add_flag(obj: Any, field: str, message: str) -> None:
    """Append a soft flag to abstraction_flags/abstraction_notes in place."""
    flags: List[str] = list(getattr(obj, "abstraction_flags", None) or [])
    if field not in flags:
        flags.append(field)
    obj.abstraction_flags = flags

    existing = (getattr(obj, "abstraction_notes", None) or "").strip()
    note = f"{AUTO_PREFIX}{message}"
    obj.abstraction_notes = f"{existing} | {note}" if existing else note


# ---------------------------------------------------------------------------
# Vocabulary membership  (HARD REJECT)
# ---------------------------------------------------------------------------

def check_vocabulary(
    values: Sequence[str],
    allowed: Sequence[str],
    field_name: str,
    allow_other: bool = True,
) -> List[str]:
    """Validate a list of free-text values against a controlled vocabulary.

    Accepts an exact member, or "Other (specifier)" when allow_other.
    Raises ValueError listing every offender plus the nearest legal member,
    so a retry has something concrete to correct.
    """
    allowed_norm = {_norm(a): a for a in allowed}
    bad: List[str] = []
    fixed: List[str] = []

    for v in values:
        if allow_other and OTHER_PATTERN.match(str(v).strip()):
            fixed.append(str(v).strip())
            continue
        key = _norm(v)
        if key in allowed_norm:
            # Repair casing/whitespace drift silently.
            fixed.append(allowed_norm[key])
        else:
            bad.append(str(v))

    if bad:
        suggestions = []
        for b in bad:
            near = _nearest(b, allowed)
            suggestions.append(f"{b!r}" + (f" (did you mean {near!r}?)" if near else ""))
        raise ValueError(
            f"{field_name}: {len(bad)} value(s) not in the controlled vocabulary: "
            + "; ".join(suggestions)
            + ". Use an exact vocabulary member, or 'Other (specifier)' if nothing fits."
        )
    return fixed


def _nearest(value: str, allowed: Sequence[str]) -> Optional[str]:
    """Cheap token-overlap nearest match, for error messages only."""
    vt = set(re.findall(r"[a-z]+", _norm(value)))
    best, best_score = None, 0.0
    for a in allowed:
        at = set(re.findall(r"[a-z]+", _norm(a)))
        if not at:
            continue
        score = len(vt & at) / len(vt | at)
        if score > best_score:
            best, best_score = a, score
    return best if best_score >= 0.34 else None


def normalise_none_stated(values: Sequence[str]) -> List[str]:
    """Collapse free-text 'not stated' spellings onto the sentinel."""
    out = []
    for v in values:
        out.append(V.NONE_STATED if _norm(v) in {_norm(a) for a in V.NONE_STATED_ALIASES} else v)
    return out


# ---------------------------------------------------------------------------
# Within-field exclusivity
# ---------------------------------------------------------------------------

def check_general_domain_codes(obj: Any, domains: Sequence[str], field: str) -> None:
    """HARD. General codes may never co-occur with a specific domain code.

    Promoted from soft flag 2026-08-29: the rule has exactly one right answer,
    so a rejection plus the error text lets the model fix itself on retry.
    Soft-flagging it just moved the work to a human.
    """
    present = [d for d in domains if _norm(d) in {_norm(g) for g in V.GENERAL_DOMAIN_CODES}]
    specific = [d for d in domains if d not in present]
    # BUGFIX 2026-08-29.20: the guard was `len(domains) > 1`, which rejected a
    # record carrying TWO general codes and NO specific domain -- a combination
    # the rule PERMITS. HealthQA-BR failed all three attempts on
    # ['General psychiatry', 'General psychology'] with an empty specific list;
    # the error text even printed "alongside specific domain(s) []".
    if present and specific:
        raise ValueError(
            f"{field} contains general code(s) {present} alongside specific domain(s) "
            f"{specific}. The general codes are valid ONLY when no specific domain is "
            f"identifiable. Remove the general code if any specific domain applies; "
            f"remove the specific domains if the paper truly reports no per-condition "
            f"results. Do not return both."
        )


def check_evaluation_judging_preemptive(obj: Any, tasks: Sequence[str], field: str) -> None:
    """HARD, PER-INSTANCE ONLY. 'Evaluation/judging' must be the sole task.

    Scoped to the FULL tool, where one instance is one system. It is NOT wired
    into the condensed roll-up: a study-level record aggregates across arms, and
    a paper that evaluates a responder AND validates its judge legitimately has
    both tasks. Enforcing preemption at study level rejected correct records.
    """
    if "Evaluation/judging" in tasks and len(tasks) > 1:
        others = [t for t in tasks if t != "Evaluation/judging"]
        raise ValueError(
            f"{field} pairs 'Evaluation/judging' with {others}. Evaluation/judging is "
            f"preemptive and must be the only value. A judge always emits a label or "
            f"score; that is captured by evaluated_output_type, not by a second task."
        )


def check_other_requires_notes(obj: Any, tasks: Sequence[str], field: str) -> None:
    """HARD. system_tasks containing 'Other' requires abstraction_notes."""
    if "Other" in tasks and not (getattr(obj, "abstraction_notes", None) or "").strip():
        raise ValueError(
            f"{field} contains 'Other' but abstraction_notes is empty. Describe the task "
            f"in 1-2 sentences and explain why no other category fits."
        )


def check_flags_notes_paired(obj: Any) -> None:
    """HARD. abstraction_flags and abstraction_notes are populated together."""
    flags = getattr(obj, "abstraction_flags", None)
    notes = (getattr(obj, "abstraction_notes", None) or "").strip()
    if bool(flags) != bool(notes):
        raise ValueError(
            "abstraction_flags and abstraction_notes must be populated together or both "
            f"left null (got flags={flags!r}, notes={'set' if notes else 'null'})."
        )


# ---------------------------------------------------------------------------
# Cross-field disjointness
# ---------------------------------------------------------------------------

def check_disjoint(
    obj: Any,
    a_values: Optional[Sequence[str]],
    b_values: Optional[Sequence[str]],
    a_name: str,
    b_name: str,
    reason: str,
) -> None:
    """SOFT. Two list fields that should share no members."""
    overlap = _set(a_values) & _set(b_values)
    if overlap:
        pretty = sorted({v for v in (a_values or []) if _norm(v) in overlap})
        add_flag(obj, a_name, f"{pretty} appear in both {a_name} and {b_name}. {reason}")


def check_construct_task_overlap(obj: Any, tasks: Sequence[str], constructs: Sequence[str]) -> None:
    """SOFT. Constructs must not restate system_tasks."""
    hits = [
        (t, c) for t, c in V.CONSTRUCT_TASK_FORBIDDEN_PAIRS
        if _norm(t) in _set(tasks) and _norm(c) in _set(constructs)
    ]
    if hits:
        add_flag(
            obj, "evaluation_constructs_categories",
            "Construct restates a system_task: "
            + "; ".join(f"task {t!r} + construct {c!r}" for t, c in hits)
            + ". A construct is a clinically relevant capability, not the task format.",
        )


# ---------------------------------------------------------------------------
# Logical implication
# ---------------------------------------------------------------------------

def check_categories_not_longer_than_described(
    obj: Any, described: Sequence[str], categories: Sequence[str]
) -> None:
    """SOFT. Mapped categories cannot outnumber the author-named dimensions.

    The guide documents the reverse (described longer than categories) as
    expected, because out-of-scope dimensions are recorded but not mapped.
    The converse has no legitimate reading: every category must trace to a
    named, quantitatively reported dimension.
    """
    if len(categories) > len(described):
        raise ValueError(
            f"evaluation_constructs_categories has {len(categories)} entries but "
            f"evaluation_constructs_described has only {len(described)}. Every mapped "
            f"category must trace to a named, quantitatively reported dimension. Either "
            f"add the missing dimension(s) to _described or remove the category that has "
            f"no measurement behind it."
        )


def check_scoring_gate(obj: Any, scoring_procedures: Sequence[str], inclusion_score: int) -> None:
    """SOFT. No quantified scoring procedure => Criterion 7 fails => score 1."""
    real = [s for s in scoring_procedures if _norm(s) != _norm(V.NONE_STATED)]
    if not real and inclusion_score != 1:
        add_flag(
            obj, "inclusion_score",
            f"scoring_procedures is {V.NONE_STATED!r} for every included arm, which fails "
            f"Criterion 7 (quantified reported performance), but inclusion_score is "
            f"{inclusion_score}. A hard criterion failure yields 1.",
        )


def check_comparability_fallback(
    obj: Any,
    availabilities: Sequence[str],
    independent_systems: int,
    inclusion_score: int,
) -> None:
    """SOFT. Criterion 5 arithmetic — materials obtainable, or >=2 systems.

    Passes automatically if any included arm's items are obtainable. If none
    are, passes only via the comparability fallback, and the score is capped
    at 3. If neither limb holds, Criterion 5 fails outright and the score is 1.
    """
    obtainable = [a for a in availabilities if _norm(a) not in {_norm(x) for x in V.NON_OBTAINABLE_AVAILABILITY}]
    if obtainable:
        return

    if independent_systems < 2 and inclusion_score != 1:
        add_flag(
            obj, "inclusion_score",
            f"No included arm has obtainable materials (input_availabilities={list(availabilities)}) "
            f"and only {independent_systems} independent system(s) were evaluated, so Criterion 5 "
            f"fails on both limbs — but inclusion_score is {inclusion_score}. Expected 1.",
        )
    elif independent_systems >= 2 and inclusion_score > 3:
        add_flag(
            obj, "inclusion_score",
            f"Criterion 5 passed only via the >=2-independent-systems fallback "
            f"({independent_systems} systems, no obtainable materials), which caps the score at 3 — "
            f"but inclusion_score is {inclusion_score}.",
        )


def check_score2_confidence(obj: Any, inclusion_score: int, confidence: int) -> None:
    """SOFT. Score 2 means 'genuinely unclear', which is confidence 1 by definition."""
    if inclusion_score == 2 and confidence != 1:
        add_flag(
            obj, "inclusion_confidence",
            f"inclusion_score is 2 (at least one criterion genuinely unclear, flagged for "
            f"manual review) but inclusion_confidence is {confidence}. Score 2 implies "
            f"confidence 1.",
        )


def check_live_data_not_released(
    obj: Any, standardizations: Sequence[str], availabilities: Sequence[str]
) -> None:
    """SOFT. Live user data cannot also be a publicly released item set."""
    if "Live" in standardizations and "Publicly released" in availabilities:
        add_flag(
            obj, "input_determinism",
            "input_determinism contains 'Live' while input_availabilities "
            "contains 'Publicly released'. Live interaction data is not a released, "
            "re-runnable item set — unless these describe two different included arms, "
            "one of the two is wrong.",
        )


def check_reference_standard_judgement_coherence(
    obj: Any, descriptions: Sequence[str], judgements: Sequence[str]
) -> None:
    """SOFT. 'Not met' with no 'None stated' description anywhere."""
    if "Not met" in judgements:
        none_stated = any(
            _norm(d) in {_norm(V.NONE_STATED), _norm(V.RUBRIC_ONLY)} for d in descriptions
        )
        if not none_stated:
            add_flag(
                obj, "reference_standard_judgements",
                f"reference_standard_judgements contains 'Not met' but every "
                f"reference_standard_description names a real standard ({list(descriptions)}). "
                f"'Not met' means unanchored evaluator judgment or a rubric failing the "
                f"qualification test — the description should read {V.NONE_STATED!r}.",
            )


# ---------------------------------------------------------------------------
# Added 2026-08-29 after the 10-paper test
# ---------------------------------------------------------------------------

def count_independent(inventory: Sequence[str]) -> int:
    """Count lines in independent_systems_inventory marked 'independent'."""
    n = 0
    for line in inventory or []:
        parts = [p.strip() for p in str(line).split("|")]
        if len(parts) >= 3 and _norm(parts[-1]) == "independent":
            n += 1
    return n


def check_inventory_matches_count(obj: Any, inventory: Sequence[str], stated: int) -> None:
    """SOFT. The integer must equal the number of 'independent' inventory lines.

    Two of ten papers in the first test produced an integer that contradicted
    their own prose inventory. The model enumerates reliably and does arithmetic
    over its own list unreliably, so the list is the source of truth and the
    integer is checked against it.
    """
    malformed = [l for l in (inventory or [])
                 if len([p for p in str(l).split("|")]) < 3
                 or _norm(str(l).split("|")[-1]) not in {"independent", "authors-own"}]
    if malformed:
        add_flag(obj, "independent_systems_inventory",
                 f"{len(malformed)} inventory line(s) not in "
                 f"'<system> | <developer> | independent|authors-own' form: {malformed[:3]}. "
                 f"The count cannot be verified against them.")
        return

    computed = count_independent(inventory)
    if computed != stated:
        add_flag(obj, "independent_systems_evaluated_total",
                 f"independent_systems_evaluated_total is {stated} but the inventory lists "
                 f"{computed} system(s) marked 'independent' out of {len(inventory or [])} "
                 f"total. Trust the inventory: recount, or fix the inventory line that is "
                 f"marked wrongly.")


def check_confidence_requires_no_flags(obj: Any, confidence: int) -> None:
    """SOFT. Confidence 3 means the record is clean, not just the verdict.

    Runs LAST, after every other check, so auto-flags raised earlier in this
    validation pass are counted too.
    """
    if confidence == 3 and getattr(obj, "abstraction_flags", None):
        add_flag(obj, "inclusion_confidence",
                 f"inclusion_confidence is 3 while abstraction_flags is non-null "
                 f"({getattr(obj, 'abstraction_flags')}). A flag means a field could "
                 f"reasonably be coded differently, which caps confidence at 2.")


def check_authored_real_corpus_has_parent(
    obj: Any,
    benchmark_names: Optional[Sequence[str]],
    provenance: Sequence[str],
    reality: Sequence[str],
    parents: Optional[Sequence[str]],
) -> None:
    """SOFT, LOW PRECISION. Author-created + Real + named + no parent.

    You cannot CREATE real-world data, only collect or reuse it. So a named,
    author-assembled set of real material either was scraped first-hand or was
    built from someone else's corpus — and the second case must populate
    parent_benchmarks. This asks the reviewer to confirm which.

    Precision on the 10-paper test set was 1/3: it catches the RECAP miss but
    also fires on Qi and AUTALIC, which genuinely scraped Weibo and Reddit
    themselves. Kept anyway because a missed parent is otherwise invisible —
    there is no other signal that the field is wrongly null. Drop it if the
    review column gets noisy at scale.
    """
    if parents:
        return
    if not benchmark_names:
        return
    prov = list(provenance or [])
    # If Third-party is already listed, some item set is acknowledged as external
    # and the reviewer has the signal they need. Only fire on purely
    # author-assembled sets, where a silent parent is genuinely invisible.
    if "Author-created" not in prov or "Third-party" in prov:
        return
    if "Real" not in (reality or []):
        return
    add_flag(
        obj, "parent_benchmarks",
        f"{list(benchmark_names)} is an author-assembled set of REAL material with no "
        f"parent_benchmarks recorded. Real data is collected or reused, never created. "
        f"Confirm the items were gathered first-hand (scraped, recruited, clinically "
        f"collected) rather than selected from a prior named corpus — selecting and "
        f"re-annotating someone else's text DOES populate parent_benchmarks.",
    )


def check_other_specifier_not_excluded(obj: Any, constructs: Sequence[str]) -> None:
    """HARD. Other(specifier) must not house an out-of-scope dimension.

    Other() exists for a real construct the vocabulary lacks a term for. Using it
    to record something the exclusions rule out silently reintroduces excluded
    evaluation domains into the construct column, and because the specifier text
    is free-form, nothing else catches it.

    HARD rather than SOFT: unlike the flag-style checks, there is no paper for
    which this is the right answer. An excluded dimension is excluded however it
    is spelled. The message tells the retry exactly what to do instead.

    Live case: CACTUS produced "Other (LLM-judge vs expert correlation)",
    reasoning that Evaluation/judging is absent from the constructs vocabulary.
    It is absent because judge reliability is not a construct.
    """
    offenders = []
    for c in constructs or []:
        m = OTHER_PATTERN.match(str(c).strip())
        if not m:
            continue
        specifier = str(c).strip()[6:-1]
        for pat in V.OTHER_SPECIFIER_FORBIDDEN_PATTERNS:
            if re.search(pat, specifier, re.I):
                offenders.append((c, pat))
                break
    if not offenders:
        return
    raise ValueError(
        "evaluation_constructs_categories uses Other(...) to record something the "
        "out-of-scope list excludes: "
        + "; ".join(f"{c!r} (matched /{p}/)" for c, p in offenders)
        + ". Other(specifier) is for a REAL construct the vocabulary lacks a term for, "
        "never a workaround for an excluded dimension. Before writing Other(), check: "
        "(1) does it score a capability of a system UNDER EVALUATION, rather than the "
        "apparatus, the raters, or the client? (2) is it on the out-of-scope list or a "
        "synonym of something on it? (3) is it already carried by system_tasks, "
        "systems_tested, or scoring_procedures? If the thing is a judge's agreement with "
        "human raters, it is apparatus validity — represent it as 'Evaluation/judging' in "
        "system_tasks and 'LLM as judge/evaluator' in systems_tested, and record NO "
        "construct. Leave the dimension in evaluation_constructs_described and its metric "
        "in scoring_procedures."
    )


# NARROWED 2026-08-29.20 after 7 of 18 failures in the 436-paper run came from
# this one check, ALL matching the same pattern:
#     r"between[^.]{0,40}(llm|generated|synthetic)[^.]{0,30}and human"
# which fires on "agreement between LLM and human annotators" -- judge-human
# agreement, the semantic OPPOSITE of simulator realism and something the .10
# rules classify as out-of-scope apparatus validity. None of the 7 papers
# (DepreSym, Settanni, AUTALIC, Pugh, Badawi, MentalChat16K, Ask an Expert)
# contains a patient simulator at all.
#
# Every pattern now REQUIRES explicit simulator vocabulary; generic
# LLM-vs-human comparison no longer matches. Also removed the bare
# "human-generated text" pattern for the same reason.
SIMULATOR_VALIDATION_PATTERNS = (
    r"(simulat\w+|role[- ]?play\w*|seeker\s?sim\w*|(patient|client|seeker)\s+(lm|language model|model|agent)|synthetic (patient|client|seeker))[^.]{0,80}(validat|realis|realiz|fidelit|resembl|human[- ]like|distance to human|closer to human)",
    r"(validat|realis|realiz|fidelit|resembl)\w*[^.]{0,80}(simulat\w+|role[- ]?play\w*|seeker\s?sim\w*|(patient|client|seeker)\s+(lm|language model|model|agent))",
    r"ground[- ]truth[^.]{0,30}continuation",
)

# If any of these co-occur, the match is almost certainly rater/judge agreement
# or metric validation rather than simulator realism -- suppress.
SIMULATOR_VALIDATION_NEGATIVE = (
    r"inter[- ]?(rater|annotator)",
    r"\bagreement\b",
    r"\bkappa\b",
    r"correlat\w+[^.]{0,40}(human|expert|annotator|clinician)",
    r"human annotator",
    r"majority vote",
)



def check_type_value_not_in_description(
    obj: Any, descriptions: Optional[Sequence[str]], types: Sequence[str]
) -> None:
    """SOFT. A reference_standard_description entry that is ONLY a type value.

    Catches an entry carrying no information beyond the label -- the record named
    an arm by its type and never said what that arm's outputs were compared
    against. Live case: Lissak's
    "None -- rubric-only scoring (for automatic LLM-judge evaluation arms)",
    which was also missing from reference_standard_type, so that arm vanished
    from any count.

    NARROWED AND DOWNGRADED 2026-08-29.16. The first version split entries on
    ':' and ';' and matched the head, so any entry LABELLING its arm by type --
    "Expert/clinician ratings: 4 licensed psychologists applying the MindEval
    rubric" -- was rejected despite being informative and arguably clearer. The
    2026-08-29.15 guide prose ("run the test PER ARM", "record BOTH arms") pushes
    the model toward exactly that format, so the check fought the guidance it
    shipped alongside. Now the entry must be the bare type value, optionally with
    a trailing parenthetical, and nothing else.

    SOFT rather than HARD: a mislabelled description is a formatting defect, not
    a reason to discard an otherwise good extraction, and a check that can block
    a whole run must never be the one that is wrong.
    """
    if not descriptions:
        return
    # Defensive: a reversed call -- passing reference_standard_type where
    # descriptions belongs -- makes EVERY entry a bare vocabulary value and fires
    # on every record. That happened once (a duplicate call site with swapped
    # arguments survived a patch) and blocked an entire run through all retries.
    # A wiring bug should fail loudly at the call site, not masquerade as a data
    # defect in every record.
    _strip = lambda d: re.sub(r"\s*[(\[].*?[)\]]\s*$", "", str(d).strip()).strip().rstrip(".")
    _vocab = {_norm(t) for t in V.ReferenceStandardType.__args__}
    # Requires >=2 entries: a ONE-element list that is a bare type value is the
    # genuine defect this check exists for (Lissak), not a reversed call. A
    # reversed call passes the type list, which in practice carries 2-3 values.
    _bare = [_norm(_strip(d)) for d in descriptions]
    if len(_bare) >= 2 and all(b in _vocab for b in _bare):
        raise TypeError(
            "check_type_value_not_in_description received only controlled type values as "
            "its `descriptions` argument, which means the call site has the arguments "
            "reversed. Correct order: (obj, reference_standard_description, "
            "reference_standard_type)."
        )
    offenders = []
    for d in descriptions:
        bare = _strip(d)
        for t in V.ReferenceStandardType.__args__:
            if _norm(bare) == _norm(t):
                offenders.append((str(d)[:70], t, _norm(t) in {_norm(x) for x in types}))
    if not offenders:
        return
    missing = [t for _, t, in_types in offenders if not in_types]
    add_flag(
        obj, "reference_standard_description",
        "reference_standard_description contains an entry that is only a "
        "reference_standard_type value, with nothing describing what the arm was compared "
        "against: "
        + "; ".join(f"{d!r}" for d, _, _ in offenders)
        + (f". Also MISSING from reference_standard_type: {missing}. " if missing else ". ")
        + "Replace the entry with the comparator itself (who rated, against what key, using "
        "which instrument), and make sure the type value appears in reference_standard_type. "
        "Naming the arm by its type as a PREFIX is fine -- 'Expert/clinician ratings: 4 "
        "licensed psychologists applying the MindEval rubric' passes; a bare label does not.",
    )


def check_dataset_purpose_derivation(
    obj: Any, purpose: str, notes: Optional[str]
) -> None:
    """SOFT. A 'Both' dataset_purpose must say which data did which, with evidence.

    Two requirements, checked together because they fail together:
      (1) DERIVATION -- either 'Both' value asserts that some data trains and some
          evaluates. Naming which is what makes the claim auditable, and it is the
          requirement that made benchmark_names perfectly stable across runs.
      (2) EVIDENCE -- 'held-out split reported' additionally asserts that the paper
          DESCRIBES a separation. That is a positive claim and needs the sentence,
          the section, or the split sizes cited. Its counterpart, 'split not
          reported', is the DEFAULT and needs nothing, so the extractor is never
          asked to certify an absence.

    Deliberately narrow: silent on 'Evaluation only', 'Training or tuning only'
    and 'Not applicable', which are the common values. Flagging the common case is
    what made abstraction_flags useless before.
    """
    p = _norm(purpose or "")
    if p not in {_norm(x) for x in V.DATASET_PURPOSE_REQUIRES_DERIVATION}:
        return
    n = notes or ""
    problems = []
    if not re.search(r"train|fine[- ]?tun|distil|tuned on|evaluat|test set|held[- ]out|benchmark", n, re.I):
        problems.append(
            "abstraction_notes does not name which dataset trained and which evaluated"
        )
    if p in {_norm(x) for x in V.DATASET_PURPOSE_REQUIRES_EVIDENCE} and not re.search(
        r"held[- ]out|test set|train(ing)?[ /-]?(and[ /-]?)?(test|val)|split|unseen|"
        r"disjoint|section \d|table \d|appendix", n, re.I
    ):
        problems.append(
            "'held-out split reported' cites no evidence -- quote or name the sentence, "
            "section, or split sizes that describe the separation"
        )
    if not problems:
        return
    add_flag(
        obj, "dataset_purpose",
        f"dataset_purpose is {purpose!r} but " + "; and ".join(problems) + ". "
        "Either supply the derivation (MAGneT is the pattern: its own generated sessions "
        "train Llama-3-8B, CounselingBench evaluates it), or fall back to the default "
        "'Both -- split not reported', which asserts only what the paper shows.",
    )


def check_availability_non_default_has_evidence(
    obj: Any, availabilities: Sequence[str], notes: Optional[str]
) -> None:
    """SOFT. A non-default availability value with no supporting evidence in notes.

    'Not available' is the default; anything else is a positive claim that the
    items can be obtained, and needs a URL, repository, data-availability
    statement or offering sentence behind it. This check cannot read the paper,
    so it verifies the weaker thing it can: that the RECORD carries its own
    justification. Forcing the justification to be written is what made
    benchmark_names stable.

    Motivating case: Hasan flipped between 'Available on request' and 'Not
    available' across three identical runs, and the paper contains no
    availability statement at all -- the non-default value was invented.
    """
    # Deliberately narrow. "Publicly released" and "Fully specified in paper" are
    # self-evidencing -- the release is visible in the paper and usually already
    # named in benchmark_names -- and firing on them flagged 9/10 baseline
    # records, which is the noise level that made abstraction_flags useless in the
    # first place. Only the INFERENTIAL values are checked: those asserting a
    # route to the items that the reader cannot see for themselves.
    INFERENTIAL = {"available on request", "method reproducible, items unavailable"}
    NON_DEFAULT = {a for a in availabilities or [] if _norm(a) in INFERENTIAL}
    if not NON_DEFAULT:
        return
    if re.search(r"http|github|osf\.io|zenodo|huggingface|available (on|upon) request|"
                 r"data[- ]availability|appendix|supplement|released|repositor",
                 notes or "", re.I):
        return
    add_flag(
        obj, "input_availabilities",
        "input_availabilities claims the items are obtainable ("
        + ", ".join(sorted(NON_DEFAULT))
        + ") but abstraction_notes cites no evidence. Non-default availability requires "
        "positive evidence: a URL, a named repository, a data-availability statement, or "
        "the sentence offering access -- quote or name it in the notes. Silence in the "
        "paper means 'Not available'.",
    )


def check_simulator_validation_implies_fidelity(
    obj: Any,
    tasks: Sequence[str],
    constructs: Sequence[str],
    scoring: Optional[Sequence[str]],
    ref_desc: Optional[Sequence[str]],
) -> None:
    """SOFT. The record describes validating a simulator but omits the construct.

    Companion to check_simulation_task_needs_fidelity, which catches the opposite
    gap. This one fires when the record's OWN scoring_procedures or
    reference_standard_description describe measuring how closely simulated
    output resembles human output -- i.e. the paper reports simulator realism as
    a result -- and Simulation fidelity is nonetheless absent from constructs.

    WHY HARD. Across three identical runs, Simulation fidelity appeared in only
    1/3 for both MindEval and PAIR-SAFE, the two papers that unambiguously earn
    it (MindEval hires 10 psychologists, samples 432 turns and reports t-SNE
    distance to LLM text; PAIR-SAFE validates SeekerSim against ground-truth
    continuations). It was 0-for-2 on stable assignment, making any corpus count
    of this construct undefined. Branch (h) of the construct-routing rules is
    written correctly and was being ignored two times in three, so the fix has
    to be deterministic rather than more prose.

    The evidence is drawn from fields the extractor has already written, so this
    cannot fire on a paper that never describes such a measurement.
    """
    if "simulation fidelity" in _set(constructs):
        return
    hay = " ".join(list(scoring or []) + list(ref_desc or []))
    if not hay:
        return
    hits = [p for p in SIMULATOR_VALIDATION_PATTERNS if re.search(p, hay, re.I)]
    if not hits:
        return
    if any(re.search(p, hay, re.I) for p in SIMULATOR_VALIDATION_NEGATIVE):
        return
    add_flag(
        obj, "evaluation_constructs_categories",
        "scoring_procedures / reference_standard_description describe measuring how "
        "closely simulated output resembles human output (matched "
        + "; ".join(f"/{p}/" for p in hits)
        + "), but 'Simulation fidelity' is missing from "
        "evaluation_constructs_categories. If the paper reports the realism of its "
        "patient/client/seeker simulator as a RESULT, that is Simulation fidelity per "
        "branch (h) and must be recorded. If the matched text describes something else "
        "-- similarity between two SYSTEMS UNDER TEST, or a similarity metric used to "
        "score clinician output rather than simulated client output -- say so explicitly "
        "in abstraction_notes and remove the misleading phrasing from scoring_procedures.",
    )


def check_simulation_task_needs_fidelity(
    obj: Any, tasks: Sequence[str], constructs: Sequence[str], notes: Optional[str]
) -> None:
    """SOFT. Simulation in system_tasks with no Simulation fidelity construct.

    Replaces the retired ("Simulation", "Simulation fidelity") forbidden pair,
    which caught the INVERSE of the real defect. A paper that lists Simulation
    as a task either (a) validates the simulator and reports it, in which case
    Simulation fidelity belongs in constructs, or (b) uses a simulator purely as
    apparatus to generate stimuli, in which case Simulation should not be in
    system_tasks at all. Both are legitimate; silently doing neither is not.

    MAGneT is the live case: Simulation is listed, its client agent's realism is
    never measured anywhere in the paper, and no fidelity construct is recorded.
    MindEval and PAIR-SAFE are the correct pattern and do not fire.

    Suppressed when abstraction_notes already argues the apparatus reading, so a
    reasoned record is not re-flagged.
    """
    if "simulation" not in _set(tasks):
        return
    if "simulation fidelity" in _set(constructs):
        return
    if re.search(r"apparatus|not (itself )?evaluated|not validated|held constant",
                 notes or "", re.I):
        return
    add_flag(
        obj, "system_tasks",
        "system_tasks includes 'Simulation' but no 'Simulation fidelity' construct is "
        "recorded. Either the paper measures its simulator's realism as a reported result "
        "(add the construct), or the simulator is apparatus used to generate stimuli and "
        "is not a system under test (remove the task, and say so in abstraction_notes). "
        "Doing neither leaves the record internally inconsistent.",
    )


def check_thirdparty_inputs_have_named_benchmark(
    obj: Any, provenance: Sequence[str], benchmark_names: Optional[Sequence[str]]
) -> None:
    """SOFT. Third-party inputs but benchmark_names is null.

    Third-party material came from somewhere, and in this literature that
    somewhere is usually named in the paper. Null here is occasionally right
    (unnamed scraped corpus, private clinical records), so this is a flag, not a
    reject.

    Fires on 4 of 10 records in the 2026-08-29.7 run: WundtGPT, TheraMind,
    PAIR-SAFE, CACTUS. PAIR-SAFE is the proof case — its own
    reference_standard_description names the HighLowQuality dataset, so the
    record already contains the string the field is missing.
    """
    if benchmark_names:
        return
    if "Third-party" not in list(provenance or []):
        return
    add_flag(
        obj, "benchmark_names",
        "input_provenance_types includes 'Third-party' but benchmark_names is null. "
        "Third-party evaluation material usually has a name — check the datasets, "
        "reference standard and scoring sections before leaving this null. If the source "
        "genuinely is unnamed (an unnamed scraped corpus, private clinical records), say "
        "so in abstraction_notes.",
    )


def check_benchmark_development_names_a_benchmark(
    obj: Any, type_of_study: str, benchmark_names: Optional[Sequence[str]]
) -> None:
    """SOFT. type_of_study asserts an artefact was built; the field must name it.

    Coding a paper as Benchmark development is a claim that it introduces a named
    evaluation artefact. If benchmark_names is null, one of the two fields is
    wrong and the record cannot be analysed on either.

    Fires on MindEval and CACTUS in the 2026-08-29.7 run. Both introduce named
    artefacts; MindEval's was suppressed by over-applying the framework carve-out
    in the benchmark_names description, now clarified.
    """
    if benchmark_names:
        return
    if _norm(type_of_study) != _norm("Benchmark development"):
        return
    add_flag(
        obj, "benchmark_names",
        "type_of_study is 'Benchmark development' but benchmark_names is null. That "
        "combination asserts the paper built an evaluation artefact and then declines to "
        "name it. Either name it — note that a framework, harness or environment owning a "
        "fixed input set IS a benchmark — or re-code type_of_study as 'Evaluation study'.",
    )


def check_primary_in_categories(obj: Any, primary: str, categories: Sequence[str]) -> None:
    """HARD. primary_construct must be one of evaluation_constructs_categories.

    The primary is a designation, not an extra construct. If it names something
    absent from the list, one of the two is wrong and the record cannot be
    analysed on either column.
    """
    if _norm(primary) not in _set(categories):
        raise ValueError(
            f"primary_construct is {primary!r} but evaluation_constructs_categories is "
            f"{list(categories)}. The primary must be ONE OF the mapped categories — it "
            f"designates which of them the paper is chiefly about, it does not add a new "
            f"construct. Either add {primary!r} to the categories list if the paper really "
            f"measures it, or choose the primary from the list as it stands."
        )
