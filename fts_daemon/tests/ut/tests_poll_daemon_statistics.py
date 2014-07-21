# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.poll_daemon.statistics"""

from __future__ import unicode_literals

from django.core.cache import get_cache
from fts_daemon.poll_daemon.statistics import StatisticsService
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
from mock import Mock


logger = _logging.getLogger(__name__)


class StatisticsServiceTests(FTSenderBaseTest):
    """Unit tests de StatisticsService"""

    def test_publish_statistics_calls_set(self):
        """Testea que publish_statistics() llama a cache.set()"""
        cache = Mock(get_cache('default'))

        # -----

        ss = StatisticsService(cache=cache)
        ss.publish_statistics({1: 2})

        self.assertTrue(cache.set.call_count > 0)

    def test_get_statistics_calls_get(self):
        """Testea que get_statistics() llama a cache.get()"""
        stats = {1: 2}
        cache = Mock(get_cache('default'))
        cache.get = Mock(return_value=stats)

        # -----

        ss = StatisticsService(cache=cache)
        ret = ss.get_statistics()

        self.assertTrue(cache.get.call_count > 0)
        self.assertDictEqual(stats, ret)

    def test_shoud_update_returns_true(self):
        """Testea que shoud_update() devuelva True"""
        cache = Mock(get_cache('default'))
        # -----

        ss = StatisticsService(cache=cache)
        self.assertTrue(ss.shoud_update())

    def test_shoud_update_returns_false(self):
        """Testea que shoud_update() devuelva False"""
        cache = Mock(get_cache('default'))
        # -----

        ss = StatisticsService(cache=cache)
        ss.publish_statistics({1: 2})
        self.assertFalse(ss.shoud_update())
