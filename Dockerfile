FROM python:3.11

ENV PYTHONUNBUFFERED=1

RUN pip3 install virtualenv poetry \
  && poetry config virtualenvs.create false

WORKDIR /ash
COPY ./pyproject.toml /ash/pyproject.toml
RUN poetry install --no-interaction --no-ansi

COPY ./ash /ash/ash
CMD ["python", "-m", "ash"]
