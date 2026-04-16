class BaseDriver:

    async def fetch_page(self, page, event_config, page_number):
        raise NotImplementedError
