release: playwright install chromium --with-deps
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --max-requests 100 --max-requests-jitter 10 