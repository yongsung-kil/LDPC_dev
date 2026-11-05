"""md 문서를 같은 자리의 html로 변환하고, 아이디어 대시보드(저장소 루트 index.html)를 만드는 렌더러.

사용법 (3_LDPC_ideas/ 기준, 다른 위치에서 실행해도 동작):
    python render.py                  # 폴더 안의 md 전체를 변환하고 index.html을 다시 만든다
    python render.py README.md        # 지정한 파일만 변환 (대시보드는 만들지 않는다)

동작:
    - 각 {이름}.md 옆에 {이름}.html을 만든다 (md가 정본, html은 열람용 파생물). GitHub Pages는
      저장소 루트를 소스로 두어 어느 폴더의 html이든 그대로 서빙한다 (루트 .nojekyll이 밑줄로
      시작하는 _pm/ 폴더를 공개에서 빠지지 않게 한다)
    - 문서 안의 상대 링크 가운데 변환 대상 md를 가리키는 것은 그 md의 html로 바꾼다. 그 밖의
      링크는 가리키는 파일 그대로 둔다
    - 일괄 변환 대상: 3_LDPC_ideas/ 아래 전체 md (제외: _pm/, _template/, Sim_Output/,
      __pycache__/). 변환 대상 문서가 링크로 가리키는 md(예: _pm/tasks/의 논문 분석 메모)는
      제외 폴더 안이라도 함께 변환한다 (한 단계만)
    - 대시보드 (저장소 루트 index.html): 아이디어 폴더({번호3자리}_{이름}/)마다 README.md의
      머리줄(제목, 출처, 상태)과 📌 요약 절의 "논문 아이디어", "실험 결과" 항목, 출처 상세의
      "적용 분석 메모" 링크를 읽어 카드 하나를 만든다. 카드를 누르면 그 README.html로 간다
      (README 형식은 보고서작성규칙.md 16절). 링크는 저장소 루트 기준 상대 경로다
    - 일괄 변환 뒤 3_LDPC_ideas/ 안에 남은, 이번에 만들지 않은 render.py 산출 html은 지운다
      (이름이 바뀌거나 변환 대상에서 빠진 md의 묵은 산출물)
    - 렌더 뒤 html 안의 상대 링크가 가리키는 파일과 앵커가 있는지 검사해 없는 것을 보고한다

규격: HTML 작성 가이드 (정적 파일, 상대 링크만, 외부 자원 없음, :root css 변수와
어두운 모드, 시스템 글꼴). 모든 CSS 선택자는 최상위 래퍼 id 아래로 가둔다.

필요 패키지: markdown (pip install markdown)
"""
import os
import re
import sys
from html import escape
from pathlib import Path
from urllib.parse import quote, unquote

import markdown
from markdown.extensions.toc import slugify_unicode

IDEAS_DIR = Path(__file__).resolve().parent
REPO_ROOT = IDEAS_DIR.parent
EXCLUDE_DIR_NAMES = {"_pm", "_template", "Sim_Output", "__pycache__"}
IDEA_FOLDER_PATTERN = re.compile(r"^\d{3}_")

DASHBOARD_PATH = REPO_ROOT / "index.html"      # 저장소 루트 (GitHub Pages 소스가 루트이므로 입구)
RENDER_MARK = "<!-- render.py가 "              # 산출 html의 표식. 묵은 산출물 정리 때 이것이 있는 파일만 지운다
STALE_SCAN_SKIP = {"Sim_Output", "__pycache__"}
DASHBOARD_TITLE = "논문 아이디어 적용 대시보드"
PAPER_ARCHIVE_URL = "https://yongsung-kil.github.io/ECC_papers/"

DOC_WRAPPER_ID = "ldpcDocRoot"
DASH_WRAPPER_ID = "ldpcDashRoot"

SUMMARY_HEADING = "요약"
SOURCE_HEADING = "출처 상세"
FEATURE_LABEL = "논문 아이디어"
RESULT_LABEL = "실험 결과"
MEMO_LABEL = "적용 분석 메모"

MD_EXTENSIONS = ["extra", "toc"]
MD_EXTENSION_CONFIGS = {"toc": {"slugify": slugify_unicode}}

# 상태 배지의 판정 낱말 -> css class. 순서는 대시보드 집계 표시 순서이기도 하다
STATUS_ORDER = [
    ("반영됨", "done"),
    ("성공", "ok"),
    ("조건부 유효", "ok"),
    ("실험중", "pending"),
    ("대기", "pending"),
    ("실패", "fail"),
    ("폐기", "fail"),
]

THEME_STYLE = """
:root {
    --bg: #ffffff;
    --surface: #f6f8fa;
    --row: #fbfcfd;
    --text: #24292f;
    --muted: #57606a;
    --border: #d0d7de;
    --accent: #0969da;
    --ok: #1a7f37;
    --warn: #bc4c00;
    --better: #d1242f;
    --worse: #0550ae;
}
@media (prefers-color-scheme: dark) {
    :root {
        --bg: #0d1117;
        --surface: #161b22;
        --row: #11161d;
        --text: #e6edf3;
        --muted: #8b949e;
        --border: #30363d;
        --accent: #4493f8;
        --ok: #3fb950;
        --warn: #f0883e;
        --better: #ff7b72;
        --worse: #79c0ff;
    }
}
body { margin: 0; background: var(--bg); color: var(--text); }
"""

DOC_STYLE = """
#ldpcDocRoot {
    margin: 0 auto;
    padding: 24px 24px 80px;
    max-width: 880px;
    color: var(--text);
    font-family: "Segoe UI", "Malgun Gothic", "맑은 고딕", "Apple SD Gothic Neo", sans-serif;
    font-size: 16px;
    line-height: 1.7;
}
#ldpcDocRoot *, #ldpcDocRoot *::before, #ldpcDocRoot *::after { box-sizing: border-box; }
#ldpcDocRoot .doc-nav { font-size: 0.9em; color: var(--muted); }
#ldpcDocRoot .doc-nav a { margin-right: 12px; }
#ldpcDocRoot h1, #ldpcDocRoot h2, #ldpcDocRoot h3, #ldpcDocRoot h4 { line-height: 1.3; margin: 1.6em 0 0.6em; }
#ldpcDocRoot h1 { font-size: 1.9em; border-bottom: 2px solid var(--border); padding-bottom: 0.3em; }
#ldpcDocRoot h2 { font-size: 1.45em; border-bottom: 1px solid var(--border); padding-bottom: 0.25em; }
#ldpcDocRoot h3 { font-size: 1.15em; }
#ldpcDocRoot h4 { font-size: 1.0em; }
#ldpcDocRoot a { color: var(--accent); text-decoration: none; }
#ldpcDocRoot a:hover { text-decoration: underline; }
#ldpcDocRoot p, #ldpcDocRoot ul, #ldpcDocRoot ol { margin: 0.6em 0; }
#ldpcDocRoot li { margin: 0.25em 0; }
#ldpcDocRoot blockquote {
    margin: 0.8em 0;
    padding: 0.4em 1em;
    border-left: 4px solid var(--border);
    color: var(--muted);
    background: var(--surface);
}
#ldpcDocRoot table {
    border-collapse: collapse;
    margin: 1em 0;
    display: block;
    overflow-x: auto;
}
#ldpcDocRoot th, #ldpcDocRoot td {
    border: 1px solid var(--border);
    padding: 6px 12px;
    text-align: left;
    white-space: nowrap;
}
#ldpcDocRoot th { background: var(--surface); }
#ldpcDocRoot tr:nth-child(even) td { background: var(--row); }
#ldpcDocRoot code {
    font-family: Consolas, "D2Coding", monospace;
    font-size: 0.9em;
    background: var(--surface);
    padding: 0.15em 0.4em;
    border-radius: 4px;
}
#ldpcDocRoot pre {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px 16px;
    overflow-x: auto;
}
#ldpcDocRoot pre code { background: none; padding: 0; }
#ldpcDocRoot hr { border: none; border-top: 1px solid var(--border); margin: 2em 0; }
#ldpcDocRoot .better { color: var(--better); font-weight: 600; }
#ldpcDocRoot .worse { color: var(--worse); font-weight: 600; }
"""

DASH_STYLE = """
#ldpcDashRoot {
    margin: 0 auto;
    padding: 32px 32px 96px;
    max-width: 1180px;
    color: var(--text);
    font-family: "Segoe UI", "Malgun Gothic", "맑은 고딕", "Apple SD Gothic Neo", sans-serif;
    font-size: 16px;
    line-height: 1.7;
}
#ldpcDashRoot *, #ldpcDashRoot *::before, #ldpcDashRoot *::after { box-sizing: border-box; }
#ldpcDashRoot a {
    color: var(--accent);
    text-decoration: none;
    transition: color 150ms cubic-bezier(0.22, 1, 0.36, 1);
}
#ldpcDashRoot a:hover { text-decoration: underline; }
#ldpcDashRoot a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }
#ldpcDashRoot strong { font-weight: 600; }
#ldpcDashRoot h1 { font-size: 28px; line-height: 1.15; font-weight: 500; margin: 0 0 8px; }
#ldpcDashRoot .intro { margin: 0 0 20px; color: var(--muted); }
#ldpcDashRoot .site-nav {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 20px;
    margin: 0 0 32px;
    padding: 0;
    list-style: none;
    font-size: 14px;
    line-height: 20px;
}
#ldpcDashRoot .site-nav li a { color: var(--muted); }
#ldpcDashRoot .site-nav li a:hover { color: var(--accent); }
#ldpcDashRoot .stats {
    display: flex;
    flex-wrap: wrap;
    gap: 16px 40px;
    margin: 0 0 32px;
    padding: 0;
    list-style: none;
}
#ldpcDashRoot .stats li { display: flex; flex-direction: column; gap: 4px; }
#ldpcDashRoot .stats .label { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; line-height: 20px; color: var(--muted); }
#ldpcDashRoot .stats .count {
    font-family: Consolas, "D2Coding", monospace;
    font-size: 28px;
    line-height: 1;
    font-weight: 500;
    font-variant-numeric: tabular-nums;
}
#ldpcDashRoot .dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 4px;
    background: var(--muted);
    flex: none;
}
#ldpcDashRoot .status-ok .dot, #ldpcDashRoot .status-done .dot { background: var(--ok); }
#ldpcDashRoot .status-fail .dot { background: var(--worse); }
#ldpcDashRoot .status-pending .dot { background: var(--warn); }
#ldpcDashRoot .cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    align-items: start;
    gap: 16px;
    margin: 0;
    padding: 0;
    list-style: none;
}
#ldpcDashRoot .card {
    position: relative;
    display: flex;
    flex-direction: column;
    padding: 20px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--bg);
    transition: background-color 150ms cubic-bezier(0.22, 1, 0.36, 1);
}
#ldpcDashRoot .card:hover { background: var(--surface); }
#ldpcDashRoot .card-head {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0 0 8px;
    font-size: 13px;
    line-height: 20px;
    color: var(--muted);
}
#ldpcDashRoot .num {
    font-family: Consolas, "D2Coding", monospace;
    font-weight: 500;
    font-variant-numeric: tabular-nums;
}
#ldpcDashRoot .status { display: inline-flex; align-items: center; gap: 8px; }
#ldpcDashRoot .card h2 { font-size: 17px; line-height: 1.4; font-weight: 600; margin: 0 0 4px; }
#ldpcDashRoot .card h2 a { color: var(--text); }
#ldpcDashRoot .card h2 a:hover { text-decoration: none; }
#ldpcDashRoot .card h2 a::after { content: ""; position: absolute; inset: 0; }
#ldpcDashRoot .card .source { margin: 0 0 4px; font-size: 13px; line-height: 20px; color: var(--muted); }
#ldpcDashRoot .card .status-note { margin: 0 0 12px; font-size: 13px; line-height: 20px; color: var(--muted); }
#ldpcDashRoot .card h3 {
    margin: 16px 0 4px;
    font-size: 13px;
    line-height: 20px;
    font-weight: 500;
    color: var(--muted);
}
#ldpcDashRoot .card ul { margin: 0; padding-left: 20px; font-size: 15px; line-height: 22px; list-style: disc; }
#ldpcDashRoot .card li { margin: 4px 0; }
#ldpcDashRoot .card .links {
    position: relative;
    z-index: 1;
    display: flex;
    gap: 16px;
    margin: 16px 0 0;
    font-size: 13px;
    line-height: 20px;
}
#ldpcDashRoot .card code {
    font-family: Consolas, "D2Coding", monospace;
    font-size: 13px;
    background: var(--surface);
    padding: 2px 6px;
    border-radius: 4px;
}
#ldpcDashRoot .better { color: var(--better); font-weight: 600; }
#ldpcDashRoot .worse { color: var(--worse); font-weight: 600; }
#ldpcDashRoot .empty { color: var(--muted); }
@media (max-width: 600px) {
    #ldpcDashRoot { padding: 16px 16px 64px; }
    #ldpcDashRoot .cards { grid-template-columns: 1fr; }
}
"""

DOC_FRAME = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<!-- render.py가 {source}에서 만든 파일. md가 정본이므로 이 파일을 손으로 고치지 않는다 -->
<style>{theme}{style}</style>
</head>
<body>
<div id="{wrapper_id}">
{nav}{body}
</div>
</body>
</html>
"""

DASH_FRAME = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<!-- render.py가 아이디어 폴더의 README.md에서 만든 파일. md가 정본이므로 이 파일을 손으로 고치지 않는다 -->
<style>{theme}{style}</style>
</head>
<body>
<div id="{wrapper_id}">
<h1>{title}</h1>
<p class="intro">{intro}</p>
<ul class="site-nav">
{nav}
</ul>
<ul class="stats">
{stats}
</ul>
<ul class="cards">
{cards}
</ul>
</div>
</body>
</html>
"""


# ----------------------------------------------------------------------------
# 공통: md 변환과 링크 처리
# ----------------------------------------------------------------------------

def convert_markdown(md_text):
    """md 본문을 html 조각으로 바꾼다 (표, 각주 등 extra 문법과 제목 id 포함)."""
    return markdown.markdown(
        md_text, extensions=MD_EXTENSIONS, extension_configs=MD_EXTENSION_CONFIGS
    )


def convert_inline(md_text):
    """한 줄 md(굵게, 코드, span)를 html 조각으로 바꾼다. 바깥 <p>는 벗긴다."""
    html = markdown.markdown(md_text, extensions=["extra"]).strip()
    if html.startswith("<p>") and html.endswith("</p>"):
        html = html[3:-4]
    return html


def extract_title(md_text, fallback):
    """첫 h1 제목을 페이지 제목으로 쓴다. 없으면 파일 이름."""
    for line in md_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def split_href(href):
    """href를 (경로, 조각)으로 나눈다. 조각은 '#…' 또는 빈 문자열."""
    if "#" in href:
        path, fragment = href.split("#", 1)
        return path, "#" + fragment
    return href, ""


def is_external(href):
    return href.startswith(("http://", "https://", "mailto:"))


def resolve_link_target(base_dir, href_path):
    """문서 폴더 기준 상대 링크가 가리키는 파일 경로 (퍼센트 인코딩을 푼다)."""
    return (base_dir / unquote(href_path)).resolve()


def html_path_for(md_path):
    """md의 html 산출 경로: 같은 폴더, 같은 이름."""
    return md_path.with_suffix(".html")


def rewrite_relative_links(html_body, md_path, rendered_md_paths):
    """본문의 상대 링크를 html 위치 기준으로 다시 쓴다.

    변환 대상 md를 가리키는 링크는 그 md의 html로 바꾸고, 그 밖의 파일을 가리키는 링크는
    가리키는 파일 그대로 둔다. 같은 문서 안의 앵커(#…)와 외부 주소는 그대로 둔다.
    """
    html_dir = html_path_for(md_path).parent

    def replace(match):
        href = match.group(1)
        if is_external(href) or href.startswith("#"):
            return match.group(0)
        path, fragment = split_href(href)
        target = resolve_link_target(md_path.parent, path)
        if path.endswith(".md") and target in rendered_md_paths:
            target = html_path_for(target)
        return 'href="' + relative_href(html_dir, target) + fragment + '"'
    return re.sub(r'href="([^"]+)"', replace, html_body)


def linked_md_paths(md_path):
    """문서가 링크로 가리키는 md 파일 가운데 3_LDPC_ideas 안에 실재하는 것."""
    text = md_path.read_text(encoding="utf-8")
    found = set()
    for href in re.findall(r"\]\(([^)\s]+)\)", text):
        if is_external(href):
            continue
        path, _ = split_href(href)
        if not path.endswith(".md"):
            continue
        target = resolve_link_target(md_path.parent, path)
        if target.is_file() and target.is_relative_to(IDEAS_DIR):
            found.add(target)
    return found


def collect_render_targets():
    """일괄 변환 대상 md 목록: 제외 폴더 밖의 전체 md + 그 문서들이 링크로 가리키는 md."""
    primary = []
    for md_path in sorted(IDEAS_DIR.rglob("*.md")):
        relative_parts = md_path.relative_to(IDEAS_DIR).parts[:-1]
        if any(part in EXCLUDE_DIR_NAMES for part in relative_parts):
            continue
        primary.append(md_path)
    linked = set()
    for md_path in primary:
        linked |= linked_md_paths(md_path)
    extra = sorted(linked - set(primary))
    return primary + extra


def relative_href(from_dir, target_path):
    """폴더 from_dir에서 target_path로 가는 상대 링크 (슬래시 구분, 퍼센트 인코딩)."""
    rel = Path(os.path.relpath(target_path, from_dir)).as_posix()
    return quote(rel)


def dashboard_href_from(md_path):
    """문서의 html 위치에서 대시보드로 가는 상대 경로. 3_LDPC_ideas 밖의 문서면 None."""
    if not md_path.is_relative_to(IDEAS_DIR):
        return None
    return relative_href(html_path_for(md_path).parent, DASHBOARD_PATH)


def render_file(md_path, rendered_md_paths):
    """md 파일 하나를 형제 html로 변환하고 산출 경로를 돌려준다."""
    md_text = md_path.read_text(encoding="utf-8")
    body = convert_markdown(md_text)
    body = rewrite_relative_links(body, md_path, rendered_md_paths)
    dashboard_href = dashboard_href_from(md_path)
    nav = ""
    if dashboard_href:
        nav = '<nav class="doc-nav"><a href="{}">대시보드로</a></nav>\n'.format(dashboard_href)
    page = DOC_FRAME.format(
        title=escape(extract_title(md_text, md_path.stem)),
        source=md_path.relative_to(REPO_ROOT).as_posix(),
        theme=THEME_STYLE,
        style=DOC_STYLE,
        wrapper_id=DOC_WRAPPER_ID,
        nav=nav,
        body=body,
    )
    html_path = html_path_for(md_path)
    html_path.write_text(page, encoding="utf-8")
    return html_path


# ----------------------------------------------------------------------------
# 대시보드: 아이디어 README 읽기
# ----------------------------------------------------------------------------

def section_lines(lines, heading_keyword):
    """'## … {heading_keyword}' 절의 본문 줄 목록 (다음 '## ' 전까지)."""
    inside = False
    collected = []
    for line in lines:
        if line.startswith("## "):
            if inside:
                break
            inside = heading_keyword in line
            continue
        if inside:
            collected.append(line)
    return collected


def parse_summary_items(lines):
    """요약 절을 {항목 이름: [1단계 bullet 문장, …]}로 읽는다.

    형식 (보고서작성규칙.md 1절, 16절):
        - **항목 이름**:            (들여쓰기 0)
            - 1단계 bullet          (들여쓰기 4)
                - 2단계 bullet      (들여쓰기 8, 카드에 싣지 않음)
    bullet이 여러 줄로 감겨 있으면 이어지는 줄을 앞 bullet에 붙인다.
    """
    items = {}
    label = None
    last_depth = None            # 직전 bullet의 단계 (0 항목, 1 카드에 싣는 bullet, 2 이하 생략)
    for raw in section_lines(lines, SUMMARY_HEADING):
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if stripped.startswith("- "):
            depth = indent // 4
            text = stripped[2:].strip()
            if depth == 0:
                match = re.match(r"^\*\*(.+?)\*\*:?\s*(.*)$", text)
                if match:
                    label = match.group(1).strip()
                    items[label] = []
                    rest = match.group(2).strip()
                    if rest:
                        items[label].append(rest)
                    last_depth = 0
                    continue
                label = None
                last_depth = None
                continue
            if label is None:
                continue
            if depth == 1:
                items[label].append(text)
            last_depth = depth
            continue
        # 들여쓰기 없는 일반 문단은 bullet 목록의 끝이다 (예: "참고) …" 문단)
        if indent == 0:
            label = None
            last_depth = None
            continue
        # 감긴 줄: 직전 bullet이 1단계일 때만 이어 붙인다 (0단계는 머리글 뒤 본문이 있을 때)
        if label is None or not items.get(label):
            continue
        if last_depth in (0, 1):
            items[label][-1] = items[label][-1] + " " + stripped
    return items


def parse_memo_link(lines):
    """출처 상세의 '적용 분석 메모' 항목 아래 첫 md 링크 (글, href). 없으면 None."""
    seen_label = False
    for raw in section_lines(lines, SOURCE_HEADING):
        if MEMO_LABEL in raw:
            seen_label = True
        if not seen_label:
            continue
        match = re.search(r"\[([^\]]+)\]\(([^)\s]+)\)", raw)
        if match:
            return match.group(1), match.group(2)
        stripped = raw.strip()
        if seen_label and stripped.startswith("- ") and MEMO_LABEL not in raw and not raw.startswith(" "):
            break   # 다음 0단계 항목으로 넘어감
    return None


def status_class(badge):
    for word, css in STATUS_ORDER:
        if word in badge:
            return css
    return "pending"


def parse_idea_readme(md_path, rendered_md_paths):
    """아이디어 README 하나에서 카드 재료를 읽는다."""
    folder = md_path.parent
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    h1 = extract_title(text, folder.name)
    match = re.match(r"^(\d{3})\s+\S+?:\s*(.+)$", h1)
    if match:
        number, title = match.group(1), match.group(2).strip()
    else:
        number, title = folder.name[:3], h1

    source, status = "", ""
    for line in lines:
        match = re.match(r"^출처:\s*(.+?)\s*\|\s*상태:\s*(.+?)\s*$", line)
        if match:
            source, status = match.group(1), match.group(2)
            break
    badge = re.split(r"\s*\(", status, maxsplit=1)[0].strip() or "대기"
    note = status[len(badge):].strip().strip("()").strip()

    summary = parse_summary_items(lines)
    memo = parse_memo_link(lines)
    memo_href = None
    if memo:
        memo_text, href = memo
        path, fragment = split_href(href)
        target = resolve_link_target(folder, path)
        if path.endswith(".md") and target in rendered_md_paths:
            target = html_path_for(target)
        # README 폴더 기준 경로를 대시보드 자리(저장소 루트) 기준으로 옮긴다
        memo_href = relative_href(REPO_ROOT, target) + fragment

    return {
        "number": number,
        "title": title,
        "href": relative_href(REPO_ROOT, html_path_for(md_path)),
        "source": source,
        "badge": badge,
        "note": note,
        "css": status_class(badge),
        "features": summary.get(FEATURE_LABEL, []),
        "results": summary.get(RESULT_LABEL, []),
        "memo_href": memo_href,
    }


def collect_ideas(rendered_md_paths):
    ideas = []
    for folder in sorted(IDEAS_DIR.iterdir()):
        if not folder.is_dir() or not IDEA_FOLDER_PATTERN.match(folder.name):
            continue
        readme = folder / "README.md"
        if readme.is_file():
            ideas.append(parse_idea_readme(readme, rendered_md_paths))
    return ideas


# ----------------------------------------------------------------------------
# 대시보드: html 조립
# ----------------------------------------------------------------------------

def bullet_list(sentences, empty_text):
    if not sentences:
        return '<p class="empty">{}</p>'.format(escape(empty_text))
    return "<ul>" + "".join("<li>{}</li>".format(convert_inline(s)) for s in sentences) + "</ul>"


def build_card(idea):
    parts = [
        '<li class="card status-{}">'.format(idea["css"]),
        '<div class="card-head"><span class="num">{}</span>'
        '<span class="status"><span class="dot"></span>{}</span></div>'.format(
            escape(idea["number"]), escape(idea["badge"])),
        '<h2><a href="{}">{}</a></h2>'.format(idea["href"], convert_inline(idea["title"])),
    ]
    if idea["source"]:
        parts.append('<p class="source">출처: {}</p>'.format(escape(idea["source"])))
    if idea["note"]:
        parts.append('<p class="status-note">{}</p>'.format(convert_inline(idea["note"])))
    parts.append("<h3>특징</h3>")
    parts.append(bullet_list(idea["features"], "요약의 논문 아이디어 항목이 없음"))
    parts.append("<h3>실험 결과</h3>")
    parts.append(bullet_list(idea["results"], "요약의 실험 결과 항목이 없음"))
    links = ['<a href="{}">상세 보고서</a>'.format(idea["href"])]
    if idea["memo_href"]:
        links.append('<a href="{}">논문 분석 메모</a>'.format(idea["memo_href"]))
    parts.append('<p class="links">{}</p>'.format("".join(links)))
    parts.append("</li>")
    return "\n".join(parts)


def build_stats(ideas):
    counts = {}
    for idea in ideas:
        counts[idea["badge"]] = counts.get(idea["badge"], 0) + 1
    ordered = [word for word, _ in STATUS_ORDER if word in counts]
    ordered += sorted(word for word in counts if word not in ordered)
    tiles = ['<li><span class="label">전체</span><span class="count">{}</span></li>'.format(len(ideas))]
    for word in ordered:
        tiles.append(
            '<li class="status-{}"><span class="label"><span class="dot"></span>{}</span>'
            '<span class="count">{}</span></li>'.format(status_class(word), escape(word), counts[word]))
    return "\n".join(tiles)


def site_href(md_name, heading_text=None):
    """대시보드에서 3_LDPC_ideas/ 문서의 html로 가는 링크 (제목 id는 slugify_unicode 규칙)."""
    href = relative_href(REPO_ROOT, html_path_for(IDEAS_DIR / md_name))
    if heading_text:
        href += "#" + quote(slugify_unicode(heading_text, "-"))
    return href


def build_site_nav():
    links = [
        ("동작 흐름", site_href("README.md", "동작 흐름")),
        ("논문 분석 아카이브", PAPER_ARCHIVE_URL),
        ("아이디어 현황표", site_href("README.md", "아이디어 현황표")),
        ("실험 로그", site_href("실험로그.md")),
        ("새 논문 적용 규칙", site_href("새논문적용규칙.md")),
        ("보고서 작성 규칙", site_href("보고서작성규칙.md")),
    ]
    return "\n".join('<li><a href="{}">{}</a></li>'.format(href, escape(text)) for text, href in links)


def render_dashboard(rendered_md_paths):
    ideas = collect_ideas(rendered_md_paths)
    intro = "논문 아이디어를 2_LDPC_base 시뮬레이터에 하나씩 적용해 본 결과. 카드를 누르면 상세 보고서로 간다."
    page = DASH_FRAME.format(
        title=DASHBOARD_TITLE,
        theme=THEME_STYLE,
        style=DASH_STYLE,
        wrapper_id=DASH_WRAPPER_ID,
        intro=escape(intro),
        nav=build_site_nav(),
        stats=build_stats(ideas),
        cards="\n".join(build_card(idea) for idea in ideas),
    )
    DASHBOARD_PATH.write_text(page, encoding="utf-8")
    return DASHBOARD_PATH, ideas


def remove_stale_html(produced):
    """3_LDPC_ideas/ 안의 render.py 산출 html 가운데 이번 일괄 변환이 만들지 않은 것을 지운다.

    이름이 바뀌거나 변환 대상에서 빠진 md의 묵은 산출물이 대상이다. 표식(RENDER_MARK)이
    없는 html은 render.py가 만든 것이 아니므로 건드리지 않는다.
    """
    keep = set(produced)
    removed = []
    for html_path in sorted(IDEAS_DIR.rglob("*.html")):
        if html_path in keep:
            continue
        if any(part in STALE_SCAN_SKIP for part in html_path.relative_to(IDEAS_DIR).parts[:-1]):
            continue
        head = html_path.read_text(encoding="utf-8", errors="ignore")[:800]
        if RENDER_MARK not in head:
            continue
        html_path.unlink()
        removed.append(html_path)
    return removed


# ----------------------------------------------------------------------------
# 검사
# ----------------------------------------------------------------------------

def check_links(html_paths):
    """만든 html의 상대 링크가 가리키는 파일과 앵커가 있는지 검사하고 깨진 것을 돌려준다."""
    broken = []
    for html_path in html_paths:
        text = html_path.read_text(encoding="utf-8")
        for href in re.findall(r'href="([^"]+)"', text):
            if is_external(href):
                continue
            path, fragment = split_href(href)
            target = html_path if not path else resolve_link_target(html_path.parent, path)
            if not target.is_file():
                broken.append((html_path, href, "파일 없음"))
                continue
            if fragment and target.suffix == ".html":
                anchor = unquote(fragment[1:])
                if 'id="{}"'.format(anchor) not in target.read_text(encoding="utf-8"):
                    broken.append((html_path, href, "앵커 없음"))
    return broken


def shown_path(path):
    """출력용 경로: 3_LDPC_ideas/ 기준, 그 밖이면 저장소 루트 기준."""
    for base in (IDEAS_DIR, IDEAS_DIR.parent):
        if path.is_relative_to(base):
            return str(path.relative_to(base))
    return str(path)


def main():
    sys.stdout.reconfigure(encoding="utf-8")   # Windows 콘솔 한글 출력 보장
    batch_targets = collect_render_targets()
    if len(sys.argv) > 1:
        targets = [Path(arg).resolve() for arg in sys.argv[1:]]
        missing = [str(p) for p in targets if not p.is_file()]
        if missing:
            sys.exit(f"파일 없음: {', '.join(missing)}")
        outside = [str(p) for p in targets if not p.is_relative_to(REPO_ROOT)]
        if outside:
            sys.exit(f"저장소 밖의 파일은 변환하지 않음: {', '.join(outside)}")
        make_dashboard = False
    else:
        targets = batch_targets
        make_dashboard = True
    rendered_md_paths = set(batch_targets) | set(targets)

    produced = []
    for md_path in targets:
        html_path = render_file(md_path, rendered_md_paths)
        produced.append(html_path)
        print(f"변환: {shown_path(html_path)}")

    if make_dashboard:
        html_path, ideas = render_dashboard(rendered_md_paths)
        produced.append(html_path)
        print(f"대시보드: {shown_path(html_path)} (카드 {len(ideas)}개)")
        for idea in ideas:
            lacking = [name for name, key in ((FEATURE_LABEL, "features"), (RESULT_LABEL, "results"))
                       if not idea[key]]
            if lacking:
                print(f"  주의: {idea['number']} README 요약에 {', '.join(lacking)} 항목이 없음")
        for stale_path in remove_stale_html(produced):
            print(f"정리: {shown_path(stale_path)} (이번에 만들지 않은 html이라 지움)")

    broken = check_links(produced)
    for html_path, href, reason in broken:
        print(f"링크 깨짐 ({reason}): {shown_path(html_path)} -> {href}")
    print(f"완료: {len(produced)}개, 깨진 링크 {len(broken)}개")


if __name__ == "__main__":
    main()
