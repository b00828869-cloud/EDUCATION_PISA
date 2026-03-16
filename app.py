import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="PISA Education Dashboard", layout="wide")


# =========================
# GLOBAL STYLE
# =========================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #F7F9FC 0%, #EEF3F8 100%);
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

h1, h2, h3 {
    color: #111827;
    letter-spacing: -0.02em;
}

div[data-testid="stAlert"] {
    border-radius: 18px;
    border: 1px solid rgba(0,0,0,0.05);
    box-shadow: 0 10px 30px rgba(17, 24, 39, 0.06);
}

div[data-baseweb="select"] > div,
div[role="radiogroup"] {
    border-radius: 14px !important;
}

[data-testid="stMetric"] {
    background: #111111;
    border-radius: 22px;
    padding: 18px 20px;
    box-shadow: 0 14px 35px rgba(0, 0, 0, 0.18);
    border: 1px solid rgba(255,255,255,0.05);
}

[data-testid="stMetricLabel"] {
    color: rgba(255,255,255,0.78) !important;
    font-weight: 600;
}

[data-testid="stMetricValue"] {
    color: white !important;
    font-weight: 800;
}

[data-testid="stMetricDelta"] {
    color: #C7D2FE !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 24px !important;
    border: 1px solid rgba(15, 23, 42, 0.06) !important;
    box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08) !important;
    background: rgba(255,255,255,0.88) !important;
    backdrop-filter: blur(4px);
    padding: 0.35rem 0.6rem 0.8rem 0.6rem;
}

div[data-testid="stPlotlyChart"] {
    border-radius: 18px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
@keyframes fadeUp {
    from {
        opacity: 0;
        transform: translateY(14px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    animation: fadeUp 0.6s ease-out;
}

div[data-testid="stMetric"] {
    animation: fadeUp 0.5s ease-out;
}

div[data-testid="stPlotlyChart"] {
    animation: fadeUp 0.7s ease-out;
}
</style>
""", unsafe_allow_html=True)
# =========================
# DATA LOADING
# =========================
@st.cache_data
def load_data():
    df = pd.read_excel("data/Total_PISA.xlsx")

    df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed", na=False)]

    df.columns = (
        df.columns.astype(str)
        .str.replace("\xa0", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    rename_dict = {
        "Year/Study": "year",
        "Jurisdiction": "country",
        "Mathematics scale Average": "math_score",
        "science scale Average": "science_score",
        "reading scale Average": "reading_score",
        "status of parents (hisei) Average": "hisei",
        "experience of being bullied Average": "bullying",
        "access to money Average": "access_to_money",
        "current support for learning at home Average": "home_support",
        "index teacher support in mathematics lessons Average": "teacher_support_math",
        "Class Period Mathematics Average": "class_period_math",
        "Class Period Science Average": "class_period_science",
        "Class Periods Language Average": "class_period_language",
        "number of students Average": "n_students",
        "student-teacher ratio Average": "student_teacher_ratio",
        "teachers fully certified Average": "teachers_fully_certified",
        "sense of belonging to school Average": "belonging",
        "parent attitudes toward mathematics Average": "parent_attitudes_math",
        "economic. social and cultural status Average": "escs",
        "GINI INDICATOR": "gini",
        "region": "region",
        "Gender gap (boys - girls) Mathematics": "gender_gap_math",
        "Gender gap (boys - girls) Readings": "gender_gap_reading",
        "GDP": "gdp",
        "spending on education": "education_spending",
        "Duration of FULL and PARTIAL school closures (in weeks)": "school_closure_weeks",
    }

    df = df.rename(columns=rename_dict)
    df = df.replace(["—", "-", " "], pd.NA)

    numeric_cols = [
        "year",
        "math_score",
        "science_score",
        "reading_score",
        "hisei",
        "bullying",
        "access_to_money",
        "home_support",
        "teacher_support_math",
        "class_period_math",
        "class_period_science",
        "class_period_language",
        "n_students",
        "student_teacher_ratio",
        "teachers_fully_certified",
        "belonging",
        "parent_attitudes_math",
        "escs",
        "gini",
        "gender_gap_math",
        "gender_gap_reading",
        "gdp",
        "education_spending",
        "school_closure_weeks",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    required_cols = ["year", "country", "math_score", "reading_score", "science_score", "region"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    return df


df = load_data()

# =========================
# GLOBAL SETTINGS
# =========================
oecd_label = "International Average (OECD)"
df_oecd = df[df["country"] == oecd_label].copy()
df_countries = df[df["country"] != oecd_label].copy()

df["overall_score"] = df[["math_score", "reading_score", "science_score"]].mean(axis=1)
df_countries["overall_score"] = df_countries[["math_score", "reading_score", "science_score"]].mean(axis=1)
df_oecd["overall_score"] = df_oecd[["math_score", "reading_score", "science_score"]].mean(axis=1)

score_options = {
    "All subjects": "overall_score",
    "Mathematics": "math_score",
    "Reading": "reading_score",
    "Science": "science_score",
}

subject_colors = {
    "Math": "#00B48F",
    "Reading": "#0024D3",
    "Science": "#EA3FCD",
}

score_color_map = {
    "All subjects": "#111111",
    "Mathematics": "#00B48F",
    "Reading": "#0024D3",
    "Science": "#EA3FCD",
}

factor_options = {
    "Economic, social and cultural status (ESCS)": "escs",
    "Parents' occupational status (HISEI)": "hisei",
    "Bullying": "bullying",
    "Teacher support in mathematics": "teacher_support_math",
    "Sense of belonging": "belonging",
    "Student-teacher ratio": "student_teacher_ratio",
    "GINI indicator": "gini",
}

driver_region_colors = {
    "Europe": "#4E79A7",
    "Asia": "#F28E2B",
    "North America": "#E15759",
    "South America": "#76B7B2",
    "Oceania": "#59A14F",
    "Africa": "#EDC948",
    "Middle East": "#B07AA1",
}

metric_toolbox = {
    "Math score": """
**Math score** measures how well 15-year-old students can formulate, apply and interpret mathematics in real-life situations.

PISA scores are standardized:
- OECD average ≈ 500
- Standard deviation ≈ 100

A difference of around 20 points is often interpreted as a meaningful learning gap.
""",

    "Reading score": """
**Reading score** measures students’ ability to understand, use, evaluate and reflect on written texts.

It captures reading literacy rather than simple decoding skills.
""",

    "Science score": """
**Science score** measures how well students can engage with science-related issues and ideas as reflective citizens.

It focuses on scientific reasoning and applied understanding.
""",

    "Gender gap": """
**Gender gap** is calculated as:

**boys' average score − girls' average score**

- Positive value → boys outperform girls
- Negative value → girls outperform boys
- 0 → equal performance
""",

    "ESCS": """
**ESCS** (*Economic, Social and Cultural Status*) is a composite PISA index used to approximate students’ socio-economic background.

It combines:
- parental education
- highest parental occupational status (HISEI)
- home possessions

Higher ESCS values indicate more advantaged socio-economic conditions.
""",

    "GDP": """
**GDP per capita** is used here as a proxy for national wealth and overall economic development.

It helps compare education outcomes with the broader macroeconomic context.
""",

    "Education spending": """
**Education spending** captures the level of national investment in education.

It reflects quantity of spending, not necessarily spending efficiency.
""",

    "Sense of belonging": """
**Sense of belonging** measures how strongly students feel accepted, supported and included in their school community.

Higher values usually reflect stronger school attachment.
""",

    "Teacher support": """
**Teacher support** measures students’ perception of how often teachers provide support in mathematics lessons.

It reflects perceived instructional support, not an objective measure of teacher quality.
"""
}
# =========================
# SIDEBAR
# =========================
st.sidebar.title("Controls")

available_countries = sorted(df_countries["country"].dropna().unique())

default_country_index = (
    available_countries.index("France") if "France" in available_countries else 0
)

selected_country = st.sidebar.selectbox(
    "Select country",
    available_countries,
    index=default_country_index,
)

selected_score_label = st.sidebar.selectbox(
    "Select score",
    list(score_options.keys()),
)

selected_score = score_options[selected_score_label]
main_color = score_color_map[selected_score_label]

# Fixed year = latest available year
selected_year = int(df_countries["year"].dropna().max())

st.sidebar.markdown("---")
st.sidebar.markdown("## Metric toolbox")

selected_metric_info = st.sidebar.selectbox(
    "Learn more about a metric",
    list(metric_toolbox.keys()),
    key="metric_toolbox_select"
)

st.sidebar.info(metric_toolbox[selected_metric_info])


# =========================
# FILTERS
# =========================
df_year = df_countries[df_countries["year"] == selected_year].copy()
df_oecd_year = df_oecd[df_oecd["year"] == selected_year].copy()

country_data = df_year[df_year["country"] == selected_country].copy()

if country_data.empty:
    st.error("No data available for this country selection.")
    st.stop()

selected_region = country_data["region"].iloc[0]

region_data = df_year[df_year["region"] == selected_region].copy()
region_data = region_data.dropna(subset=[selected_score])

if region_data.empty:
    st.error("No regional comparison data available.")
    st.stop()

country_score = country_data[selected_score].iloc[0]
region_mean = region_data[selected_score].mean()

region_data["rank"] = region_data[selected_score].rank(ascending=False, method="min")
country_rank = int(
    region_data.loc[region_data["country"] == selected_country, "rank"].iloc[0]
)
total_countries_region = region_data["country"].nunique()

oecd_value = None
if not df_oecd_year.empty and selected_score in df_oecd_year.columns:
    oecd_value = df_oecd_year[selected_score].iloc[0]

# =========================
# HEADER
# =========================
st.markdown(
    """
    <div style="
        display:inline-block;
        padding:8px 14px;
        border-radius:999px;
        background:rgba(17,24,39,0.06);
        color:#111827;
        font-weight:600;
        font-size:14px;
        margin-bottom:10px;
    ">
        OECD Programme for International Student Assessment (PISA)
    </div>
    """,
    unsafe_allow_html=True
)

st.title("Global Education Performance Dashboard")

st.markdown(
    f"""
This dashboard explores results from the **OECD PISA assessment**, an international study that evaluates the
skills of **15-year-old students** around the world.

PISA measures how well students can **apply knowledge and solve problems** in three core domains:

- 📘 **Reading**
- ➗ **Mathematics**
- 🔬 **Science**

Below, we analyze the performance of **{selected_country}** in **{int(selected_year)}**,  
compared with other countries in **{selected_region}**.
"""
)
# =========================
# KPI ROW
# =========================
col1, col2, col3, col4 = st.columns(4)

with col1:
    if selected_score_label == "All subjects":
        st.metric("Overall score", f"{country_score:.1f}")
    else:
        st.metric(f"{selected_score_label} score", f"{country_score:.1f}")

with col2:
    if selected_score_label == "All subjects":
        st.metric(f"Average overall score in {selected_region}", f"{region_mean:.1f}")
    else:
        st.metric(f"Average score in {selected_region}", f"{region_mean:.1f}")

with col3:
    st.metric("Rank in region", f"{country_rank} / {total_countries_region}")

with col4:
    if oecd_value is not None and pd.notna(oecd_value):
        st.metric("Gap vs OECD", f"{country_score - oecd_value:+.1f}")
    else:
        st.metric("Gap vs OECD", "N/A")

# =========================
# NARRATIVE 1
# =========================
if country_score > region_mean:
    position_text = f"above the average in {selected_region}"
elif country_score < region_mean:
    position_text = f"below the average in {selected_region}"
else:
    position_text = f"exactly at the average in {selected_region}"

if oecd_value is not None and pd.notna(oecd_value):
    if country_score > oecd_value:
        oecd_text = "above the OECD benchmark"
    elif country_score < oecd_value:
        oecd_text = "below the OECD benchmark"
    else:
        oecd_text = "exactly at the OECD benchmark"
else:
    oecd_text = "with no OECD benchmark available"

st.info(
    f"In **{int(selected_year)}**, **{selected_country}** ranks **{country_rank} out of {total_countries_region}** "
    f"in **{selected_region}** for **{selected_score_label.lower()}**. "
    f"It stands **{position_text}** and is **{oecd_text}**."
)

# =========================
# CHART 1 — REGIONAL RANKING
# =========================
with st.container(border=True):
    st.markdown("### Overview")
    st.subheader(f"{selected_score_label} ranking in {selected_region}")

    ranking_view = st.radio(
        "Select ranking view",
        ["Current year ranking", "Rank evolution over time"],
        horizontal=True,
        key="ranking_view_mode"
    )

    if ranking_view == "Current year ranking":

        if selected_score_label == "All subjects":
            region_rank = region_data.dropna(subset=["math_score", "reading_score", "science_score"]).copy()
            region_rank["total_score"] = region_rank[["math_score", "reading_score", "science_score"]].sum(axis=1)
            region_rank = region_rank.sort_values("total_score", ascending=False)

            fig_ranking = go.Figure()

            fig_ranking.add_trace(go.Bar(
                x=region_rank["math_score"],
                y=region_rank["country"],
                orientation="h",
                name="Math",
                marker=dict(color=subject_colors["Math"]),
                customdata=region_rank[["total_score"]],
                hovertemplate="<b>%{y}</b><br>Math: %{x:.1f}<br>Total: %{customdata[0]:.1f}<extra></extra>",
            ))

            fig_ranking.add_trace(go.Bar(
                x=region_rank["reading_score"],
                y=region_rank["country"],
                orientation="h",
                name="Reading",
                marker=dict(color=subject_colors["Reading"]),
                customdata=region_rank[["total_score"]],
                hovertemplate="<b>%{y}</b><br>Reading: %{x:.1f}<br>Total: %{customdata[0]:.1f}<extra></extra>",
            ))

            fig_ranking.add_trace(go.Bar(
                x=region_rank["science_score"],
                y=region_rank["country"],
                orientation="h",
                name="Science",
                marker=dict(color=subject_colors["Science"]),
                customdata=region_rank[["total_score"]],
                hovertemplate="<b>%{y}</b><br>Science: %{x:.1f}<br>Total: %{customdata[0]:.1f}<extra></extra>",
            ))

            fig_ranking.update_layout(
                barmode="stack",
                height=max(700, 30 * len(region_rank)),
                plot_bgcolor="rgba(255,255,255,0)",
                paper_bgcolor="rgba(255,255,255,0)",
                margin=dict(l=20, r=20, t=20, b=20),
                bargap=0.15,
                font=dict(color="#111827"),
                xaxis=dict(
                    title="Total score (Math + Reading + Science)",
                    showgrid=True,
                    gridcolor="rgba(17,24,39,0.08)",
                    zeroline=False,
                ),
                yaxis=dict(title="", autorange="reversed"),
                legend=dict(orientation="h", y=1.05),
            )

            st.plotly_chart(fig_ranking, use_container_width=True)

        else:
            region_data_sorted = region_data.sort_values(selected_score, ascending=False).copy()
            ranking_colors = [
                main_color if c == selected_country else "#D7DCE5"
                for c in region_data_sorted["country"]
            ]

            fig_ranking = go.Figure()
            fig_ranking.add_trace(go.Bar(
                x=region_data_sorted[selected_score],
                y=region_data_sorted["country"],
                orientation="h",
                marker=dict(color=ranking_colors),
                text=region_data_sorted[selected_score].round(1),
                textposition="outside",
                textfont=dict(size=12),
                cliponaxis=False,
                customdata=region_data_sorted[["rank"]],
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    + f"{selected_score_label} score: "
                    + "%{x:.1f}<br>"
                    + "Rank: %{customdata[0]:.0f}<br>"
                    + f"Region: {selected_region}"
                    + "<extra></extra>"
                ),
            ))

            fig_ranking.update_layout(
                height=max(700, 30 * len(region_data_sorted)),
                plot_bgcolor="rgba(255,255,255,0)",
                paper_bgcolor="rgba(255,255,255,0)",
                margin=dict(l=20, r=70, t=20, b=20),
                showlegend=False,
                bargap=0.15,
                font=dict(color="#111827"),
                xaxis=dict(
                    title=f"{selected_score_label} score",
                    showgrid=True,
                    gridcolor="rgba(17,24,39,0.08)",
                    zeroline=False,
                ),
                yaxis=dict(title="", autorange="reversed"),
            )

            st.plotly_chart(fig_ranking, use_container_width=True)

    else:
        if selected_score_label == "All subjects":
            st.info("Rank evolution over time is available for single-subject views only.")
        else:
            rank_history = df_countries[
                (df_countries["region"] == selected_region)
                & (df_countries["country"].notna())
            ][["year", "country", selected_score]].dropna().copy()

            # Compute yearly regional ranks
            rank_history["rank"] = (
                rank_history.groupby("year")[selected_score]
                .rank(ascending=False, method="min")
            )

            # Latest year rank of selected country
            latest_year = rank_history["year"].max()
            latest_ranks = rank_history[rank_history["year"] == latest_year].copy()

            selected_rank_latest = latest_ranks.loc[
                latest_ranks["country"] == selected_country, "rank"
            ].iloc[0]

            # Keep selected country + nearest neighbours in latest ranking
            latest_ranks["distance_to_selected"] = (
                latest_ranks["rank"] - selected_rank_latest
            ).abs()

            peer_countries = latest_ranks.sort_values("distance_to_selected")["country"].head(6).tolist()

            if selected_country not in peer_countries:
                peer_countries.append(selected_country)

            plot_rank_history = rank_history[
                rank_history["country"].isin(peer_countries)
            ].copy()

            fig_rank_trend = go.Figure()

            for country in peer_countries:
                country_df = plot_rank_history[
                    plot_rank_history["country"] == country
                ].sort_values("year")

                if country == selected_country:
                    fig_rank_trend.add_trace(go.Scatter(
                        x=country_df["year"],
                        y=country_df["rank"],
                        mode="lines+markers+text",
                        name=country,
                        line=dict(color="#7030CE", width=4),
                        marker=dict(size=10, color="#7030CE"),
                        text=country_df["rank"].astype(int),
                        textposition="top center",
                        customdata=country_df[selected_score],
                        hovertemplate=(
                            f"<b>{country}</b><br>"
                            + "Year: %{x}<br>"
                            + "Rank: %{y:.0f}<br>"
                            + f"{selected_score_label} score: "
                            + "%{customdata:.1f}<extra></extra>"
                        ),
                    ))
                else:
                    fig_rank_trend.add_trace(go.Scatter(
                        x=country_df["year"],
                        y=country_df["rank"],
                        mode="lines+markers",
                        name=country,
                        line=dict(color="rgba(107,114,128,0.55)", width=2),
                        marker=dict(size=7, color="rgba(107,114,128,0.75)"),
                        customdata=country_df[selected_score],
                        hovertemplate=(
                            f"<b>{country}</b><br>"
                            + "Year: %{x}<br>"
                            + "Rank: %{y:.0f}<br>"
                            + f"{selected_score_label} score: "
                            + "%{customdata:.1f}<extra></extra>"
                        ),
                    ))

            fig_rank_trend.update_layout(
                height=620,
                plot_bgcolor="rgba(255,255,255,0)",
                paper_bgcolor="rgba(255,255,255,0)",
                margin=dict(l=20, r=20, t=20, b=20),
                font=dict(color="#111827"),
                xaxis=dict(
                    title="Year",
                    tickmode="linear",
                    showgrid=False,
                    zeroline=False,
                ),
                yaxis=dict(
                    title="Regional rank",
                    autorange="reversed",
                    showgrid=True,
                    gridcolor="rgba(17,24,39,0.08)",
                    zeroline=False,
                    dtick=1,
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="left",
                    x=0
                ),
            )

            st.plotly_chart(fig_rank_trend, use_container_width=True)

            selected_country_history = plot_rank_history[
                plot_rank_history["country"] == selected_country
            ].sort_values("year")

            first_rank = int(selected_country_history["rank"].iloc[0])
            last_rank = int(selected_country_history["rank"].iloc[-1])

            if last_rank < first_rank:
                rank_text = "improved"
            elif last_rank > first_rank:
                rank_text = "declined"
            else:
                rank_text = "remained stable"

            st.caption(
                f"{selected_country} {rank_text} from rank {first_rank} to rank {last_rank} "
                f"in {selected_region} between {int(selected_country_history['year'].iloc[0])} "
                f"and {int(selected_country_history['year'].iloc[-1])}."
            )

# =========================
# CHART 2 — TRENDS
# =========================
with st.container(border=True):
    st.markdown(f"### {selected_score_label} trends over time")

    # ---- ALL SUBJECTS VIEW ----
    if selected_score_label == "All subjects":
        trend_col, covid_col = st.columns([5, 1.3], gap="large")

        country_trend_all = df_countries[df_countries["country"] == selected_country][
            ["year", "math_score", "reading_score", "science_score", "school_closure_weeks"]
        ].copy()

        with trend_col:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=country_trend_all["year"],
                y=country_trend_all["math_score"],
                mode="lines+markers",
                name="Math",
                line=dict(color=subject_colors["Math"], width=4),
                marker=dict(size=11, color=subject_colors["Math"])
            ))
            fig.add_trace(go.Scatter(
                x=country_trend_all["year"],
                y=country_trend_all["reading_score"],
                mode="lines+markers",
                name="Reading",
                line=dict(color=subject_colors["Reading"], width=4),
                marker=dict(size=11, color=subject_colors["Reading"])
            ))
            fig.add_trace(go.Scatter(
                x=country_trend_all["year"],
                y=country_trend_all["science_score"],
                mode="lines+markers",
                name="Science",
                line=dict(color=subject_colors["Science"], width=4),
                marker=dict(size=11, color=subject_colors["Science"])
            ))

            fig.add_vrect(
                x0=2019,
                x1=2022,
                fillcolor="#FED34C",
                opacity=0.18,
                layer="below",
                line_width=0,
                annotation_text="COVID period",
                annotation_position="top left"
            )

            fig.update_layout(
                height=560,
                plot_bgcolor="rgba(255,255,255,0)",
                paper_bgcolor="rgba(255,255,255,0)",
                margin=dict(l=10, r=10, t=10, b=10),
                font=dict(color="#111827"),
                xaxis=dict(title="Year", showgrid=False),
                yaxis=dict(
                    title="Score",
                    showgrid=True,
                    gridcolor="rgba(17,24,39,0.08)"
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="left",
                    x=0
                )
            )

            st.plotly_chart(fig, use_container_width=True)

            latest = country_trend_all.sort_values("year").iloc[-1]
            best_subject = max(
                [
                    ("Mathematics", latest["math_score"]),
                    ("Reading", latest["reading_score"]),
                    ("Science", latest["science_score"])
                ],
                key=lambda x: x[1]
            )[0]

            st.info(
                f"In **{int(selected_year)}**, **{selected_country}** performs best in **{best_subject.lower()}** among the three PISA domains."
            )

        with covid_col:
            st.markdown(
                """
                <div style="
                    background: rgba(254, 211, 76, 0.20);
                    border: 1px solid rgba(254, 211, 76, 0.45);
                    border-radius: 22px;
                    padding: 20px 18px;
                    box-shadow: 0 10px 24px rgba(0,0,0,0.05);
                    margin-top: 6px;
                    margin-bottom: 14px;
                ">
                    <div style="font-size: 22px; font-weight: 800; color: #111827; margin-bottom: 10px;">
                        COVID impact
                    </div>
                    <div style="font-size: 13px; color: #374151; line-height: 1.55;">
                        Duration of full and partial school closures is shown here as a proxy for pandemic-related disruption.
                        Lower values indicate less educational disruption.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            selected_closure = (
                country_data["school_closure_weeks"].iloc[0]
                if "school_closure_weeks" in country_data.columns else np.nan
            )

            region_closure_mean = (
                region_data["school_closure_weeks"].mean()
                if "school_closure_weeks" in region_data.columns else np.nan
            )

            closure_rank = None
            closure_total = None
            if "school_closure_weeks" in region_data.columns:
                closure_df = region_data[["country", "school_closure_weeks"]].dropna().copy()
                if not closure_df.empty and selected_country in closure_df["country"].values:
                    closure_df["closure_rank"] = closure_df["school_closure_weeks"].rank(
                        ascending=True, method="min"
                    )
                    closure_rank = int(
                        closure_df.loc[
                            closure_df["country"] == selected_country, "closure_rank"
                        ].iloc[0]
                    )
                    closure_total = closure_df["country"].nunique()

            st.metric(
                "School closures",
                f"{selected_closure:.1f} wks" if pd.notna(selected_closure) else "N/A"
            )
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            st.metric(
                "Regional average",
                f"{region_closure_mean:.1f} wks" if pd.notna(region_closure_mean) else "N/A"
            )
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            if closure_rank is not None and closure_total is not None:
                st.metric("Best closure rank", f"{closure_rank} / {closure_total}")

    # ---- SINGLE SUBJECT VIEW ----
    else:
        trend_col, covid_col = st.columns([5, 1.3], gap="large")

        country_trend = (
            df_countries[df_countries["country"] == selected_country]
            [["year", selected_score, "school_closure_weeks"]]
            .dropna(subset=["year", selected_score])
            .copy()
        )

        region_trend = (
            df_countries[df_countries["region"] == selected_region]
            .groupby("year", as_index=False)[selected_score]
            .mean()
        )

        oecd_trend = df_oecd[["year", selected_score]].dropna()

        with trend_col:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=country_trend["year"],
                y=country_trend[selected_score],
                mode="lines+markers",
                name=selected_country,
                line=dict(color=main_color, width=4),
                marker=dict(size=10, color=main_color)
            ))

            fig.add_trace(go.Scatter(
                x=region_trend["year"],
                y=region_trend[selected_score],
                mode="lines+markers",
                name=f"{selected_region} average",
                line=dict(color="#6B7280", width=2.5),
                marker=dict(size=8, color="#6B7280")
            ))

            fig.add_trace(go.Scatter(
                x=oecd_trend["year"],
                y=oecd_trend[selected_score],
                mode="lines+markers",
                name="OECD average",
                line=dict(color="black", dash="dot", width=2),
                marker=dict(size=7, color="black")
            ))

            fig.add_vrect(
                x0=2019,
                x1=2022,
                fillcolor="#FED34C",
                opacity=0.18,
                layer="below",
                line_width=0,
                annotation_text="COVID period",
                annotation_position="top left"
            )

            fig.update_layout(
                height=560,
                plot_bgcolor="rgba(255,255,255,0)",
                paper_bgcolor="rgba(255,255,255,0)",
                margin=dict(l=10, r=10, t=10, b=10),
                font=dict(color="#111827"),
                xaxis=dict(title="Year", showgrid=False),
                yaxis=dict(
                    title=f"{selected_score_label} score",
                    showgrid=True,
                    gridcolor="rgba(17,24,39,0.08)"
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="left",
                    x=0
                )
            )

            st.plotly_chart(fig, use_container_width=True)

            country_trend_sorted = country_trend.sort_values("year")
            if len(country_trend_sorted) >= 2:
                first_year = int(country_trend_sorted["year"].iloc[0])
                last_year = int(country_trend_sorted["year"].iloc[-1])
                first_value = country_trend_sorted[selected_score].iloc[0]
                last_value = country_trend_sorted[selected_score].iloc[-1]
                delta_value = last_value - first_value

                if delta_value > 0:
                    trend_text = "improved"
                elif delta_value < 0:
                    trend_text = "declined"
                else:
                    trend_text = "remained stable"

                st.info(
                    f"From **{first_year}** to **{last_year}**, **{selected_country}** has **{trend_text}** "
                    f"in **{selected_score_label.lower()}**, with a change of **{delta_value:+.1f} points**."
                )

        with covid_col:
            st.markdown(
                """
                <div style="
                    background: rgba(254, 211, 76, 0.20);
                    border: 1px solid rgba(254, 211, 76, 0.45);
                    border-radius: 22px;
                    padding: 20px 18px;
                    box-shadow: 0 10px 24px rgba(0,0,0,0.05);
                    margin-top: 6px;
                    margin-bottom: 14px;
                ">
                    <div style="font-size: 22px; font-weight: 800; color: #111827; margin-bottom: 10px;">
                        COVID impact
                    </div>
                    <div style="font-size: 13px; color: #374151; line-height: 1.55;">
                        Duration of full and partial school closures is shown here as a proxy for pandemic-related disruption.
                        Lower values indicate less educational disruption.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            selected_closure = (
                country_data["school_closure_weeks"].iloc[0]
                if "school_closure_weeks" in country_data.columns else np.nan
            )

            region_closure_mean = (
                region_data["school_closure_weeks"].mean()
                if "school_closure_weeks" in region_data.columns else np.nan
            )

            closure_rank = None
            closure_total = None
            if "school_closure_weeks" in region_data.columns:
                closure_df = region_data[["country", "school_closure_weeks"]].dropna().copy()
                if not closure_df.empty and selected_country in closure_df["country"].values:
                    closure_df["closure_rank"] = closure_df["school_closure_weeks"].rank(
                        ascending=True, method="min"
                    )
                    closure_rank = int(
                        closure_df.loc[
                            closure_df["country"] == selected_country, "closure_rank"
                        ].iloc[0]
                    )
                    closure_total = closure_df["country"].nunique()

            st.metric(
                "School closures",
                f"{selected_closure:.1f} wks" if pd.notna(selected_closure) else "N/A"
            )
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            st.metric(
                "Regional average",
                f"{region_closure_mean:.1f} wks" if pd.notna(region_closure_mean) else "N/A"
            )
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            if closure_rank is not None and closure_total is not None:
                st.metric("Best closure rank", f"{closure_rank} / {closure_total}")

# =========================
# DRIVERS TILE
# =========================
with st.container(border=True):
    st.markdown("### Structural drivers")

    if selected_score_label != "All subjects":
        st.subheader(f"Drivers of {selected_score_label.lower()} performance ({int(selected_year)})")

        scatter_y_min = df_year[selected_score].min()
        scatter_y_max = df_year[selected_score].max()
        scatter_padding = 5

        corr_labels = {
            "math_score": "Math",
            "reading_score": "Reading",
            "science_score": "Science",
            "escs": "ESCS",
            "gdp": "GDP",
            "education_spending": "Spending",
        }

        def make_driver_scatter(data, x_col, x_label):
            plot_data = data.dropna(subset=[x_col, selected_score]).copy()
            if plot_data.empty:
                return None

            fig = px.scatter(
                plot_data,
                x=x_col,
                y=selected_score,
                color="region",
                hover_name="country",
                color_discrete_map=driver_region_colors,
                labels={
                    x_col: x_label,
                    selected_score: f"{selected_score_label} score",
                    "region": "Region",
                },
            )

            for trace in fig.data:
                region_name = trace.name
                region_countries = plot_data.loc[plot_data["region"] == region_name, "country"].tolist()

                marker_sizes = [16 if c == selected_country else 9 for c in region_countries]
                marker_line_widths = [2.5 if c == selected_country else 0 for c in region_countries]
                marker_line_colors = ["#111111" if c == selected_country else "rgba(0,0,0,0)" for c in region_countries]

                trace.update(
                    marker=dict(
                        size=marker_sizes,
                        line=dict(width=marker_line_widths, color=marker_line_colors),
                        opacity=0.82,
                    ),
                    hovertemplate=(
                        "<b>%{hovertext}</b><br>"
                        + f"{x_label}: "
                        + "%{x:,.2f}<br>"
                        + f"{selected_score_label} score: "
                        + "%{y:.1f}<br>"
                        + "Region: %{fullData.name}"
                        + "<extra></extra>"
                    ),
                )

            x = plot_data[x_col].astype(float).values
            y = plot_data[selected_score].astype(float).values

            if len(x) >= 2:
                slope, intercept = np.polyfit(x, y, 1)
                x_line = np.linspace(x.min(), x.max(), 100)
                y_line = slope * x_line + intercept

                y_pred = slope * x + intercept
                ss_res = np.sum((y - y_pred) ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                r2 = 1 - ss_res / ss_tot if ss_tot != 0 else np.nan

                fig.add_scatter(
                    x=x_line,
                    y=y_line,
                    mode="lines",
                    name="Trend",
                    line=dict(color="black", width=2),
                    hovertemplate="Global trend<extra></extra>",
                    showlegend=False,
                )

                fig.add_annotation(
                    x=0.98,
                    y=0.95,
                    xref="paper",
                    yref="paper",
                    text=f"R² = {r2:.2f}",
                    showarrow=False,
                    font=dict(size=12, color="black"),
                    bgcolor="rgba(255,255,255,0.8)",
                )

            if not df_oecd_year.empty:
                oecd_y = df_oecd_year[selected_score].iloc[0] if selected_score in df_oecd_year.columns else None
                oecd_x = df_oecd_year[x_col].iloc[0] if x_col in df_oecd_year.columns else None

                if pd.notna(oecd_y):
                    fig.add_hline(
                        y=oecd_y,
                        line_width=1.5,
                        line_dash="dot",
                        line_color="black",
                        annotation_text=f"OECD avg: {oecd_y:.1f}",
                        annotation_position="bottom right",
                    )

                if pd.notna(oecd_x):
                    fig.add_vline(
                        x=oecd_x,
                        line_width=1.5,
                        line_dash="dot",
                        line_color="black",
                        annotation_text="OECD avg",
                        annotation_position="top left",
                    )

            selected_point = plot_data[plot_data["country"] == selected_country]
            if not selected_point.empty:
                fig.add_annotation(
                    x=selected_point[x_col].iloc[0],
                    y=selected_point[selected_score].iloc[0],
                    text=selected_country,
                    showarrow=True,
                    arrowhead=1,
                    ax=22,
                    ay=-24,
                    font=dict(size=11, color="#111111"),
                    bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="rgba(0,0,0,0.15)",
                    borderwidth=1,
                )

            fig.update_layout(
                height=420,
                plot_bgcolor="rgba(255,255,255,0)",
                paper_bgcolor="rgba(255,255,255,0)",
                margin=dict(l=10, r=10, t=20, b=10),
                font=dict(color="#111827"),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="left",
                    x=0,
                    title=None,
                ),
            )

            fig.update_xaxes(
                showgrid=True,
                gridcolor="rgba(17,24,39,0.08)",
                zeroline=False,
            )

            fig.update_yaxes(
                showgrid=True,
                gridcolor="rgba(17,24,39,0.08)",
                zeroline=False,
                range=[scatter_y_min - scatter_padding, scatter_y_max + scatter_padding],
                title=f"{selected_score_label} score",
            )

            return fig

        corr_vars = [
            "math_score",
            "reading_score",
            "science_score",
            "escs",
            "gdp",
            "education_spending",
        ]

        corr_data = df_year[corr_vars].dropna()
        fig_corr = None

        if not corr_data.empty:
            corr_matrix = corr_data.corr()
            corr_matrix.index = [corr_labels[c] for c in corr_matrix.index]
            corr_matrix.columns = [corr_labels[c] for c in corr_matrix.columns]

            fig_corr = px.imshow(
                corr_matrix,
                text_auto=".2f",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                aspect="auto",
            )

            fig_corr.update_layout(
                height=420,
                plot_bgcolor="rgba(255,255,255,0)",
                paper_bgcolor="rgba(255,255,255,0)",
                margin=dict(l=10, r=10, t=20, b=10),
                coloraxis_colorbar=dict(
                    title="r",
                    thickness=14,
                    len=0.75,
                ),
                font=dict(color="#111827"),
            )

        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)

        with row1_col1:
            st.markdown(f"**{selected_score_label} vs Economic, social and cultural status (ESCS)**")
            fig_escs = make_driver_scatter(df_year, "escs", "Economic, social and cultural status (ESCS)")
            if fig_escs is not None:
                st.plotly_chart(fig_escs, use_container_width=True)
            else:
                st.warning("No data available for ESCS scatterplot.")

        with row1_col2:
            st.markdown(f"**{selected_score_label} vs GDP**")
            fig_gdp = make_driver_scatter(df_year, "gdp", "GDP")
            if fig_gdp is not None:
                st.plotly_chart(fig_gdp, use_container_width=True)
            else:
                st.warning("No data available for GDP scatterplot.")

        with row2_col1:
            st.markdown(f"**{selected_score_label} vs Education spending**")
            fig_spending = make_driver_scatter(df_year, "education_spending", "Education spending")
            if fig_spending is not None:
                st.plotly_chart(fig_spending, use_container_width=True)
            else:
                st.warning("No data available for education spending scatterplot.")

        with row2_col2:
            st.markdown("**Correlation matrix**")
            if fig_corr is not None:
                st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.warning("Not enough data for the correlation matrix.")

        if not corr_data.empty:
            strongest_corr = corr_data.corr()[selected_score].drop(selected_score).abs().idxmax()
            strongest_value = corr_data.corr()[selected_score].drop(selected_score).loc[strongest_corr]
            strongest_label = corr_labels.get(strongest_corr, strongest_corr)
            direction = "positive" if strongest_value > 0 else "negative"

            st.markdown("---")
            st.info(
                f"In {int(selected_year)}, the strongest statistical association with "
                f"{selected_score_label.lower()} performance is **{strongest_label}** "
                f"(r = {strongest_value:.2f}, {direction} relationship). "
                f"This suggests that countries with higher {strongest_label} tend to "
                f"show higher {selected_score_label.lower()} scores."
            )
    else:
        st.info("Select a single subject to unlock detailed drivers analysis.")

# =========================
# GENDER GAP
# =========================
with st.container(border=True):
    st.markdown("### Gender differences")
    st.subheader(f"Gender gap in performance ({int(selected_year)})")

    gender_gap_options = {
        "Mathematics": "gender_gap_math",
        "Reading": "gender_gap_reading",
    }

    gender_gap_label_map = {
        "gender_gap_math": "Gender gap in mathematics (boys - girls)",
        "gender_gap_reading": "Gender gap in reading (boys - girls)",
    }

    selected_gap_label = st.selectbox(
        "Select gender gap metric",
        list(gender_gap_options.keys()),
        key="gender_gap_selectbox"
    )

    selected_gap_col = gender_gap_options[selected_gap_label]

    if selected_gap_col in df_year.columns:
        gap_data = df_year[["country", "region", selected_gap_col]].dropna().copy()

        if not gap_data.empty:
            gap_data = gap_data.sort_values(selected_gap_col, ascending=True)

            gap_colors = []
            for _, row in gap_data.iterrows():
                if row["country"] == selected_country:
                    gap_colors.append("#0024D3" if selected_gap_col == "gender_gap_reading" else "#00B48F")
                elif row[selected_gap_col] > 0:
                    gap_colors.append("#4E79A7")
                else:
                    gap_colors.append("#EA3FCD")

            fig_gap = go.Figure()

            fig_gap.add_trace(go.Bar(
                x=gap_data[selected_gap_col],
                y=gap_data["country"],
                orientation="h",
                marker=dict(color=gap_colors),
                text=gap_data[selected_gap_col].round(1),
                textposition="outside",
                cliponaxis=False,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    + f"{gender_gap_label_map[selected_gap_col]}: "
                    + "%{x:.1f}<br>"
                    + "Positive → boys outperform girls<br>"
                    + "Negative → girls outperform boys"
                    + "<extra></extra>"
                ),
            ))

            fig_gap.add_vline(
                x=0,
                line_width=2,
                line_color="black",
            )

            fig_gap.update_layout(
                height=max(850, 24 * len(gap_data)),
                plot_bgcolor="rgba(255,255,255,0)",
                paper_bgcolor="rgba(255,255,255,0)",
                margin=dict(l=20, r=60, t=20, b=20),
                showlegend=False,
                bargap=0.15,
                font=dict(color="#111827"),
                xaxis=dict(
                    title=gender_gap_label_map[selected_gap_col],
                    showgrid=True,
                    gridcolor="rgba(17,24,39,0.08)",
                    zeroline=False,
                ),
                yaxis=dict(
                    title="",
                    autorange="reversed"
                ),
            )

            st.plotly_chart(fig_gap, use_container_width=True)

            selected_gap_value = gap_data.loc[
                gap_data["country"] == selected_country, selected_gap_col
            ].iloc[0]

            if selected_gap_value > 0:
                gap_text = "boys outperform girls"
            elif selected_gap_value < 0:
                gap_text = "girls outperform boys"
            else:
                gap_text = "boys and girls perform equally"

            st.info(
                f"In **{int(selected_year)}**, for **{selected_gap_label.lower()}**, "
                f"**{gap_text}** in **{selected_country}**, with a gap of **{selected_gap_value:.1f} points**."
            )

            st.caption(
                "Positive values indicate higher scores for boys. Negative values indicate higher scores for girls."
            )
        else:
            st.warning("No gender gap data available for this year.")
    else:
        st.warning("Selected gender gap metric is not available in the dataset.")

# =========================
# RADAR
# =========================
with st.container(border=True):
    st.markdown("### Country comparison")
    st.subheader(f"Radar comparison ({int(selected_year)})")

    rival_country = st.selectbox(
        "Select rival country",
        [c for c in available_countries if c != selected_country],
        key="radar_rival_country"
    )

    radar_vars = [
        "math_score",
        "reading_score",
        "science_score",
        "escs",
        "gdp",
        "education_spending",
        "belonging",
        "teacher_support_math",
    ]

    radar_labels = {
        "math_score": "Math",
        "reading_score": "Reading",
        "science_score": "Science",
        "escs": "ESCS",
        "gdp": "GDP",
        "education_spending": "Spending",
        "belonging": "Belonging",
        "teacher_support_math": "Teacher support",
    }

    radar_data = df_year[df_year["country"].isin([selected_country, rival_country])].copy()
    radar_data = radar_data[["country"] + radar_vars].dropna()

    if radar_data.shape[0] == 2:
        df_norm_base = df_year[radar_vars].copy()
        min_vals = df_norm_base.min()
        max_vals = df_norm_base.max()

        radar_scaled = radar_data.copy()
        for col in radar_vars:
            if max_vals[col] != min_vals[col]:
                radar_scaled[col] = (radar_scaled[col] - min_vals[col]) / (max_vals[col] - min_vals[col])
            else:
                radar_scaled[col] = 0.5

        categories = [radar_labels[v] for v in radar_vars]
        categories_closed = categories + [categories[0]]

        fig_radar = go.Figure()

        selected_values = radar_scaled[
            radar_scaled["country"] == selected_country
        ][radar_vars].values.flatten().tolist()
        selected_values_closed = selected_values + [selected_values[0]]

        rival_values = radar_scaled[
            radar_scaled["country"] == rival_country
        ][radar_vars].values.flatten().tolist()
        rival_values_closed = rival_values + [rival_values[0]]

        fig_radar.add_trace(go.Scatterpolar(
            r=selected_values_closed,
            theta=categories_closed,
            fill="toself",
            name=selected_country,
            line=dict(color="#7030CE", width=4),
            fillcolor="rgba(112, 48, 206, 0.18)"
        ))

        fig_radar.add_trace(go.Scatterpolar(
            r=rival_values_closed,
            theta=categories_closed,
            fill="toself",
            name=rival_country,
            line=dict(color="#FED34C", width=4),
            fillcolor="rgba(254, 211, 76, 0.24)"
        ))

        fig_radar.update_layout(
            height=620,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            polar=dict(
                bgcolor="rgba(255,255,255,0)",
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    showline=False,
                    gridcolor="rgba(17,24,39,0.12)",
                    tickfont=dict(color="#6B7280"),
                ),
                angularaxis=dict(
                    gridcolor="rgba(17,24,39,0.08)",
                    tickfont=dict(size=12, color="#111827"),
                )
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.05,
                xanchor="left",
                x=0,
                bgcolor="rgba(255,255,255,0.75)"
            ),
            margin=dict(l=30, r=30, t=30, b=30),
        )

        st.plotly_chart(fig_radar, use_container_width=True)

        selected_raw = radar_data[radar_data["country"] == selected_country].iloc[0]
        rival_raw = radar_data[radar_data["country"] == rival_country].iloc[0]

        better_dims = []
        for var in radar_vars:
            if selected_raw[var] > rival_raw[var]:
                better_dims.append(radar_labels[var])

        if better_dims:
            shown_dims = ", ".join(better_dims[:3])
            st.info(
                f"In **{int(selected_year)}**, **{selected_country}** outperforms **{rival_country}** on "
                f"**{shown_dims}**."
            )
        else:
            st.info(
                f"In **{int(selected_year)}**, **{rival_country}** matches or exceeds **{selected_country}** on most displayed dimensions."
            )
    else:
        st.warning("Not enough comparable data to build the radar chart for these two countries.")