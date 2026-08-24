"""md 문서를 같은 자리의 html로 변환하는 렌더러.

사용법 (3_LDPC_ideas/ 기준, 다른 위치에서 실행해도 동작):
    python render.py                  # 폴더 안의 md 전체를 일괄 변환
    python render.py README.md        # 지정한 파일만 변환

동작:
    - 각 {이름}.md 옆에 {이름}.html을 만든다 (md가 정본, html은 열람용 파생물)
    - 문서 안의 .md 링크는 .html 링크로 바꿔서 html끼리 이동이 이어지게 한다
    - 일괄 변환 대상: 3_LDPC_ideas/ 아래 전체 md.
      제외: _pm/, _template/, Sim_Output/, __pycache__/

산출 html은 브라우저 열람과 Confluence 붙여넣기를 함께 감당한다. 그래서 모든 CSS
선택자를 최상위 래퍼 id(WRAPPER_ID) 아래로 가두고, 붙여넣을 범위를 주석으로 표시한다.
Confluence에 올릴 때는 <!doctype html>부터가 아니라 "복사 시작"과 "복사 끝" 사이만
복사한다 (<body> 태그가 딸려 가면 Confluence 페이지 전체가 물든다).

필요 패키지: markdown (pip install markdown)
"""
import re
import sys
from pathlib import Path

import markdown

IDEAS_DIR = Path(__file__).resolve().parent
EXCLUDE_DIR_NAMES = {"_pm", "_template", "Sim_Output", "__pycache__"}

WRAPPER_ID = "ldpcDocRoot"

PAGE_STYLE = """
#ldpcDocRoot {
    --text: #24292f;
    --muted: #57606a;
    --border: #d0d7de;
    --surface: #f6f8fa;
    --accent: #0969da;
    margin: 0 auto;
    padding: 32px 24px 80px;
    max-width: 880px;
    color: var(--text);
    font-family: "Segoe UI", "Malgun Gothic", "맑은 고딕", sans-serif;
    font-size: 16px;
    line-height: 1.7;
    background: #ffffff;
}
#ldpcDocRoot *, #ldpcDocRoot *::before, #ldpcDocRoot *::after { box-sizing: border-box; }
#ldpcDocRoot h1, #ldpcDocRoot h2, #ldpcDocRoot h3, #ldpcDocRoot h4 { line-height: 1.3; margin: 1.6em 0 0.6em; }
#ldpcDocRoot h1 { font-size: 1.9em; border-bottom: 2px solid var(--border); padding-bottom: 0.3em; }
#ldpcDocRoot h2 { font-size: 1.45em; border-bottom: 1px solid var(--border); padding-bottom: 0.25em; }
#ldpcDocRoot h3 { font-size: 1.15em; }
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
#ldpcDocRoot tr:nth-child(even) td { background: #fbfcfd; }
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
"""

PAGE_FRAME = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
</head>
<body>
<!-- ############################## 복사 시작 ############################## -->
<div id="{wrapper_id}">
<style>{style}</style>
{body}
</div>
<!-- ############################## 복사 끝 ############################## -->
</body>
</html>
"""


def extract_title(md_text, fallback):
    """첫 h1 제목을 페이지 제목으로 쓴다. 없으면 파일 이름."""
    for line in md_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def redirect_md_links_to_html(html_body):
    """본문 안의 .md 링크를 .html로 바꾼다 (외부 http 링크는 그대로 둔다)."""
    def replace(match):
        href = match.group(1)
        if href.startswith(("http://", "https://")):
            return match.group(0)
        return 'href="' + re.sub(r"\.md(?=$|#)", ".html", href) + '"'
    return re.sub(r'href="([^"]+\.md(?:#[^"]*)?)"', replace, html_body)


def render_file(md_path):
    """md 파일 하나를 형제 html로 변환하고 산출 경로를 돌려준다."""
    md_text = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(md_text, extensions=["extra"])
    body = redirect_md_links_to_html(body)
    page = PAGE_FRAME.format(
        title=extract_title(md_text, md_path.stem),
        wrapper_id=WRAPPER_ID,
        style=PAGE_STYLE,
        body=body,
    )
    html_path = md_path.with_suffix(".html")
    html_path.write_text(page, encoding="utf-8")
    return html_path


def collect_render_targets():
    """일괄 변환 대상 md 목록 (제외 폴더 아래는 걸러낸다)."""
    targets = []
    for md_path in sorted(IDEAS_DIR.rglob("*.md")):
        relative_parts = md_path.relative_to(IDEAS_DIR).parts[:-1]
        if any(part in EXCLUDE_DIR_NAMES for part in relative_parts):
            continue
        targets.append(md_path)
    return targets


def main():
    sys.stdout.reconfigure(encoding="utf-8")   # Windows 콘솔 한글 출력 보장
    if len(sys.argv) > 1:
        targets = [Path(arg).resolve() for arg in sys.argv[1:]]
        missing = [str(p) for p in targets if not p.is_file()]
        if missing:
            sys.exit(f"파일 없음: {', '.join(missing)}")
    else:
        targets = collect_render_targets()

    for md_path in targets:
        html_path = render_file(md_path)
        try:
            shown = html_path.relative_to(IDEAS_DIR)
        except ValueError:
            shown = html_path
        print(f"변환: {shown}")
    print(f"완료: {len(targets)}개")


if __name__ == "__main__":
    main()
