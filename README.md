# NCBI BLAST GUI Application (Docker Ready)

This project is a desktop application with a Graphical User Interface (GUI) for interacting with the NCBI BLAST service. It allows users to submit BLAST searches using a visual interface and view results within the application. This repository is configured to allow easy building and running of the application using Docker.

## Features
- Submit BLAST searches (blastn, blastx) to NCBI.
- Select target databases (nt, nr, est, etc.).
- Input sequence directly into a text area.
- Configure common BLAST parameters (e.g., exclude Landoltia, definition format).
- View search status and results within the GUI.
- GUI remains responsive during long searches due to threaded operations.

## Prerequisites
- **Docker Desktop**: Installed and running on your system (Mac, Windows, or Linux).
- **For macOS users (to see the GUI)**:
    - **XQuartz**: Install from [xquartz.org](https://www.xquartz.org/). After installation, **log out and log back into your Mac or restart your Mac.**
- **For Windows users (to see the GUI)**:
    - An X Server like **VcXsrv** (recommended) or **Xming**. Ensure it's running and configured to allow connections (e.g., by disabling access control during VcXsrv setup).
- **For Linux users (to see the GUI)**:
    - Your desktop environment's X server should work. You'll need to authorize connections from Docker.

## Project Files
- `app.py`: The Python `tkinter` application script.
- `requirements.txt`: Python dependencies (primarily `requests`).
- `Dockerfile`: Instructions to build the Docker image for the application.

## Running the Application with Docker (Step-by-Step)

**Step 1: Get the Code**
Clone this repository to your local machine (if you haven't already).
```bash
# Example:
# git clone <repository-url>
# cd <repository-directory>
```

**Step 2: Build the Docker Image**
Navigate to the root directory of the project (where the `Dockerfile` is located) in your terminal/command prompt and run:
```bash
docker build -t blast-gui-app .
```
This will create a Docker image named `blast-gui-app`. If you pull new changes for `app.py` or other project files from the repository later, you will need to re-run this `docker build` command to update your local image with those changes.

**Step 3: Configure X Server Access (Crucial for GUI Display)**

*   **macOS (XQuartz):**
    1.  **Open XQuartz.**
    2.  In XQuartz Preferences (XQuartz Menu > Preferences > Security), **ensure "Allow connections from network clients" is CHECKED.**
    3.  **Determine Your Mac's IP Address:** Open your regular Mac Terminal and find your IP address (e.g., for Wi-Fi, type `ipconfig getifaddr en0`). Note this IP (e.g., `192.168.1.100`).
    4.  **Allow Docker to Connect to XQuartz:** Open an **XQuartz terminal window** (usually opens with XQuartz, or right-click Dock icon > Applications > Terminal). Type the following, replacing `YOUR_MAC_IP_ADDRESS` with your actual IP:
        ```bash
        xhost + YOUR_MAC_IP_ADDRESS
        ```
        Example: `xhost + 192.168.1.100`
        (Alternatively, for simpler local testing, you can use `xhost +` in the XQuartz terminal, which is less secure as it allows all local connections.)

*   **Linux:**
    In your host terminal, run:
    ```bash
    xhost +
    ```
    (For better security, consider `xhost +local:docker` if your setup supports it easily.)

*   **Windows (VcXsrv):**
    1.  Start VcXsrv.
    2.  During setup (XLaunch), on the "Extra settings" page, **check "Disable access control"**.

**Step 4: Run the Docker Container**

*   **macOS:**
    In your regular Mac Terminal (not XQuartz terminal), run the following, replacing `YOUR_MAC_IP_ADDRESS` with your actual IP:
    ```bash
    docker run -it --rm \
        -e DISPLAY=YOUR_MAC_IP_ADDRESS:0 \
        blast-gui-app
    ```
    Example: `docker run -it --rm -e DISPLAY=192.168.1.100:0 blast-gui-app`

*   **Linux:**
    ```bash
    docker run -it --rm \
        --env="DISPLAY" \
        --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
        blast-gui-app
    ```

*   **Windows (VcXsrv & Docker Desktop):**
    Use `host.docker.internal` to refer to your host machine from the container:
    ```bash
    docker run -it --rm \
        -e DISPLAY=host.docker.internal:0 \
        blast-gui-app
    ```
    (If `host.docker.internal` doesn't work, you may need to use your host's specific IP address on the Docker network.)

**Step 5: Use the Application**
The NCBI BLAST GUI application window should appear on your desktop. You can now input your sequence, select parameters, and run BLAST searches.

**Step 6: Stopping the Application**
- Close the GUI window.
- The Docker container will stop and be removed automatically (due to `--rm`).
- (Optional) For macOS/Linux, you can revoke X server access: `xhost - YOUR_MAC_IP_ADDRESS` or `xhost -` in the XQuartz/host terminal.

## Troubleshooting GUI Display Issues
- **"Cannot open display" / "tkinter.TclError: no display name and no $DISPLAY environment variable"**:
    - Ensure your X Server (XQuartz, VcXsrv, etc.) is running on your host.
    - Double-check the `xhost + ...` command (macOS/Linux) or "Disable access control" (VcXsrv on Windows).
    - Verify the `DISPLAY` environment variable in your `docker run` command is correct for your OS and network setup.
    - For macOS, ensure XQuartz security preferences allow network clients.
    - Restarting XQuartz or even your Mac (after XQuartz install/config) can sometimes help.
```
