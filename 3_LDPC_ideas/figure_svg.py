"""보고서 그림(svg)을 그리는 공용 도구.

아이디어 폴더의 make_figures.py가 이 모듈의 함수로 그림을 조립해 그 폴더의 figures/ 아래에
svg 파일로 저장한다. README.md는 그 svg를 markdown 이미지 문법으로 가리키고
(`![그림 1. 설명](figures/이름.svg)`), render.py가 html을 만들 때 svg 내용을 페이지 안에 넣는다.

색:
    - 모든 색은 페이지의 css 변수(--text, --muted, --border, --bg, --surface, --mark-better,
      --mark-worse, --warn)를 읽는다. 페이지 안에서는 밝은 모드와 어두운 모드를 페이지와 함께 따른다
    - svg 파일을 단독으로 열면 변수 뒤의 기본값(밝은 모드 색)으로 그려진다
    - 색의 뜻은 보고서 전체에서 같다: 빨강(better)은 개선, 파랑(worse)은 열화,
      주황(change)은 논문이 바꾼 것, 회색(neutral)은 기준선과 기존 구조
    - 글자는 색을 입지 않는다. 뜻은 글자 옆의 색 표식과 낱말("개선", "악화")이 함께 전한다

그림 종류:
    - horizontal_bar_chart: 조건별 값 하나씩을 기준선과 비교하는 가로 막대
    - line_chart: 순서가 있는 가로축 위의 꺾은선 (iteration 궤적, 조건 세기별 변화)
    - 개념 그림과 구성 그림: text, box, arrow, column_bar 같은 조각을 좌표로 직접 놓는다

값을 읽는 길:
    - 막대와 점에 마우스를 올리면 값이 뜬다 (svg의 title 요소, 스크립트 없음)
    - 모든 값은 README의 표에도 있다. 표의 값을 그대로 그리려면 read_md_table로 읽는다
"""
import re
from html import escape
from pathlib import Path

FIGURE_CLASS = "ldpc-fig"
DEFAULT_WIDTH = 760

TONE_NEUTRAL = "neutral"
TONE_BETTER = "better"
TONE_WORSE = "worse"
TONE_CHANGE = "change"

FIGURE_STYLE = """
.ldpc-fig { font-family: "Segoe UI", "Malgun Gothic", "맑은 고딕", "Apple SD Gothic Neo", sans-serif; }
.ldpc-fig .surface { fill: var(--bg, #ffffff); }
.ldpc-fig text { fill: var(--text, #24292f); font-size: 13px; }
.ldpc-fig text.muted { fill: var(--muted, #57606a); }
.ldpc-fig text.small { font-size: 12px; }
.ldpc-fig text.strong { font-weight: 600; }
.ldpc-fig text.head { font-size: 14px; font-weight: 600; }
.ldpc-fig .grid { stroke: var(--border, #d0d7de); stroke-width: 1; fill: none; }
.ldpc-fig .reference { stroke: var(--text, #24292f); stroke-width: 1; fill: none; opacity: 0.6; }
.ldpc-fig .mark-neutral { fill: var(--muted, #57606a); }
.ldpc-fig .mark-faint { fill: var(--muted, #57606a); opacity: 0.4; }
.ldpc-fig .mark-strong { fill: var(--text, #24292f); opacity: 0.82; }
.ldpc-fig .mark-better { fill: var(--mark-better, #d1242f); }
.ldpc-fig .mark-worse { fill: var(--mark-worse, #0550ae); }
.ldpc-fig .mark-change { fill: var(--warn, #bc4c00); }
.ldpc-fig .line-neutral, .ldpc-fig .line-better, .ldpc-fig .line-worse, .ldpc-fig .line-change {
    fill: none; stroke-width: 2; stroke-linejoin: round; stroke-linecap: round;
}
.ldpc-fig .line-neutral { stroke: var(--muted, #57606a); }
.ldpc-fig .line-better { stroke: var(--mark-better, #d1242f); }
.ldpc-fig .line-worse { stroke: var(--mark-worse, #0550ae); }
.ldpc-fig .line-change { stroke: var(--warn, #bc4c00); }
.ldpc-fig .ring { stroke: var(--bg, #ffffff); stroke-width: 2; }
.ldpc-fig .cut { fill: none; stroke: var(--muted, #57606a); stroke-width: 1; stroke-dasharray: 3 3; }
.ldpc-fig .box { fill: var(--surface, #f6f8fa); stroke: var(--border, #d0d7de); stroke-width: 1; }
.ldpc-fig .box-change { fill: var(--surface, #f6f8fa); stroke: var(--warn, #bc4c00); stroke-width: 2; }
.ldpc-fig .arrow { stroke: var(--muted, #57606a); stroke-width: 1.5; fill: none; }
.ldpc-fig .arrow-head { fill: var(--muted, #57606a); }
.ldpc-fig .hit { fill: transparent; }
"""


# ----------------------------------------------------------------------------
# 숫자와 글자
# ----------------------------------------------------------------------------

def coordinate(value):
    """좌표를 소수 한 자리까지의 짧은 글자로 바꾼다 (같은 입력이면 늘 같은 svg가 나온다)."""
    return "{:.1f}".format(value).rstrip("0").rstrip(".")


def format_fixed3(value):
    """비율 값을 소수 셋째 자리까지 적는다 (0.484, 1.000). 막대 끝의 값 표시에 쓴다."""
    return "{:.3f}".format(value)


def format_short(value):
    """비율 값을 짧게 적는다 (0, 0.25, 0.641, 1.0). 축 눈금과 설명 글에 쓴다."""
    if value == 0:
        return "0"
    if value == int(value):
        return "{:.1f}".format(value)
    return "{:.3g}".format(value)


def estimate_text_width(content, font_size=13):
    """글자 폭 어림값 (px). 한글과 전각 기호는 1em, 영문과 숫자는 그보다 좁게 잡는다."""
    em = 0.0
    for character in content:
        if ord(character) >= 0x1100:
            em += 1.0
        elif character == " ":
            em += 0.3
        elif character in "()[],.:;'|!ilI1":
            em += 0.34
        elif character.isupper() or character.isdigit():
            em += 0.6
        else:
            em += 0.54
    return em * font_size


# ----------------------------------------------------------------------------
# 조각
# ----------------------------------------------------------------------------

def text(x, y, content, classes="", anchor="start"):
    class_attribute = ' class="{}"'.format(classes) if classes else ""
    anchor_attribute = "" if anchor == "start" else ' text-anchor="{}"'.format(anchor)
    return '<text x="{}" y="{}"{}{}>{}</text>'.format(
        coordinate(x), coordinate(y), class_attribute, anchor_attribute, escape(content))


def text_lines(x, y, lines, classes="", anchor="start", line_height=17):
    """여러 줄 글. y는 첫 줄의 기준선이다."""
    return "".join(text(x, y + index * line_height, content, classes, anchor)
                   for index, content in enumerate(lines))


def segment(x1, y1, x2, y2, classes):
    return '<line x1="{}" y1="{}" x2="{}" y2="{}" class="{}"/>'.format(
        coordinate(x1), coordinate(y1), coordinate(x2), coordinate(y2), classes)


def rectangle(x, y, width, height, classes, corner=0):
    corner_attribute = ' rx="{}"'.format(coordinate(corner)) if corner else ""
    return '<rect x="{}" y="{}" width="{}" height="{}"{} class="{}"/>'.format(
        coordinate(x), coordinate(y), coordinate(width), coordinate(height), corner_attribute, classes)


def row_bar(x, y, width, height, classes, corner=4):
    """왼쪽 기준선에서 오른쪽으로 자라는 가로 막대. 값 쪽 끝만 둥글다."""
    if width <= 0:
        return ""
    corner = min(corner, width, height / 2)
    return ('<path d="M{x},{y} h{run} a{r},{r} 0 0 1 {r},{r} v{rise} a{r},{r} 0 0 1 -{r},{r} h-{run} z" '
            'class="{c}"/>').format(
                x=coordinate(x), y=coordinate(y), run=coordinate(width - corner), r=coordinate(corner),
                rise=coordinate(height - 2 * corner), c=classes)


def column_bar(x, baseline_y, width, height, classes, corner=4):
    """아래 기준선에서 위로 자라는 세로 막대. 값 쪽 끝(위)만 둥글다."""
    if height <= 0:
        return ""
    corner = min(corner, height, width / 2)
    return ('<path d="M{x},{y} v-{rise} a{r},{r} 0 0 1 {r},-{r} h{run} a{r},{r} 0 0 1 {r},{r} v{rise} z" '
            'class="{c}"/>').format(
                x=coordinate(x), y=coordinate(baseline_y), rise=coordinate(height - corner),
                r=coordinate(corner), run=coordinate(width - 2 * corner), c=classes)


def box(x, y, width, height, lines, classes="box"):
    """모서리가 둥근 상자와 가운데 정렬 글. 첫 줄은 굵게, 나머지 줄은 옅게 쓴다."""
    parts = [rectangle(x, y, width, height, classes, corner=8)]
    line_height = 18
    first_baseline = y + height / 2 - (len(lines) - 1) * line_height / 2 + 4.5
    for index, content in enumerate(lines):
        classes_for_line = "strong" if index == 0 else "muted small"
        parts.append(text(x + width / 2, first_baseline + index * line_height, content,
                          classes_for_line, anchor="middle"))
    return "".join(parts)


def arrow(points, head_length=9, head_half_width=4.5):
    """꺾은선 화살표. points는 (x, y) 목록이고 마지막 점에 화살촉이 붙는다."""
    (x1, y1), (x2, y2) = points[-2], points[-1]
    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    unit_x, unit_y = (x2 - x1) / length, (y2 - y1) / length
    base_x, base_y = x2 - unit_x * head_length, y2 - unit_y * head_length
    shaft = list(points[:-1]) + [(base_x, base_y)]
    shaft_points = " ".join("{},{}".format(coordinate(px), coordinate(py)) for px, py in shaft)
    head_points = " ".join("{},{}".format(coordinate(px), coordinate(py)) for px, py in (
        (x2, y2),
        (base_x - unit_y * head_half_width, base_y + unit_x * head_half_width),
        (base_x + unit_y * head_half_width, base_y - unit_x * head_half_width),
    ))
    return '<polyline points="{}" class="arrow"/><polygon points="{}" class="arrow-head"/>'.format(
        shaft_points, head_points)


def with_tooltip(content, tooltip):
    """조각 묶음에 마우스를 올리면 뜨는 글을 붙인다."""
    return "<g><title>{}</title>{}</g>".format(escape(tooltip), content)


def legend_row(x, y, entries, kind="square"):
    """범례 한 줄. entries는 (tone, 이름) 목록. kind는 square(막대용)나 line(꺾은선용)."""
    parts = []
    cursor = x
    for tone, name in entries:
        if kind == "line":
            parts.append(segment(cursor, y - 4, cursor + 18, y - 4, "line-" + tone))
            parts.append('<circle cx="{}" cy="{}" r="4" class="mark-{}"/>'.format(
                coordinate(cursor + 9), coordinate(y - 4), tone))
            swatch_width = 18
        else:
            parts.append(rectangle(cursor, y - 10, 10, 10, "mark-" + tone, corner=2))
            swatch_width = 10
        parts.append(text(cursor + swatch_width + 6, y, name, "small"))
        cursor += swatch_width + 6 + estimate_text_width(name, 12) + 22
    return "".join(parts)


# ----------------------------------------------------------------------------
# 그림 파일
# ----------------------------------------------------------------------------

def figure_document(width, height, label, parts):
    """조각들을 svg 문서 하나로 감싼다. label은 화면 낭독기가 읽는 그림 설명이다."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" class="{cls}" viewBox="0 0 {w} {h}" '
        'width="{w}" height="{h}" role="img" aria-label="{label}">\n'
        "<style>{style}</style>\n"
        '<rect x="0" y="0" width="{w}" height="{h}" class="surface"/>\n'
        "{body}\n"
        "</svg>\n"
    ).format(cls=FIGURE_CLASS, w=coordinate(width), h=coordinate(height), label=escape(label, quote=True),
             style=FIGURE_STYLE, body="\n".join(part for part in parts if part))


def write_figure(path, svg_text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg_text, encoding="utf-8", newline="\n")
    return path


# ----------------------------------------------------------------------------
# README 표 읽기
# ----------------------------------------------------------------------------

def read_md_table(md_path, heading_keyword):
    """md 문서에서 heading_keyword가 든 제목 아래 첫 표를 (머리 칸 목록, 행 목록)으로 읽는다.

    칸 안의 html 태그(색 표시 span)는 벗기고 글자만 남긴다.
    """
    lines = Path(md_path).read_text(encoding="utf-8").splitlines()
    inside_section = False
    table_lines = []
    for line in lines:
        if line.startswith("#"):
            if table_lines:
                break
            inside_section = heading_keyword in line
            continue
        if not inside_section:
            continue
        if line.lstrip().startswith("|"):
            table_lines.append(line.strip())
        elif table_lines:
            break
    if len(table_lines) < 3:
        raise ValueError("'{}' 제목 아래에서 표를 찾지 못함: {}".format(heading_keyword, md_path))

    def cells_of(row):
        cells = [re.sub(r"<[^>]+>", "", cell).strip() for cell in row.strip("|").split("|")]
        return cells
    header = cells_of(table_lines[0])
    rows = [cells_of(row) for row in table_lines[2:]]
    return header, rows


def first_number(cell):
    """표 칸의 글에서 첫 숫자를 읽는다 (예: '1.00e+00 (전 프레임 실패)' -> 1.0)."""
    match = re.search(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", cell)
    if not match:
        raise ValueError("칸에서 숫자를 찾지 못함: {!r}".format(cell))
    return float(match.group(0))


# ----------------------------------------------------------------------------
# 가로 막대: 조건별 값 하나씩을 기준선과 비교
# ----------------------------------------------------------------------------

def tone_against_baseline(value, baseline_value, lower_is_better):
    if value == baseline_value:
        return TONE_NEUTRAL
    improved = value < baseline_value if lower_is_better else value > baseline_value
    return TONE_BETTER if improved else TONE_WORSE


def horizontal_bar_chart(rows, *, label, value_axis_title, baseline_index=0, baseline_name="기준선",
                         lower_is_better=True, value_max=1.0, ticks=(0, 0.25, 0.5, 0.75, 1.0),
                         tone_names=None, value_format=format_fixed3, tick_format=format_short,
                         width=DEFAULT_WIDTH):
    """조건마다 값 하나를 가로 막대로 그리고, 기준선 행의 값에 세로 기준선을 긋는다.

    rows는 (조건 이름, 값) 목록. 기준선과 같은 값은 회색, 나아진 값은 빨강, 나빠진 값은 파랑이다.
    """
    tone_names = tone_names or {
        TONE_NEUTRAL: "기준선과 같음",
        TONE_BETTER: "기준선보다 개선",
        TONE_WORSE: "기준선보다 악화",
    }
    row_height, bar_height = 26, 14
    plot_left = 26 + max(estimate_text_width(name) for name, _ in rows)
    plot_right = width - 64
    plot_top = 62
    plot_bottom = plot_top + row_height * len(rows)
    height = plot_bottom + 50
    baseline_value = rows[baseline_index][1]

    def x_of(value):
        return plot_left + (plot_right - plot_left) * value / value_max

    tones = [tone_against_baseline(value, baseline_value, lower_is_better) for _, value in rows]
    parts = []
    legend_entries = [(tone, tone_names[tone]) for tone in (TONE_NEUTRAL, TONE_BETTER, TONE_WORSE)
                      if tone in tones]
    parts.append(legend_row(plot_left, 18, legend_entries))

    for tick in ticks:
        parts.append(segment(x_of(tick), plot_top, x_of(tick), plot_bottom, "grid"))
        parts.append(text(x_of(tick), plot_bottom + 17, tick_format(tick), "muted small", anchor="middle"))
    parts.append(text((plot_left + plot_right) / 2, plot_bottom + 38, value_axis_title,
                      "muted small", anchor="middle"))

    for index, ((name, value), tone) in enumerate(zip(rows, tones)):
        row_top = plot_top + row_height * index
        bar_top = row_top + (row_height - bar_height) / 2
        text_baseline = row_top + row_height / 2 + 4.5
        row_parts = [
            rectangle(0, row_top, width, row_height, "hit"),
            text(plot_left - 10, text_baseline, name, "strong" if index == baseline_index else "",
                 anchor="end"),
            row_bar(plot_left, bar_top, x_of(value) - plot_left, bar_height, "mark-" + tone),
            text(x_of(value) + 7, text_baseline, value_format(value), "small"),
        ]
        parts.append(with_tooltip("".join(row_parts), "{}: {}".format(name, value_format(value))))

    parts.append(segment(x_of(baseline_value), plot_top - 6, x_of(baseline_value), plot_bottom, "reference"))
    parts.append(text(x_of(baseline_value), plot_top - 12,
                      "{} {}".format(baseline_name, value_format(baseline_value)), "small", anchor="middle"))
    return figure_document(width, height, label, parts)


# ----------------------------------------------------------------------------
# 꺾은선: 순서가 있는 가로축 위의 변화
# ----------------------------------------------------------------------------

def line_chart(series, x_values, *, label, y_max, y_ticks, y_axis_title, x_axis_title,
               x_tick_values=None, x_tick_labels=None, y_tick_format=format_short,
               value_format=format_short, mark_every_point=False,
               width=DEFAULT_WIDTH, height=300, end_label_width=200):
    """꺾은선 그림. series는 dict 목록이다.

    각 dict: name(범례 이름), values(x_values와 같은 길이), tone, end_label(선 끝 옆에 쓰는 글 줄 목록).
    x_tick_labels가 없으면 x_tick_values의 숫자를 그대로 쓴다.
    mark_every_point가 참이면 모든 점에 표식을 찍고, 거짓이면 선의 끝점에만 찍는다.
    """
    plot_left, plot_right = 56, width - end_label_width
    plot_top, plot_bottom = 64, height - 52
    inner_pad = 16
    x_min, x_max = min(x_values), max(x_values)

    def x_of(value):
        span = (x_max - x_min) or 1
        return plot_left + inner_pad + (plot_right - plot_left - 2 * inner_pad) * (value - x_min) / span

    def y_of(value):
        return plot_bottom - (plot_bottom - plot_top) * value / y_max

    parts = [legend_row(16, 20, [(item["tone"], item["name"]) for item in series], kind="line")]
    parts.append(text(16, 46, y_axis_title, "muted small"))

    for tick in y_ticks:
        parts.append(segment(plot_left, y_of(tick), plot_right, y_of(tick), "grid"))
        parts.append(text(plot_left - 8, y_of(tick) + 4, y_tick_format(tick), "muted small", anchor="end"))

    x_tick_values = list(x_tick_values if x_tick_values is not None else x_values)
    x_tick_labels = list(x_tick_labels if x_tick_labels is not None
                         else [format_short(value) for value in x_tick_values])
    for tick, tick_label in zip(x_tick_values, x_tick_labels):
        parts.append(text(x_of(tick), plot_bottom + 18, tick_label, "muted small", anchor="middle"))
    parts.append(text((plot_left + plot_right) / 2, plot_bottom + 40, x_axis_title,
                      "muted small", anchor="middle"))

    tick_label_of = dict(zip(x_tick_values, x_tick_labels))
    for item in series:
        tone = item["tone"]
        points = [(x_of(x), y_of(y)) for x, y in zip(x_values, item["values"])]
        parts.append('<polyline points="{}" class="line-{}"/>'.format(
            " ".join("{},{}".format(coordinate(px), coordinate(py)) for px, py in points), tone))
        marked = points if mark_every_point else points[-1:]
        for px, py in marked:
            parts.append('<circle cx="{}" cy="{}" r="5" class="mark-{} ring"/>'.format(
                coordinate(px), coordinate(py), tone))
        for (px, py), x, y in zip(points, x_values, item["values"]):
            position_name = tick_label_of.get(x, "{} {}".format(x_axis_title.split(" ")[0], format_short(x)))
            parts.append(with_tooltip(
                '<circle cx="{}" cy="{}" r="9" class="hit"/>'.format(coordinate(px), coordinate(py)),
                "{}, {}: {}".format(item["name"], position_name, value_format(y))))
        end_x, end_y = points[-1]
        end_lines = item.get("end_label") or []
        block_height = (len(end_lines) - 1) * 17
        first_baseline = end_y + 4.5 - block_height / 2
        first_baseline = max(plot_top + 4.5, min(first_baseline, plot_bottom - 5 - block_height))
        for index, content in enumerate(end_lines):
            parts.append(text(end_x + 14, first_baseline + index * 17, content,
                              "strong" if index == 0 else "muted small"))
    return figure_document(width, height, label, parts)
