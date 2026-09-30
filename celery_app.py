from celery import Celery
from flask import current_app
import os

def make_celery(app=None):
    """Create Celery instance with Flask app context"""
    if app is None:
        from app import create_app
        app = create_app()
    
    celery = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/3'),
        broker=app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/2'),
        include=[
            'tasks.email_tasks',
            'tasks.notification_tasks',
            'tasks.payment_tasks',
            'tasks.game_tasks',
            'tasks.cleanup_tasks'
        ]
    )
    
    # Update Celery config from Flask config
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        beat_schedule={
            'cleanup-expired-sessions': {
                'task': 'tasks.cleanup_tasks.cleanup_expired_sessions',
                'schedule': 3600.0,  # Every hour
            },
            'process-withdrawals': {
                'task': 'tasks.payment_tasks.process_pending_withdrawals',
                'schedule': 300.0,  # Every 5 minutes
            },
            'send-daily-reports': {
                'task': 'tasks.notification_tasks.send_daily_reports',
                'schedule': 86400.0,  # Daily at midnight
            },
            'check-kyc-expiry': {
                'task': 'tasks.cleanup_tasks.check_kyc_expiry',
                'schedule': 86400.0,  # Daily
            },
            'generate-daily-stats': {
                'task': 'tasks.game_tasks.generate_daily_stats',
                'schedule': 86400.0,  # Daily at midnight
            },
        }
    )
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Create celery instance for import
celery = make_celery()

if __name__ == '__main__':
    celery.start()