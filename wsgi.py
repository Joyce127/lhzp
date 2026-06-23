"""WSGI 生产入口 — 供 gunicorn 使用"""
from app import create_app

app = create_app()
