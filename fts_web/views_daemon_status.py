# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import get_cache
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from fts_daemon.poll_daemon.statistics import StatisticsService
import logging as logging_


logger = logging_.getLogger(__name__)


statistics_service = StatisticsService(cache=get_cache('default'))


def _update_context_with_statistics(context):
    """Metodo utilitario. Recibe un contexto, y setea en el
    las estadisticas del Daemon."""
    daemon_stats = statistics_service.get_statistics()
    stats_timestamp = daemon_stats.get('_time', None)
    if stats_timestamp is None:
        context['daemon_stats_valid'] = False
    else:
        delta = timezone.now() - stats_timestamp
        if delta.days != 0:
            context['daemon_stats_valid'] = False
            logger.warn("_update_context_with_statistics(): delta.days: %s",
                        delta.days)
        # elif delta.seconds == 0 and delta.microseconds > 20000:
        elif delta.seconds > settings.FTS_DAEMON_STATS_VALIDEZ:
            context['daemon_stats_valid'] = False
        else:
            context['daemon_stats_valid'] = True

    context['daemon_stats'] = daemon_stats


class DaemonStatusView(TemplateView):
    """Devuelve HTML con informacion de status / estadisticas
    del Daemon"""

    template_name = "estado/daemon_status.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DaemonStatusView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DaemonStatusView, self).get_context_data(**kwargs)
        _update_context_with_statistics(context)
        return context
