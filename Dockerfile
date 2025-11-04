FROM python:3.14-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y curl 

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY requirements.txt .

RUN uv pip install -r requirements.txt --system

COPY TicketingSystem/ .

EXPOSE 8000

CMD ["python", "manage.py","runserver","0.0.0.0:8000"]