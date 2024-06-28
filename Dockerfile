# Stage 1: Build environment with virtual environment
FROM python:3.9-slim AS build-env 

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
RUN pip install --upgrade pip

# Install project dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the entire project into the build environment
WORKDIR /app
COPY . .

RUN chmod +x main.py

# Stage 2: Final minimal image with distroless base
# FROM gcr.io/distroless/python3-debian10
FROM python:3.9-slim 

# Copy the virtual environment from the build environment
COPY --from=build-env /venv /venv
ENV PATH="/venv/bin:$PATH"

# Set the working directory to the project directory
WORKDIR /app

# Copy the entire project from the build environment
COPY --from=build-env /app /app

# Set the entrypoint command to run your Python script
CMD ["python", "/app/main.py"]
