import asyncio
import random
from config.settings import DELAY_BASE, DELAY_PAGE, DELAY_CATEGORY, DELAY_EVENT, DELAY_JITTER

DELAY_PAGE = 60
DELAY_CATEGORY = 300
DELAY_EVENT = 1800


async def apply_delay(stage='page'):
    if stage=='page':
        delay = random.uniform(DELAY_PAGE, DELAY_PAGE + DELAY_JITTER)
    elif stage=='category':
        delay = random.uniform(DELAY_CATEGORY, DELAY_CATEGORY + DELAY_JITTER)
    elif stage=='event':
        delay = random.uniform(DELAY_EVENT, DELAY_EVENT + DELAY_JITTER)
    else:
        delay = random.uniform(DELAY_BASE, DELAY_BASE + DELAY_JITTER)
    await asyncio.sleep(delay)
