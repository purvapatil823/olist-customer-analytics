import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Olist Dashboard", layout="wide")
st.title("Olist Customer Analytics Dashboard")
st.caption("Brazilian e-commerce marketplace (2016-2018): satisfaction, segmentation, and retention analysis")

orders = pd.read_csv("dashboard_orders.csv")
seg = pd.read_csv("dashboard_seg.csv")
risk = pd.read_csv("dashboard_risk.csv")
preds = pd.read_csv("dashboard_predictions.csv")

name_col = "segment_name" if "segment_name" in risk.columns else risk.columns[0]

tabs = st.tabs(["Executive Summary", "Segments", "Delivery & Risk",
                "Risk Flagging Tool", "Geography"])

with tabs[0]:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Revenue (BRL)", f"{orders['payment_total'].sum():,.0f}")
    k2.metric("Total Orders", f"{len(orders):,}")
    k3.metric("Satisfaction Rate", f"{seg['satisfied'].mean()*100:.1f}%")
    k4.metric("Repeat Buyers", "3.1%")

    left, right = st.columns(2)
    with left:
        st.subheader("Revenue Share by Segment")
        val_col = "revenue_share_pct" if "revenue_share_pct" in risk.columns else risk.columns[-1]
        st.plotly_chart(px.pie(risk, names=name_col, values=val_col, hole=0.4), key="pie1")
    with right:
        st.subheader("Satisfaction by Delivery Outcome")
        d = (seg.dropna(subset=["late_delivery"]).groupby("late_delivery")["satisfied"].mean()*100).reset_index()
        d["Outcome"] = d["late_delivery"].map({0.0: "On time", 1.0: "Late"})
        fig = px.bar(d, x="Outcome", y="satisfied", color="Outcome",
                     color_discrete_map={"On time": "#4c72b0", "Late": "#c44e52"},
                     labels={"satisfied": "Satisfaction %"})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, key="bar_deliv")

    st.subheader("Order Value Distribution")
    max_v = st.slider("Show orders up to (BRL)", 50, 1000, 500, 50)
    hd = orders[orders["payment_total"] <= max_v]
    st.plotly_chart(px.histogram(hd, x="payment_total", nbins=60,
                    labels={"payment_total": "Order Value (BRL)"}), key="hist1")

with tabs[1]:
    st.subheader("Segment Overview")
    st.dataframe(risk)
    s = (seg.groupby("segment_name")["satisfied"].mean()*100).reset_index().sort_values("satisfied")
    st.plotly_chart(px.bar(s, x="segment_name", y="satisfied",
                    labels={"satisfied": "Satisfaction %", "segment_name": "Segment"}), key="seg_sat1")

with tabs[2]:
    st.subheader("Satisfaction Rate by Segment")
    s = (seg.groupby("segment_name")["satisfied"].mean()*100).reset_index().sort_values("satisfied")
    st.plotly_chart(px.bar(s, x="segment_name", y="satisfied",
                    labels={"satisfied": "Satisfaction %", "segment_name": "Segment"}), key="seg_sat2")

with tabs[3]:
    st.subheader("At-Risk Order Flagging")
    st.write("Drag the slider to set the risk threshold. Orders above it are flagged for service recovery.")
    t = st.slider("Risk threshold", 0.0, 1.0, 0.30, 0.05)
    preds["dissatisfied"] = 1 - preds["satisfied"]
    flagged = preds["risk_score"] >= t
    tp = ((flagged) & (preds["dissatisfied"] == 1)).sum()
    recall = tp / preds["dissatisfied"].sum() * 100
    precision = tp / max(flagged.sum(), 1) * 100
    m1, m2, m3 = st.columns(3)
    m1.metric("Orders flagged", f"{flagged.mean()*100:.1f}%")
    m2.metric("Dissatisfied caught (recall)", f"{recall:.1f}%")
    m3.metric("Flags genuine (precision)", f"{precision:.1f}%")

with tabs[4]:
    st.subheader("Orders by State")
    metric = st.selectbox("Show", ["Number of orders", "Total revenue", "Avg order value"])
    g = orders.groupby("customer_state")
    if metric == "Number of orders":
        data = g.size().reset_index(name="value")
    elif metric == "Total revenue":
