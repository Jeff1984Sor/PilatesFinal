dev:
	@echo "Run Django and FastAPI in separate terminals:"
	@echo "python backend/manage.py runserver"
	@echo "uvicorn api.main:app --reload"

migrate:
	python backend/manage.py migrate

test:
	pytest
