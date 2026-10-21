"""논문 아카이브 DB에서 사이클, trapping set, 실패 진단 후보 논문을 뽑는다.
실행 (repo 루트에서): python -I 4_H_matrix_tool/_pm/tasks/20261021_cycle_trapping_tool/후보목록/extract.py ../LDPC_Paper_Analysis
출력: 이 폴더에 {A_cycle_count,B_trapping_enum,C_failure_diag}.jsonl (초록 포함)과 *_titles.txt (제목만)
"""
import sqlite3, json, os, re, sys
OUT = os.path.dirname(os.path.abspath(__file__))
ARCH = sys.argv[1]
c = sqlite3.connect(os.path.join(ARCH, 'data/papers.db'))
rows = c.execute("select id,source,title,authors,abstract,published,content_type,status,doi from papers").fetchall()

def norm(p):
    return p.replace(os.sep, '/')

txt = {}
for root, _, files in os.walk(os.path.join(ARCH, 'data/pdfs')):
    for f in files:
        if f.endswith('.txt'):
            txt[f[:-4]] = norm(os.path.join(root, f))
md = {}
for root, _, files in os.walk(os.path.join(ARCH, 'criteria/stage3/results')):
    for f in files:
        if f.endswith('.md'):
            md[f[:-3]] = norm(os.path.join(root, f))

def sid(pid):
    return pid.replace(':', '_')

cats = {
    'A_cycle_count': [
        r'\bgirth\b', r'short cycle', r'cycle (enumerat|count|distribution|spectrum|detect)',
        r'count(ing)? (of )?(short )?cycles', r'number of cycles', r'cycles? (in|of) (the )?tanner graph',
        r'tanner graph cycle', r'4-cycle', r'6-cycle', r'cycle-free', r'cycle structure', r'cycle multiplicit',
    ],
    'B_trapping_enum': [
        r'trapping set', r'absorbing set', r'stopping set', r'elementary trapping', r'leafless',
        r'pseudo-?codeword', r'instanton', r'near-?codeword',
        r'error[- ]floor (estimat|predict|analys|character)', r'dominant (error|trapping|absorbing)',
        r'harmful (structure|subgraph|cycle|trapping)',
        r'trapping[- ]set (ontology|search|enumerat|identif|charact)',
    ],
    'C_failure_diag': [
        r'decod(ing|er) failure', r'post-?processing', r'failed (codeword|decoding|frame)',
        r'uncorrect(ed|able)', r'undetected error', r'oscillat',
        r'trapping set (break|escap|aware|mitigat|detect|identif)', r'bit[- ]flipping .*trapping',
        r'error pattern.*(analy|identif)', r'importance sampling', r'unsatisfied check',
    ],
}
res = {k: [] for k in cats}
for pid, src, title, authors, abstract, pub, ctype, status, doi in rows:
    t = (title or '') + ' ' + (abstract or '')
    tl = t.lower()
    if not any(w in tl for w in ('ldpc', 'low-density', 'low density', 'tanner')):
        continue
    for k, pats in cats.items():
        h = [p for p in pats if re.search(p, tl)]
        if h:
            res[k].append(dict(
                id=pid, sid=sid(pid), year=(re.findall(r'(19|20)\d\d', pub or '') and re.search(r'(19|20)\d\d', pub).group(0)) or '', venue_type=ctype, status=status,
                title=title, authors=(json.loads(authors)[:4] if authors else []), abstract=abstract, doi=doi,
                txt=txt.get(sid(pid)), stage3_md=md.get(sid(pid)), matched=h))
for k, v in res.items():
    v.sort(key=lambda x: (x['txt'] is None, -int(x['year'] or 0)))
    with open(os.path.join(OUT, f'{k}.jsonl'), 'w', encoding='utf-8') as f:
        for r in v:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    n_txt = sum(1 for r in v if r['txt'])
    print(k, len(v), 'with_txt', n_txt, 'filtered_in', sum(1 for r in v if r['status'] == 'filtered_in'))
ids = {k: set(r['id'] for r in v) for k, v in res.items()}
print('A&B', len(ids['A_cycle_count'] & ids['B_trapping_enum']),
      'B&C', len(ids['B_trapping_enum'] & ids['C_failure_diag']),
      'A&C', len(ids['A_cycle_count'] & ids['C_failure_diag']))
print('union', len(set().union(*ids.values())))

for k, v in res.items():
    with open(os.path.join(OUT, f'{k}_titles.txt'), 'w', encoding='utf-8') as f:
        f.write('# id | year | fulltext(T=txt available, -=abstract only) | title\n')
        for r in v:
            f.write(f"{r['id']} | {r['year']} | {'T' if r['txt'] else '-'} | {r['title']}\n")
