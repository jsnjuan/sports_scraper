from config.settings import CONTEXT_RESTART_INTERVAL, MAX_RETRIES_PER_PAGE
from core.persistence import (
    load_metadata,
    save_metadata,
    save_page,
)
from core.delays import apply_delay
from sites.base_driver import NO_MORE_PAGES

async def run_event(browser_manager, driver, event_config):

    did_any_work = False
    categories = event_config["categories"]
    for i, category in enumerate(categories):

        print(f"Starting category: {category}")

        did_work = await run_category(
            browser_manager,
            driver,
            event_config,
            category
        )
        
        if did_work:
            did_any_work = True
            # Only delay if there are more categories to process in this event
            if i < len(categories) - 1:
                await apply_delay(stage='category')

    return did_any_work


async def run_category(browser_manager, driver, event_config, category):

    category_config = {
        **event_config,
        "distance": category
    }

    did_work = await run_pages(browser_manager, driver, category_config)
    # Note: run_pages already handles its own internal delays between pages.
    # We return did_work so run_event can decide if it needs to delay before the next category.
    return did_work


async def run_pages(browser_manager, driver, category_config):

    metadata = load_metadata(category_config)

    if metadata and metadata.get("completed"):
        print("Event is completed. Skipping.")
        return False

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

    try:
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

                if result == NO_MORE_PAGES:
                    return True

                if not result:
                    retry += 1
                    continue

                if total_pages is None:
                    total_pages = result.get("totalpages", 1)
                    metadata["total_pages"] = total_pages

                records = result["records"]

                if not records:
                    metadata["completed"] = True
                    save_metadata(category_config, metadata)
                    return True

                save_page(category_config, page_number, records)

                metadata["last_page_scraped"] = page_number
                metadata["total_records"] += len(records)

                save_metadata(category_config, metadata)

                break

            else:
                print("Too many failures. Aborting.")
                return True

            if page_number >= total_pages:
                metadata["completed"] = True
                save_metadata(category_config, metadata)
                print("Event completed.")
                return True

            page_number += 1
            await apply_delay(stage='page')
    finally:
        await page.close()
