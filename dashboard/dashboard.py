import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

sns.set_theme(style="whitegrid")
st.set_page_config(page_title="Olist E-Commerce Dashboard", page_icon="🛒", layout="wide")


@st.cache_data
def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main_data.csv")
    df = pd.read_csv(path, parse_dates=["order_purchase_timestamp", "order_delivered_customer_date",
                                        "order_estimated_delivery_date"])
    df["is_late"] = df["is_late"].astype(bool)
    return df


main_df = load_data()

# ---------------- Sidebar ----------------
st.sidebar.header("Filter Data")
min_date = main_df["order_purchase_timestamp"].min().date()
max_date = main_df["order_purchase_timestamp"].max().date()
date_range = st.sidebar.date_input("Rentang tanggal pembelian", value=(min_date, max_date),
                                   min_value=min_date, max_value=max_date)
states = sorted(main_df["customer_state"].unique())
selected_states = st.sidebar.multiselect("State pelanggan", states, default=states)

if len(date_range) != 2:
    st.info("Pilih tanggal awal dan akhir pada sidebar.")
    st.stop()

mask = (
    (main_df["order_purchase_timestamp"].dt.date >= date_range[0])
    & (main_df["order_purchase_timestamp"].dt.date <= date_range[1])
    & (main_df["customer_state"].isin(selected_states))
)
df = main_df[mask]
if df.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()
order_df = df.drop_duplicates("order_id")

# ---------------- Header & metrics ----------------
st.title("🛒 Dashboard Analisis E-Commerce (Olist)")
st.caption("Pesanan berstatus delivered, Januari 2017 - Agustus 2018. Revenue = total harga produk (tanpa ongkir), dalam BRL.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Pesanan", f"{order_df['order_id'].nunique():,}")
c2.metric("Total Revenue", f"{df['price'].sum():,.0f}")
c3.metric("Rata-rata Review", f"{order_df['review_score'].mean():.2f}")
c4.metric("Pesanan Terlambat", f"{order_df['is_late'].mean() * 100:.1f}%")

tab1, tab2, tab3 = st.tabs(["Kategori Produk", "Keterlambatan & Review", "RFM Pelanggan"])

# ---------------- Tab 1: Kategori ----------------
with tab1:
    st.subheader("Kategori dengan Revenue Tertinggi dan Terendah")
    cat_df = df.groupby("product_category")["price"].sum().sort_values(ascending=False)
    n_top = st.slider("Jumlah kategori teratas", 5, 15, 10)
    col_a, col_b = st.columns(2)
    with col_a:
        fig, ax = plt.subplots(figsize=(7, 5))
        top = cat_df.head(n_top).reset_index()
        sns.barplot(data=top, y="product_category", x="price", color="#1f77b4", ax=ax)
        ax.set_title(f"{n_top} Kategori Revenue Tertinggi"); ax.set_xlabel("Revenue (BRL)"); ax.set_ylabel("")
        st.pyplot(fig)
    with col_b:
        fig, ax = plt.subplots(figsize=(7, 5))
        bottom = cat_df.tail(5).reset_index().sort_values("price")
        sns.barplot(data=bottom, y="product_category", x="price", color="#d62728", ax=ax)
        ax.set_title("5 Kategori Revenue Terendah"); ax.set_xlabel("Revenue (BRL)"); ax.set_ylabel("")
        st.pyplot(fig)
    st.write(f"Top {n_top} kategori menyumbang **{cat_df.head(n_top).sum() / cat_df.sum() * 100:.1f}%** dari total revenue pada filter ini.")

    st.subheader("Tren Revenue Bulanan")
    monthly = df.groupby(df["order_purchase_timestamp"].dt.to_period("M"))["price"].sum()
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(monthly.index.astype(str), monthly.values, marker="o", color="#1f77b4")
    ax.set_ylabel("Revenue (BRL)"); ax.tick_params(axis="x", rotation=60)
    st.pyplot(fig)

# ---------------- Tab 2: Keterlambatan ----------------
with tab2:
    st.subheader("Persentase Pesanan Terlambat per State")
    min_orders = st.slider("Minimal jumlah pesanan per state", 50, 1000, 300, step=50)
    state_df = (order_df.groupby("customer_state")
                .agg(orders=("order_id", "count"), late_pct=("is_late", "mean"), avg_review=("review_score", "mean")))
    state_df["late_pct"] *= 100
    state_df = state_df[state_df["orders"] >= min_orders].sort_values("late_pct", ascending=False).reset_index()
    nat = order_df["is_late"].mean() * 100
    col_a, col_b = st.columns([2, 1])
    with col_a:
        if state_df.empty:
            st.info("Tidak ada state yang memenuhi minimal pesanan.")
        else:
            fig, ax = plt.subplots(figsize=(8, 6))
            colors = ["#d62728" if v > nat * 1.5 else "#9ecae1" for v in state_df["late_pct"]]
            sns.barplot(data=state_df, y="customer_state", x="late_pct", hue="customer_state",
                        palette=colors, legend=False, ax=ax)
            ax.axvline(nat, color="black", linestyle="--")
            ax.set_title(f"% Pesanan Terlambat (rata-rata {nat:.1f}%, merah = >1,5x rata-rata)")
            ax.set_xlabel("% pesanan terlambat"); ax.set_ylabel("")
            st.pyplot(fig)
    with col_b:
        rv = order_df.groupby("is_late")["review_score"].mean().reindex([False, True])
        fig, ax = plt.subplots(figsize=(4, 6))
        sns.barplot(x=["Tepat waktu", "Terlambat"], y=rv.values, hue=["Tepat waktu", "Terlambat"],
                    palette=["#2ca02c", "#d62728"], legend=False, ax=ax)
        for i, v in enumerate(rv.values):
            ax.text(i, v + 0.08, f"{v:.2f}", ha="center")
        ax.set_ylim(0, 5); ax.set_ylabel("Rata-rata review score"); ax.set_title("Review: Tepat Waktu vs Terlambat")
        st.pyplot(fig)

# ---------------- Tab 3: RFM ----------------
with tab3:
    st.subheader("Segmentasi Pelanggan (RFM)")
    st.caption("Recency dihitung dari 1 hari setelah pembelian terakhir pada data terfilter. Pelanggan dengan 2 pesanan atau lebih = Repeat Buyer; "
               "pelanggan sekali beli dibagi dengan median Recency dan Monetary (binning).")
    ref_date = df["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
    rfm = (df.groupby("customer_unique_id")
           .agg(last_order=("order_purchase_timestamp", "max"), frequency=("order_id", "nunique"), monetary=("price", "sum"))
           .reset_index())
    rfm["recency"] = (ref_date - rfm["last_order"]).dt.days
    med_r, med_m = rfm["recency"].median(), rfm["monetary"].median()

    def segment(r):
        if r["frequency"] >= 2:
            return "Repeat Buyer"
        if r["recency"] <= med_r:
            return "Recent High Spender" if r["monetary"] > med_m else "Recent Low Spender"
        return "Lapsed High Spender" if r["monetary"] > med_m else "Lapsed Low Spender"

    rfm["segment"] = rfm.apply(segment, axis=1)
    seg = (rfm.groupby("segment").agg(customers=("customer_unique_id", "count"), avg_monetary=("monetary", "mean"),
                                      avg_recency=("recency", "mean")).reset_index())
    order = ["Recent High Spender", "Recent Low Spender", "Lapsed High Spender", "Lapsed Low Spender", "Repeat Buyer"]
    seg["segment"] = pd.Categorical(seg["segment"], order, ordered=True)
    seg = seg.sort_values("segment")
    pal = ["#1f77b4", "#9ecae1", "#d62728", "#fcae91", "#2ca02c"]
    m1, m2, m3 = st.columns(3)
    m1.metric("Jumlah Pelanggan", f"{len(rfm):,}")
    m2.metric("Repeat Buyer", f"{(rfm['frequency'] >= 2).mean() * 100:.1f}%")
    m3.metric("Median Recency (hari)", f"{med_r:.0f}")
    col_a, col_b = st.columns(2)
    with col_a:
        fig, ax = plt.subplots(figsize=(7, 4))
        sns.barplot(data=seg, x="customers", y="segment", hue="segment", palette=pal, legend=False, ax=ax)
        ax.set_title("Jumlah Pelanggan per Segmen"); ax.set_xlabel("Pelanggan"); ax.set_ylabel("")
        st.pyplot(fig)
    with col_b:
        fig, ax = plt.subplots(figsize=(7, 4))
        sns.barplot(data=seg, x="avg_monetary", y="segment", hue="segment", palette=pal, legend=False, ax=ax)
        ax.set_title("Rata-rata Belanja per Segmen (BRL)"); ax.set_xlabel("Monetary"); ax.set_ylabel("")
        st.pyplot(fig)
    st.dataframe(seg.round(1), hide_index=True)

st.caption("Sumber data: Brazilian E-Commerce Public Dataset by Olist")
