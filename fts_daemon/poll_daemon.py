'''
Created on Mar 27, 2014

@author: Horacio G. de Oro
'''
import logging
import time


logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    from django.conf import settings
    from fts_web.models import GrupoAtencion
    while True:
        for ga in GrupoAtencion.objects.all():
            print " - {}".format(ga.nombre)
        time.sleep(20)
