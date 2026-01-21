import sqlite3
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu
from collections import defaultdict


DB_FILE = "cell_counts.db"


def fetch_response_data(conn):
    """
    Returns:
        dict[cell_population] = {
            "yes": [percentages],
            "no":  [percentages]
        }
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            f.population,
            c.response,
            f.percentage
        FROM cell_population_frequencies f
        JOIN cell_counts_csv c
          ON f.sample = c.sample
        WHERE
            c.treatment = 'miraclib'
            AND c.sample_type = 'PBMC'
            AND c.response IN ('yes', 'no')
    """)

    data = defaultdict(lambda: {"yes": [], "no": []})

    for population, response, percentage in cursor.fetchall():
        data[population][response].append(percentage)

    return data


def plot_boxplots(data):
    populations = sorted(data.keys())

    responder_data = [data[p]["yes"] for p in populations]
    non_responder_data = [data[p]["no"] for p in populations]

    fig, ax = plt.subplots(figsize=(10, 6))

    positions_yes = [i * 2 for i in range(len(populations))]
    positions_no = [i * 2 + 0.8 for i in range(len(populations))]

    ax.boxplot(
        responder_data,
        positions=positions_yes,
        widths=0.6,
        patch_artist=True,
        boxprops=dict(facecolor="lightblue"),
        medianprops=dict(color="black")
    )

    ax.boxplot(
        non_responder_data,
        positions=positions_no,
        widths=0.6,
        patch_artist=True,
        boxprops=dict(facecolor="salmon"),
        medianprops=dict(color="black")
    )

    ax.set_xticks([i * 2 + 0.4 for i in range(len(populations))])
    ax.set_xticklabels(populations, rotation=45)
    ax.set_ylabel("Relative Frequency")
    ax.set_title("Immune Cell Relative Frequencies\nResponders vs Non-Responders (PBMC, Miraclib)")

    ax.legend(
        handles=[
            plt.Line2D([0], [0], color="lightblue", lw=6, label="Responders"),
            plt.Line2D([0], [0], color="salmon", lw=6, label="Non-Responders"),
        ],
        loc="upper right"
    )

    plt.tight_layout()
    fig.savefig("responders_vs_nonresponders_cell_pops.png", dpi=300)
    plt.close(fig)

def statistical_tests(data):
    print("\nStatistical comparison (Mann–Whitney U test)")
    print("------------------------------------------------")

    significant = []

    for population, groups in data.items():
        responders = groups["yes"]
        non_responders = groups["no"]

        if len(responders) < 3 or len(non_responders) < 3:
            continue  # not enough data

        stat, p_value = mannwhitneyu(
            responders, non_responders, alternative="two-sided"
        )

        print(f"{population:<15} p = {p_value:.4g}")

        if p_value < 0.05:
            significant.append(population)

    print("\nSignificant populations (p < 0.05):")
    if significant:
        for pop in significant:
            print(f" - {pop}")
    else:
        print(" None")
import sqlite3

DB_FILE = "cell_counts.db"


def baseline_melanoma_pbmc_summary(conn):
    cursor = conn.cursor()

    print("\nBaseline melanoma PBMC samples (miraclib)")
    print("========================================")

    # A. Total samples
    cursor.execute("""
        SELECT COUNT(*)
        FROM cell_counts_csv
        WHERE
            condition = 'melanoma'
            AND treatment = 'miraclib'
            AND sample_type = 'PBMC'
            AND time_from_treatment_start = 0
    """)
    total_samples = cursor.fetchone()[0]
    print(f"Total baseline PBMC samples: {total_samples}")

    # B. Samples per project
    print("\nSamples per project:")
    cursor.execute("""
        SELECT project, COUNT(*) AS n
        FROM cell_counts_csv
        WHERE
            condition = 'melanoma'
            AND treatment = 'miraclib'
            AND sample_type = 'PBMC'
            AND time_from_treatment_start = 0
        GROUP BY project
    """)
    for project, n in cursor.fetchall():
        print(f"  {project}: {n}")

    # C. Subjects by response
    print("\nSubjects by response:")
    cursor.execute("""
        SELECT response, COUNT(DISTINCT subject) AS n
        FROM cell_counts_csv
        WHERE
            condition = 'melanoma'
            AND treatment = 'miraclib'
            AND sample_type = 'PBMC'
            AND time_from_treatment_start = 0
        GROUP BY response
    """)
    for response, n in cursor.fetchall():
        print(f"  {response}: {n}")

    # D. Subjects by sex
    print("\nSubjects by sex:")
    cursor.execute("""
        SELECT sex, COUNT(DISTINCT subject) AS n
        FROM cell_counts_csv
        WHERE
            condition = 'melanoma'
            AND treatment = 'miraclib'
            AND sample_type = 'PBMC'
            AND time_from_treatment_start = 0
        GROUP BY sex
    """)
    for sex, n in cursor.fetchall():
        print(f"  {sex}: {n}")

def avg_b_cells_male_responders_baseline():
    """
    Considering melanoma males, compute the average number of B cells
    for responders at baseline (time_from_treatment_start = 0),
    using PBMC samples treated with miraclib.
    """

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                AVG(b_cell) AS avg_b_cells
            FROM cell_counts_csv
            WHERE
                condition = 'melanoma'
                AND sex = 'M'
                AND response = 'yes'
                AND time_from_treatment_start = 0
                AND b_cell IS NOT NULL
        """)

        result = cursor.fetchone()
        return result[0]

def main():
    with sqlite3.connect(DB_FILE) as conn:
        data = fetch_response_data(conn)
        baseline_melanoma_pbmc_summary(conn)
    statistical_tests(data)
    plot_boxplots(data)
    avg_b = avg_b_cells_male_responders_baseline()

    if avg_b is None:
        print(
            "No baseline PBMC samples found for melanoma male responders "
            "treated with miraclib."
        )
    else:
        print(
            f"Average B-cell count for melanoma male responders "
            f"at baseline (time=0): {avg_b:.2f}"
        )


if __name__ == "__main__":
    main()
