import asyncio
import json
from core.browser_manager import BrowserManager
from core.engine import run_event
from sites.asdeporte_driver import AsDeporteDriver
from sites.cronocom_driver import CronocomDriver


async def main():

    with open("config/events_metadata.json") as f:
        events = json.load(f)

    browser_manager = BrowserManager()
    await browser_manager.start()

    for event in events:

        if event["site"] == "asdeporte":
            driver = AsDeporteDriver()
        elif event["site"] == "cronocom":
            driver = CronocomDriver()
        else:
            continue

        print(f"Iniciando evento: {event['event_slug']}")

        await run_event(
            browser_manager,
            driver,
            event
        )

    await browser_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
