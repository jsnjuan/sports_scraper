# Sentinel returned by drivers that have no more pages to fetch (not an error).
NO_MORE_PAGES = "NO_MORE_PAGES"


class BaseDriver:

    async def fetch_page(self, page, event_config, page_number):
        raise NotImplementedError
