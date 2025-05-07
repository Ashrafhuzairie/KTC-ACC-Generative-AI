# FROM python:3.10-slim-buster

# WORKDIR /app

# COPY . /app

# RUN pip install -r requirements.txt

# CMD ["python3", "app.py"]


# Use Python 3.10 slim image
FROM python:3.10-slim-buster

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose port 8080 to match your Flask app
EXPOSE 8080

# Set environment variable to ensure Flask binds correctly
ENV PYTHONUNBUFFERED=1

# Run the Flask app
CMD ["python3", "app.py"]
