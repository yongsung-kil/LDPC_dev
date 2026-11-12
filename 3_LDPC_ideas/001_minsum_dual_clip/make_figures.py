"""001 보고서의 그림을 만들어 figures/ 아래 svg로 저장한다.

실행 (이 폴더에서):
    python make_figures.py
`python render.py`(3_LDPC_ideas/)가 html을 만들기 전에 이 파일을 먼저 실행한다.

그림과 재료:
    - fig1_idea.svg            개념 그림. 숫자는 설명용 예시 (메시지 5개, edge 상한 7, P=2, Q=4)
    - fig2_environment.svg     README "결과 2" 표의 FER을 그대로 읽어 그린다
    - fig3_system.svg          구성 그림. 디코더 반복 구조 안에서 바뀐 자리
    - fig4_fer_by_clip.svg     README "결과 1" 표의 FER을 그대로 읽어 그린다
    - fig5_dv4_errors.svg      아래 DV4_ERRORS_PER_FRAME (iteration별 로그에서 옮긴 값)
"""
import sys
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EXPERIMENT_DIR.parent))

import figure_svg as fig   # noqa: E402  (3_LDPC_ideas/figure_svg.py)

README_PATH = EXPERIMENT_DIR / "README.md"
FIGURES_DIR = EXPERIMENT_DIR / "figures"

# dv=4 열의 비트 오류 수, 64프레임 평균 (수렴해 빠진 프레임은 0으로 셈), iteration 1부터 20까지.
# 출처: Sim_Output의 dualclip_p7q7, dualclip_p2q3 실행 (E=200)의 log_iter_fixed_error_p200.csv에서
# bit_err_dv4_mean × active_frames / 64
DV4_ERRORS_PER_FRAME = {
    "no_clip_7_7": [187.656, 47.828, 9.969, 2.578, 1.047, 0.875, 0.844, 0.844, 0.844, 0.844,
                    0.828, 0.828, 0.828, 0.828, 0.828, 0.828, 0.828, 0.828, 0.828, 0.828],
    "clip_2_3": [176.172, 138.344, 88.344, 80.234, 79.375, 79.281, 79.203, 79.203, 79.203, 79.203,
                 79.203, 79.203, 79.203, 79.203, 79.203, 79.203, 79.203, 79.203, 79.203, 79.203],
}


def draw_idea():
    """그림 1. 검사 노드가 돌려주는 두 값(min1, min2)에 서로 다른 상한 P, Q를 두는 것."""
    width, height = 760, 292
    baseline_y, unit = 232, 22           # 메시지 크기 1이 22px

    def bar_top(value):
        return baseline_y - value * unit

    parts = []

    # 왼쪽: 검사식에 들어온 메시지 크기
    incoming = [7, 4, 6, 7, 5]
    min1_value, min2_value = sorted(incoming)[:2]
    parts.append(fig.text(24, 30, "검사식에 들어온 메시지 크기", "head"))
    parts.append(fig.text(24, 49, "예시: 메시지 5개, 크기 상한 7", "muted small"))
    bar_width, bar_gap, first_x = 26, 14, 34
    for index, value in enumerate(incoming):
        x = first_x + index * (bar_width + bar_gap)
        center = x + bar_width / 2
        is_min = value in (min1_value, min2_value)
        parts.append(fig.column_bar(x, baseline_y, bar_width, value * unit,
                                    "mark-strong" if is_min else "mark-faint"))
        parts.append(fig.text(center, bar_top(value) - 7, str(value), "small", anchor="middle"))
        if value == min1_value:
            parts.append(fig.text(center, baseline_y + 19, "min1", "strong", anchor="middle"))
            parts.append(fig.text(center, baseline_y + 37, "가장 작은 값", "muted small", anchor="middle"))
        if value == min2_value:
            parts.append(fig.text(center, baseline_y + 19, "min2", "strong", anchor="middle"))
            parts.append(fig.text(center, baseline_y + 37, "둘째로 작은 값", "muted small", anchor="middle"))
    parts.append(fig.segment(24, baseline_y, 232, baseline_y, "grid"))

    # 가운데 화살표
    parts.append(fig.text_lines(278, 132, ["가장 작은", "두 값만 돌려줌"], "muted small", anchor="middle", line_height=16))
    parts.append(fig.arrow([(250, 162), (306, 162)]))

    # 가운데: 기존 min-sum
    parts.append(fig.text(330, 30, "기존 min-sum", "head"))
    parts.append(fig.text(330, 49, "두 값을 그대로 돌려줌", "muted small"))
    for x, name, value in ((352, "min1", min1_value), (424, "min2", min2_value)):
        center = x + 20
        parts.append(fig.column_bar(x, baseline_y, 40, value * unit, "mark-strong"))
        parts.append(fig.text(center, bar_top(value) - 7, str(value), "small", anchor="middle"))
        parts.append(fig.text(center, baseline_y + 19, name, "strong", anchor="middle"))
        parts.append(fig.text(center, baseline_y + 37, "{} 그대로".format(value), "muted small", anchor="middle"))
    parts.append(fig.segment(330, baseline_y, 486, baseline_y, "grid"))

    parts.append(fig.segment(512, 20, 512, 272, "grid"))

    # 오른쪽: 논문의 이중 상한
    clip_p, clip_q = 2, 4
    parts.append(fig.text(538, 30, "논문: 이중 상한 클리핑", "head"))
    parts.append(fig.text(538, 49, "min1은 P, min2는 Q에서 잘라 돌려줌", "muted small"))
    for x, name, value, limit, limit_name in ((562, "min1", min1_value, clip_p, "P"),
                                              (664, "min2", min2_value, clip_q, "Q")):
        center = x + 20
        kept = min(value, limit)
        parts.append(fig.rectangle(x + 0.5, bar_top(value), 39, (value - kept) * unit, "cut", corner=4))
        parts.append(fig.column_bar(x, baseline_y, 40, kept * unit, "mark-strong", corner=0))
        parts.append(fig.text(center, bar_top(value) - 7, str(value), "muted small", anchor="middle"))
        if (value - kept) * unit >= 20:
            parts.append(fig.text(center, bar_top(value) + (value - kept) * unit / 2 + 4, "잘림",
                                  "muted small", anchor="middle"))
        parts.append(fig.segment(x - 8, bar_top(limit), x + 48, bar_top(limit), "line-change"))
        parts.append(fig.text(x + 53, bar_top(limit) + 4.5, "{} = {}".format(limit_name, limit), "strong"))
        parts.append(fig.text(center, baseline_y + 19, name, "strong", anchor="middle"))
        parts.append(fig.text(center, baseline_y + 37, "{} → {}".format(value, kept), "muted small", anchor="middle"))
    parts.append(fig.segment(538, baseline_y, 736, baseline_y, "grid"))

    label = ("검사식에 들어온 메시지 다섯 개 가운데 가장 작은 값 min1과 둘째로 작은 값 min2만 돌려준다. "
             "기존 min-sum은 두 값을 그대로 돌려주고, 논문은 min1을 상한 P에서, min2를 상한 Q에서 잘라 돌려준다.")
    return fig.figure_document(width, height, label, parts)


def draw_environment_contrast():
    """그림 2. 같은 클리핑이 환경에 따라 FER을 개선하기도 악화시키기도 하는 것 (결과 2 표)."""
    header, rows = fig.read_md_table(README_PATH, "결과 2.")
    clip_names = header[1:]
    series = []
    for row in rows:
        values = [fig.first_number(cell) for cell in row[1:]]
        improved = values[-1] < values[0]
        series.append({
            "name": row[0] + " 환경",
            "values": values,
            "tone": fig.TONE_BETTER if improved else fig.TONE_WORSE,
            "end_label": [
                "FER {} → {}".format(fig.format_short(values[0]), fig.format_short(values[-1])),
                "클리핑할수록 개선" if improved else "클리핑할수록 악화",
            ],
        })
    return fig.line_chart(
        series, list(range(len(clip_names))),
        label="클리핑을 강하게 할수록 상한 여유 환경의 FER은 1.0에서 0으로 내려가고, "
              "비율 복원 환경의 FER은 0에서 1.0으로 올라간다.",
        y_max=1.0, y_ticks=(0, 0.5, 1.0),
        y_axis_title="FER (프레임 오류율, 낮을수록 좋음)",
        x_axis_title="클리핑 세기 (오른쪽일수록 상한 P, Q가 낮음)",
        x_tick_labels=clip_names, mark_every_point=True, height=290, end_label_width=190,
    )


def draw_system():
    """그림 3. 디코더 반복 구조 안에서 바뀐 자리."""
    width, height = 760, 262
    top_y, bottom_y, box_height = 34, 162, 58
    parts = [
        fig.box(20, top_y, 124, box_height, ["채널 LLR", "크기 ch"]),
        fig.box(204, top_y, 168, box_height, ["변수 노드", "합산과 비트 판정"]),
        fig.box(540, top_y, 200, box_height, ["검사 노드", "min1, min2 찾기"]),
        fig.box(540, bottom_y, 200, box_height, ["이중 상한 클리핑", "min1 ≤ P, min2 ≤ Q"], "box-change"),
        fig.box(292, bottom_y, 180, box_height, ["메시지 재구성", "부호를 붙여 돌려줌"]),
        fig.box(20, bottom_y, 124, box_height, ["복호 결과", "판정 비트"]),
        fig.arrow([(144, top_y + 29), (204, top_y + 29)]),
        fig.arrow([(372, top_y + 29), (540, top_y + 29)]),
        fig.text(456, top_y + 19, "보내는 메시지 (V2C)", "muted small", anchor="middle"),
        fig.arrow([(640, top_y + box_height), (640, bottom_y)]),
        fig.arrow([(540, bottom_y + 29), (472, bottom_y + 29)]),
        fig.arrow([(340, bottom_y), (340, top_y + box_height)]),
        fig.text(350, 131, "돌려주는 메시지 (C2V)", "muted small"),
        fig.arrow([(236, top_y + box_height), (236, bottom_y + 29), (144, bottom_y + 29)]),
        fig.text(566, 131, "최대 20회 반복", "muted small", anchor="middle"),
        fig.rectangle(586, bottom_y + box_height + 13, 10, 10, "mark-change", corner=2),
        fig.text(602, bottom_y + box_height + 22, "논문이 바꾼 곳", "small"),
    ]
    label = ("채널 LLR이 변수 노드로 들어가고, 변수 노드와 검사 노드가 메시지를 주고받으며 최대 20회 반복한다. "
             "논문이 바꾼 곳은 검사 노드가 찾은 min1, min2를 메시지로 재구성하기 직전의 이중 상한 클리핑 한 곳이다.")
    return fig.figure_document(width, height, label, parts)


def draw_fer_by_clip():
    """그림 4. LLR_MATRIX_HD_1 환경에서 (P,Q)별 FER (결과 1 표)."""
    header, rows = fig.read_md_table(README_PATH, "결과 1.")
    fer_column = header.index("FER")
    bars = [(row[0], fig.first_number(row[fer_column])) for row in rows]
    return fig.horizontal_bar_chart(
        bars,
        label="LLR_MATRIX_HD_1 환경에서 클리핑을 건 모든 (P,Q)의 FER이 기준선 0.484보다 높다.",
        value_axis_title="FER (프레임 오류율, 낮을수록 좋음)",
        baseline_index=0, baseline_name="기준선",
        tone_names={
            fig.TONE_NEUTRAL: "기준선과 같음 (클리핑 없음)",
            fig.TONE_BETTER: "기준선보다 개선",
            fig.TONE_WORSE: "기준선보다 악화",
        },
    )


def draw_dv4_errors():
    """그림 5. dv=4 열의 비트 오류가 iteration을 따라 줄어드는 모습."""
    iterations = list(range(1, 21))
    no_clip = DV4_ERRORS_PER_FRAME["no_clip_7_7"]
    clipped = DV4_ERRORS_PER_FRAME["clip_2_3"]
    series = [
        {"name": "(2,3) 클리핑", "values": clipped, "tone": fig.TONE_WORSE,
         "end_label": ["{:.1f}개에서 멈춤".format(clipped[-1]), "더 줄지 않음 (전 프레임 실패)"]},
        {"name": "클리핑 없음 (7,7)", "values": no_clip, "tone": fig.TONE_NEUTRAL,
         "end_label": ["{:.1f}개까지 줄어듦".format(no_clip[-1])]},
    ]
    return fig.line_chart(
        series, iterations,
        label="클리핑 없음은 dv=4 열의 오류가 iteration 5까지 1개 안팎으로 줄지만, "
              "(2,3) 클리핑은 iteration 5부터 약 79개에서 더 줄지 않는다.",
        y_max=200, y_ticks=(0, 50, 100, 150, 200),
        y_axis_title="dv=4 열의 비트 오류 수 (프레임당 평균)",
        x_axis_title="iteration (복호 반복 횟수)",
        x_tick_values=(1, 5, 10, 15, 20), x_tick_labels=("1", "5", "10", "15", "20"),
        value_format=lambda value: "{:.1f}개".format(value),
        y_tick_format=lambda value: "{:d}".format(int(value)),
        height=290, end_label_width=210,
    )


FIGURES = {
    "fig1_idea.svg": draw_idea,
    "fig2_environment.svg": draw_environment_contrast,
    "fig3_system.svg": draw_system,
    "fig4_fer_by_clip.svg": draw_fer_by_clip,
    "fig5_dv4_errors.svg": draw_dv4_errors,
}

if __name__ == "__main__":
    for file_name, draw in FIGURES.items():
        fig.write_figure(FIGURES_DIR / file_name, draw())
