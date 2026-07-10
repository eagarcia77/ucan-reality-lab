FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN mkdir -p /app/app/data/uploads /app/app/data/scorm /app/app/data/projects \
    && useradd --create-home --uid 10001 ucan \
    && chown -R ucan:ucan /app
USER ucan
EXPOSE 8151
HEALTHCHECK --interval=20s --timeout=8s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8151/api/health', timeout=5)" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8151"]
