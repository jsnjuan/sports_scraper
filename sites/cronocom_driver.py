import asyncio
from sites.base_driver import BaseDriver

class CronocomDriver(BaseDriver):

    async def fetch_page(self, page, event_config, page_number):
        # The Cronocom API returns all the data in a single JSON requested by the client
        # So we only need to fetch the data on page 1, and return None for consecutive pages to stop
        if page_number > 1:
            return None

        base_url = event_config['base_url']
        expected_json_path = f"data/data_{event_config['distance'].lower()}.json"
        
        if base_url.endswith("index.html"):
            json_url = base_url.replace("index.html", expected_json_path)
        elif base_url.endswith("/"):
            json_url = base_url + expected_json_path
        else:
            json_url = base_url + "/" + expected_json_path

        try:
            # We directly fetch the JSON endpoint instead of relying on the UI to trigger it
            response = await page.goto(json_url, wait_until="networkidle")
            
            if not response or response.status != 200:
                print(f"Failed to fetch {json_url}, HTTP status: {response.status if response else 'Unknown'}")
                return None
            
            # Read the JSON response body directly
            cronocom_data = await response.json()
            
            if not cronocom_data or not isinstance(cronocom_data, list):
                print(f"Empty or invalid data returned for distance {event_config['distance']}")
                return None

            # Structure it the way the engine expects
            return {
                "totalpages": 1,
                "records": cronocom_data
            }

        except Exception as e:
            print("Exception during cronocom direct API fetch:", e)
            return None
