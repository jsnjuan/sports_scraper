from config.settings import CONTEXT_RESTART_INTERVAL, MAX_RETRIES_PER_PAGE
from core.persistence import (
    load_metadata,
    save_metadata,
    save_page,
)
from core.delays import apply_delay

async def run_event(browser_manager, driver, event_config):

    for category in event_config["categories"]:

        print(f"Starting category: {category}")

        await run_category(
            browser_manager,
            driver,
            event_config,
            category
        )


async def run_category(browser_manager, driver, event_config, category):

    category_config = {
        **event_config,
        "distance": category
    }

    await run_pages(browser_manager, driver, category_config)


async def run_pages(browser_manager, driver, category_config):

    metadata = load_metadata(category_config)

    if metadata and metadata.get("completed"):
        print("Event is completed. Skipping.")
        return

    if not metadata:
        metadata = {
            "event_slug": category_config["event_slug"],
            "site": category_config["site"],
            "distance": category_config["distance"],
            "last_page_scraped": 0,
            "total_pages": None,
            "completed": False,
            "total_records": 0
        }

    page_number = metadata["last_page_scraped"] + 1
    total_pages = metadata.get("total_pages")

    page = await browser_manager.new_page()

    while True:

        if page_number % CONTEXT_RESTART_INTERVAL == 0:
            await page.close()
            await browser_manager.restart_context()
            page = await browser_manager.new_page()

        retry = 0

        while retry < MAX_RETRIES_PER_PAGE:

            print(f"Loading page number: {page_number}")

            result = await driver.fetch_page(
                page,
                category_config,
                page_number
            )

            if result == "TOKEN_EXPIRED":
                retry += 1
                continue

            if not result:
                retry += 1
                continue

            if total_pages is None:
                total_pages = result["totalpages"]
                metadata["total_pages"] = total_pages

            records = result["records"]

            if not records:
                metadata["completed"] = True
                save_metadata(category_config, metadata)
                return

            save_page(category_config, page_number, records)

            metadata["last_page_scraped"] = page_number
            metadata["total_records"] += len(records)

            save_metadata(category_config, metadata)

            break

        else:
            print("Too many failures. Aborting.")
            return

        if page_number >= total_pages:
            metadata["completed"] = True
            save_metadata(category_config, metadata)
            print("Event completed.")
            return

        page_number += 1
        await apply_delay()
