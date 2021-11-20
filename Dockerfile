FROM python:3.8

WORKDIR /home

ENV TELEGRAM_API_TOKEN=
ENV TELEGRAM_ACCESS_ID=

RUN pip install -U pip aiogram
COPY *.py ./

ENTRYPOINT ["python3", "main.py"]
