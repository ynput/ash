FROM python:3.10
ENV PYTHONUNBUFFERED=1

RUN pip3 install virtualenv poetry

RUN mkdir /ash
COPY . /ash/
WORKDIR /ash

RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi

CMD ["poetry", "run", "python", "-m", "ash"]

