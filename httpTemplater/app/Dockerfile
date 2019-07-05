FROM python:3.7-slim-stretch

WORKDIR /usr/src/app
COPY . .
RUN pip --disable-pip-version-check install --no-cache-dir -r requirements.txt

EXPOSE 8080
