FROM python:3.11.8-slim-bullseye

ENV PYTHONUNBUFFERED True

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

ENV PORT 8000

RUN pip install --no-cache-dir -r requirements.txt

# As an example here we're running the web service with one worker on uvicorn.
CMD exec uvicorn server:app --host 0.0.0.0 --port ${PORT} --workers 1