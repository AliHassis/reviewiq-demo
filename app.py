import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import Counter
import io

from utils import (
    get_text, detect_review_column, detect_date_column, detect_rating_column,
    detect_reply_column, find_critical_words, count_critical_reviews,
    calculate_reputation_score,
    RESTAURANT_POSITIVE_KEYWORDS, RESTAURANT_NEGATIVE_KEYWORDS,
)
from analyzer import analyze_basic, calculate_response_rate

st.set_page_config(
    page_title="ReviewIQ Demo — Restaurants",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "lang" not in st.session_state:
    st.session_state.lang = "ar"
if "reviews_df" not in st.session_state:
    st.session_state.reviews_df = None
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "review_col" not in st.session_state:
    st.session_state.review_col = None


def t(key):
    return get_text(key, st.session_state.lang)


# --- CSS ---
dark_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo' !important; }
    .stApp { background-color: #0e1117; color: #fafafa; }
    [data-testid="stSidebar"] { background-color: #1e293b; }
    [data-testid="stAppDeployButton"] { display: none; }
    #MainMenu, footer { visibility: hidden; }
    header { background-color: transparent !important; }
    .stMetric {
        background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155;
    }
    [data-testid="stSlider"] { direction: ltr; }
    .kpi-card {
        background-color: #1e293b; padding: 20px; border-radius: 12px;
        border: 1px solid #334155; text-align: center;
    }
    .kpi-card h2 { margin: 0; font-size: 2rem; }
    .kpi-card p { margin: 5px 0 0 0; font-size: 0.9rem; color: #94a3b8; }
    .reputation-green { border-color: #2ecc71; }
    .reputation-green h2 { color: #2ecc71; }
    .reputation-yellow { border-color: #f39c12; }
    .reputation-yellow h2 { color: #f39c12; }
    .reputation-red { border-color: #e74c3c; }
    .reputation-red h2 { color: #e74c3c; }
    .critical-card {
        background-color: #1a0000; border: 2px solid #e74c3c;
        border-radius: 10px; padding: 15px; margin-bottom: 10px;
    }
    .critical-card p { color: #fca5a5; }
    .critical-card .reason { color: #ef4444; font-weight: bold; font-size: 0.85rem; }
    .demo-badge {
        background: linear-gradient(90deg, #f39c12, #e67e22);
        color: white; padding: 5px 15px; border-radius: 20px;
        font-weight: bold; display: inline-block; margin-bottom: 10px;
    }
</style>
"""

rtl_css = """
<style>
    .main .block-container { direction: rtl; }
    [data-testid="stSidebar"] > div { direction: rtl; }
</style>
"""

st.markdown(dark_css, unsafe_allow_html=True)
if st.session_state.lang == "ar":
    st.markdown(rtl_css, unsafe_allow_html=True)


# --- Sidebar ---
with st.sidebar:
    st.title("ReviewIQ Demo 🍽️")
    st.markdown('<span class="demo-badge">DEMO</span>', unsafe_allow_html=True)

    lang_options = {"العربية": "ar", "English": "en"}
    selected_lang = st.radio(
        t("language"),
        list(lang_options.keys()),
        index=0 if st.session_state.lang == "ar" else 1,
        horizontal=True,
    )
    st.session_state.lang = lang_options[selected_lang]

    st.divider()

    page = st.radio(
        "📄",
        [t("page_collection"), t("page_analysis")],
        label_visibility="collapsed",
    )


# ==================== PAGE 1: COLLECTION ====================
if page == t("page_collection"):
    st.header(t("page_collection"))

    source = st.selectbox(
        t("select_source"),
        [t("custom_csv"), t("tripadvisor_csv")],
    )

    if source == t("custom_csv"):
        uploaded = st.file_uploader(t("upload_file"), type=["csv", "xlsx", "xls"], key="custom_file")
        if uploaded:
            try:
                if uploaded.name.endswith(".csv"):
                    df = pd.read_csv(uploaded)
                    df = df.head(200)
                else:
                    df = pd.read_excel(uploaded)
                    df = df.head(200)
                review_col = detect_review_column(df)
                if review_col:
                    st.session_state.reviews_df = df
                    st.session_state.review_col = review_col
                    st.success(t("reviews_fetched").format(count=len(df)))
                else:
                    st.error(t("no_reviews"))
            except Exception as e:
                st.error(t("error_fetch").format(error=str(e)))

    elif source == t("tripadvisor_csv"):
        st.markdown(t("csv_instructions_tripadvisor"))
        uploaded = st.file_uploader(t("upload_csv"), type=["csv"], key="tripadvisor_csv")
        if uploaded:
            try:
                df = pd.read_csv(uploaded)
                df = df.head(200)
                review_col = detect_review_column(df)
                if review_col:
                    st.session_state.reviews_df = df
                    st.session_state.review_col = review_col
                    st.success(t("reviews_fetched").format(count=len(df)))
                else:
                    st.error(t("no_reviews"))
            except Exception as e:
                st.error(t("error_fetch").format(error=str(e)))

    # Preview
    if st.session_state.reviews_df is not None and not st.session_state.reviews_df.empty:
        df = st.session_state.reviews_df
        review_col = st.session_state.review_col

        critical_count, critical_indices = count_critical_reviews(df, review_col)
        if critical_count > 0:
            st.error(t("critical_alert").format(count=critical_count))

        st.subheader(t("preview"))

        display_cols = []
        if review_col and review_col in df.columns:
            display_cols.append(review_col)
        rating_col = detect_rating_column(df)
        if rating_col and rating_col in df.columns:
            display_cols.append(rating_col)
        date_col = detect_date_column(df)
        if date_col and date_col in df.columns:
            display_cols.append(date_col)

        if not display_cols:
            display_cols = list(df.columns[:4])

        st.dataframe(df[display_cols].head(100), use_container_width=True, height=400)


# ==================== PAGE 2: ANALYSIS ====================
elif page == t("page_analysis"):
    st.header(t("page_analysis"))

    if st.session_state.reviews_df is None or st.session_state.reviews_df.empty:
        st.info(t("no_data"))
    else:
        df = st.session_state.reviews_df
        review_col = st.session_state.review_col
        reviews_list = df[review_col].astype(str).tolist()

        analysis = st.session_state.analysis

        # KPI
        if analysis and "sentiments" in analysis:
            rep_score = calculate_reputation_score(df, analysis, review_col)
            score_class = "reputation-green" if rep_score > 70 else ("reputation-yellow" if rep_score >= 40 else "reputation-red")

            kpi0, kpi1, kpi2, kpi3 = st.columns(4)
            with kpi0:
                st.markdown(f'<div class="kpi-card {score_class}"><h2>{rep_score}</h2><p>{t("reputation_score")}</p></div>', unsafe_allow_html=True)
            with kpi1:
                st.markdown(f'<div class="kpi-card"><h2>{len(df)}</h2><p>{t("total_reviews")}</p></div>', unsafe_allow_html=True)
            with kpi2:
                rating_col = detect_rating_column(df)
                avg_r = round(df[rating_col].mean(), 2) if rating_col else "—"
                st.markdown(f'<div class="kpi-card"><h2>⭐ {avg_r}</h2><p>{t("avg_rating")}</p></div>', unsafe_allow_html=True)
            with kpi3:
                sents = analysis["sentiments"]
                neg = sents.count("Negative") + sents.count("سلبي")
                neg_pct = round(neg / len(sents) * 100, 1) if sents else 0
                st.markdown(f'<div class="kpi-card"><h2>{neg_pct}%</h2><p>{t("negative_pct")}</p></div>', unsafe_allow_html=True)
        else:
            kpi1, kpi2 = st.columns(2)
            with kpi1:
                st.metric(t("total_reviews"), len(df))
            with kpi2:
                rating_col = detect_rating_column(df)
                avg_rating = round(df[rating_col].mean(), 2) if rating_col else "—"
                st.metric(t("avg_rating"), f"⭐ {avg_rating}")

        st.divider()

        # Filters
        with st.expander(t("filters")):
            filter_cols = st.columns(3)
            filtered_df = df.copy()

            with filter_cols[0]:
                rating_col = detect_rating_column(df)
                if rating_col:
                    rating_range = st.slider(t("filter_rating"), 1, 5, (1, 5))
                    filtered_df = filtered_df[
                        (filtered_df[rating_col] >= rating_range[0]) &
                        (filtered_df[rating_col] <= rating_range[1])
                    ]

            with filter_cols[1]:
                date_col = detect_date_column(df)
                if date_col:
                    try:
                        filtered_df[date_col] = pd.to_datetime(filtered_df[date_col], errors="coerce")
                        min_date = filtered_df[date_col].min()
                        max_date = filtered_df[date_col].max()
                        if pd.notna(min_date) and pd.notna(max_date):
                            date_range = st.date_input(
                                t("filter_date"),
                                value=(min_date.date(), max_date.date()),
                                min_value=min_date.date(),
                                max_value=max_date.date(),
                            )
                            if len(date_range) == 2:
                                filtered_df = filtered_df[
                                    (filtered_df[date_col].dt.date >= date_range[0]) &
                                    (filtered_df[date_col].dt.date <= date_range[1])
                                ]
                    except Exception:
                        pass

            with filter_cols[2]:
                keyword = st.text_input(t("filter_keyword"))
                if keyword:
                    filtered_df = filtered_df[
                        filtered_df[review_col].astype(str).str.contains(keyword, case=False, na=False)
                    ]

            reviews_list = filtered_df[review_col].astype(str).tolist()
            st.caption(f"{len(reviews_list)} {t('total_reviews').lower()}")

        # Analyze
        if st.button(t("analyze"), type="primary", use_container_width=True):
            with st.spinner(t("analyzing")):
                try:
                    result = analyze_basic(reviews_list)
                    st.session_state.analysis = result
                    st.success(t("analysis_complete"))
                    st.rerun()
                except Exception as e:
                    st.error(t("error_analysis").format(error=str(e)))

        # Results
        if st.session_state.analysis:
            analysis = st.session_state.analysis
            sentiments = analysis.get("sentiments", [])

            if sentiments:
                pos = sentiments.count("Positive") + sentiments.count("إيجابي")
                neg = sentiments.count("Negative") + sentiments.count("سلبي")
                neu = sentiments.count("Neutral") + sentiments.count("محايد")

                fig_pie = px.pie(
                    names=[t("positive"), t("negative"), t("neutral")],
                    values=[pos, neg, neu],
                    color_discrete_sequence=["#2ecc71", "#e74c3c", "#95a5a6"],
                    title=t("sentiment_dist"),
                )
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#fafafa",
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            complaints = analysis.get("complaints", [])
            if complaints:
                st.subheader(t("top_complaints"))
                fig_comp = px.bar(
                    x=[c["count"] for c in complaints],
                    y=[c["text"] for c in complaints],
                    orientation="h",
                    color_discrete_sequence=["#e74c3c"],
                    labels={"x": t("count"), "y": t("complaint")},
                )
                fig_comp.update_layout(
                    yaxis={"autorange": "reversed"},
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#fafafa",
                )
                st.plotly_chart(fig_comp, use_container_width=True)

            praises = analysis.get("praises", [])
            if praises:
                st.subheader(t("top_praises"))
                fig_praise = px.bar(
                    x=[p["count"] for p in praises],
                    y=[p["text"] for p in praises],
                    orientation="h",
                    color_discrete_sequence=["#2ecc71"],
                    labels={"x": t("count"), "y": t("praise")},
                )
                fig_praise.update_layout(
                    yaxis={"autorange": "reversed"},
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#fafafa",
                )
                st.plotly_chart(fig_praise, use_container_width=True)

            recommendations = analysis.get("recommendations", [])
            if recommendations:
                st.subheader(t("recommendations"))
                for i, rec in enumerate(recommendations, 1):
                    st.info(f"**{i}.** {rec}")

            summary = analysis.get("summary", "")
            if summary:
                st.subheader(t("executive_summary"))
                st.markdown(f"> {summary}")

            # Keyword Sentiment Map
            st.subheader(t("keyword_sentiment"))
            if sentiments:
                try:
                    all_pos_keywords = RESTAURANT_POSITIVE_KEYWORDS.get("ar", []) + RESTAURANT_POSITIVE_KEYWORDS.get("en", [])
                    all_neg_keywords = RESTAURANT_NEGATIVE_KEYWORDS.get("ar", []) + RESTAURANT_NEGATIVE_KEYWORDS.get("en", [])
                    all_keywords = list(set(all_pos_keywords + all_neg_keywords))

                    word_pos_count = Counter()
                    word_neg_count = Counter()

                    for rev_text, sent in zip(reviews_list, sentiments[:len(reviews_list)]):
                        rev_lower = rev_text.lower()
                        for word in all_keywords:
                            if word.lower() in rev_lower:
                                if sent in ("Positive", "إيجابي"):
                                    word_pos_count[word] += 1
                                elif sent in ("Negative", "سلبي"):
                                    word_neg_count[word] += 1

                    word_scores = {}
                    for word in all_keywords:
                        p = word_pos_count.get(word, 0)
                        n = word_neg_count.get(word, 0)
                        total = p + n
                        if total > 0:
                            word_scores[word] = (p - n) / total

                    if word_scores:
                        sorted_words = sorted(word_scores.items(), key=lambda x: -(word_pos_count.get(x[0], 0) + word_neg_count.get(x[0], 0)))
                        sorted_words = sorted_words[:30]

                        fig_ksm, ax_ksm = plt.subplots(figsize=(12, 6))
                        ax_ksm.set_facecolor("#0e1117")
                        fig_ksm.set_facecolor("#0e1117")

                        for i, (word, score) in enumerate(sorted_words):
                            total_count = word_pos_count.get(word, 0) + word_neg_count.get(word, 0)
                            font_size = min(24, max(10, 8 + total_count * 2))

                            if score > 0.2:
                                color = "#2ecc71"
                            elif score < -0.2:
                                color = "#e74c3c"
                            else:
                                color = "#95a5a6"

                            x = (i % 6) / 6 + 0.08
                            y = 1.0 - (i // 6) / 5 - 0.1

                            ax_ksm.text(x, y, word, fontsize=font_size, color=color,
                                        ha="center", va="center", fontweight="bold",
                                        transform=ax_ksm.transAxes)

                        ax_ksm.axis("off")
                        plt.tight_layout()
                        st.pyplot(fig_ksm)
                        plt.close(fig_ksm)
                except Exception as e:
                    st.warning(str(e))

            # Critical Reviews
            critical_count, critical_indices = count_critical_reviews(df, review_col)
            if critical_count > 0:
                st.subheader(t("critical_reviews_urgent"))
                for idx in critical_indices[:10]:
                    rev_text = str(df.loc[idx, review_col])
                    found_words = find_critical_words(rev_text)
                    words_str = "، ".join(found_words) if st.session_state.lang == "ar" else ", ".join(found_words)
                    reason = t("critical_reason").format(word=words_str)
                    st.markdown(f"""<div class="critical-card">
                        <p>{rev_text[:300]}</p>
                        <div class="reason">{reason}</div>
                    </div>""", unsafe_allow_html=True)

            # Full version notices
            st.divider()
            full_version_msg = t("full_version_only")
            st.warning(f"📊 Excel Export — {full_version_msg}")
            st.warning(f"📄 PDF Export — {full_version_msg}")
            st.warning(f"🤖 AI Response Suggestions — {full_version_msg}")
            st.warning(f"🖼️ Restaurant Logo — {full_version_msg}")
