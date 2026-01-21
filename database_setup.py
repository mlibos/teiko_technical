import sqlite3
import csv

DB_FILE = "cell_counts.db"
CSV_FILE = "cell-count.csv"

def initialize_db(conn):
    cursor = conn.cursor()
    # Drop table if it already exists
    cursor.execute("DROP TABLE IF EXISTS projects")
    cursor.execute("DROP TABLE IF EXISTS subjects")
    cursor.execute("DROP TABLE IF EXISTS treatments")
    cursor.execute("DROP TABLE IF EXISTS samples")
    cursor.execute("DROP TABLE IF EXISTS cell_counts")



    cursor.executescript("""
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY,
        project_id INTEGER NOT NULL,
        subject_code TEXT NOT NULL,
        condition TEXT,
        age INTEGER,
        sex TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(id),
        UNIQUE(project_id, subject_code)
    );

    CREATE TABLE IF NOT EXISTS treatments (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS samples (
        id INTEGER PRIMARY KEY,
        subject_id INTEGER NOT NULL,
        treatment_id INTEGER,
        response TEXT,
        sample_code TEXT,
        sample_type TEXT,
        time_from_treatment_start REAL,
        FOREIGN KEY (subject_id) REFERENCES subjects(id),
        FOREIGN KEY (treatment_id) REFERENCES treatments(id)
    );

    CREATE TABLE IF NOT EXISTS cell_counts (
        sample_id INTEGER PRIMARY KEY,
        b_cell REAL,
        cd8_t_cell REAL,
        cd4_t_cell REAL,
        nk_cell REAL,
        monocyte REAL,
        FOREIGN KEY (sample_id) REFERENCES samples(id)
    );
    """)

    conn.commit()
def load_csv(conn, csv_file):
    cursor = conn.cursor()

    with open(csv_file, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Insert project
            cursor.execute(
                "INSERT OR IGNORE INTO projects (name) VALUES (?)",
                (row["project"],)
            )
            cursor.execute(
                "SELECT id FROM projects WHERE name = ?",
                (row["project"],)
            )
            project_id = cursor.fetchone()[0]

            # Insert subject
            cursor.execute("""
                INSERT OR IGNORE INTO subjects
                (project_id, subject_code, condition, age, sex)
                VALUES (?, ?, ?, ?, ?)
            """, (
                project_id,
                row["subject"],
                row["condition"],
                int(row["age"]) if row["age"] else None,
                row["sex"]
            ))

            cursor.execute("""
                SELECT id FROM subjects
                WHERE project_id = ? AND subject_code = ?
            """, (project_id, row["subject"]))
            subject_id = cursor.fetchone()[0]

            # Insert treatment
            cursor.execute(
                "INSERT OR IGNORE INTO treatments (name) VALUES (?)",
                (row["treatment"],)
            )
            cursor.execute(
                "SELECT id FROM treatments WHERE name = ?",
                (row["treatment"],)
            )
            treatment_id = cursor.fetchone()[0]

            # Insert sample
            cursor.execute("""
                INSERT INTO samples
                (subject_id, treatment_id, response, sample_code,
                 sample_type, time_from_treatment_start)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                subject_id,
                treatment_id,
                row["response"],
                row["sample"],
                row["sample_type"],
                float(row["time_from_treatment_start"])
                if row["time_from_treatment_start"] else None
            ))

            sample_id = cursor.lastrowid

            # Insert cell counts
            cursor.execute("""
                INSERT INTO cell_counts
                (sample_id, b_cell, cd8_t_cell, cd4_t_cell, nk_cell, monocyte)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sample_id,
                float(row["b_cell"]) if row["b_cell"] else None,
                float(row["cd8_t_cell"]) if row["cd8_t_cell"] else None,
                float(row["cd4_t_cell"]) if row["cd4_t_cell"] else None,
                float(row["nk_cell"]) if row["nk_cell"] else None,
                float(row["monocyte"]) if row["monocyte"] else None
            ))

    conn.commit()

def wide_table(conn):
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS cell_counts_csv")

    cursor.execute("""
    CREATE TABLE cell_counts_csv (
        project TEXT,
        subject TEXT,
        condition TEXT,
        age INTEGER,
        sex TEXT,
        treatment TEXT,
        response TEXT,
        sample TEXT,
        sample_type TEXT,
        time_from_treatment_start REAL,
        b_cell REAL,
        cd8_t_cell REAL,
        cd4_t_cell REAL,
        nk_cell REAL,
        monocyte REAL
    )
    """)

    with open("cell-count.csv", newline="") as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for row in reader:
            cursor.execute("""
                INSERT INTO cell_counts_csv VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                row[0], row[1], row[2],
                int(row[3]) if row[3] else None,
                row[4], row[5], row[6], row[7], row[8],
                float(row[9]) if row[9] else None,
                float(row[10]) if row[10] else None,
                float(row[11]) if row[11] else None,
                float(row[12]) if row[12] else None,
                float(row[13]) if row[13] else None,
                float(row[14]) if row[14] else None
            ))

    conn.commit()


def relative_cell_pops(conn):
    cursor = conn.cursor()

    # Drop table if it already exists
    cursor.execute("DROP TABLE IF EXISTS cell_population_frequencies")

    # Create and populate the table
    cursor.execute("""
    CREATE TABLE cell_population_frequencies AS
    WITH totals AS (
        SELECT
            sample,
            (b_cell + cd8_t_cell + cd4_t_cell + nk_cell + monocyte) AS total_count,
            b_cell,
            cd8_t_cell,
            cd4_t_cell,
            nk_cell,
            monocyte
        FROM cell_counts_csv
    )
    SELECT
        sample,
        total_count,
        'b_cell' AS population,
        b_cell AS count,
        (b_cell / total_count) AS percentage
    FROM totals

    UNION ALL

    SELECT
        sample,
        total_count,
        'cd8_t_cell',
        cd8_t_cell,
        (cd8_t_cell / total_count)
    FROM totals

    UNION ALL

    SELECT
        sample,
        total_count,
        'cd4_t_cell',
        cd4_t_cell,
        (cd4_t_cell / total_count)
    FROM totals

    UNION ALL

    SELECT
        sample,
        total_count,
        'nk_cell',
        nk_cell,
        (nk_cell / total_count)
    FROM totals

    UNION ALL

    SELECT
        sample,
        total_count,
        'monocyte',
        monocyte,
        (monocyte / total_count)
    FROM totals
    """)

    conn.commit()
    return cursor

def print_relative_cell_summary(conn, limit=20):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            sample,
            population,
            count,
            ROUND(percentage, 2) AS percentage
        FROM cell_population_frequencies
        ORDER BY sample, population
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    print(f"{'Sample':<15} {'Population':<15} {'Count':>8} {'%':>8}")
    print("-" * 50)

    for sample, population, count, pct in rows:
        print(f"{sample:<15} {population:<15} {count:>8} {pct:>7.2f}")

def main():
    with sqlite3.connect(DB_FILE, timeout=30) as conn:
        initialize_db(conn)
        load_csv(conn, CSV_FILE)
        wide_row = wide_table(conn)
        relative_cell_pops(conn)
        print_relative_cell_summary(conn)


if __name__ == "__main__":
    main()
