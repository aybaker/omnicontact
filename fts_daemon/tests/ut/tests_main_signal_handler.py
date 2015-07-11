# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.locks"""

from __future__ import unicode_literals


import logging
import multiprocessing
import os
import random
import signal
import sys
import time


from fts_web.tests.utiles import FTSenderBaseTest

MSG_EN_LOOP = 'en-loop'
MSG_FINALIZADO_LIMPIAMENTE = 'finalizado-limpiamente'

def main_sin_handler(conn):
    while True:
        conn.send(MSG_EN_LOOP)
        time.sleep(0.05)


def main_con_handler(conn, successful_exit_status):
    continue_running_holder = [True]

    def signal_handler(signum, _):
        logging.info("CHILD: signal_handler() - signal: %s", signum)
        if signum == signal.SIGTERM:
            logging.info("CHILD: seteando continue_running = False")
            continue_running_holder[0] = False

    signal.signal(signal.SIGTERM, signal_handler)

    while continue_running_holder[0]:
        logging.info("CHILD: enviando: %s", MSG_EN_LOOP)
        conn.send(MSG_EN_LOOP)
        time.sleep(0.05)

    logging.info("CHILD: se ha salido del loop. Enviando: %s", MSG_FINALIZADO_LIMPIAMENTE)
    conn.send(MSG_FINALIZADO_LIMPIAMENTE)

    logging.info("CHILD: haciendo exit")
    sys.exit(successful_exit_status)

class MainSinSignalHandlerTest(FTSenderBaseTest):

    def test_finaliza_abruptamente(self):
        parent_conn, child_conn = multiprocessing.Pipe()
        process = multiprocessing.Process(target=main_sin_handler,
                                          args=(child_conn, ))
        process.start()
        response = parent_conn.recv()
        self.assertEqual(response, MSG_EN_LOOP)

        os.kill(process.pid, signal.SIGTERM)
        process.join(timeout=5)
        self.assertFalse(process.is_alive())

        while parent_conn.poll():
            response = parent_conn.recv()
            self.assertEqual(response, MSG_EN_LOOP)

        self.assertEqual(process.exitcode, -1 * signal.SIGTERM)

class MainConSignalHandlerTest(FTSenderBaseTest):

    SUCCESSFUL_EXIT_STATUS = random.randint(11, 99)

    def test_finaliza_con_gracia(self):
        parent_conn, child_conn = multiprocessing.Pipe()
        process = multiprocessing.Process(target=main_con_handler,
                                          args=(child_conn, self.SUCCESSFUL_EXIT_STATUS))
        process.start()
        response = parent_conn.recv()
        self.assertEqual(response, MSG_EN_LOOP)

        logging.info("PARENT: enviando signal")
        os.kill(process.pid, signal.SIGTERM)
        logging.info("PARENT: se realizara join()")
        process.join(timeout=5)
        logging.info("PARENT: join() finalizado")

        self.assertFalse(process.is_alive())
        logging.info("PARENT: exit code: %s", process.exitcode)

        while True:
            if parent_conn.poll():
                logging.info("PARENT: parent_conn.poll() devolvio True")
                response = parent_conn.recv()
                if response == MSG_EN_LOOP:
                    continue
                elif response == MSG_FINALIZADO_LIMPIAMENTE:
                    self.assertFalse(parent_conn.poll(), "Se encontraron mas mensajes "
                                                         "posteriores a "
                                                         "MSG_FINALIZADO_LIMPIAMENTE")
                    break
                else:
                    self.fail("Mensaje invalido: {0}".format(response))

            self.fail("No se encontro mensaje MSG_FINALIZADO_LIMPIAMENTE")

        self.assertEqual(process.exitcode, self.SUCCESSFUL_EXIT_STATUS)
