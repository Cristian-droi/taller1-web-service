FROM python:3.12-slim

WORKDIR /work

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY read_value_yf.py app.py ./

# Run as a non-root user
RUN useradd --create-home appuser
USER appuser

EXPOSE 5000

# Production WSGI server instead of Flask's development server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "app:app"]
