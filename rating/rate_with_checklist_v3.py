"""v3 rating run: apply the frozen rater checklist (v6.1) to every study-benchmark arm with an LLM, from the PDF only.

Usage:
  # 1. check that every study maps to a PDF (no API calls, prints the match table)
  python rate_with_checklist_v3.py checklist_rating_input_all619.csv ./pdfs v3_ratings.csv --model claude-sonnet-4-6 --check-pdfs
  # 2. pilot on a few rows
  python rate_with_checklist_v3.py checklist_rating_input_all619.csv ./pdfs v3_ratings.csv --model claude-sonnet-4-6 --rows 45-50
  # 3. full run (resumable: rows already in v3_ratings.csv are skipped)
  python rate_with_checklist_v3.py checklist_rating_input_all619.csv ./pdfs v3_ratings.csv --model claude-sonnet-4-6 --workers 4

Requires: pip install anthropic pymupdf pandas ; env ANTHROPIC_API_KEY.
Reuses extracted_text/<study_id>.txt when present; otherwise extracts from the matched PDF and saves the text.
Output: one row per arm with the 11 step codes, a verbatim supporting sentence (+page) per step, the model's one-line reason,
and the three dimension totals computed by the workbook rule (any Poor -> Poor; NR majority -> NR; all High -> High; else Adequate).
The checklist file is read at start and its SHA-256 is written into every output row, so a changed checklist is visible."""
import os, re, json, argparse, difflib, hashlib, time, pandas as pd
_BEDROCK_MODEL_MAP={'claude-sonnet-4-6':'us.anthropic.claude-sonnet-4-6'}  # pass --model us.anthropic.claude-sonnet-4-6 on Bedrock
from concurrent.futures import ThreadPoolExecutor, as_completed
ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('pdf_dir'); ap.add_argument('output'); ap.add_argument('--model',required=True)
ap.add_argument('--text-dir',default='extracted_text'); ap.add_argument('--checklist',default='checklist_v6-1_frozen.md'); ap.add_argument('--max-chars',type=int,default=400000)
ap.add_argument('--rows',default=''); ap.add_argument('--workers',type=int,default=1); ap.add_argument('--check-pdfs',action='store_true')
a=ap.parse_args(); os.makedirs(a.text_dir,exist_ok=True)

CODES=['IA','IB','IC','R0','RA','RB','RC','RD','SA','SB','SC']
ALLOWED={'IA':['IA0','IA1','IA2','IA3'],'IB':['IB0','IB1','IB2','IB-NR','NA'],'IC':['IC1','IC2'],'R0':['R0-NA','R0-applies'],
 'RA':['RA1','RA2','RA3','RA-NR','NA'],'RB':['RB1','RB2','RB3','RB-NR','NA'],'RC':['RC1','RC2','RC3','RC-NR','NA'],'RD':['RD1','RD2','RD3','RD-NR','NA'],
 'SA':['SA0','SA1','SA2','SA3','SA4'],'SB':['SB1','SB2','SB3','NA'],'SC':['SC1','SC2','SC3','NA']}
# step -> rating, as in the workbook Step_lookup sheet
LOOK={'IA0': 'NA', 'IA1': 'Poor', 'IA2': 'High', 'IA3': 'Adequate', 'IB0': 'NA', 'IB1': 'High', 'IB2': 'Adequate', 'IC1': 'High', 'IC2': 'Adequate', 'RA1': 'Poor', 'RA2': 'High', 'RA3': 'Adequate', 'RB1': 'Poor', 'RB2': 'High', 'RB3': 'Adequate', 'RC1': 'Poor', 'RC2': 'High', 'RC3': 'Adequate', 'RD1': 'Poor', 'RD2': 'High', 'RD3': 'Adequate', 'SA0': 'NA', 'SA1': 'Poor', 'SA2': 'Adequate', 'SA3': 'High', 'SA4': 'Adequate', 'SB1': 'Poor', 'SB2': 'High', 'SB3': 'Adequate', 'SC1': 'Poor', 'SC2': 'High', 'SC3': 'Adequate', 'IB-NR': 'NR', 'RA-NR': 'NR', 'RB-NR': 'NR', 'RC-NR': 'NR', 'RD-NR': 'NR'}
LOOK['NA']='NA'
RATING_WORDS={'poor','adequate','high','nr','na','n/a'}
DIMS={'inputs':['IA','IB','IC'],'reference_standard':['RA','RB','RC','RD'],'scoring':['SA','SB','SC']}
def total(steps,dim,r0):
    if dim=='reference_standard' and r0=='R0-NA': return 'NA'
    rs=[LOOK.get(steps.get(c,''),None) for c in DIMS[dim]]
    if any(r is None for r in rs): return 'INCOMPLETE'
    if 'Poor' in rs: return 'Poor'
    rs=[r for r in rs if r!='NA']
    if not rs: return 'NA'
    if 2*sum(r=='NR' for r in rs)>len(rs): return 'NR'
    return 'High' if all(r=='High' for r in rs) else 'Adequate'

checklist=open(a.checklist,encoding='utf8').read(); CK_SHA=hashlib.sha256(checklist.encode('utf8')).hexdigest()[:12]
SYSTEM=("You are a rater applying a benchmark-quality checklist to ONE research report, exactly as a trained human rater would. "
 "Rules: (1) Evidence is this report only. Do not use anything you know about the dataset, its source paper, or its authors from elsewhere. "
 "If the report does not state something, choose the NA or NR step the checklist specifies; never infer. (2) Rate only the named benchmark; ignore other benchmarks in the same report. "
 "(3) The input lists what to rate: the items, the reference standard (R0), and the scoring procedure. Where these are marked 'hand-prespecified', rate exactly those; if you believe the pre-specification is wrong, still rate it as given and say why in 'dispute'. "
 "Where they are marked 'abstraction-derived pointers', they are hints only: identify the headline procedure yourself by the checklist's headline-only rule (abstract, main results tables/figures, or stated research question; if two headline procedures, rate the weaker), and set R0 to R0-NA only if no human-made standard is used by any headline procedure. "
 "(4) Code EVERY criterion on its own merits with a STEP CODE (never a rating word such as 'Poor'), even after an earlier criterion in the same dimension is Poor, so step-level comparison is possible; the totals are computed afterwards by the workbook rule. Under R0-NA give 'NA' for RA-RD; for LLM-generated items give IB0. (4a) Evidence discipline: never infer who labelled items or where labels came from — not from the platform (a subreddit source does not make labels proxy labels), not from the dataset's name, not from a sentence about the task or framework design. The sentence you cite for RA must say who produced the labels; for RB it must say what the labels are based on; for RD it must describe a check of the labels. If no such sentence exists, the step is NR (or RD1 for the authors' own labels). (4c) Within each criterion, test the steps IN ORDER and stop at the first that applies: for RD, check RD1 first — if the labels are the authors' own (made for this paper) and the report gives neither a basis (RB-NR) nor a check, that is RD1, not RD3. A constrained-choice or direct-category output needs no extraction rule (SB2 is reachable); SB3 for a missing extraction rule applies only when outputs are free text. "
 "(4b) If the report evaluates no model at all (benchmark proposed without evaluation), give SA0 and the step 'NA' for SB and SC. (5) For each step give one verbatim sentence from the report that supports the choice, with its page marker, or the string 'nothing in the report'. "
 "(6) Return ONLY a JSON object with keys: " + ", ".join(CODES) + " (each an object {\"step\": <code>, \"evidence\": <verbatim sentence or 'nothing in the report'>, \"page\": <page marker>, \"reason\": <one short clause>}), "
 "'headline_procedure' (one sentence: which scoring procedure and which reference standard you rated), and 'dispute' (string, empty if none).\n\n"
 "THE CHECKLIST (v6.1, frozen):\n" + checklist)

def pdf_text(path):
    import fitz
    doc=fitz.open(path); return ''.join(f"\n[[PAGE {i}]]\n"+p.get_text() for i,p in enumerate(doc,1))
def norm(s): return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9 ]',' ',str(s).lower())).strip()
def find_pdf(row,files):
    if isinstance(row.pdf_filename,str) and row.pdf_filename and os.path.exists(os.path.join(a.pdf_dir,row.pdf_filename)): return os.path.join(a.pdf_dir,row.pdf_filename),1.0
    key=norm(row.study_id); best=max(files,key=lambda f: difflib.SequenceMatcher(None,key,norm(f)).ratio())
    return os.path.join(a.pdf_dir,best),difflib.SequenceMatcher(None,key,norm(best)).ratio()
def want(r):
    if not a.rows: return True
    s=set()
    for part in re.split(r'[,\s]+',a.rows):
        if not part: continue
        if '-' in part: lo,hi=part.split('-'); s.update(range(int(lo),int(hi)+1))
        else: s.add(int(part))
    return int(r) in s

Q=pd.read_csv(a.input,dtype=str).fillna(''); files=[f for f in os.listdir(a.pdf_dir) if f.lower().endswith('.pdf')]
if a.check_pdfs:
    seen={}
    for _,r in Q.iterrows():
        if r.study_id in seen: continue
        tp=os.path.join(a.text_dir,f"{r.study_id}.txt")
        if os.path.exists(tp): seen[r.study_id]=('cached text',1.0); continue
        seen[r.study_id]=find_pdf(r,files)
    out=pd.DataFrame([{'study_id':k,'matched_pdf':os.path.basename(v[0]),'similarity':round(v[1],2)} for k,v in seen.items()]).sort_values('similarity')
    out.to_csv('pdf_match_check.csv',index=False); print(out.head(40).to_string()); print(f'\n{len(out)} studies; {int((out.similarity<0.6).sum())} with similarity < 0.60 — check these and fill pdf_filename in the input CSV before running.'); raise SystemExit

done=set()
if os.path.exists(a.output):
    prev=pd.read_csv(a.output,dtype=str).fillna('')
    good=prev[(prev.IA_step!='FAILED')].drop_duplicates('row',keep='last')
    nfail=len(prev)-len(good)
    if nfail: good.to_csv(a.output,index=False); print(f'dropped {nfail} FAILED/duplicate rows; they will be retried')
    done=set(good.row.astype(int)); print('resuming;',len(done),'rows already done')
import anthropic
client=anthropic.Anthropic(); cache={}
def get_text(r):
    tp=os.path.join(a.text_dir,f"{r.study_id}.txt")
    if r.study_id in cache: return cache[r.study_id]
    if os.path.exists(tp): t=open(tp,encoding='utf8').read()
    else: path,_=find_pdf(r,files); t=pdf_text(path); open(tp,'w',encoding='utf8').write(t)
    cache[r.study_id]=t; return t
def rate(r):
    text=get_text(r)
    user=(f"ROW {r.row}\nBENCHMARK TO RATE: {r.benchmark}\n{('Identified in the paper as: '+r.benchmark_identification) if r.benchmark_identification else ''}\n"
          f"{('Other benchmarks in this paper — ignore: '+r.other_benchmarks_to_ignore) if r.other_benchmarks_to_ignore else ''}\n"
          f"PROVENANCE: {r.provenance}\nPRE-SPECIFICATION STATUS: {r.prespecification}\n"
          f"ITEMS TO RATE: {r.input_to_rate}\nR0: {r.R0_prespecified}\nREFERENCE STANDARD TO RATE: {r.reference_standard_to_rate}\nSCORING PROCEDURE TO RATE: {r.scoring_method_to_rate}\n\n"
          f"REPORT TITLE: {r.title}\n\nREPORT TEXT (page markers [[PAGE n]]):\n{text[:a.max_chars]}")
    j=None; raw=''
    for attempt in range(5):
        try:
            msg=client.messages.create(model=a.model,max_tokens=5000,temperature=0,system=SYSTEM+(' Output must be a single valid JSON object and nothing else.' if attempt else ''),messages=[{'role':'user','content':user}])
        except Exception as e:
            wait=60*(attempt+1) if 'rate' in str(e).lower() or '429' in str(e) or 'overloaded' in str(e).lower() else 20*(attempt+1)
            print('API error row',r.row,'-',str(e)[:200],'| retrying in',wait,'s'); time.sleep(wait); continue
        raw=msg.content[0].text; out=raw[raw.find('{'):raw.rfind('}')+1]
        try: j=json.loads(out); break
        except Exception as e: print('JSON parse failed row',r.row,'-',e)
    rec={'row':int(r.row),'study_id':r.study_id,'benchmark':r.benchmark,'master_idx':r.get('master_idx',''),'prespecification':r.prespecification,'model':a.model,'checklist_sha':CK_SHA}
    if j is None:
        os.makedirs('failed_responses',exist_ok=True); open(f'failed_responses/row_{r.row}.txt','w',encoding='utf8').write(raw)
        for c in CODES: rec[f'{c}_step']='FAILED'
        for d in DIMS: rec[f'{d}_total']='FAILED'
        return rec
    def parse(j):
        steps={}; recs={}
        for c in CODES:
            v=j.get(c,{}) if isinstance(j.get(c),dict) else {'step':str(j.get(c,''))}
            step=str(v.get('step','')).strip()
            if c=='R0' and r.prespecification.startswith('hand') : step=r.R0_prespecified   # R0 fixed for the sample
            if c=='IB' and step.upper() in ('NA','N/A'): step='IB0'
            if c in ('RA','RB','RC','RD') and steps.get('R0')=='R0-NA' and step.upper() in ('NA','N/A',''): step='NA'
            if step not in ALLOWED[c]: step=f'INVALID:{step}'
            steps[c]=step; recs[c]=(step,str(v.get('evidence',''))[:600],str(v.get('page',''))[:40],str(v.get('reason',''))[:600])
        return steps,recs
    steps,recs=parse(j)
    # Repair step (runner fix, not a rubric change): if any step code is a rating word or otherwise not a step code,
    # ask once for the same JSON with step codes substituted; keep the INVALID marker if the repair also fails.
    bad=[c for c in CODES if steps[c].startswith('INVALID')]
    if bad:
        fix=("Your previous answer used a value that is not a step code for: "+', '.join(bad)+". Replace every value that is a rating word "
             "(Poor/Adequate/High/NA/NR) or anything else that is not a step code from the rubric tables with the correct step code "
             "(for example RB-NR, RC2, RD1, IC2). A criterion that comes after a Poor in the same dimension still gets its own step code. "
             "Return the complete JSON object again, unchanged except for those values, and nothing else.")
        try:
            msg2=client.messages.create(model=a.model,max_tokens=5000,temperature=0,system=SYSTEM,
                 messages=[{'role':'user','content':user},{'role':'assistant','content':raw},{'role':'user','content':fix}])
            raw2=msg2.content[0].text; j2=json.loads(raw2[raw2.find('{'):raw2.rfind('}')+1])
            steps2,recs2=parse(j2)
            if sum(s.startswith('INVALID') for s in steps2.values())<len(bad): steps,recs=steps2,recs2; print('repaired step codes row',r.row,'(was',bad,')')
        except Exception as e: print('repair failed row',r.row,'-',str(e)[:120])
    for c in CODES:
        rec[f'{c}_step']=steps[c]; rec[f'{c}_evidence'],rec[f'{c}_page'],rec[f'{c}_reason']=recs[c][1],recs[c][2],recs[c][3]
    for d in DIMS: rec[f'{d}_total']=total(steps,d,steps['R0'])
    rec['headline_procedure']=str(j.get('headline_procedure',''))[:600]; rec['dispute']=str(j.get('dispute',''))[:600]
    return rec
todo=[r for _,r in Q.iterrows() if want(r.row) and int(r.row) not in done]; print(len(todo),'rows to rate')
def flush(rec):
    pd.DataFrame([rec]).to_csv(a.output,mode='a',header=not os.path.exists(a.output),index=False)
    print('done',rec['row'],str(rec['benchmark'])[:40],'|',' '.join(rec[f'{c}_step'] for c in CODES),'|',rec['inputs_total'],rec['reference_standard_total'],rec['scoring_total'])
if a.workers<=1:
    for r in todo: flush(rate(r))
else:
    with ThreadPoolExecutor(a.workers) as ex:
        for f in as_completed([ex.submit(rate,r) for r in todo]): flush(f.result())
print('finished; output', a.output)
