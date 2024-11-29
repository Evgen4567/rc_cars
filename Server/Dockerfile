ARG PYTHON_VERSION=3.13

FROM acidrain/python-poetry:${PYTHON_VERSION}-alpine AS poetry
WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.in-project true \
  && poetry config virtualenvs.create true
RUN poetry install --no-root

FROM python:${PYTHON_VERSION}-alpine
WORKDIR /app
COPY --from=poetry /app/.venv /app/.venv
COPY src/ /app/src
COPY client.html /app/client.html
ENV \
  PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
ENTRYPOINT ["python"]
CMD ["-m", "src"]
