"""
FER Plot Tool — LDPC 디코딩 결과 그래프 생성
엑셀에서 복붙한 탭/스페이스 구분 데이터를 읽어 FER 곡선을 그린다.
사용법 및 스타일 레퍼런스는 sample_data.txt 참조.
"""
import sys
import os
import re
import math
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

plt.rcParams['font.family'] = ['Times New Roman', 'Malgun Gothic']
plt.rcParams['font.weight'] = 'bold'
plt.rcParams['axes.labelweight'] = 'bold'
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['axes.unicode_minus'] = False

# 번호 -> 값 매핑
COLOR_MAP = {
    1: '#000000',  # 검정
    2: '#E31A1C',  # 빨강
    3: '#1F78B4',  # 파랑
    4: '#33A02C',  # 초록
    5: '#FF7F00',  # 주황
    6: '#6A3D9A',  # 보라
}
MARKER_MAP = {
    1: 'o',   # ●
    2: 's',   # ■
    3: '^',   # ▲
    4: 'D',   # ◆
    5: 'v',   # ▼
    6: '<',   # ◁
    7: '>',   # ▷
    8: 'p',   # ⬠
    9: 'h',   # ⬡
    10: '*',  # ★
    11: 'o',   # ○ (빈)
    12: 's',   # □ (빈)
    13: '^',   # △ (빈)
    14: 'D',   # ◇ (빈)
    15: 'v',   # ▽ (빈)
    16: '<',   # ◁ (빈)
    17: '>',   # ▷ (빈)
    18: 'p',   # ⬠ (빈)
    19: 'h',   # ⬡ (빈)
    20: '*',   # ☆ (빈)
}
LINESTYLE_MAP = {
    1: '-',    # 실선
    2: '--',   # 대시
    3: '-.',   # 대시점
    4: ':',    # 점선
}

# 플롯 설정
Y_LABEL = 'FER'
Y_TOP = 1.0
TITLE_FORMAT = 'FER vs {x_label}'
FIGSIZE = (8, 6)
DPI = 150

FONT_TITLE = 17
FONT_AXIS_LABEL = 15
FONT_TICK = 12
FONT_LEGEND = 12
FONT_CAPTION = 9

GRID_STYLE = '--'
GRID_ALPHA = 0.5

CAPTION_BGCOLOR = '#E8E8E8'
CAPTION_EDGECOLOR = '#CCCCCC'

# 시리즈 기본값
DEFAULTS = {
    'color': [1, 2, 3, 4, 5, 6],
    'marker': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    'linestyle': [1],
    'linewidth': [1.5],
    'markersize': [5],
}


def parse_file(text):
    """파일 텍스트 -> (스타일, 데이터 텍스트) 분리"""
    styles = {}
    data_lines = []
    in_desc = False
    in_data = False

    for line in text.split('\n'):
        stripped = line.strip()
        # --- 설명 블록 토글
        if stripped == '---':
            in_desc = not in_desc
            continue
        if in_desc:
            continue
        if not stripped:
            continue
        # #data 이후는 모두 데이터
        if in_data:
            data_lines.append(stripped)
            continue
        if stripped.lower() == '#data':
            in_data = True
            continue
        if stripped.startswith('#'):
            parts = re.split(r'[\t ]+', stripped, maxsplit=1)
            key = parts[0][1:].lower()
            if len(parts) > 1:
                styles[key] = parts[1]
            continue
        data_lines.append(stripped)

    return styles, '\n'.join(data_lines)


def parse_data(data_text):
    """데이터 텍스트 -> (x_label, series_names, x_values, y_dict)"""
    lines = [l.strip() for l in data_text.strip().split('\n') if l.strip()]

    header = re.split(r'[\t ]+', lines[0])
    x_label = header[0]
    series_names = header[1:]

    x_values = []
    y_dict = {name: [] for name in series_names}

    for line in lines[1:]:
        parts = re.split(r'[\t ]+', line)
        x_values.append(float(parts[0]))
        for i, name in enumerate(series_names):
            y_dict[name].append(float(parts[i + 1]))

    return x_label, series_names, x_values, y_dict


def resolve_styles(styles, n_series):
    """스타일 딕셔너리 -> 시리즈별 (color, marker, linewidth, markersize) 리스트"""
    def parse_nums(raw, as_float=False):
        vals = re.split(r'[\t ]+', raw.strip())
        return [float(v) for v in vals] if as_float else [int(v) for v in vals]

    def extend(vals, default, n):
        """vals를 n개로 확장 (부족하면 default 순환)"""
        result = []
        for i in range(n):
            if i < len(vals):
                result.append(vals[i])
            else:
                result.append(default[i % len(default)])
        return result

    # 색상
    if 'color' in styles:
        c_nums = extend(parse_nums(styles['color']), DEFAULTS['color'], n_series)
    else:
        c_nums = extend([], DEFAULTS['color'], n_series)
    colors = [COLOR_MAP.get(n, COLOR_MAP[1]) for n in c_nums]

    # 마커
    if 'marker' in styles:
        m_nums = extend(parse_nums(styles['marker']), DEFAULTS['marker'], n_series)
    else:
        m_nums = extend([], DEFAULTS['marker'], n_series)
    markers = [MARKER_MAP.get(n, MARKER_MAP[1]) for n in m_nums]
    marker_filled = [n <= 10 for n in m_nums]  # 1~10: 꽉찬, 11~20: 빈

    # 선 종류
    if 'linestyle' in styles:
        ls_nums = extend(parse_nums(styles['linestyle']), DEFAULTS['linestyle'], n_series)
    else:
        ls_nums = extend([], DEFAULTS['linestyle'], n_series)
    linestyles = [LINESTYLE_MAP.get(n, LINESTYLE_MAP[1]) for n in ls_nums]

    # 선 굵기
    if 'linewidth' in styles:
        lw = extend(parse_nums(styles['linewidth'], as_float=True), DEFAULTS['linewidth'], n_series)
    else:
        lw = extend([], DEFAULTS['linewidth'], n_series)

    # 심볼 크기
    if 'markersize' in styles:
        ms = extend(parse_nums(styles['markersize'], as_float=True), DEFAULTS['markersize'], n_series)
    else:
        ms = extend([], DEFAULTS['markersize'], n_series)

    return colors, markers, marker_filled, linestyles, lw, ms


def nice_step(data_range, target_ticks=8):
    """데이터 범위에서 깔끔한 tick 간격 계산"""
    raw = data_range / target_ticks
    mag = 10 ** math.floor(math.log10(raw))
    residual = raw / mag
    if residual <= 1:
        nice = 1
    elif residual <= 2:
        nice = 2
    elif residual <= 5:
        nice = 5
    else:
        nice = 10
    return nice * mag


def plot_fer(x_label, series_names, x_values, y_dict,
             colors, markers, marker_filled, linestyles, linewidths, markersizes,
             comments=None, output_file=None):
    """FER 곡선 플롯"""
    fig, ax = plt.subplots(figsize=FIGSIZE)

    for i, name in enumerate(series_names):
        fillstyle = 'full' if marker_filled[i] else 'none'
        ax.plot(x_values, y_dict[name],
                color=colors[i], marker=markers[i], fillstyle=fillstyle,
                linestyle=linestyles[i],
                markersize=markersizes[i], linewidth=linewidths[i],
                label=name)

    # Y축
    ax.set_yscale('log')
    all_y = [v for ys in y_dict.values() for v in ys if v > 0]
    y_bottom = 10 ** math.floor(math.log10(min(all_y)))
    ax.set_ylim(bottom=y_bottom, top=Y_TOP)

    # X축
    x_min, x_max = min(x_values), max(x_values)
    step = nice_step(x_max - x_min)
    tick_start = math.floor(x_min / step) * step
    tick_end = math.ceil(x_max / step) * step
    ticks = []
    t = tick_start
    while t <= tick_end + step * 0.01:
        ticks.append(round(t, 10))
        t += step
    ax.set_xticks(ticks)
    ax.set_xlim(ticks[0], ticks[-1])
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useOffset=False))

    ax.set_xlabel(x_label, fontsize=FONT_AXIS_LABEL)
    ax.set_ylabel(Y_LABEL, fontsize=FONT_AXIS_LABEL)
    ax.set_title(TITLE_FORMAT.format(x_label=x_label), fontsize=FONT_TITLE)
    ax.legend(fontsize=FONT_LEGEND)
    ax.tick_params(axis='both', labelsize=FONT_TICK)
    ax.grid(True, which='both', ls=GRID_STYLE, alpha=GRID_ALPHA)

    # 하단 캡션
    if comments:
        fig.subplots_adjust(bottom=0.18)
        fig.text(0.5, 0.05, comments, ha='center', va='center', fontsize=FONT_CAPTION,
                 fontstyle='italic',
                 bbox=dict(boxstyle='round,pad=0.4', facecolor=CAPTION_BGCOLOR,
                           edgecolor=CAPTION_EDGECOLOR))
    else:
        fig.tight_layout()

    if output_file:
        fig.savefig(output_file, dpi=DPI)
        print(f"저장: {output_file}")
    else:
        plt.show()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fer_plot.py <data_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    styles, data_text = parse_file(text)
    x_label, names, x_vals, y_dict = parse_data(data_text)
    colors, markers, mf, ls, lw, ms = resolve_styles(styles, len(names))
    comments = styles.get('comments', '').replace('|', '\n').strip() or None

    # 출력 파일명: 입력파일과 같은 폴더에 fig_YYMMDD_HH_mm_ss.png
    ts = datetime.now().strftime('%y%m%d_%H_%M_%S')
    out_dir = os.path.dirname(os.path.abspath(input_file))
    out = os.path.join(out_dir, f'fig_{ts}.png')

    print(f"X축: {x_label}, 시리즈: {names}, 데이터: {len(x_vals)}행")
    plot_fer(x_label, names, x_vals, y_dict,
             colors, markers, mf, ls, lw, ms, comments, out)
