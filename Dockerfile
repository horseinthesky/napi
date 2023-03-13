FROM mwalbeck/python-poetry:1.4-3.11 as deps
COPY pyproject.toml .
RUN : \
  && poetry config virtualenvs.create false \
  && poetry export --without-hashes --format requirements.txt --output requirements.txt \
  && pip install \
    --no-cache-dir \
    --disable-pip-version-check \
    --root-user-action=ignore \
    -r requirements.txt -t ./bundle/

FROM python:3.11.2-slim-bullseye
ENV HOST=:: PORT=8080
COPY --from=deps /bundle/ /usr/local/lib/python3.11/site-packages/
WORKDIR /app
COPY . .
ENTRYPOINT ["sh", "-c", "/usr/local/lib/python3.11/site-packages/bin/uvicorn napi_server:app --host $HOST --port $PORT --workers $(nproc)" ]
