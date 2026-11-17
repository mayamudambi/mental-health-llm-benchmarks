# Benchmarks for Evaluating Generative Large Language Models in Mental Health: A Systematic Review — materials, code, and rating data

Companion repository for the article (citation and DOI to be added at publication). The online supplement (Supplement 1) contains the eMethods, eTables, PRISMA checklist (eAppendix 1), search strategies (eAppendix 2), the quality rubric (eAppendix 3), and the abstraction and rating prompts and procedure (eAppendix 4). This repository holds the full-length materials and the data behind the quality ratings. The benchmark-level (n = 453) and study-level (n = 433) tables are published at https://tinyurl.com/mhbenchmarkatlas.

## Authors

Samantha Matthews,<sup>1</sup> Maya Mudambi,<sup>2</sup> Hao Yu,<sup>3,4</sup> John Torous,<sup>5</sup> Jina Suh,<sup>6</sup> Jason M. Nagata,<sup>7</sup> Pat Pataranutaporn,<sup>8</sup> Jonathan H. Cantor,<sup>9</sup> Ryan K. McBain<sup>1</sup>

<sup>1</sup> RAND, Arlington, VA, USA · <sup>2</sup> University of Massachusetts Amherst, Amherst, MA, USA · <sup>3</sup> Harvard Pilgrim Health Care Institute, Boston, MA, USA · <sup>4</sup> Harvard Medical School, Boston, MA, USA · <sup>5</sup> Beth Israel Deaconess Medical Center, Boston, MA, USA · <sup>6</sup> School of Computer Science & Engineering, University of Washington, Seattle, WA, USA · <sup>7</sup> University of California, San Francisco, San Francisco, CA, USA · <sup>8</sup> MIT Media Lab, MIT, Cambridge, MA, USA · <sup>9</sup> RAND, Santa Monica, CA, USA

**Corresponding author:** Samantha Matthews, MPhil, MPA, RAND, 1200 South Hayes Street, Arlington, VA 22202; smatthew@rand.org

## License

## License

Code (`.py` files and JSON Schemas in `abstraction/` and `rating/`) is released under the MIT License; see `LICENSE`.

All other materials — prompts, rubric, vocabularies, data files, and documentation — are released under the Creative Commons Attribution 4.0 International License (CC BY 4.0); see `LICENSE-DATA`. Please cite the article when reusing them.

Verbatim quotations from included reports in `data/llm_runs/` remain the copyright of their original authors, are reproduced for scholarly purposes, and are not covered by either license.

## Contents

| Folder | What it holds |
|---|---|
| `abstraction/` | Everything used for LLM-assisted data abstraction: the two system prompts exactly as sent to the model (`system_prompt_study.txt`, `system_prompt_benchmark.txt`; each contains the written extraction guide, the benchmark-level instructions and field definitions where applicable, and the output schema), controlled vocabularies (`vocab_lists.json`, `vocabularies.py`), the extraction guide as the Python module the scripts load (`extraction_guide_condensed.py`), output schemas as pydantic models (`schema_condensed.py`, `schema_benchmark.py`) and as rendered JSON Schema (`schema_study_level.json`, `schema_benchmark_level.json`), validation rules (`validators.py`), and the extraction scripts (`abstract_articles_condensed.py`, `abstract_benchmarks.py`). |
| `rating/` | The frozen quality rubric applied by human raters and the LLM (`checklist_v6-1_frozen.md`; SHA-256 below), the rating script with its system prompt and repair call (`rate_with_checklist_v3.py`), the per-arm input file with the prespecified items, reference standard, and scoring procedure for the validation sample and abstraction-derived pointers for the remaining arms (`checklist_rating_input_all619.csv`), and a short README with the run command and design. |
| `data/` | `validation_sample_ratings.xlsx` — step codes and dimension ratings from each human rater, each LLM run, the LLM majority, and the published rating for the 100-arm validation sample (README tab inside). `all_arms_step_codes_and_ratings.xlsx` — final step codes, dimension ratings, and rating source for all 619 study–benchmark arms. `llm_runs/` — raw output of every LLM rating run (step code, verbatim evidence quote, page, and reason for each rubric step), plus the hand-coded record for the one arm the model declined to process. `post_run_recodes.xlsx` — every step code changed after human review of the LLM majority: the 34 arms re-reviewed on step SA0 (14 codes and 13 scoring ratings changed) and 5 arms re-reviewed after a co-author check of the benchmark table (5 codes; 3 scoring, 1 reference-standard, and 1 inputs rating changed), each with the code before and after and the reason; tie-breaks in the validation sample are visible in `validation_sample_ratings.xlsx` (`published_source`, `published_note`). |

## How the pieces fit

1. Reports were abstracted with `abstraction/abstract_articles_condensed.py` (study level) and `abstraction/abstract_benchmarks.py` (benchmark level), each sending the PDF plus the corresponding system prompt to Claude Sonnet 4.6 at temperature 0 and validating the returned JSON against the schema, vocabularies, and `validators.py`.
2. Quality ratings were produced with `rating/rate_with_checklist_v3.py`, which sends the full report text and the rubric to the same model and returns a step code with a verbatim quotation for each rubric step. Each arm was rated in 3 independent runs (validation sample) or 2 runs plus a third where the first 2 differed (remaining arms); the majority step code was kept. Dimension ratings follow the fixed rule in the rubric (any Poor step → Poor; Not reported on more than half of rated steps → Not reported; all High → High; otherwise Adequate).
3. For the validation sample, 2 human raters applied the same rubric independently; where they agreed, the human rating is the published rating; where they disagreed, the lead rater's rating is used. `data/validation_sample_ratings.xlsx` has every rating side by side.

## Integrity

SHA-256 hashes of the prompt and rubric files are listed in `HASHES.txt`. Every LLM rating record carries the rubric hash (`checklist_sha`) and every abstraction record carries the hashes of the guide, schema, and system prompt in force when it was produced.

## Not included

Full texts of the included reports are not redistributed. The evidence columns in `data/llm_runs/` contain only short verbatim quotations with page numbers.
