FROM python
RUN apt-get update && apt-get install fonts-noto-cjk fonts-noto-color-emoji
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --only main --no-root --no-directory
COPY . .
RUN poetry install --only main
CMD poetry run python -m main.py
