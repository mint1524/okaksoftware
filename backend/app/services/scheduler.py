from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..core.config import get_settings
from ..core.db import AsyncSessionMaker
from ..jobs.cleanup import cleanup_expired_tokens

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self):
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self._configured = False

    def configure(self):
        if self._configured:
            return

        cron = CronTrigger.from_crontab(self.settings.cleanup_cron)

        async def run_cleanup():
            removed = await cleanup_expired_tokens(AsyncSessionMaker)
            if removed:
                logger.info("Removed %s expired purchase sessions", removed)

        self.scheduler.add_job(run_cleanup, cron, id="cleanup_expired_tokens", replace_existing=True)
        self._configured = True

    def start(self):
        if not self.settings.scheduler_enabled:
            logger.info("Scheduler disabled via configuration")
            return
        self.configure()
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    async def shutdown(self):
        if self.scheduler.running:
            await self.scheduler.shutdown()
            logger.info("Scheduler shut down")


scheduler = Scheduler()
