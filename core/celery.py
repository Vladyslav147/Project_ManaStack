import os
from celery import Celery

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Используем строку здесь, чтобы рабочему процессу не нужно было 
# сериализовать объект конфигурации при использовании Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим задачи (tasks.py) во всех приложениях (apps)
app.autodiscover_tasks()