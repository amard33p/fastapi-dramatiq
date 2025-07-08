"""Scheduled Periodic Jobs using Periodiq.

This module defines periodic Dramatiq actors that are executed by the Periodiq
scheduler. Currently it contains a single job that logs a message every 30
seconds.  Periodiq's cron specs only allow minute-level granularity, so we
combine a cron-based entrypoint that fires every minute with a second message
using a 30-second delay to achieve the 30-second cadence requested by the
user.
"""

from datetime import datetime, timezone
import logging

import dramatiq
from periodiq import cron

logger = logging.getLogger(__name__)


@dramatiq.actor
def log_heartbeat():
    """Write a heartbeat log line with the current UTC timestamp."""

    logger.info("[heartbeat] %s", datetime.now(timezone.utc).isoformat())


@dramatiq.actor(periodic=cron("* * * * *"))
def schedule_heartbeat():
    """Entry-point for Periodiq.

    This actor is executed every minute by Periodiq.  It immediately enqueues a
    `log_heartbeat` message and schedules another one with a 30-second delay so
    that the log runs roughly every 30 seconds.
    """

    # Immediate heartbeat
    log_heartbeat.send()

    # Second heartbeat 30 seconds later (30_000 ms)
    log_heartbeat.send_with_options(delay=30_000)
