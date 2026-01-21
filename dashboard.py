import os
import sqlite3
import pandas as pd
from dash import Dash, dcc, html, dash_table, Input, Output
import plotly.express as px

DB_FILE = "cell_counts.db"

# -------------------------
# Data loading helpers
# -------------------------

def load_relative_frequencies():
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql_query(
            "SELECT * FROM cell_population_frequencies", conn
        )

def load_response_data():
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql_query("""
            SELECT
                f.sample,
                f.population,
                f.percentage,
                c.response,
                c.sex
            FROM cell_population_frequencies f
            JOIN cell_counts_csv c
              ON f.sample = c.sample
            WHERE
                c.treatment = 'miraclib'
                AND c.sample_type = 'PBMC'
                AND c.response IN ('yes', 'no')
        """, conn)

def load_sex_subject_counts():
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql_query("""
            SELECT
                sex,
                COUNT(DISTINCT subject) AS count
            FROM cell_counts_csv
            WHERE
                condition = 'melanoma'
                AND treatment = 'miraclib'
                AND sample_type = 'PBMC'
            GROUP BY sex
        """, conn)

def load_baseline_summary():
    with sqlite3.connect(DB_FILE) as conn:
        samples = pd.read_sql_query("""
            SELECT project, COUNT(*) AS count
            FROM cell_counts_csv
            WHERE
                condition = 'melanoma'
                AND treatment = 'miraclib'
                AND sample_type = 'PBMC'
                AND time_from_treatment_start = 0
            GROUP BY project
        """, conn)

        response = pd.read_sql_query("""
            SELECT response, COUNT(DISTINCT subject) AS count
            FROM cell_counts_csv
            WHERE
                condition = 'melanoma'
                AND treatment = 'miraclib'
                AND sample_type = 'PBMC'
                AND time_from_treatment_start = 0
            GROUP BY response
        """, conn)

        sex = pd.read_sql_query("""
            SELECT sex, COUNT(DISTINCT subject) AS count
            FROM cell_counts_csv
            WHERE
                condition = 'melanoma'
                AND treatment = 'miraclib'
                AND sample_type = 'PBMC'
                AND time_from_treatment_start = 0
            GROUP BY sex
        """, conn)

    return samples, response, sex

# -------------------------
# Load data once
# -------------------------

df_freq = load_relative_frequencies()
df_response = load_response_data()
df_samples, df_response_counts, df_sex_counts = load_baseline_summary()
df_sex_subjects = load_sex_subject_counts()

populations = sorted(df_freq["population"].unique())

# -------------------------
# Dash app
# -------------------------

app = Dash(__name__)
app.title = "Miraclib Immune Response Dashboard"

app.layout = html.Div(
    style={"padding": "20px", "fontFamily": "Arial"},
    children=[
        html.H1("Miraclib Immune Response Dashboard"),
        html.Hr(),

        html.Label("Select immune cell population:"),
        dcc.Dropdown(
            id="population-dropdown",
            options=[{"label": p, "value": p} for p in populations],
            value=populations,
            multi=True
        ),

        html.Br(),

        # -------------------------
        # Responders vs Non-Responders
        # -------------------------
        html.H2("Responders vs Non-Responders (PBMC)"),
        dcc.Graph(id="response-boxplot"),

        html.Hr(),

        # -------------------------
        # Male vs Female SUBJECT COUNTS (FIXED)
        # -------------------------
        html.H2("Male vs Female Subjects (PBMC)"),
        dcc.Graph(
            figure=px.bar(
                df_sex_subjects,
                x="sex",
                y="count",
                title="Male vs Female Subjects",
                labels={"count": "Number of Subjects", "sex": "Sex"}
            )
        ),

        html.Hr(),

        # -------------------------
        # Baseline summaries
        # -------------------------
        html.H2("Baseline Melanoma PBMC Summary"),
        html.Div(
            style={"display": "flex", "gap": "40px"},
            children=[
                dcc.Graph(
                    figure=px.bar(
                        df_samples,
                        x="project",
                        y="count",
                        title="Samples per Project"
                    )
                ),
                dcc.Graph(
                    figure=px.bar(
                        df_response_counts,
                        x="response",
                        y="count",
                        title="Subjects by Response"
                    )
                ),
                dcc.Graph(
                    figure=px.bar(
                        df_sex_counts,
                        x="sex",
                        y="count",
                        title="Subjects by Sex (Baseline)"
                    )
                ),
            ]
        ),

        html.Hr(),

        # -------------------------
        # Table
        # -------------------------
        html.H2("Relative Cell Population Frequencies"),
        dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in df_freq.columns],
            data=df_freq.to_dict("records"),
            page_size=15,
            sort_action="native",
            filter_action="native",
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left"}
        ),
    ]
)

# -------------------------
# Callbacks
# -------------------------

@app.callback(
    Output("response-boxplot", "figure"),
    Input("population-dropdown", "value")
)
def update_response_boxplot(selected_populations):
    filtered = df_response[df_response["population"].isin(selected_populations)]

    fig = px.box(
        filtered,
        x="population",
        y="percentage",
        color="response",
        title="Relative Frequencies by Response",
        labels={
            "percentage": "Relative Frequency",
            "population": "Cell Population"
        }
    )
    fig.update_layout(boxmode="group")
    return fig

# -------------------------
# Run app
# -------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=False, host="0.0.0.0", port=port)

