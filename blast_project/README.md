# BLAST Search Project

This script submits a DNA sequence to NCBI BLAST, retrieves the results, and processes them.

## Prerequisites

- Python 3
- `requests` library

## Setup

1.  **Clone the repository (or download the files).**
2.  **Navigate to the `blast_project` directory:**
    ```bash
    cd blast_project
    ```
3.  **Install dependencies:**
    Create a virtual environment (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
    Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Script

To run the BLAST search and analysis:

```bash
python main.py
```

The script will first prompt you to:
1.  **Select the BLAST program**: Enter `blastn` or `blastx`.
2.  **Select the database** (if `blastn` was chosen): Enter `est` or `nr/nt`. If `blastx` was chosen, the `nr` database is automatically used.

Then, the script will:
1. Submit a predefined DNA sequence to the NCBI BLAST service using your selected program and database.
2. Periodically check the status of the search.
3. Once the search is complete, retrieve the results in XML format.
4. Parse these results to extract initial hit information.
5. Fetch detailed GenBank data (full Definition and Organism) for each hit.
6. Filter out results where the organism is "Landoltia punctata".
7. Print the top 3 final results (excluding "Landoltia punctata") in a table format, including the full definition.

### Output
The script will print status updates to the console, including the RID (Request ID) of the BLAST search, current search status, processing steps, and finally, the formatted table of results.

### Customization
- **DNA Sequence**: You can change the `dna_sequence` variable in `main.py` to your sequence of interest.
- **Number of Results**: The script aims to find 3 results after filtering. This can be adjusted by changing the condition `if len(final_results) >= 3:` and the slicing `initial_hits[:20]` if more initial hits need to be processed.

## Note
- The script interacts with NCBI servers. Please be mindful of their usage policies and avoid sending too many requests in a short period. The script includes `time.sleep(1)` calls between NCBI requests to be respectful.
- Internet connectivity is required to run the script.
