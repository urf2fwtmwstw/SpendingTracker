FROM python:3.11-slim

WORKDIR /app

# Install dependencies needed by the project and Makefile
RUN apt-get update && \
    apt-get install -y --no-install-recommends make openssl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Generate RSA keys as defined in the Makefile payload
RUN make generate_RSA_keys

# Create a startup script to run migrations and then start the app
RUN echo '#!/bin/bash\n\
set -e\n\
alembic upgrade head\n\
exec uvicorn main:app --host 0.0.0.0 --port 8000\n\
' > /app/run.sh && chmod +x /app/run.sh

# Expose the application port
EXPOSE 8000

# Run the startup script
CMD ["/app/run.sh"]
