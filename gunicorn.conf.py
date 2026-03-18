# gunicorn configuration for Render deployment
# Save as gunicorn.conf.py in your project root

bind = "0.0.0.0:8000"
workers = 3
worker_class = "sync"
max_requests = 1000
max_requests_jitter = 50
timeout = 30
loglevel = "info"
accesslog = "-"
errorlog = "-"

# You can adjust workers based on your Render plan
# For Django, use: gunicorn config.wsgi:application --config gunicorn.conf.py
