FROM python:3

RUN mkdir /app/
WORKDIR /app/

ADD requirements.txt /app/
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED True

ADD . /app/

CMD python podbook.py
