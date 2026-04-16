import asyncio
from sites.base_driver import BaseDriver


class AsDeporteDriver(BaseDriver):

    async def fetch_page(self, page, event_config, page_number):

        url = (
            f"{event_config['base_url']}"
            f"?distancia={event_config['distance']}"
            f"&page={page_number}"
            f"&perpage={event_config['per_page']}"
        )

        import json
        graphql_data = None
        response_event = asyncio.Event()

        async def handle_response(response):
            nonlocal graphql_data
            if "/_/graphql" in response.url and response.request.method == "POST":
                try:
                    data = await response.json()
                    if data and "data" in data:
                        target = data["data"].get("getEventResults") or data["data"].get("findResult")
                        if target and "records" in target:
                            graphql_data = target
                            response_event.set()
                except Exception:
                    pass

        page.on("response", handle_response)

        try:
            await page.goto(url, wait_until="domcontentloaded")
            try:
                await asyncio.wait_for(response_event.wait(), timeout=10.0)
                print("Event set successfully!")
            except asyncio.TimeoutError:
                print("Timeout waiting for graphql response!")
            
            page.remove_listener("response", handle_response)
            
            data = graphql_data
            if not data:
                print("Graphql data is None")
                return None

            print("Graphql data has keys:", data.keys())

            return data

        except Exception as e:
            print("Exception during page fetch:", e)
            return None
