fmt:
	ruff check --fix && ruff format

lint:
	ruff check

deps-dev:
	pip install -r requirements/dev.txt

run:
	gunicorn main:app -k uvicorn.workers.UvicornWorker