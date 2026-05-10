import asyncio
import urllib.parse
from sites.base_driver import BaseDriver, NO_MORE_PAGES

class ChronosportDriver(BaseDriver):

    async def fetch_page(self, page, event_config, page_number):
        # The API used by chronosport.mx / meta.mx (sportmaniacs) can be from 
        # two types, it can return all data in the first request, or it can 
        # take a json name from the 1st call and then call it to get the data JSON. 
        # The type depends in the URL type        
        if page_number > 1:
            return NO_MORE_PAGES

        def extract_competition_id(url, url_type):
            if url_type==1:
                try:
                    return url.split("#")[-2].split('/')[-2]
                except Exception as e:
                    print(f"Error extracting competition_id: {e}")
            elif url_type==2:
                try:
                    return url.split("/")[-2]
                except Exception as e:
                    print(f"Error extracting competition_id: {e}")
            else:
                return None
        
        url = event_config['category_url']
        data_json_urls = set()
        url_type = None
        if url.endswith("results#rankings"):
            url_type = 1
        elif url.endswith("/rankings"):
            url_type = 2
        else:
            raise NotImplementedError("The URL type is not yet supported")
                
        
        catches = {"metadata":None, "final_data":None}

        competition_id = extract_competition_id(url, url_type)

        response_event = asyncio.Event()

        async def handle_response(response):
            nonlocal url_type
            nonlocal data_json_urls
            if url_type == 1:
                if competition_id in response.url:
                    content_type = response.headers.get("content-type", "")
                    if "application/json" not in content_type:
                        return  # Skip non-JSON responses
                
                    try:
                        data = await response.json()
                        if isinstance(data.get("data"), dict) and "Rankings" in data.get("data", {}):
                            print("--- Data JSON detected in the network ---")
                            catches["final_data"] = data
                            response_event.set()
                    except Exception as e:
                        print(f"Error processing JSON: {e}")
            elif url_type == 2:
                unquoted_url = urllib.parse.unquote(response.url)
                if f"/rankings/{event_config['distance']}" in unquoted_url and not catches["metadata"]:
                    print("--- First JSON detected in the network ---")
                    try:
                        metadata = await response.json()
                        catches["metadata"] = metadata

                        for item in metadata.get("data", []):
                            if item.get("split") == "META" and item.get("type") == "":
                                uri = item.get("resources", {}).get("uri")
                                if uri:
                                    data_json_urls.add(uri)

                    except Exception as e:
                        print(f"Error processing 1st JSON: {e}")
                elif data_json_urls and any(candidate in unquoted_url for candidate in data_json_urls):
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
                print("Event set successfully, data JSON captured")
            except asyncio.TimeoutError:
                    print("ERROR: JSON was never captured")
            
            page.remove_listener("response", handle_response)
            
            if url_type==1:
                data = catches["final_data"]["data"]["Rankings"]
                if not data:
                    print("JSON data is None")
                    return None
                    
                return {
                    "totalpages": 1,
                    "records": data
                }
            elif url_type==2:
                data = catches["final_data"]
                if not data:
                    print("JSON data is None")
                    return None

                print("JSON data has keys:", data.keys())

                return {
                    "totalpages": 1,
                    "records": data["data"]
                }

        except Exception as e:
            print("Exception during page fetch:", e)
            return None
    
    