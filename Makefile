fmt:
	black . && ruff format && isort .

lint:
	ruff check

deps:
	pip install -r requirements.txt

run:
	gunicorn main:app -k uvicorn.workers.UvicornWorker