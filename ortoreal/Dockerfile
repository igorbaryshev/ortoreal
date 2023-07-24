FROM python:3.11-slim-bullseye

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

ENV LANG ru_RU.UTF-8

ENV LC_ALL ru_RU.UTF-8 

CMD ["gunicorn", "--bind", "0:8000", "ortoreal.wsgi"]
