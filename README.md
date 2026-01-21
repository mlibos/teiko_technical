# Cell Analysis for Bob Loblaw (Teiko Technical Takehome)


---

## Repository Overview

The project includes:

- A **relational SQLite database** built from cell-count.csv
- **Analysis scripts** to provide the answers to Part 2: Initial Analysis and Part 3: Statistical Analysis as well as the question: Considering Melanoma males, what is the average number of B cells for responders at time=0? 
- **Saved figures** for boxplots of cell populations of responders vs non-responders
- An **interactive Dash dashboard** for data exploration and sharing, hosted on your own local device after running the script.

---

## Instructions for Running Scripts

### 1. Install the Needed Dependencies
From the repository root:

'''bash
pip install pandas matplotlib plotly dash kaleido scipy

### 2. Build the Database
I've already included the built and loaded sqlite db for this project under cell_counts.db but if you wanted to replicate the process then run the data then simply run: python database_setup.py
This will create the SQLite database cell_counts.db, load the cell-count.csv file into it, create normalized relational tables, a wide CSV-like table, and generate a edrived table of relative immune cell population frequencies. (The script is idempotent and can be rerun!)

### 3. Run Analysis Scripts
Run the analysis scripts by using: python data_analysis.py
This script will output the responder vs non responder comparisons, answer the B-cell count question for male responders, and save an image of boxplots for cell population frequencies.
Output should look like this:

Baseline melanoma PBMC samples (miraclib)
========================================
Total baseline PBMC samples: 656

Samples per project:
  prj1: 384
  prj3: 272

Subjects by response:
  no: 325
  yes: 331

Subjects by sex:
  F: 312
  M: 344

Statistical comparison (Mann–Whitney U test)
------------------------------------------------
b_cell          p = 0.001109
cd4_t_cell      p = 0.0001839
cd8_t_cell      p = 0.7707
monocyte        p = 0.007881
nk_cell         p = 0.4034

Significant populations (p < 0.05):
 - b_cell
 - cd4_t_cell
 - monocyte
Average B-cell count for melanoma male responders with any treatment and from any project at baseline (time=0): 10206.15

### 4. Launch the Dashboard
By running: python dashboard.py and then opening the forwarded port (default is 8050) the dashboard should be loaded. Here's an example screenshot of the dashboard:
<img width="1902" height="906" alt="image" src="https://github.com/user-attachments/assets/0f7c801a-3bea-4df6-b480-d765c73d1ee5" />

## Repository Design and Schema Overview
The database is implemented in SQLite and has the following normalized relational design:
Core Tables:
projects- Stores project-level metadata
subjects- Represents patients-linked to each project
treatments- Normalized treatment names
samples- Individual biological samples
cell_counts- Raw immune cell counts per sample

Wide Table:
cell_counts_csv- One-row-per-sample representation of original CSV

Derived Analytics Table:
cell_population_frequencies- Long-format tables with the relative frequencies of different cells in each sample

## Design Rationale and Scalability
Normalization of the data prevents data duplication and enforces consistency. A wide table allows for easier analytics and visualization workflows, and the derived table allows for decoupling of expensive computations from downstreaam analysis.
The design scales well to hundreds of projects with thousands of samples and subjects, can be expanded to include multiple diseases, treatments, and timepoints, and is suited to handle additional analytics. SQLite can be replaced with mySQL or PostgreSQL for an
online cloud data warehouse server with minimal changes. 

I chose to design the code in this structure because it was the easiest way for me to get a working implementation quickly that I could refine and iterate upon to provide the proper analysis. I chose to use dash by plotly because it is a lightweight framework for generating a simple dashboard quickly using python and SQLite was the natural choice for a serverless SQL language that integrated well into python.

Please let me know if there are any bugs or issues and I will be sure to address them!
Munir Libos Florez

