FROM python:3.11-alpine

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
# Ensure Python can import packages from src/
ENV PYTHONPATH=/gl1tch-card/src

WORKDIR /gl1tch-card

COPY requirements.txt ./requirements.txt
RUN apk add --no-cache git && pip3 install --no-cache-dir -r requirements.txt

RUN git config --global user.name "gl1tch-bot"
RUN git config --global user.email "41898282+github-actions[bot]@users.noreply.github.com"

COPY src/ ./src/



ENTRYPOINT ["python3", "src/main.py"]
