# Use the official Python base image
FROM python:3.12

# Set the working directory
WORKDIR /app

# Copy application code into the container
COPY . /app
# Upgrade pip to the latest version
RUN python -m pip install --upgrade pip
# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the entry point to your application
CMD ["python", "test.py"]
