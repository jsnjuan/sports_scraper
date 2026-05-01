import asyncio
import json
from core.browser_manager import BrowserManager
from core.engine import run_event
from core.delays import apply_delay
from sites.asdeporte_driver import AsDeporteDriver
from sites.cronocom_driver import CronocomDriver
from sites.metamx_driver import MetamxDriver
from sites.marcate_driver import MarcateDriver
from sites.chronosport_driver import ChronosportDriver

async def main():

    with open("config/events_metadata.json", encoding="utf-8") as f:
        events = json.load(f)

    browser_manager = BrowserManager()
    await browser_manager.start()

    for event in events:

        if event["site"] == "asdeporte":
            driver = AsDeporteDriver()
        elif event["site"] == "cronocom":
            driver = CronocomDriver()
        elif event["site"] == "metamx":
            driver = MetamxDriver()
        elif event["site"] == "marcate":
            driver = MarcateDriver()
        elif event["site"] == "chronosport":
            driver = ChronosportDriver()
        else:
            continue

        print(f"Starting event: {event['event_slug']}")

        did_work = await run_event(
            browser_manager,
            driver,
            event
        )

        if did_work and event != events[-1]:
            await apply_delay(stage='event')

    await browser_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
