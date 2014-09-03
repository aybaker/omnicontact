# -*- coding: utf-8 -*-

"""
Tests de vistas
"""

from __future__ import unicode_literals

from fts_web.tests.utiles import FTSenderBaseTest
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse


class CampanaCrearTest(FTSenderBaseTest):

    def setUp(self):
        self.user = User.objects.create_user('user', 'user@e.com', 'user')
        self.assertTrue(self.client.login(username='user', password='user'))
        self.campana = self.crear_campana()

    def test_datos_basicos_campana_renderiza_ok(self):
        """...cuando campana esta en definicion"""

        response = self.client.get(reverse('datos_basicos_campana',
                                           args=[self.campana.id]))

        self.assertTemplateUsed(response, "campana/nueva_edita_campana.html")
        self.assertContains(response, self.campana.nombre)

    def test_datos_basicos_campana_lanza_error(self):
        """...cuando campana esta cerrada"""

        self.campana.activar()
        response = self.client.get(reverse('datos_basicos_campana',
                                           args=[self.campana.id]))

        self.assertTemplateUsed(response, "campana/nueva_edita_campana.html")
        self.assertContains(response, self.campana.nombre)
