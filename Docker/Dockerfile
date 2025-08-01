FROM python:3.12-alpine3.22

# Install build dependencies for compiling Python packages
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers \
    python3-dev \
    && rm -rf /var/cache/apk/*

# Upgrade pip
RUN pip install --upgrade pip

# Install poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Set Python path
ENV PYTHONPATH=/app/src

# Copy only dependency files first (for caching)
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root --without dev

# Copy the rest of the project
COPY config /app/config
COPY src /app/src

# Default command (adjust the path based on your actual main file location)
CMD ["poetry", "run", "python", "src/weather_mcp/main.py"]
