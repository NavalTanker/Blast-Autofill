# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install tkinter, tcl for GUI, and ca-certificates for HTTPS requests
RUN apt-get update && apt-get install -y \
    tk \
    tcl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents (which includes app.py) into the container at /usr/src/app
COPY app.py .
# If there were other assets like images or config files needed by app.py, they'd be copied too.
# For this project, app.py is self-contained with requirements.txt.

# Define environment variable for X display forwarding (can be overridden at runtime)
ENV DISPLAY=:0

# Command to run the application
CMD ["python", "./app.py"]
