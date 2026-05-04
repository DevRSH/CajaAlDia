#!/usr/bin/env bash
# Backend de desarrollo en 8001 para no pisar otros servicios en 8000.
cd "$(dirname "$0")"
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
