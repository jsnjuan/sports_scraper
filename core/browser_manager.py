from playwright.async_api import async_playwright
from config.settings import HEADLESS


class BrowserManager:

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=HEADLESS)
        await self._create_context()

    async def _create_context(self):
        self.context = await self.browser.new_context()

    async def new_page(self):
        return await self.context.new_page()

    async def restart_context(self):
        print("♻ Reiniciando contexto completo...")
        await self.context.close()
        await self._create_context()

    async def close(self):
        await self.browser.close()
        await self.playwright.stop()
