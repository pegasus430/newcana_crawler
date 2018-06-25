import sys
import json

from runner import run
from httpclient import HttpClient
from jsonutils import loadJson, try_get_list
from disp_filter import get_dispensary_filter
from weedmaps_helpers import WeedMapsDespensaryExtractor, WeedMapsDetailsExtractor


class WeedMapsDispensaryScraper(object):
    def __init__(self, dispesary_filter, http_client):
        self._http_client = http_client
        self._weedmaps_disp_extractor = WeedMapsDespensaryExtractor(
            dispesary_filter,
            WeedMapsDetailsExtractor(HttpClient())
        )

        self._url = "https://api-g.weedmaps.com/wm/v2/location?include%5B%5D=" \
                    "regions.listings&region_slug={0}&page_size=150"

    def produce(self, state):
        should_continue = True
        while should_continue:
            url = self._url.format(state.replace(' ', '-'))
            response = self._http_client.get(url)
            json_data = loadJson(response.content)
            listings = try_get_list(json_data, "data", "regions", "dispensary", "listings")
            if len(listings) == 0:
                break
            for l in listings[0]:
                url_list = try_get_list(l, "slug")
                if len(url_list) > 0:
                    yield url_list[0]
            should_continue = False

    def consume(self, item_from_poroduce):
        if not item_from_poroduce:
            return None
        url = self.reconstruct_url(item_from_poroduce)
        response = self._http_client.get(url)
        if response.success:
            json_data = loadJson(response.content)
            return self._weedmaps_disp_extractor.extract(json_data)
        return None

    @staticmethod
    def reconstruct_url(url_part):
        return "https://api-g.weedmaps.com/wm/web/v1/listings/" + url_part + "/menu?type=dispensary"


def scrape(arr):
    dispFilter = get_dispensary_filter(arr)
    wmScraper = WeedMapsDispensaryScraper(dispFilter, HttpClient())
    result = run(dispFilter.get_state_names(), wmScraper.produce, wmScraper.consume)

    return json.dumps(result)


if __name__ == "__main__":
    print (scrape(sys.argv[1:]))