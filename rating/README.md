# Quality rating

- `checklist_v6-1_frozen.md` — the step-coded quality checklist applied by the human raters and the LLM (SHA-256 89719b5112da…). A reader version of the rubric is published as eAppendix 3 of the article supplement; the rating procedure is in eAppendix 4.
- `rate_with_checklist_v3.py` — the rating script. It sends the full text of one report with the rubric to Claude Sonnet 4.6 (temperature 0), requires a step code and a verbatim quotation with page for every rubric step, repeats the call once if a rating word is returned in place of a step code, and writes the rubric hash into every output row.
- `checklist_rating_input_all619.csv` — one row per study–benchmark arm: for rows 1–100 (the validation sample) the items, reference standard, and scoring procedure to rate, specified in advance and identical to the human raters' workbook; for rows 101–619 the abstraction-derived pointers from which the model identified the headline procedure itself.

Run (the folder of report PDFs is not supplied):

    python rate_with_checklist_v3.py checklist_rating_input_all619.csv ./pdfs out.csv --model claude-sonnet-4-6 --workers 4 --rows 1-619

Design: rows 1–100 were rated in 3 independent runs; rows 101–619 in 2 runs, with a third run for arms on which the first 2 differed on any step code. The final step code for each arm is the majority across runs (`../data/all_arms_step_codes_and_ratings.xlsx`); raw output of every run is in `../data/llm_runs/`.
