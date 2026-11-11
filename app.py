import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. 网页基础设置（必须放在第一句）
st.set_page_config(page_title="BOM差异分析看板", layout="wide", page_icon="📊")

# ==========================================
# 🔒 隐藏菜单与底部信息（只读模式设置）
# ==========================================
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}  /* 隐藏右上角三个点 */
        footer {visibility: hidden;}     /* 隐藏底部的 Streamlit 标识 */
        header {visibility: hidden;}     /* 隐藏顶部黑条 */
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# 清除上传缓存的警告
st.session_state.update(st.session_state)

# 2. 侧边栏：数据源与导航
with st.sidebar:
    st.header("📁 数据源管理")
    uploaded_file = st.file_uploader("上传领料明细 Excel", type=["xlsx", "csv"])
    
    st.info("""
    **Excel 格式要求：**
    需包含列：`班组`、`日期`、`BOM标准用量`、`实际领用量`
    """)
    
    st.divider()
    
    # 页面切换
    st.write("**导航菜单：**")
    page = st.radio(
        "选择模块：",
        ["📈 BOM差异分析", "🏠 成本中心", "📦 物料管控", "🔔 预警日志"],
        label_visibility="collapsed"
    )

# 3. 顶部标题区
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📊 物料领用量 vs BOM标准用量")
    st.caption("💡 数据支持 Excel 动态导入，自动计算班组差异")
with col2:
    if st.button("🚨 班组差异预警", type="primary", use_container_width=True):
        st.toast("预警已触发！已将超耗数据发送给车间主任", icon="⚠️")

st.divider()

# 4. 数据加载（如果没有上传文件，自动使用模拟数据）
@st.cache_data
def load_data(file):
    if file is not None:
        return pd.read_excel(file)
    else:
        # 模拟数据
        data = {
            "班组": ["甲班", "乙班", "丙班", "丁班"] * 3,
            "日期": ["2022-10-01", "2022-10-02", "2022-10-03", "2022-10-05",
                   "2022-10-07", "2022-10-08", "2022-10-09", "2022-10-10",
                   "2022-10-11", "2022-10-12", "2022-10-13", "2022-10-14"],
            "物料编码": ["M-1001"] * 12,
            "BOM标准用量": [500, 450, 700, 400, 500, 450, 700, 400, 500, 450, 700, 400],
            "实际领用量": [550, 420, 850, 390, 580, 460, 810, 380, 510, 440, 780, 410]
        }
        return pd.DataFrame(data)

df = load_data(uploaded_file)

# 统一计算差异列
df["差异数量"] = df["实际领用量"] - df["BOM标准用量"]
df["差异金额"] = df["差异数量"] * 5.0 # 假设单价5元

# 按班组汇总，用于画图
group_df = df.groupby("班组").agg({
    "BOM标准用量": "sum",
    "实际领用量": "sum"
}).reset_index()

# 5. 页面内容渲染区（根据左侧的选择，显示不同内容）
if page == "📈 BOM差异分析":
    # --- 画图逻辑 ---
    st.subheader("📈 班组物料损耗对比")
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=group_df['班组'], y=group_df['BOM标准用量'],
        name='标准用量', marker_color='#1f77b4'
    ))
    fig.add_trace(go.Bar(
        x=group_df['班组'], y=group_df['实际领用量'],
        name='实际领用', marker_color='#d62728'
    ))
    
    fig.update_layout(
        barmode='group',
        plot_bgcolor='rgba(255,255,255,1)',
        paper_bgcolor='rgba(255,255,255,1)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20),
        height=400
    )
    
    # 添加红色箭头标注
    fig.add_annotation(
        x="丙班", y=850, text="⚠️ 严重超耗",
        showarrow=True, arrowhead=2, arrowcolor="red", ax=40, ay=-40
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # --- 表格逻辑 ---
    st.subheader("📋 班组差异明细表")
    def highlight_diff(row):
        styles = [''] * len(row)
        if row["差异数量"] > 50:
            styles[3] = 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'
            styles[4] = 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'
        return styles
    
    st.dataframe(df.style.apply(highlight_diff, axis=1), use_container_width=True, height=350)
    
    # --- 底部按钮 ---
    st.divider()
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("⬇️ 导出差异报告", data=csv, file_name='BOM差异报告.csv', mime='text/csv', use_container_width=True, type="primary")
    with col_btn2:
        if st.button("✉️ 生成班组追踪单", use_container_width=True):
            st.success("已生成各班组追踪单 PDF，可发送至企业微信！")

elif page == "🏠 成本中心":
    st.subheader("🏠 成本中心概览")
    st.info("这里展示全厂总成本、材料费、人工费的大盘数据。")
    st.metric(label="本月总领料成本 (预估)", value="¥1,250,000", delta="-2.5%")

elif page == "📦 物料管控":
    st.subheader("📦 物料管控明细数据")
    st.write("这里展示最原始的底层数据。")
    st.dataframe(df, use_container_width=True)

elif page == "🔔 预警日志":
    st.subheader("🔔 异常预警日志")
    st.warning("⚠️ 丙班 2022-10-02 物料 M-1001 超耗严重，已发送拦截通知。")
    st.success("✅ 甲班 2022-10-01 损耗率正常。")