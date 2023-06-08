FROM python:3.10
ENV PYTHONUNBUFFERED=1

RUN pip3 install virtualenv poetry

WORKDIR /ash
COPY ./pyproject.toml /ash/pyproject.toml

RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi

COPY . /ash/
CMD ["python", "-m", "ash"]

