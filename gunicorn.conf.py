"""gunicorn 生产配置"""

import multiprocessing

bind = "0.0.0.0:8080"
workers = multiprocessing.cpu_count()  # Apple Silicon M 系列约 8-10 个
threads = 2
worker_class = "sync"
timeout = 120
keepalive = 5

# 日志
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"

# 进程命名
proc_name = "lhzp-app"

# 优雅重启
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 50

# 生产安全
preload_app = True
