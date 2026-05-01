import asyncio
from sites.base_driver import BaseDriver, NO_MORE_PAGES

class ChronosportDriver(BaseDriver):

    async def fetch_page(self, page, event_config, page_number):
        # The API used by chronosport.mx / meta.mx (sportmaniacs) returns all the data in a single JSON 
        # requested by the client, so we only need to fetch the data on page 1, and return None for 
        # consecutive pages to stop, this in order to align the most complex pagination logic implemented 
        # for other driver
        if page_number > 1:
            return NO_MORE_PAGES

        def extract_competition_id(url):
            try:
                return url.split("#")[-1]
            except Exception as e:
                print("Error extracting competition_id: {e}")

        url = event_config['category_url']
        catches = {"final_data":None}

        competition_id = extract_competition_id(url)

        response_event = asyncio.Event()

        async def handle_response(response):
            if competition_id in response.url:
                content_type = response.headers.get("content-type", "")
                if "application/json" not in content_type:
                    return  # Skip non-JSON responses
            
                print("--- Data JSON detected in the network ---")
                try:
                    data = await response.json()
                    catches["final_data"] = data
                    response_event.set()
                except Exception as e:
                    print(f"Error processing JSON: {e}")

            
        page.on("response", handle_response)
        # We have processed up to this point

        try:
            await page.goto(url, wait_until="domcontentloaded")
            try:
                await asyncio.wait_for(response_event.wait(), timeout=10.0)
                print("Event set successfully, data JSON captured")
            except asyncio.TimeoutError:
                    print("ERROR: JSON was never captured")
            
            page.remove_listener("response", handle_response)
            
            data = catches["final_data"]["data"]["Rankings"]
            if not data:
                print("JSON data is None")
                return None
                
            return {
                "totalpages": 1,
                "records": data
            }

        except Exception as e:
            print("Exception during page fetch:", e)
            return None
    
    