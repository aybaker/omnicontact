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

    def method_that_call_another_method(self):
        return self.some_method_b('')


class TestAntipatternsMockeoDeServicios(TestCase):
    """Demuestra formas peligrosas de utilizar mocks, con ejemplos
    de tests que pasan, pero NO debrian pasar
    """

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


class TestMockConAutospec(TestCase):
    """Tests de comportamiento de 'create_autospec()'.

    Basicamente crea una instancia con todos sus metodos mockeados.
    Por lo tanto, no se podra ejecutar ninguno de los metodos reales.
    """

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

        self.assertEquals(servicio_b.servicio_a.some_method_a("VAL"), 'd-e-f')


class TestMockeoDeServicio(TestCase):
    """Testea todos los casos que debe soportar una buena implementacion
    de Mock para mockear servicios.
    """

    def setUp(self):
        self.servicio_b = ServicioB()
        self.servicio_b = Mock(spec_set=self.servicio_b, wraps=self.servicio_b)

    def test_funcionalidad_original_puede_ser_llamada(self):
        with self.assertRaises(UnaExcepcion):
            self.servicio_b.some_method_b("")

    def test_respeta_method_signatures(self):
        with self.assertRaises(TypeError):
            self.servicio_b.some_method_b()

        with self.assertRaises(TypeError):
            self.servicio_b.some_method_b("1", "2")

    def test_falla_si_intenta_setear_atributo_inexistente(self):
        with self.assertRaises(AttributeError):
            self.servicio_b.some_method_que_no_existe = Mock()

    def test_permite_usar_returns_value(self):
        self.servicio_b.some_method_b.return_value = 'abc'
        value = self.servicio_b.some_method_b()
        self.assertEquals(value, 'abc')

    def test_permite_usar_side_effect(self):
        self.servicio_b.some_method_b.side_effect = KeyError()
        with self.assertRaises(KeyError):
            self.servicio_b.some_method_b("")

    def test_permite_mockear_metodo_de_servicio_de_servicio(self):
        with self.assertRaises(UnaExcepcion):
            self.servicio_b.servicio_a.some_method_a("")

        #
        # ATENCION! Al llamar a `servicio_a.some_method_a()` SIN PARAMETROS,
        #   ESTA LLAMADA DEBERIA FALLAR! ¿Por que no se estan controlando
        #   la validez de los parametros?
        #
        # Lo mas raro es que, ANTES de cambiar 'rteurn_value', si no se
        #   especifican los parametros requeridos, falla!
        #
        self.servicio_b.servicio_a.some_method_a.return_value = 'abc'
        value = self.servicio_b.servicio_a.some_method_a()
        self.assertEquals(value, 'abc')


class TestLlamadaViaSelfEnServicio(TestCase):

    def test_llamada_via_self_no_es_mockeada(self):
        """
        `method_that_call_another_method()` llama a `self.some_method_b()`.

        Pero `some_method_b()` es ejecutado SIN IMPORTAR que se haya seteado
        `some_method_b.return_value = 'abc'`
        """
        self.servicio_b = ServicioB()
        self.servicio_b = Mock(spec_set=self.servicio_b, wraps=self.servicio_b)

        self.servicio_b.some_method_b.return_value = 'abc'
        with self.assertRaises(UnaExcepcion):
            self.servicio_b.method_that_call_another_method()

    def test_fix_llamada_via_self(self):
        """
        Para solucionar el problema, moquear el metodo ANTES que la instancia
        del servicio.
        """
        self.servicio_b = ServicioB()
        self.servicio_b.some_method_b = Mock(return_value='zyx')
        self.servicio_b = Mock(spec_set=self.servicio_b, wraps=self.servicio_b)

        value = self.servicio_b.method_that_call_another_method()
        self.assertEquals(value, 'zyx')
