FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py db.py init_db.py ./

RUN useradd --create-home --uid 10001 appuser
USER appuser
EXPOSE 5000

CMD ["sh", "-c", "python init_db.py && exec gunicorn --workers 2 --bind 0.0.0.0:5000 --access-logfile - app:app"]
