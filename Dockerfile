FROM python:3.8-alpine

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY snyk_npm_test snyk_npm_test

CMD ["hypercorn", "--bind", "0.0.0.0:8000", "snyk_npm_test.api:app"]
