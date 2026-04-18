import asyncio
from sites.base_driver import BaseDriver, NO_MORE_PAGES

class MetamxDriver(BaseDriver):

    async def fetch_page(self, page, event_config, page_number):
        # The API used by meta.mx/sportmaniacs returns all the data in a single JSON requested by the client
        # So we only need to fetch the data on page 1, and return None for consecutive pages to stop, 
        # this in order to align the most complex pagination logic implemented for other driver
        if page_number > 1:
            return NO_MORE_PAGES

        def extract_competition_id(url):
            try:
                return url.split("/")[-2]
            except Exception as e:
                print("Error extracting competition_id: {e}")

        url = event_config['base_url']
        catches = {"metadata":None, "final_data":None}
        data_json_url = None
        competition_id = extract_competition_id(url)

        response_event = asyncio.Event()

        async def handle_response(response):
            nonlocal data_json_url
            if f"/rankings/{event_config['distance']}" in response.url and not catches["metadata"]:
                print("--- First JSON detected in the network ---")
                try:
                    metadata = await response.json()
                    catches["metadata"] = metadata
                    data_json_url = metadata["data"][0]["resources"]["uri"]
                except Exception as e:
                    print(f"Error processing 1st JSON: {e}")
            elif data_json_url and data_json_url in response.url:
                print("--- Second JSON detected in the network ---")
                try:
                    catches["final_data"] = await response.json()
                    response_event.set()
                except Exception as e:
                    print(f"Error processing 2nd JSON: {e}")
                    pass
            
        page.on("response", handle_response)
        # We have processed up to this point

        try:
            await page.goto(url, wait_until="domcontentloaded")
            try:
                await asyncio.wait_for(response_event.wait(), timeout=10.0)
                print("Event set successfully, both JSONs captured")
            except asyncio.TimeoutError:
                if not catches["metadata"]:
                    print("ERROR: 1st JSON captured, 2nd JSON never went through the network | URL didn't match.")
                elif not catches["metadata"]:
                    print("ERROR: URI was obtained, 2nd JSON was never loaded")
            
            page.remove_listener("response", handle_response)
            
            data = catches["final_data"]
            if not data:
                print("JSON data is None")
                return None

            print("JSON data has keys:", data.keys())

            return data

        except Exception as e:
            print("Exception during page fetch:", e)
            return None
