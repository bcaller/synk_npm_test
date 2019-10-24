docker build -f Dockerfile.test -t snyk-api-test . && \
docker run --rm snyk-api-test
