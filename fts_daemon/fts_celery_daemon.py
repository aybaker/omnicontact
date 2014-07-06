# -*- coding: utf-8 -*-
"""

"""

from __future__ import absolute_import
from __future__ import unicode_literals

from celery import Celery
import logging as _logging


logger = _logging.getLogger('fts_celery_daemon')

app = Celery('fts_daemon.fts_celery',
             broker='redis://localhost',
             include=['fts_daemon.fts_celery'])


# Optional configuration, see the application user guide.
app.conf.update(
    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_RESULT_SERIALIZER='json',
    CELERY_ROUTES={
        'fts_daemon.fts_celery.finalizar_campana': {
            'queue': 'finalizar_campana'
        },
    },
)

if __name__ == '__main__':
    logger.info("Iniciando Celery daemon...")
    app.start()
