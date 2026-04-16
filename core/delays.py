import asyncio
import random
from config.settings import DELAY_BASE, DELAY_JITTER


async def apply_delay():
    delay = random.uniform(DELAY_BASE, DELAY_BASE + DELAY_JITTER)
    await asyncio.sleep(delay)
