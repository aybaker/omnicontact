# -*- coding: utf-8 -*-

"""Tests comportamiento de libreria de mock"""
from __future__ import unicode_literals

from django.test.testcases import TestCase
from mock import Mock, create_autospec


class UnaExcepcion(BaseException):
    pass


class ServicioA(object):

    def __init__(self):
        pass

    def some_method_a(self, un_param):
        raise(UnaExcepcion())


class ServicioB(object):

    def __init__(self):
        self.servicio_a = ServicioA()

    def some_method_b(self, un_param):
        raise(UnaExcepcion())


class TestMockeoDeServicios(TestCase):

    def test_problemas_con_mock(self):

        servicio_b = ServicioB()

        # llamamos a metodo con parametros validos -> ok
        with self.assertRaises(UnaExcepcion):
            servicio_b.some_method_b("VALUE")

        # si no pasamos parametros, debe fallar
        with self.assertRaises(TypeError):
            servicio_b.some_method_b()

        # ----- Ahora mostramos xq esta mal usar Mock() -----

        # 1. no reporta problemas de parametros
        servicio_b.some_method_b = Mock()
        servicio_b.some_method_b()

        # 2. no reporta problemas de funciones inexistentes
        servicio_b.some_method_que_no_existe = Mock()
        servicio_b.some_method_que_no_existe()

        # 3. no reporta problemas de atributos inexistentes
        servicio_b.servicio_que_no_existe = Mock()
        servicio_b.servicio_que_no_existe.some_method_que_no_existe()

    def test_create_autospec_mockea_metodos(self):

        # creamos mock usando `create_autospec()`
        servicio_b = create_autospec(ServicioB)

        # llamamos metodo mockeado. NO GENERA EXCEPCION
        servicio_b.some_method_b("VALUE")
        servicio_b.some_method_b.assert_called_with("VALUE")

        # aunque esta mockeqado, verifica parametros
        with self.assertRaises(TypeError):
            servicio_b.some_method_b()

    def test_create_autospec_side_effect(self):
        """
        EJEMPLO de como usar 'side_effect'
        """

        # creamos mock usando `create_autospec()`
        servicio_b = create_autospec(ServicioB)

        # seteamos `side_effect`
        servicio_b.some_method_b.side_effect = UnaExcepcion()

        # llamamos a metodo con parametros validos
        with self.assertRaises(UnaExcepcion):
            servicio_b.some_method_b("VALUE")

    def test_create_autospec_return_value(self):
        """
        EJEMPLO de como usar 'return_value'
        """

        # creamos mock usando `create_autospec()`
        servicio_b = create_autospec(ServicioB)

        # seteamos `return_value`
        servicio_b.some_method_b.return_value = 'a-b-c'

        self.assertEquals(servicio_b.some_method_b("VAL"), 'a-b-c')

    def test_metodo_de_servicio_de_servicio(self):
        """
        EJEMPLO de como mockear ATRIBUTO.

        El truco es pasar una instancia y usar `instance=True`
        """
        # creamos mock usando `create_autospec()`
        servicio_b = create_autospec(ServicioB(), instance=True)

        # seteamos `return_value`
        servicio_b.servicio_a.some_method_a.return_value = 'd-e-f'

        self.assertEquals(servicio_b.servicio_a.some_method_a("VAL"),
                          'd-e-f')
