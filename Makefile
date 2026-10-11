.PHONY: up down reset bootstrap test e2e build-plugin lint

up:
	docker compose up --build -d

down:
	docker compose down

reset:
	docker compose down -v
	docker compose up --build -d

bootstrap:
	docker compose run --rm superset-bootstrap

build-plugin:
	cd packages/superset-jalali-datefilter/frontend && npm ci && npm run gen && npm test && npm run build

test:
	python -m pytest packages/superset-jalali-sql/tests packages/superset-jalali-datefilter/tests host-app/tests -q

e2e:
	cd tests/e2e && npm ci && npx playwright test

lint:
	ruff check packages bootstrap host-app tests docker/superset/superset_config.py
	cd packages/superset-jalali-datefilter/frontend && npx tsc --noEmit
