from celery import current_app as current_celery_app

def make_celery(app):
    current_celery_app.conf.update(app.config, namespace='CELERY')
    TaskBase = current_celery_app.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    current_celery_app.Task = ContextTask
    return current_celery_app