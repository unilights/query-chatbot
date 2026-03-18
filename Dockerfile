# ── Stage 1: Base image ───────────────────────────────────────────────────────
# We use a slim Python 3.13 image to keep the container small.
FROM python:3.13-slim

# ── Set working directory inside the container ────────────────────────────────
# Everything will live at /app inside the container.
WORKDIR /app

# ── Install dependencies first (layer caching trick) ─────────────────────────
# Copying requirements.txt before the rest of the code means Docker only
# re-installs packages when requirements.txt actually changes — not on every
# code change. This makes rebuilds much faster.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy the application code ─────────────────────────────────────────────────
COPY app.py .
COPY src/ ./src/
COPY data/ ./data/

# ── Streamlit config ──────────────────────────────────────────────────────────
# Tell Streamlit to not open a browser (useless inside a container) and to
# listen on all interfaces so it's reachable from outside the container.
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_PORT=8501

# ── Expose the port Streamlit runs on ─────────────────────────────────────────
EXPOSE 8501

# ── Start command ─────────────────────────────────────────────────────────────
CMD ["streamlit", "run", "app.py"]
