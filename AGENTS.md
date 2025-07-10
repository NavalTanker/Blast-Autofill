## Agent Instructions for NCBI BLAST GUI Application

- The primary goal is to develop a functional GUI application in `app.py` using `tkinter`.
- Ensure NCBI API calls are handled in a non-blocking way (e.g., using threads) to keep the GUI responsive.
- Provide clear user feedback within the GUI for all operations (submission, status, errors, results).
- Focus on usability for the GUI elements.
- `requests` library is used for HTTP calls. `tkinter` is used for the GUI.
- All necessary BLAST logic (submission, status check, results fetching, parsing) will be consolidated into `app.py`.
- Ensure graceful error handling for API issues or unexpected responses.
- Code should be well-commented, especially the GUI event handling and threading parts.
