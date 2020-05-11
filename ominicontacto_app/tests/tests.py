# -*- coding: utf-8 -*-
# Copyright (C) 2018 Freetech Solutions

# This file is part of OMniLeads

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#

# Tests de integración (no usar en un entorno de producción de un cliente!!)

# tener en cuenta que las credenciales del agente que se va a testar deben estar igualmente
# especificadas en las variables  de entorno AGENTE_USERNAME y AGENTE_PASSWORD; además este agente
# debe estar asignado al menos a una campaña
# Por otra parte las credenciales del admin deberan estar especificadas en las variables de entorno
# ADMIN_USERNAME y ADMIN_PASSWORD

# Prerequisitos:
# 1) Chrome (o Chromium) 76 instalado, tarjeta de audio presente en el host
# 2) chromedriver desde
# "https://chromedriver.storage.googleapis.com/76.0.3809.68/chromedriver_linux64.zip"

# 3) instalar selenium y copiar el geckodriver en /usr/bin del host donde corre omniapp

# 4) Instalar xvfb y pyvirtualdisplay
# sudo apk add xvfb
# pip install pyvirtualdisplay --user

# 3) Probar este codigo como punto de partida hacia un server sin DJANGO_DEBUG_TOOLBAR

# 4)Para testear los tests de integración:
# "$TESTS_INTEGRACION='True' LOGIN_FAILURE_LIMIT=10 python ominicontacto_app/tests/tests.py"
# Para los que necesitan audio en el browser, agregar "$BROWSER_REAL='True'"

from __future__ import unicode_literals

import os
import socket
import unittest
import uuid
import random

from time import sleep

try:
    from pyvirtualdisplay import Display
    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options
except ImportError:
    pass

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
USER = os.getenv('USER')

CAMPANA_MANUAL = os.getenv('CAMPANA_MANUAL')

AGENTE_USERNAME = 'agente' + uuid.uuid4().hex[:5]
AGENTE_PASSWORD = '098098ZZZ'

BROWSER_REAL = os.getenv('BROWSER_REAL')
TESTS_INTEGRACION = os.getenv('TESTS_INTEGRACION')
LOGIN_FAILURE_LIMIT = int(os.getenv('LOGIN_FAILURE_LIMIT'))

MSG_MICROFONO = 'Se necesita un browser real con micrófono'

TESTS_INTEGRACION_HOSTNAME = os.getenv('TESTS_INTEGRACION_HOSTNAME')
if not TESTS_INTEGRACION_HOSTNAME:
    TESTS_INTEGRACION_HOSTNAME = socket.gethostname()


@unittest.skipIf(TESTS_INTEGRACION != 'True', 'Ignorando tests de integración')
class IntegrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # super(IntegrationTests, cls).setUpClass()
        cls.setUp()
        cls._login(ADMIN_USERNAME, ADMIN_PASSWORD)
        group_name = 'group' + uuid.uuid4().hex[:5]
        cls.crear_grupo(group_name)
        cls.crear_agente(AGENTE_USERNAME, AGENTE_PASSWORD)
        if BROWSER_REAL == 'True':
            cls.asignar_agente_campana_manual()
        cls.tearDown()

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument('--use-fake-ui-for-media-stream')
        chrome_options.add_argument('--use-fake-device-for-media-stream')
        chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en'})
        chrome_options.add_argument('--ignore-certificate-errors')
        # si se pone visible=1 se muestra el browser en medio de los tests
        self.display = Display(visible=1, size=(1366, 768))
        self.display.start()
        self.browser = webdriver.Chrome(options=chrome_options)

    @classmethod
    def tearDown(self):
        self.browser.close()
        self.display.stop()

    @classmethod
    def _login(self, username, password):
        self.browser.get('https://{0}'.format(TESTS_INTEGRACION_HOSTNAME))
        self.browser.find_element_by_name('username').send_keys(username)
        self.browser.find_element_by_name('password').send_keys(password)
        self.browser.find_element_by_tag_name('button').click()
        sleep(2)

    def get_href(self, href):
        link = self.browser.find_element_by_xpath(href)
        href = link.get_attribute('href')
        self.browser.get(href)

    @classmethod
    def asignar_agente_campana_manual(self):
        list_manual_href = self.browser.find_element_by_xpath(
            '//a[contains(@href,"/campana_manual/lista/")]')
        href_manual = list_manual_href.get_attribute('href')
        self.browser.get(href_manual)
        link_add_agent = self.browser.find_element_by_xpath(
            '//tr[@id=\'{0}\']/td/div//a[contains(@href, "/queue_member/")]'.format(CAMPANA_MANUAL))
        href_add_agent = link_add_agent.get_attribute('href')
        self.browser.get(href_add_agent)
        self.browser.find_element_by_xpath('//select/option[contains(text(), \'{0}\')]'
                                           .format(AGENTE_USERNAME)).click()
        self.browser.find_element_by_xpath((
            "//button[@id='id_guardar']")).click()
        sleep(1)

    @classmethod
    def crear_agente(self, username, password):
        link_create_user = self.browser.find_element_by_id('newUser')
        href_create_user = link_create_user.get_attribute('href')
        self.browser.get(href_create_user)
        self.browser.find_element_by_id('id_0-username').send_keys(username)
        self.browser.find_element_by_id('id_0-first_name').send_keys(username)
        self.browser.find_element_by_id('id_0-password1').send_keys(password)
        self.browser.find_element_by_id('id_0-password2').send_keys(password)
        self.browser.find_element_by_id('id_0-is_agente').click()
        self.browser.find_element_by_xpath('//form[@id=\'wizardForm\']/button').click()
        sleep(1)
        self.browser.find_elements_by_xpath('//select[@id=\'id_2-grupo\']/option')[1].click()
        self.browser.find_elements_by_xpath('//form[@id=\'wizardForm\']/button')[2].click()
        sleep(1)

    @classmethod
    def crear_grupo(self, group_name):
        link_create_group = self.browser.find_element_by_xpath(
            '//a[contains(@href,"/grupo/nuevo")]')
        href_create_group = link_create_group.get_attribute('href')
        self.browser.get(href_create_group)
        self.browser.find_element_by_id('id_nombre').send_keys(group_name)
        self.browser.find_element_by_id('id_auto_attend_inbound').click()
        self.browser.find_element_by_id('id_auto_attend_dialer').click()
        self.browser.find_element_by_xpath((
            "//button[@type='submit' and @id='id_registrar']")).click()
        sleep(1)

    def crear_BD(self, path, base_datos, multinum):
        self._login(ADMIN_USERNAME, ADMIN_PASSWORD)
        href_nueva_BD = '//a[contains(@href,"/base_datos_contacto/nueva/")]'
        self.get_href(href_nueva_BD)
        self.browser.find_element_by_id('id_nombre').send_keys(base_datos)
        self.browser.find_element_by_id('id_archivo_importacion').send_keys(path)
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)

        if multinum:
            self.browser.find_element_by_xpath('//label/input[@value = "phone"]').click()
            self.browser.find_element_by_xpath('//label/input[@value = "cell"]').click()
        else:
            self.browser.find_element_by_xpath('//label/input[@value = "telefono"]').click()

        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)

    def crear_blacklist(self, path, base_datos):
        link_create_blacklist = '//a[contains(@href,"/backlist/nueva")]'
        self.get_href(link_create_blacklist)
        self.browser.find_element_by_id('id_nombre').send_keys(base_datos)
        self.browser.find_element_by_id('id_archivo_importacion').send_keys(path)
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)

    def crear_supervisor(self, username, password):
        self._login(ADMIN_USERNAME, ADMIN_PASSWORD)
        link_create_user = self.browser.find_element_by_id('newUser')
        href_create_user = link_create_user.get_attribute('href')
        self.browser.get(href_create_user)
        self.browser.find_element_by_id('id_0-username').send_keys(username)
        self.browser.find_element_by_id('id_0-password1').send_keys(password)
        self.browser.find_element_by_id('id_0-password2').send_keys(password)
        self.browser.find_element_by_id('id_0-is_supervisor').click()
        self.browser.find_element_by_xpath('//form[@id=\'wizardForm\']/button').click()
        sleep(1)

    def crear_supervisor_tipo_customer(self):
        self.browser.find_elements_by_xpath('//select[@id=\'id_1-rol\']/option')[2].click()
        self.browser.find_elements_by_xpath('//form[@id=\'wizardForm\']/button')[2].click()
        sleep(1)

    def crear_supervisor_tipo_gerente(self):
        self.browser.find_elements_by_xpath('//select[@id=\'id_1-rol\']/option')[0].click()
        self.browser.find_elements_by_xpath('//form[@id=\'wizardForm\']/button')[2].click()
        sleep(1)

    @unittest.skipIf(BROWSER_REAL != 'True', MSG_MICROFONO)
    def test_agente_se_registra_correctamente(self):
        self._login(AGENTE_USERNAME, AGENTE_PASSWORD)
        self.assertEqual(self.browser.find_element_by_id('dial_status').text,
                         'Agent connected to asterisk')

    @unittest.skipIf(BROWSER_REAL != 'True', MSG_MICROFONO)
    def test_agente_puede_realizar_llamada_fuera_de_campana(self):
        numero_externo = '351111111'
        self._login(AGENTE_USERNAME, AGENTE_PASSWORD)
        self.browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        self.browser.find_element_by_id('call_off_campaign_menu').click()
        sleep(1)
        self.browser.find_element_by_id('phone_off_camp').send_keys(numero_externo)
        self.browser.find_element_by_id('call_phone_off_campaign').click()
        webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
        sleep(1)
        self.assertEqual(self.browser.find_element_by_id('dial_status').text,
                         'Connected to {0}'.format(numero_externo))

    # def test_agente_puede_recibir_llamada_entrante(self):
    #     pass

    @unittest.skipIf(BROWSER_REAL != 'True', MSG_MICROFONO)
    def test_agente_puede_realizar_llamada_saliente_campana_sin_identificar_contacto(self):
        # asume al menos una campaña asignada al agente
        numero_externo = '351111111'
        self._login(AGENTE_USERNAME, AGENTE_PASSWORD)
        self.browser.find_element_by_id('numberToCall').send_keys(numero_externo)
        self.browser.find_element_by_id('call').click()
        sleep(1)
        self.browser.find_element_by_id('SelectCamp').click()
        webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
        self.browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        self.browser.switch_to.frame(self.browser.find_element_by_tag_name('iframe'))
        sleep(1)
        self.browser.find_element_by_id('id_btn_no_identificar').click()
        sleep(1)
        self.browser.switch_to.default_content()
        self.assertEqual(self.browser.find_element_by_id('dial_status').text,
                         'Connected to {0}'.format(numero_externo))

    # test de creacion y edicion de usuarios

    def test_crear_usuario_tipo_agente_como_administrador(self):
        # login como admin
        self._login(ADMIN_USERNAME, ADMIN_PASSWORD)
        agente_username = 'agente' + uuid.uuid4().hex[:5]
        agente_password = AGENTE_PASSWORD
        # rellenar etapa1 del wizard de creación de usuario (agente)
        self.crear_agente(agente_username, agente_password)
        self.browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        self.browser.find_elements_by_xpath('//td[text()=\'{0}\']'.format(
            agente_username))
        # Editar agente
        user_list = '//a[contains(@href,"/user/list/page1/")]'
        self.get_href(user_list)
        link_edit = '//tr[@id=\'{0}\']/td/div//a'\
                    '[contains(@href,"/user/update")]'.format(agente_username)
        self.get_href(link_edit)
        nuevo_username = 'agente' + uuid.uuid4().hex[:5]
        self.browser.find_element_by_id('id_username').clear()
        sleep(1)
        self.browser.find_element_by_id('id_username').send_keys(nuevo_username)
        self.browser.find_element_by_xpath((
            "//button[@type='submit' and @id='id_registrar']")).click()
        sleep(1)
        self.browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        self.browser.find_elements_by_xpath('//td[text()=\'{0}\']'.format(
            nuevo_username))
        # modificar grupo del agente.
        group_name = 'grupo' + uuid.uuid4().hex[:5]
        self.crear_grupo(group_name)
        self.get_href(user_list)
        link_update = "//tr[@id=\'{0}\']/td/"\
                      "a[contains(@href, '/user/agenteprofile/update/')]".format(nuevo_username)
        self.get_href(link_update)
        self.browser.find_element_by_xpath("//select[@id='id_grupo']/option[text()=\'{0}\']"
                                           .format(group_name)).click()
        sleep(1)
        self.browser.find_element_by_xpath((
            "//button[@type='submit' and @id='id_registrar']")).click()
        sleep(1)
        self.get_href(user_list)
        self.get_href(link_update)
        self.browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        self.assertTrue(self.browser.find_element_by_xpath(
            "//select[@id=\'id_grupo\']/option[text()=\'{0}\']".format(group_name)))
        # Eliminar agente
        self.get_href(user_list)
        link_delete = "//tr[@id=\'{0}\']/td/div//"\
                      "a[contains(@href,'/user/delete')]".format(nuevo_username)
        self.get_href(link_delete)
        self.browser.find_element_by_xpath((
            "//button[@type='submit']")).click()
        sleep(1)
        self.browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        self.assertFalse(self.browser.find_elements_by_xpath('//td[text()=\'{0}\']'.format(
            nuevo_username)))

    def test_crear_usuario_tipo_customer(self):
        # Creación de clientes
        customer_username = 'cliente' + uuid.uuid4().hex[:5]
        customer_password = '098098ZZZ'
        self.crear_supervisor(customer_username, customer_password)
        self.crear_supervisor_tipo_customer()
        self.browser.find_elements_by_xpath('//td[text()=\'{0}\']'.format(customer_username))
        # modificar perfil a un perfil de supervisor
        user_list = '//a[contains(@href,"/user/list/page1/")]'
        self.get_href(user_list)
        link_update = "//tr[@id=\'{0}\']/td/a[contains(@href, '/supervisor/')]".format(
                      customer_username)
        self.get_href(link_update)
        self.browser.find_elements_by_xpath("//select[@id=\'id_rol\']/option")[0].click()
        self.browser.find_element_by_xpath((
            "//button[@type='submit' and @id='id_registrar']")).click()
        sleep(1)
        self.get_href(user_list)
        self.get_href(link_update)
        self.assertTrue(self.browser.find_elements_by_xpath(
            "//select[@id=\'id_rol\']/option[@value='2' and @selected]"))
        # Volver a modificiar a un perfil de cliente
        self.get_href(user_list)
        self.get_href(link_update)
        self.browser.find_elements_by_xpath("//select[@id=\'id_rol\']/option")[2].click()
        self.browser.find_element_by_xpath((
            "//button[@type='submit' and @id='id_registrar']")).click()
        sleep(1)
        self.get_href(user_list)
        self.get_href(link_update)
        self.assertTrue(self.browser.find_elements_by_xpath(
            "//select[@id=\'id_rol\']/option[@value='4' and @selected]"))

    def test_crear_usuario_tipo_supervisor(self):
        # Creación de supervisor
        supervisor_username = 'supervisor' + uuid.uuid4().hex[:5]
        supervisor_password = '098098ZZZ'
        self.crear_supervisor(supervisor_username, supervisor_password)
        self.crear_supervisor_tipo_gerente()
        self.browser.find_elements_by_xpath('//td[text()=\'{0}\']'.format(supervisor_username))
        # modificar perfil a un perfil de administrador
        user_list = '//a[contains(@href,"/user/list/page1/")]'
        self.get_href(user_list)
        link_update = "//tr[@id=\'{0}\']/td/a[contains(@href, '/supervisor/')]".format(
                      supervisor_username)
        self.get_href(link_update)
        self.browser.find_elements_by_xpath("//select[@id=\'id_rol\']/option")[1].click()
        self.browser.find_element_by_xpath((
            "//button[@type='submit' and @id='id_registrar']")).click()
        sleep(1)
        self.get_href(user_list)
        self.get_href(link_update)
        self.assertTrue(self.browser.find_elements_by_xpath(
            "//select[@id=\'id_rol\']/option[@value='1' and @selected]"))

    # test de creación y edición de grupos

    def test_crear_grupo_con_Autounpause(self):
        self._login(ADMIN_USERNAME, ADMIN_PASSWORD)
        link_create_group = '//a[contains(@href,"/grupo/nuevo")]'
        self.get_href(link_create_group)
        group_name = 'grupo' + uuid.uuid4().hex[:5]
        auto_unpause = random.randrange(1, 99)
        self.browser.find_element_by_id('id_nombre').send_keys(group_name)
        self.browser.find_element_by_id('id_auto_unpause').send_keys(auto_unpause)
        self.browser.find_element_by_id('id_auto_attend_inbound').click()
        self.browser.find_element_by_id('id_auto_attend_dialer').click()
        self.browser.find_element_by_xpath((
            "//button[@type='submit' and @id='id_registrar']")).click()
        sleep(1)
        self.browser.find_elements_by_xpath('//td[text()=\'{0}\']'.format(group_name))
        # Editar Grupo
        group_list = '//a[contains(@href,"/grupo/list/")]'
        self.get_href(group_list)
        link_edit = "//tr[@id=\'{0}\']/td/div//a[contains(@href,'/grupo/update')]".format(
            group_name)
        self.get_href(link_edit)
        nuevo_groupname = 'grupo' + uuid.uuid4().hex[:5]
        self.browser.find_element_by_id('id_nombre').clear()
        sleep(1)
        self.browser.find_element_by_id('id_nombre').send_keys(nuevo_groupname)
        self.browser.find_element_by_xpath((
            "//button[@type='submit' and @id='id_registrar']")).click()
        sleep(1)
        self.browser.find_elements_by_xpath('//td[text()=\'{0}\']'.format(
            nuevo_groupname))
        # Eliminar grupo
        self.get_href(group_list)
        link_delete = "//tr[@id=\'{0}\']/td/div//a[contains(@href,'/grupo/delete')]".format(
            nuevo_groupname)
        self.get_href(link_delete)
        self.browser.find_element_by_xpath((
            "//button[@type='submit']")).click()
        sleep(1)
        self.assertFalse(self.browser.find_elements_by_xpath('//td[text()=\'{0}\']'.format(
            nuevo_groupname)))

    def test_crear_grupo_sin_Autounpause(self):
        self._login(ADMIN_USERNAME, ADMIN_PASSWORD)
        group_name = 'grupo' + uuid.uuid4().hex[:5]
        self.crear_grupo(group_name)
        self.browser.find_elements_by_xpath('//td[text()=\'{0}\']'.format(group_name))

    # Acceso Web Administrador
    def test_acceso_web_administrador_acceso_exitoso(self):
        self._login(ADMIN_USERNAME, ADMIN_PASSWORD)
        self.assertTrue(self.browser.find_element_by_xpath(
            '//div/a[contains(@href, "/accounts/logout/")]'))

    def test_acceso_web_administrador_acceso_denegado(self):
        clave_erronea = "test"
        self._login(ADMIN_USERNAME, clave_erronea)
        self.assertEqual(self.browser.find_element_by_xpath(
            '//div[@class="alert alert-danger"]/p').text,
            'Invalid Username/Password, please try again')

    # Acceso web Agente
    def test_acceso_web_agente_acceso_exitoso(self):
        self._login(AGENTE_USERNAME, AGENTE_PASSWORD)
        self.assertTrue(self.browser.find_element_by_xpath(
            '//a[contains(@href, "/agente/logout/")]'))

    def test_acceso_web_agente_acceso_denegado(self):
        clave_erronea = "test"
        self._login(AGENTE_USERNAME, clave_erronea)
        self.assertEqual(self.browser.find_element_by_xpath(
            '//div[@class="alert alert-danger"]/p').text,
            'Invalid Username/Password, please try again')

    # Acceso web Supervisor
    def test_accesos_web_supervisor_acceso_exitoso(self):
        supervisor_username = 'supervisor' + uuid.uuid4().hex[:5]
        supervisor_password = '098098ZZZ'
        self.crear_supervisor(supervisor_username, supervisor_password)
        self.crear_supervisor_tipo_gerente()
        # Deslogueo como admin
        deslogueo = '//a[contains(@href, "/accounts/logout/")]'
        self.get_href(deslogueo)
        # Logueo como supervisor
        self._login(supervisor_username, supervisor_password)
        self.assertTrue(self.browser.find_element_by_xpath(
            '//a[contains(@href, "/accounts/logout/")]'))

    def test_acceso_web_supervisor_acceso_denegado(self):
        # Creación supervisor que vamos a usar para simular un acceso denegado
        supervisor_username = 'supervisor' + uuid.uuid4().hex[:5]
        supervisor_password = '098098ZZZ'
        self.crear_supervisor(supervisor_username, supervisor_password)
        clave_erronea = 'test'
        # Deslogueo como admin
        deslogueo = '//a[contains(@href, "/accounts/logout/")]'
        self.get_href(deslogueo)
        # Logueo como supervisor
        self._login(supervisor_username, clave_erronea)
        self.assertEqual(self.browser.find_element_by_xpath(
            '//div[@class="alert alert-danger"]/p').text,
            'Invalid Username/Password, please try again')

    # Acceso web Customer
    def test_acceso_web_cliente_acceso_exitoso(self):
        # Creación supervisor que vamos a usar para simular un acceso exitoso
        customer_username = 'cliente' + uuid.uuid4().hex[:5]
        customer_password = '098098ZZZ'
        self.crear_supervisor(customer_username, customer_password)
        self.crear_supervisor_tipo_customer()
        # Deslogue como admin
        deslogueo = '//a[contains(@href, "/accounts/logout/")]'
        self.get_href(deslogueo)
        # Logueo como cliente
        self._login(customer_username, customer_password)
        self.assertTrue(self.browser.find_element_by_xpath(
            '//div/a[contains(@href, "/accounts/logout/")]'))

    def test_acceso_web_cliente_acceso_denegado(self):
        # Creación supervisor que vamos a usar para simular un acceso denegado
        customer_username = 'cliente' + uuid.uuid4().hex[:5]
        customer_password = '098098ZZZ'
        self.crear_supervisor(customer_username, customer_password)
        self.crear_supervisor_tipo_customer()
        clave_erronea = 'test'
        # Deslogue como admin
        deslogueo = '//a[contains(@href, "/accounts/logout/")]'
        self.get_href(deslogueo)
        # Logueo como cliente
        self._login(customer_username, clave_erronea)
        self.assertEqual(self.browser.find_element_by_xpath(
            '//div[@class="alert alert-danger"]/p').text,
            'Invalid Username/Password, please try again')

    def test_bloqueo_y_desbloqueo_de_un_usuario(self):
        clave_erronea = 'test'
        # Intento loguearme 12 veces para bloquear la cuenta del usuario
        intentos = LOGIN_FAILURE_LIMIT + 2
        for i in range(intentos):
            self._login(AGENTE_USERNAME, clave_erronea)
        texto_error = self.browser.find_element_by_xpath('//div/p').text
        self.assertEqual(texto_error[0:24], 'Haz tratado de loguearte')
        # Vamos al Admin de django para desbloquear este usuario
        self.browser.get('https://{0}/admin'.format(TESTS_INTEGRACION_HOSTNAME))
        self.browser.find_element_by_name('username').send_keys(ADMIN_USERNAME)
        self.browser.find_element_by_name('password').send_keys(ADMIN_PASSWORD)
        self.browser.find_element_by_xpath('//div/input[@type="submit"]').click()
        sleep(2)
        defender = '//a[contains(@href, "/admin/defender/")]'
        self.get_href(defender)
        bloqued_user = '//a[contains(@href, "/admin/defender/blocks/")]'
        self.get_href(bloqued_user)
        self.browser.find_element_by_xpath(
            '//form[@action="/admin/defender/blocks/username/{0}/unblock"]/input[@type="submit"]'
            .format(AGENTE_USERNAME)).click()
        sleep(2)
        # Deslogueo como admin
        self.browser.get('https://{0}/'.format(TESTS_INTEGRACION_HOSTNAME))
        deslogueo = '//a[contains(@href, "/accounts/logout/")]'
        self.get_href(deslogueo)
        # Compruebo que el usuario esta desbloqueado
        self._login(AGENTE_USERNAME, AGENTE_PASSWORD)
        self.assertTrue(self.browser.find_element_by_xpath(
            '//div/a[contains(@href, "/agente/logout/")]'))

    def test_crear_modificar_eliminar_audio(self):
        # Crear audio
        self._login(ADMIN_USERNAME, ADMIN_PASSWORD)
        audio_list = '//a[contains(@href,"/audios/")]'
        self.get_href(audio_list)
        audio_create = '//a[contains(@href,"/audios/create/")]'
        self.get_href(audio_create)
        descripcion_audio = 'audio' + uuid.uuid4().hex[:5]
        self.browser.find_element_by_id('id_descripcion').send_keys(descripcion_audio)
        wav_path = "/home/{0}/ominicontacto/test/wavs/8k16bitpcm.wav". format(USER)
        self.browser.find_element_by_id('id_audio_original').send_keys(wav_path)
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)
        self.browser.find_elements_by_xpath('//tr[text()=\'{0}\']'.format(
            descripcion_audio))
        # Modificar Audio
        duracion_wav_path = 13
        duracion_nuevo_wav = 35
        self.browser.find_element_by_xpath(
            '//tr[@id=\'{0}\']//a[contains(@href, "/update/")]'.format(descripcion_audio)).click()
        nuevo_wav = "/home/{0}/ominicontacto/test/wavs/audio1.wav".format(USER)
        self.browser.find_element_by_id('id_audio_original').send_keys(nuevo_wav)
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)
        self.browser.find_element_by_xpath(
            '//tr[@id=\'{0}\']//a[contains(@href, "/update/")]'.format(descripcion_audio)).click()
        self.browser.find_element_by_id('id_audio_original').send_keys(nuevo_wav)
        self.assertNotEqual(self.browser.find_element_by_xpath(
            "//input[text()=\'{0}\']".format(duracion_nuevo_wav)), duracion_wav_path)
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)
        # Eliminar Audio
        self.browser.find_element_by_xpath(
            '//tr[@id=\'{0}\']//a[contains(@href, "/eliminar/")]'.format(descripcion_audio)).click()
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)
        self.assertFalse(self.browser.find_elements_by_xpath('//tr[text()=\'{0}\']'
                         .format(nuevo_wav)))

    def test_subir_audio_erroneo(self):
        self._login(ADMIN_USERNAME, ADMIN_PASSWORD)
        audio_list = '//a[contains(@href,"/audios/")]'
        self.get_href(audio_list)
        audio_create = '//a[contains(@href,"/audios/create/")]'
        self.get_href(audio_create)
        descripcion_audio = 'audio' + uuid.uuid4().hex[:5]
        self.browser.find_element_by_id('id_descripcion').send_keys(descripcion_audio)
        wav_path = "/home/{0}/ominicontacto/test/wavs/error_audio.mp3".format(USER)
        self.browser.find_element_by_id('id_audio_original').send_keys(wav_path)
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)
        self.browser.find_elements_by_xpath('//ul/li[text()="Allowed files: .wav"]')

    def test_pausa_productiva(self):
        # crear pausa productiva
        self._login(ADMIN_USERNAME, ADMIN_PASSWORD)
        link_create_pausa = '//a[contains(@href,"/pausa/nuevo")]'
        self.get_href(link_create_pausa)
        pausa_nueva = 'pausa_pro' + uuid.uuid4().hex[:5]
        self.browser.find_element_by_id('id_nombre').send_keys(pausa_nueva)
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)
        self.assertTrue(self.browser.find_elements_by_xpath('//td[text()=\'{0}\']'.format(
            pausa_nueva)))
        # modificar pausa productiva
        link_edit = '//tr[@id=\'{0}\']//a[contains(@href, "/pausa/update/")]'.format(pausa_nueva)
        self.get_href(link_edit)
        pausa_recreativa = 'pausa_rec' + uuid.uuid4().hex[:5]
        self.browser.find_element_by_id('id_nombre').clear()
        sleep(1)
        self.browser.find_element_by_id('id_nombre').send_keys(pausa_recreativa)
        self.browser.find_element_by_xpath("//select/option[@value = 'R']").click()
        sleep(1)
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)
        self.assertTrue(self.browser.find_elements_by_xpath('//td[text()=\'{0}\']'.format(
            pausa_recreativa)))
        # eliminar pausa recreativa
        link_delete = "//tr[@id=\'{0}\']//a[contains(@href, '/pausa/delete/')]".format(
            pausa_recreativa)
        self.get_href(link_delete)
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)
        self.assertTrue(self.browser.find_elements_by_xpath(
            "//tr[@id='pausa_eliminada']//td[contains(text(), \'{0}\')]".format(pausa_recreativa)))
        # reactivar pausa recreativa
        link_reactivate = "//tr[@id='pausa_eliminada']//td[@id=\'{0}\']//"\
            "a[contains(@href, '/pausa/delete/')]".format(pausa_recreativa)
        self.get_href(link_reactivate)
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)
        self.assertTrue(self.browser.find_elements_by_xpath('//td[text()=\'{0}\']'.format(
            pausa_recreativa)))

    def test_pausa_recreativa(self):
        # crear pausa recreativa
        self._login(ADMIN_USERNAME, ADMIN_PASSWORD)
        link_create_pausa = '//a[contains(@href,"/pausa/nuevo")]'
        self.get_href(link_create_pausa)
        pausa_nueva = 'pausa_rec' + uuid.uuid4().hex[:5]
        self.browser.find_element_by_id('id_nombre').send_keys(pausa_nueva)
        self.browser.find_element_by_xpath("//select/option[@value = 'R']").click()
        sleep(1)
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)
        self.assertTrue(self.browser.find_elements_by_xpath('//td[text()=\'{0}\']'.format(
            pausa_nueva)))
        # modificar pausa recreativa
        link_edit = '//tr[@id=\'{0}\']//a[contains(@href, "/pausa/update/")]'.format(pausa_nueva)
        self.get_href(link_edit)
        pausa_productiva = 'pausa_pro' + uuid.uuid4().hex[:5]
        self.browser.find_element_by_id('id_nombre').clear()
        sleep(1)
        self.browser.find_element_by_id('id_nombre').send_keys(pausa_productiva)
        self.browser.find_element_by_xpath("//select/option[@value = 'P']").click()
        sleep(1)
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)
        self.assertTrue(self.browser.find_elements_by_xpath('//td[text()=\'{0}\']'.format(
            pausa_productiva)))
        # eliminar pausa productiva
        link_delete = "//tr[@id=\'{0}\']//a[contains(@href, '/pausa/delete/')]".format(
            pausa_productiva)
        self.get_href(link_delete)
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)
        self.assertTrue(self.browser.find_elements_by_xpath(
            "//tr[@id='pausa_eliminada']//td[contains(text(), \'{0}\')]".format(pausa_productiva)))
        # reactivar pausa productiva
        link_reactivate = "//tr[@id='pausa_eliminada']//td[@id=\'{0}\']//"\
            "a[contains(@href, '/pausa/delete/')]".format(pausa_productiva)
        self.get_href(link_reactivate)
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
        sleep(1)
        self.assertTrue(self.browser.find_elements_by_xpath('//td[text()=\'{0}\']'.format(
            pausa_productiva)))

        # Base de datos de contactos
    def test_crear_ocultar_base_de_datos(self):
        # Crear nueva base de datos
        try:
            csv_path = "/home/{0}/ominicontacto/ominicontacto_app/static/ominicontacto"\
                "/oml-example-db.csv".format(USER)
            BD_nueva = 'BD' + uuid.uuid4().hex[:5]
            multinum = False
            self.crear_BD(csv_path, BD_nueva, multinum)
            self.browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            self.assertTrue(self.browser.find_elements_by_xpath('//tr[@id=\'{0}\']'.format(
                BD_nueva)))
            print('--Se pudo crear una BD.--')
        except ValueError:
            print('--ERROR: No se pudo crear una BD.--')
        # Ocultar Base de datos
        try:
            lista_BD = '//a[contains(@href,"/base_datos_contacto/")]'
            self.get_href(lista_BD)
            ocultar_BD = '//tr[@id=\'{0}\']//td//a[contains(@href, "/ocultar/")]'.format(
                BD_nueva)
            self.get_href(ocultar_BD)
            self.browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            self.assertFalse(self.browser.find_elements_by_xpath('//tr[@id=\'{0}\']'.format(
                BD_nueva)))
            self.browser.find_element_by_xpath('//a[@onclick]').click()
            sleep(1)
            self.browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            desocultar = '//tr[@id=\'{0}\']//td//a[contains(@href, "/desocultar/")]'.format(
                BD_nueva)
            self.get_href(desocultar)
            self.assertTrue(self.browser.find_elements_by_xpath('//tr[@id=\'{0}\']'.format(
                BD_nueva)))
            print('--Se oculto y desoculto con exito una base de datos.--')
        except ValueError:
            print('--ERROR: No se pudo ocultar y desocultar una base de datos.--')

    def test_editar_eliminar_lista_contacto_base(self):
        # Editar Lista de Contacto
        try:
            csv_path = "/home/{0}/ominicontacto/ominicontacto_app/static/ominicontacto"\
                "/oml-example-db.csv".format(USER)
            BD_nueva = 'BD' + uuid.uuid4().hex[:5]
            multinum = False
            self.crear_BD(csv_path, BD_nueva, multinum)
            lista_contacto = '//tr[@id=\'{0}\']//a[contains(@href, "/list_contacto/")]'.format(
                BD_nueva)
            self.get_href(lista_contacto)
            contacto = '4553101'
            editar_contacto = '//tr[@id=\'{0}\']//td//a[contains(@href, "/update/")]'.format(
                contacto)
            self.get_href(editar_contacto)
            self.browser.find_element_by_id('id_telefono').clear()
            sleep(1)
            nuevo_telefono = '4789032'
            self.browser.find_element_by_id('id_telefono').send_keys(nuevo_telefono)
            self.browser.find_element_by_xpath("//button[@type='submit']").click()
            sleep(1)
            self.assertTrue(self.browser.find_elements_by_xpath('//tr[@id=\'{0}\']'.format(
                nuevo_telefono)))
            print('--Se pudo editar un contacto en la BD.--')
        except ValueError:
            print('--ERROR: No se pudo editar un contacto en la BD.--')
        # Eliminar lista de contacto
        try:
            lista_BD = '//a[contains(@href,"/base_datos_contacto/")]'
            self.get_href(lista_BD)
            lista_contacto = '//tr[@id=\'{0}\']//a[contains(@href, "/list_contacto/")]'.format(
                BD_nueva)
            self.get_href(lista_contacto)
            eliminar_contacto = '//tr[@id=\'{0}\']//td//a[contains(@href, "/eliminar/")]'.format(
                nuevo_telefono)
            self.get_href(eliminar_contacto)
            self.browser.find_element_by_xpath("//button[@type='submit']").click()
            sleep(1)
            self.assertFalse(self.browser.find_elements_by_xpath('//tr[@id=\'{0}\']'.format(
                nuevo_telefono)))
            print('--Se pudo eliminar un contacto en la BD.--')
        except ValueError:
            print('--ERROR: No se pudo eliminar un contacto en la BD.--')

    def test_crear_agregar_contacto_base_multinum(self):
        # Crear Base Multinum
        try:
            csv_path = "/home/{0}/ominicontacto/test/base_prueba_multinum.csv".format(USER)
            BD_nueva = 'BD' + uuid.uuid4().hex[:5]
            multinum = True
            self.crear_BD(csv_path, BD_nueva, multinum)
            self.browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            self.assertTrue(self.browser.find_elements_by_xpath('//tr[@id=\'{0}\']'.format(
                BD_nueva)))
            print('--Se pudo crear una BD Multinum.--')
        except ValueError:
            print('--ERROR: No se pudo crear una BD Multinum.--')
        # Agregar un Contacto
        try:
            agregar_contacto = '//tr[@id=\'{0}\']//td//a[contains'\
                               '(@href, "/agregar_contacto/")]'.format(BD_nueva)
            self.get_href(agregar_contacto)
            telefono = '3456789'
            cell = '154352879'
            self.browser.find_element_by_id('id_telefono').send_keys(telefono)
            self.browser.find_element_by_id('id_cell').send_keys(cell)
            self.browser.find_element_by_xpath("//button[@type='submit']").click()
            sleep(1)
            self.browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            lista_contacto = '//tr[@id=\'{0}\']//a[contains(@href, "/list_contacto/")]'.format(
                BD_nueva)
            self.get_href(lista_contacto)
            self.assertTrue(self.browser.find_elements_by_xpath('//tr[@id=\'{0}\']'.format(
                telefono)))
            print('--Se pudo agregar un solo contacto a la BD.--')
        except ValueError:
            print('--ERROR: No se pudo agregar un solo contacto a la BD.--')

    def test_crear_agregar_csv_base_multinum(self):
        # Agregar un CSV
        try:
            import ipdb; ipdb.set_trace()
            csv_path = "/home/{0}/ominicontacto/test/base_prueba_multinum.csv".format(USER)
            BD_nueva = 'BD' + uuid.uuid4().hex[:5]
            multinum = True
            self.crear_BD(csv_path, BD_nueva, multinum)
            nuevo_path = "/home/{0}/ominicontacto/test/base_prueba_multinum2.csv".format(USER)
            lista_BD = '//a[contains(@href,"/base_datos_contacto/")]'
            self.get_href(lista_BD)
            agregar_csv = '//tr[@id=\'{0}\']//td//a[contains(@href, "/actualizar/")]'.format(
                BD_nueva)
            self.get_href(agregar_csv)
            self.browser.find_element_by_id('id_archivo_importacion').send_keys(nuevo_path)
            self.browser.find_element_by_xpath("//button[@type='submit']").click()
            sleep(1)
            self.browser.find_element_by_xpath("//button[@type='submit']").click()
            sleep(1)
            numero = '351351319'
            self.get_href(lista_BD)
            lista_contacto = '//tr[@id=\'{0}\']//a[contains(@href, "/list_contacto/")]'.format(
                BD_nueva)
            self.get_href(lista_contacto)
            self.assertTrue(self.browser.find_elements_by_xpath('//tr[@id=\'{0}\']'.format(
                numero)))
            print('--Se puede agregar contactos a la BD a través de un .CSV--')
        except ValueError:
            print('--ERROR: No se pudo agregar contactos a la BD a través de un CSV.--')

    def test_crear_blacklist(self):
        try:
            # Crear nueva blacklist
            self._login(ADMIN_USERNAME, ADMIN_PASSWORD)
            blacklist = 'blacklist' + uuid.uuid4().hex[:5]
            csv_path = "/home/{0}/ominicontacto/test/planilla-ejemplo-0.csv".format(USER)
            self.crear_blacklist(csv_path, blacklist)
            self.assertTrue(self.browser.find_elements_by_xpath('//td[contains(text(), \'{0}\')]'
                            .format(blacklist)))
            print('--Se pudo crear un Blacklist.--')
        except ValueError:
            print('--ERROR: No se pudo crear un Blacklist.--')
        # Verificación que solo muestra la ultima Blacklist subida
        try:
            nueva_blacklist = 'blacklist' + uuid.uuid4().hex[:5]
            csv_nueva = "/home/{0}/ominicontacto/test/planilla-ejemplo-0.csv".format(USER)
            self.crear_blacklist(csv_nueva, nueva_blacklist)
            self.assertFalse(self.browser.find_elements_by_xpath('//td[contains(text(), \'{0}\')]'
                             .format(blacklist)))
            self.assertTrue(self.browser.find_elements_by_xpath('//td[contains(text(), \'{0}\')]'
                            .format(nueva_blacklist)))
            print('--Se verifico que solo muestra la ultima Blacklist.--')
        except ValueError:
            print('--No se pudo verificar que solo se muestra la ultima Blacklist.--')


if __name__ == '__main__':
    # para poder ejecutar los tests desde fuera del entorno
    unittest.main()
