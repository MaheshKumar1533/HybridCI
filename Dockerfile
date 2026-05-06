FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir pytest pytest-xdist

# No entrypoint because execution_layer.py calls docker run with pytest command directly
