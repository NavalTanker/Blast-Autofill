# NCBI BLAST GUI Application

This project is a desktop application with a Graphical User Interface (GUI) for interacting with the NCBI BLAST service. It allows users to submit BLAST searches using a visual interface and view results within the application.

## Features
- Submit BLAST searches (blastn, blastx) to NCBI.
- Select target databases (nt, nr, est, etc.).
- Input sequence directly into a text area.
- Configure common BLAST parameters (e.g., exclude Landoltia, definition format).
- View search status and results within the GUI.

## Running the Application

1.  **Clone the repository (if you haven't already):**
    ```bash
    # git clone <repository-url>
    # cd <repository-name>
    ```
    (Replace with actual clone commands when repository is available)

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate   # On Windows
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    (`tkinter` is part of Python's standard library. `requests` is used for NCBI API calls.)

4.  **Run the application:**
    ```bash
    python app.py
    ```
    This will launch the GUI window.

## Development
This application is built using Python and `tkinter` for the GUI. All core logic is contained within `app.py`.

(Further development notes, if any, can be added here.)
