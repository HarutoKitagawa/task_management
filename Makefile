migrate-up:
	docker-compose exec backend poetry run alembic upgrade head
migrate-down:
	docker-compose exec backend poetry run alembic downgrade -1
migrate-create:
	@if [ -z "$(name)" ]; then \
		read -p "Enter migration name: " name; \
		docker-compose exec backend poetry run alembic revision --autogenerate -m "$$name"; \
	else \
		docker-compose exec backend poetry run alembic revision --autogenerate -m "$(name)"; \
	fi
migrate-reset:
	@read -p "[WARNING] All tables will be dropped. Are you sure? (Y/n): " confirm; \
	if [ "$$confirm" = "Y" ] || [ "$$confirm" = "y" ] || [ -z "$$confirm" ]; then \
		echo "Dropping all tables..."; \
		docker-compose exec backend poetry run alembic downgrade base; \
	else \
		echo "Operation cancelled."; \
	fi
pytest:
	docker-compose exec backend poetry run pytest