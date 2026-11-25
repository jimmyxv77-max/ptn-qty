import math
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="卷径与涂布极片最大片数计算器",
    page_icon=None,
    layout="centered",
)

# 预设固定最大卷半径 (mm) —— 区分厂区与正负极（参考表格 Plant 3 / Plant 4 数值）
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
st.caption("不计卷筒直径，仅按分切卷自身最大半径与极片厚度估算最大卷长及可容涂布片数")

with st.sidebar:
    st.header("固定参数设置")
    allow_custom_r = st.checkbox("允许临时微调固定最大卷半径", value=False)
    st.markdown("**当前内置固定最大卷半径 (mm)**")
    preset_df = pd.DataFrame(
        [
            {"厂区": plant, "极性": pol, "最大卷半径 (mm)": r_val}
            for plant, pol_map in DEFAULT_MAX_RADIUS_MM.items()
            for pol, r_val in pol_map.items()
        ]
    )
    st.dataframe(preset_df, use_container_width=True, hide_index=True)

col_a, col_b = st.columns(2)
with col_a:
    plant_choice = st.selectbox("选择厂区", list(DEFAULT_MAX_RADIUS_MM.keys()))
with col_b:
    polarity_choice = st.selectbox("选择极性", ["正极 (Cathode)", "负极 (Anode)"])

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
    st.info(f"当前固定极限最大卷半径：**{max_radius_mm:.1f} mm**（{plant_choice} · {polarity_choice}）")

st.divider()
st.subheader("输入工艺参数")

c1, c2 = st.columns(2)
with c1:
    calender_thickness_um = st.number_input(
        "辊压厚度 (μm)",
        min_value=0.1,
        max_value=2000.0,
        value=95.0,
        step=0.5,
        help="请输入分切/辊压后的极片厚度，单位 μm",
    )
with c2:
    coated_piece_length_m = st.number_input(
        "涂布单片极片长度 (m)",
        min_value=0.001,
        max_value=10000.0,
        value=0.856,
        step=0.001,
        format="%.3f",
        help="请输入单张/单片涂布极片长度，单位 m",
    )

ref_piece_qty = st.number_input(
    "参考/计划片数（可选，用于对比是否超限）",
    min_value=0,
    max_value=1000000,
    value=1000,
    step=10,
)

# 核心计算
max_roll_length_m = (math.pi * (max_radius_mm ** 2)) / calender_thickness_um
max_piece_count = int(math.floor(max_roll_length_m / coated_piece_length_m))
actual_max_used_length_m = max_piece_count * coated_piece_length_m
remaining_length_m = max_roll_length_m - actual_max_used_length_m

ref_total_length_m = ref_piece_qty * coated_piece_length_m
diff_vs_ref_m = max_roll_length_m - ref_total_length_m

st.divider()
st.subheader("计算结果")

m1, m2, m3 = st.columns(3)
m1.metric("卷最大长度 (m)", f"{max_roll_length_m:.2f} m")
m2.metric("涂布极片最大片数 (片)", f"{max_piece_count:,} 片")
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