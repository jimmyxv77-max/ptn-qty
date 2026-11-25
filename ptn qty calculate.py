import math
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="卷径与涂布极片最大片数计算器",
    page_icon=None,
    layout="centered",
)

# 预设固定最大卷半径 R (mm)（分切卷本身净半径，不含卷芯，对应表格 Plant 3 / Plant 4 MAX）
DEFAULT_MAX_RADIUS_MM = {
    "Plant 3（三厂）": {
        "正极 (Cathode)": 172.0,
        "负极 (Anode)": 175.0,
    },
    "Plant 4（四厂）": {
        "正极 (Cathode)": 160.0,
        "负极 (Anode)": 191.0,
    },
}

st.title("卷径与涂布极片最大片数计算器")
st.caption("对齐 Excel 圆环公式：L_max = (π·D·R + π·R²) / U，结合厂区与正负极固定卷半径上限计算最大涂布片数")

with st.sidebar:
    st.header("固定参数设置")
    reel_diameter_mm = st.number_input(
        "卷芯直径 D / reel diameter (mm)",
        min_value=0.0,
        max_value=500.0,
        value=95.0,
        step=1.0,
        help="对应 Excel 中的 C 列 reel diameter（默认 95 mm）",
    )
    pi_mode = st.radio(
        "π 取值方式",
        ["精确圆周率 math.pi (3.14159...)", "Excel 固定值 (3.14)"],
        index=1,
    )
    pi_val = math.pi if "math.pi" in pi_mode else 3.14

    allow_custom_r = st.checkbox("允许临时微调固定最大卷半径 R", value=False)
    st.markdown("**内置固定最大卷半径 R (mm)**")
    preset_df = pd.DataFrame(
        [
            {"厂区": plant, "极性": pol, "最大卷半径 R (mm)": r_val}
            for plant, pol_map in DEFAULT_MAX_RADIUS_MM.items()
            for pol, r_val in pol_map.items()
        ]
    )
    st.dataframe(preset_df, use_container_width=True, hide_index=True)

col_a, col_b = st.columns(2)
with col_a:
    plant_choice = st.selectbox("选择厂区", list(DEFAULT_MAX_RADIUS_MM.keys()), index=1)
with col_b:
    polarity_choice = st.selectbox("选择极性", ["正极 (Cathode)", "负极 (Anode)"], index=1)

fixed_max_r = float(DEFAULT_MAX_RADIUS_MM[plant_choice][polarity_choice])
if allow_custom_r:
    max_radius_mm = st.number_input(
        "极限最大卷半径 R (mm)",
        min_value=1.0,
        max_value=2000.0,
        value=fixed_max_r,
        step=0.5,
    )
else:
    max_radius_mm = fixed_max_r
    st.info(
        f"当前固定极限最大卷半径 R：**{max_radius_mm:.1f} mm**（{plant_choice} · {polarity_choice}）｜"
        f"卷芯直径 D：**{reel_diameter_mm:.1f} mm**（总外径 {reel_diameter_mm + 2 * max_radius_mm:.1f} mm）"
    )

st.divider()
st.subheader("输入工艺参数")

default_t = 112.0 if "负极" in polarity_choice else 95.0
default_l = 0.963 if "负极" in polarity_choice else 0.856

c1, c2 = st.columns(2)
with c1:
    calender_thickness_um = st.number_input(
        "辊压厚度 U (μm)",
        min_value=0.1,
        max_value=2000.0,
        value=default_t,
        step=0.5,
        help="对应 Excel 中的 G 列 thickness (μm)",
    )
with c2:
    coated_piece_length_m = st.number_input(
        "涂布单片极片长度 (m)",
        min_value=0.001,
        max_value=10000.0,
        value=default_l,
        step=0.001,
        format="%.3f",
        help="对应 Excel 中的 I 列 length (m)",
    )

ref_piece_qty = st.number_input(
    "参考/计划片数（可选，用于对比是否超限）",
    min_value=0,
    max_value=1000000,
    value=1600,
    step=10,
)

# 核心计算：严格对应 Excel 公式 =(B*C*D + E*F)/G = (π*D*R + π*R^2)/U
max_roll_length_m = (pi_val * reel_diameter_mm * max_radius_mm + pi_val * (max_radius_mm ** 2)) / calender_thickness_um
exact_piece_float = max_roll_length_m / coated_piece_length_m
max_piece_count = int(math.floor(exact_piece_float))
actual_max_used_length_m = max_piece_count * coated_piece_length_m
remaining_length_m = max_roll_length_m - actual_max_used_length_m

ref_total_length_m = ref_piece_qty * coated_piece_length_m
diff_vs_ref_m = max_roll_length_m - ref_total_length_m

st.divider()
st.subheader("计算结果")

m1, m2, m3 = st.columns(3)
m1.metric("卷最大长度 L_max (m)", f"{max_roll_length_m:.2f} m")
m2.metric("涂布极片最大片数 (片)", f"{max_piece_count:,} 片", f"精确值 {exact_piece_float:.1f} 片")
m3.metric("满片实际占用长度 (m)", f"{actual_max_used_length_m:.2f} m", f"余量 {remaining_length_m:.2f} m")

if ref_piece_qty > 0:
    st.markdown("#### 与参考片数对比")
    if ref_piece_qty <= max_piece_count:
        st.success(
            f"参考片数 **{ref_piece_qty:,} 片**（合计 **{ref_total_length_m:.2f} m**）**未超限**，"
            f"在最大卷长内还可多放 **{max_piece_count - ref_piece_qty:,} 片**（剩余长度 **{diff_vs_ref_m:.2f} m**）。"
        )
    else:
        st.error(
            f"参考片数 **{ref_piece_qty:,} 片**（合计 **{ref_total_length_m:.2f} m**）**已超出空间上限**，"
            f"超出 **{ref_piece_qty - max_piece_count:,} 片**（超长 **{abs(diff_vs_ref_m):.2f} m**），建议按最大 **{max_piece_count:,} 片** 控制。"
        )