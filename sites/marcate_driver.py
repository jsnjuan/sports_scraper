import requests
from sites.base_driver import BaseDriver, NO_MORE_PAGES

class MarcateDriver(BaseDriver):

    async def fetch_page(self, page, event_config, page_number):
        # The API used by marcate returns all the data in a single JSON requested by the client
        # So we only need to fetch the data directly with the correct payload.
        if page_number > 1:
            return NO_MORE_PAGES

        base_url = event_config['category_url']
        try:
            competition_id = base_url.rstrip('/').split("/")[-1]
        except Exception as e:
            print(f"Error extracting competition_id from {base_url}: {e}")
            return None

        api_url = "https://resultados.marcate.events/eventos/overAll"
        payload = {
            "distancia": event_config['distance'], 
            "carreraId": competition_id
        }

        try: 
            # We use the API endpoint for the POST request instead of the result page URL
            response = requests.post(api_url, data=payload)
            response.raise_for_status()
            data = response.json()
            
            if data:
                return {
                    "totalpages": 1,
                    "records": data
                }
            else:
                print(f"No data returned for Marcate event {competition_id} and distance {event_config['distance']}")
                return NO_MORE_PAGES
            
        except Exception as e:
            print("Exception during Marcate page fetch:", e)
            return None

