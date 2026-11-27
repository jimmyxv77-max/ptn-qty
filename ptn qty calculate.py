import math
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Roll Thickness & Max Coated Pieces Calculator",
    page_icon=None,
    layout="centered",
)

# Default recommended max net single-side roll thickness R (mm) by plant & polarity
INITIAL_REC_RADIUS_MM = {
    "Plant 3": {
        "Cathode": 172.0,
        "Anode": 175.0,
    },
    "Plant 4": {
        "Cathode": 160.0,
        "Anode": 180.0,
    },
}

I18N = {
    "en": {
        "lang_label": "Language / 语言",
        "title": "Recommended Roll Thickness & Max Coated Pieces Calculator",
        "caption": "R = net single-side roll thickness (excluding core); L_max = (π·D·R + π·R²) / U with adjustable recommended max R",
        "sb_header": "Recommended & Fixed Parameters",
        "reel_d": "Core Diameter D (mm)",
        "reel_d_help": "Reel / core diameter D (default 95 mm)",
        "pi_mode": "Pi (π) Value",
        "pi_exact": "Exact math.pi (3.14159...)",
        "pi_314": "Excel fixed 3.14",
        "rec_tbl": "**Recommended Max Net Roll Thickness R (mm, editable)**",
        "reset_rec": "Reset Recommended Values to Default",
        "plant_lbl": "Select Plant",
        "pol_lbl": "Select Polarity",
        "pol_opts": ["Cathode", "Anode"],
        "cur_r_lbl": "Recommended Max Net Single-Side Thickness R (mm)",
        "rec_r_info": (
            "Recommended max net single-side thickness R: **{r:.1f} mm** ({plant} · {pol}) | "
            "Core diameter D: **{d:.1f} mm** (Total OD: {od:.1f} mm)"
        ),
        "input_sec": "Process Inputs",
        "thick_lbl": "Calendered Thickness U (μm)",
        "thick_help": "Calendered electrode thickness U (μm)",
        "piece_len_lbl": "Single Coated Piece Length (m)",
        "piece_len_help": "Length of one coated piece (m)",
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
        "title": "推荐净卷厚与涂布极片最大片数计算器",
        "caption": "R 为单边净卷厚（不含卷芯直径 D）；按 L_max = (π·D·R + π·R²) / U 与可调推荐最大卷厚计算最大片数",
        "sb_header": "推荐与固定参数设置",
        "reel_d": "卷芯直径 D (mm)",
        "reel_d_help": "卷芯直径 D（默认 95 mm）",
        "pi_mode": "圆周率 π 取值",
        "pi_exact": "精确圆周率 math.pi (3.14159...)",
        "pi_314": "Excel 固定值 (3.14)",
        "rec_tbl": "**各厂区/极性默认推荐最大净卷厚 R (mm，支持直接修改)**",
        "reset_rec": "恢复默认推荐值",
        "plant_lbl": "选择厂区",
        "pol_lbl": "选择极性",
        "pol_opts": ["正极", "负极"],
        "cur_r_lbl": "推荐最大单边净卷厚 R (mm)",
        "rec_r_info": (
            "当前推荐最大单边净卷厚 R：**{r:.1f} mm**（{plant} · {pol}）｜"
            "卷芯直径 D：**{d:.1f} mm**（总外径 {od:.1f} mm）"
        ),
        "input_sec": "输入工艺参数",
        "thick_lbl": "辊压厚度 U (μm)",
        "thick_help": "辊压后极片厚度 U（μm）",
        "piece_len_lbl": "涂布单片极片长度 (m)",
        "piece_len_help": "单张/单片涂布极片长度（m）",
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

if "rec_radius_map" not in st.session_state:
    st.session_state.rec_radius_map = {
        p: dict(pol_d) for p, pol_d in INITIAL_REC_RADIUS_MM.items()
    }


def _on_sb_change(p_name: str, pol_name: str, w_key: str):
    st.session_state.rec_radius_map[p_name][pol_name] = float(st.session_state[w_key])


def _on_main_change(p_name: str, pol_name: str, w_key: str):
    st.session_state.rec_radius_map[p_name][pol_name] = float(st.session_state[w_key])


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

    st.markdown(t["rec_tbl"])
    for p_name in ["Plant 3", "Plant 4"]:
        for pol_name in ["Cathode", "Anode"]:
            w_key = f"sb_rec_{p_name}_{pol_name}"
            st.number_input(
                f"{p_name} · {pol_name}",
                min_value=1.0,
                max_value=2000.0,
                value=float(st.session_state.rec_radius_map[p_name][pol_name]),
                step=0.5,
                key=w_key,
                on_change=_on_sb_change,
                args=(p_name, pol_name, w_key),
            )

    if st.button(t["reset_rec"], use_container_width=True):
        st.session_state.rec_radius_map = {
            p: dict(pol_d) for p, pol_d in INITIAL_REC_RADIUS_MM.items()
        }
        for p_name in ["Plant 3", "Plant 4"]:
            for pol_name in ["Cathode", "Anode"]:
                k_sb = f"sb_rec_{p_name}_{pol_name}"
                k_mn = f"main_rec_{p_name}_{pol_name}"
                if k_sb in st.session_state:
                    del st.session_state[k_sb]
                if k_mn in st.session_state:
                    del st.session_state[k_mn]
        st.rerun()

st.title(t["title"])
st.caption(t["caption"])

plant_keys = list(st.session_state.rec_radius_map.keys())
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
main_key = f"main_rec_{plant_choice}_{pol_key}"
current_rec_val = float(st.session_state.rec_radius_map[plant_choice][pol_key])

max_radius_mm = float(
    st.number_input(
        t["cur_r_lbl"],
        min_value=1.0,
        max_value=2000.0,
        value=current_rec_val,
        step=0.5,
        key=main_key,
        on_change=_on_main_change,
        args=(plant_choice, pol_key, main_key),
    )
)

st.info(
    t["rec_r_info"].format(
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

# L_max = (pi * D * R + pi * R^2) / U (R in mm, D in mm, U in um -> L_max in m)
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