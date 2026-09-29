# Atalhos de desenvolvimento. Veja README.md.
#
# Variáveis de backend/.env e frontend/.env são carregadas quando os arquivos existem;
# sem eles, valem os padrões (iguais aos do docker-compose.yml).

SHELL := /bin/bash
VENV := backend/.venv
PY := $(VENV)/bin/python
CARREGAR_ENV_BACKEND := set -a; [ -f backend/.env ] && . backend/.env; set +a
CARREGAR_ENV_FRONTEND := set -a; [ -f frontend/.env ] && . frontend/.env; set +a

.PHONY: db venv backend seed frontend test typecheck reset-db

db:
	docker compose up -d --wait db

venv: $(VENV)/.instalado

$(VENV)/.instalado: backend/requirements.txt
	[ -d $(VENV) ] || python3 -m venv $(VENV)
	$(VENV)/bin/pip install -q -r backend/requirements.txt
	touch $@

backend: db venv
	$(CARREGAR_ENV_BACKEND); cd backend && .venv/bin/python manage.py migrate && .venv/bin/python manage.py runserver 0.0.0.0:8000

seed: db venv
	$(CARREGAR_ENV_BACKEND); cd backend && .venv/bin/python manage.py migrate --no-input && .venv/bin/python manage.py popular_demo

frontend:
	$(CARREGAR_ENV_FRONTEND); cd frontend && npm install && npm run dev

test: db venv
	$(CARREGAR_ENV_BACKEND); cd backend && .venv/bin/pytest

typecheck:
	cd frontend && { [ -d node_modules ] || npm install; } && npm run typecheck

reset-db: db venv
	$(CARREGAR_ENV_BACKEND); cd backend && .venv/bin/python manage.py flush --no-input
