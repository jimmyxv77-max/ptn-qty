import math
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Roll Radius & Max Coated Pieces Calculator",
    page_icon=None,
    layout="centered",
)

# Fixed max roll radius R (mm) by plant & polarity (excluding core; aligned with Plant 3 / Plant 4 presets)
DEFAULT_MAX_RADIUS_MM = {
    "Plant 3": {
        "Cathode": 172.0,
        "Anode": 175.0,
    },
    "Plant 4": {
        "Cathode": 160.0,
        "Anode": 191.0,
    },
}

I18N = {
    "en": {
        "lang_label": "Language / 语言",
        "title": "Roll Radius & Max Coated Pieces Calculator",
        "caption": "Excludes core diameter; uses annular formula L_max = (π·D·R + π·R²) / U with fixed plant/polarity max radius R",
        "sb_header": "Fixed Parameters",
        "reel_d": "Reel / Core Diameter D (mm)",
        "reel_d_help": "Corresponds to Excel column C reel diameter (default 95 mm)",
        "pi_mode": "Pi (π) Value",
        "pi_exact": "Exact math.pi (3.14159...)",
        "pi_314": "Excel fixed 3.14",
        "allow_custom_r": "Allow temporary override of fixed max radius R",
        "preset_tbl": "**Preset Fixed Max Roll Radius R (mm)**",
        "col_plant": "Plant",
        "col_pol": "Polarity",
        "col_r": "Max Radius R (mm)",
        "plant_lbl": "Select Plant",
        "pol_lbl": "Select Polarity",
        "pol_opts": ["Cathode", "Anode"],
        "custom_r_lbl": "Max Roll Radius R (mm)",
        "fixed_r_info": (
            "Fixed max roll radius R: **{r:.1f} mm** ({plant} · {pol}) | "
            "Core diameter D: **{d:.1f} mm** (Total OD: {od:.1f} mm)"
        ),
        "input_sec": "Process Inputs",
        "thick_lbl": "Calendered Thickness U (μm)",
        "thick_help": "Corresponds to Excel column G thickness (μm)",
        "piece_len_lbl": "Single Coated Piece Length (m)",
        "piece_len_help": "Corresponds to Excel column I length (m)",
        "ref_qty_lbl": "Reference / Planned Piece Qty (optional check)",
        "result_sec": "Calculation Results",
        "m_len": "Max Roll Length L_max (m)",
        "m_qty": "Max Coated Pieces",
        "m_qty_sub": "Exact {val:.1f} pcs",
        "m_used": "Occupied Length at Max Pcs (m)",
        "m_rem": "Slack {val:.2f} m",
        "cmp_title": "Comparison vs. Reference Qty",
        "cmp_ok": (
            "Reference **{qty:,} pcs** (total **{tot:.2f} m**) is **within limit**: "
            "can add **{extra:,} more pcs** (**{rem:.2f} m** remaining)."
        ),
        "cmp_over": (
            "Reference **{qty:,} pcs** (total **{tot:.2f} m**) **exceeds limit** by "
            "**{over:,} pcs** (**{ex:.2f} m** over). Cap at **{max_q:,} pcs**."
        ),
    },
    "zh": {
        "lang_label": "Language / 语言",
        "title": "卷径与涂布极片最大片数计算器",
        "caption": "不计卷芯直径，按圆环公式 L_max = (π·D·R + π·R²) / U 与厂区/极性固定卷半径上限计算最大片数",
        "sb_header": "固定参数设置",
        "reel_d": "卷芯直径 D (mm)",
        "reel_d_help": "对应 Excel 中 C 列卷芯直径（默认 95 mm）",
        "pi_mode": "圆周率 π 取值",
        "pi_exact": "精确圆周率 math.pi (3.14159...)",
        "pi_314": "Excel 固定值 (3.14)",
        "allow_custom_r": "允许临时微调固定最大卷半径 R",
        "preset_tbl": "**内置固定最大卷半径 R (mm)**",
        "col_plant": "厂区",
        "col_pol": "极性",
        "col_r": "最大卷半径 R (mm)",
        "plant_lbl": "选择厂区",
        "pol_lbl": "选择极性",
        "pol_opts": ["正极", "负极"],
        "custom_r_lbl": "极限最大卷半径 R (mm)",
        "fixed_r_info": (
            "当前固定极限最大卷半径 R：**{r:.1f} mm**（{plant} · {pol}）｜"
            "卷芯直径 D：**{d:.1f} mm**（总外径 {od:.1f} mm）"
        ),
        "input_sec": "输入工艺参数",
        "thick_lbl": "辊压厚度 U (μm)",
        "thick_help": "对应 Excel 中 G 列厚度 (μm)",
        "piece_len_lbl": "涂布单片极片长度 (m)",
        "piece_len_help": "对应 Excel 中 I 列单片长度 (m)",
        "ref_qty_lbl": "参考/计划片数（可选，用于对比是否超限）",
        "result_sec": "计算结果",
        "m_len": "卷最大长度 L_max (m)",
        "m_qty": "涂布极片最大片数 (片)",
        "m_qty_sub": "精确值 {val:.1f} 片",
        "m_used": "满片实际占用长度 (m)",
        "m_rem": "余量 {val:.2f} m",
        "cmp_title": "与参考片数对比",
        "cmp_ok": (
            "参考片数 **{qty:,} 片**（合计 **{tot:.2f} m**）**未超限**，"
            "在最大卷长内还可多放 **{extra:,} 片**（剩余长度 **{rem:.2f} m**）。"
        ),
        "cmp_over": (
            "参考片数 **{qty:,} 片**（合计 **{tot:.2f} m**）**已超出空间上限**，"
            "超出 **{over:,} 片**（超长 **{ex:.2f} m**），建议按最大 **{max_q:,} 片** 控制。"
        ),
    },
}

with st.sidebar:
    lang = st.radio(
        "Language / 语言",
        options=["en", "zh"],
        format_func=lambda x: "English" if x == "en" else "简体中文",
        index=0,
        horizontal=True,
    )
    t = I18N[lang]

    st.divider()
    st.header(t["sb_header"])
    reel_diameter_mm = st.number_input(
        t["reel_d"],
        min_value=0.0,
        max_value=500.0,
        value=95.0,
        step=1.0,
        help=t["reel_d_help"],
    )
    pi_mode = st.radio(
        t["pi_mode"],
        [t["pi_exact"], t["pi_314"]],
        index=1,
    )
    pi_val = math.pi if pi_mode == t["pi_exact"] else 3.14

    allow_custom_r = st.checkbox(t["allow_custom_r"], value=False)
    st.markdown(t["preset_tbl"])
    preset_df = pd.DataFrame(
        [
            {
                t["col_plant"]: plant,
                t["col_pol"]: pol,
                t["col_r"]: r_val,
            }
            for plant, pol_map in DEFAULT_MAX_RADIUS_MM.items()
            for pol, r_val in pol_map.items()
        ]
    )
    st.dataframe(preset_df, use_container_width=True, hide_index=True)

st.title(t["title"])
st.caption(t["caption"])

plant_keys = list(DEFAULT_MAX_RADIUS_MM.keys())
default_plant_idx = plant_keys.index("Plant 4") if "Plant 4" in plant_keys else 0

col_a, col_b = st.columns(2)
with col_a:
    plant_choice = st.selectbox(t["plant_lbl"], plant_keys, index=default_plant_idx)
with col_b:
    pol_idx = st.selectbox(
        t["pol_lbl"],
        options=[0, 1],
        format_func=lambda i: t["pol_opts"][i],
        index=1,
    )

pol_key = "Cathode" if pol_idx == 0 else "Anode"
fixed_max_r = float(DEFAULT_MAX_RADIUS_MM[plant_choice][pol_key])

if allow_custom_r:
    max_radius_mm = st.number_input(
        t["custom_r_lbl"],
        min_value=1.0,
        max_value=2000.0,
        value=fixed_max_r,
        step=0.5,
    )
else:
    max_radius_mm = fixed_max_r
    st.info(
        t["fixed_r_info"].format(
            r=max_radius_mm,
            plant=plant_choice,
            pol=t["pol_opts"][pol_idx],
            d=reel_diameter_mm,
            od=reel_diameter_mm + 2 * max_radius_mm,
        )
    )

st.divider()
st.subheader(t["input_sec"])

default_thick = 112.0 if pol_key == "Anode" else 95.0
default_plen = 0.963 if pol_key == "Anode" else 0.856

c1, c2 = st.columns(2)
with c1:
    calender_thickness_um = st.number_input(
        t["thick_lbl"],
        min_value=0.1,
        max_value=2000.0,
        value=default_thick,
        step=0.5,
        help=t["thick_help"],
    )
with c2:
    coated_piece_length_m = st.number_input(
        t["piece_len_lbl"],
        min_value=0.001,
        max_value=10000.0,
        value=default_plen,
        step=0.001,
        format="%.3f",
        help=t["piece_len_help"],
    )

ref_piece_qty = st.number_input(
    t["ref_qty_lbl"],
    min_value=0,
    max_value=1000000,
    value=1600,
    step=10,
)

# Core calculation: L_max = (pi * D * R + pi * R^2) / U (R in mm, D in mm, U in um -> L_max in m)
max_roll_length_m = (pi_val * reel_diameter_mm * max_radius_mm + pi_val * (max_radius_mm ** 2)) / calender_thickness_um
exact_piece_float = max_roll_length_m / coated_piece_length_m
max_piece_count = int(math.floor(exact_piece_float))
actual_max_used_length_m = max_piece_count * coated_piece_length_m
remaining_length_m = max_roll_length_m - actual_max_used_length_m

ref_total_length_m = ref_piece_qty * coated_piece_length_m
diff_vs_ref_m = max_roll_length_m - ref_total_length_m

st.divider()
st.subheader(t["result_sec"])

m1, m2, m3 = st.columns(3)
m1.metric(t["m_len"], f"{max_roll_length_m:.2f} m")
m2.metric(t["m_qty"], f"{max_piece_count:,}", t["m_qty_sub"].format(val=exact_piece_float))
m3.metric(t["m_used"], f"{actual_max_used_length_m:.2f} m", t["m_rem"].format(val=remaining_length_m))

if ref_piece_qty > 0:
    st.markdown(f"#### {t['cmp_title']}")
    if ref_piece_qty <= max_piece_count:
        st.success(
            t["cmp_ok"].format(
                qty=ref_piece_qty,
                tot=ref_total_length_m,
                extra=max_piece_count - ref_piece_qty,
                rem=diff_vs_ref_m,
            )
        )
    else:
        st.error(
            t["cmp_over"].format(
                qty=ref_piece_qty,
                tot=ref_total_length_m,
                over=ref_piece_qty - max_piece_count,
                ex=abs(diff_vs_ref_m),
                max_q=max_piece_count,
            )
        )