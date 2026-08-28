# 3 workers x 4 threads = 12 concurrent requests. The bare `gunicorn app:app` this
# replaced ran a single sync worker, i.e. one request at a time.
# Pool math: 3 workers x (DB_POOL_SIZE 5 + DB_MAX_OVERFLOW 5) = 30 connections.
web: gunicorn app:app --worker-class gthread --workers 3 --threads 4 --timeout 60 --access-logfile -
