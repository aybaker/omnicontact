# -*- coding: utf-8 -*-
"""

"""

from __future__ import absolute_import
from __future__ import unicode_literals

from celery import Celery
from django.conf import settings
import logging as _logging


logger = _logging.getLogger('fts_daemon.fts_celery_daemon')

app = Celery('fts_daemon.tasks')

app.config_from_object('django.conf:settings')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.update(
    CELERY_ROUTES={
        'fts_daemon.tasks.finalizar_campana': {
            'queue': 'finalizar_campana'
        },
        'fts_daemon.tasks.esperar_y_finalizar_campana': {
            'queue': 'esperar_y_finalizar_campana'
        },
    },
)

if __name__ == '__main__':
    logger.info("Iniciando Celery daemon...")
    app.start()
