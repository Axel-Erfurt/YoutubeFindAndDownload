import requests
import logging
import json
import re

class searchyt(object):
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"
    config_regexp = re.compile(r'ytcfg\.set\(({.+?})\);')

    def __init__(self):
        self.req = requests.Session()
        self.log = logging.getLogger("ytsearch")
        headers = {"connection": "keep-alive",
                    "pragma": "no-cache",
                    "cache-control": "no-cache",
                    "upgrade-insecure-requests": "1",
                    "user-agent": searchyt.ua,
                    "accept": "*/*",
                    "accept-language": "en-US,en;q=0.9",
                    "referer": "https://www.youtube.com/",
                    "dnt": "1"}
        self.req.headers.update(headers)
        self._populate_headers()
    
    def _populate_headers(self):
        resp = self.req.get("https://www.youtube.com/")

        if resp.status_code != 200:
            self.log.debug(resp.text)
            raise Exception(f"error while scraping youtube (response code {resp.status_code})")

        result = searchyt.config_regexp.search(resp.text)
        if not result:
            self.log.debug(resp.text)
            raise Exception(f"error while searching for configuration")

        config = json.loads(result.group(1))
        if not config:
            self.log.debug(resp.text)
            raise Exception(f"error while parsing headers")

        updated_headers = {
            "x-spf-referer": "https://www.youtube.com/",
            "x-spf-previous": "https://www.youtube.com/",
            "x-youtube-utc-offset": "120",
            "x-youtube-client-name": str(config["INNERTUBE_CONTEXT_CLIENT_NAME"]),
            "x-youtube-variants-checksum": str(config["VARIANTS_CHECKSUM"]),
			"x-youtube-page-cl" : str(config["PAGE_CL"]),
			"x-youtube-client-version": str(config["INNERTUBE_CONTEXT_CLIENT_VERSION"]),
			"x-youtube-page-label": str(config["PAGE_BUILD_LABEL"])
        }
        self.log.debug(f"Headers: {updated_headers}")
        self.req.headers.update(updated_headers)

    def _traverse_data(self, data, match):
        # list
        if isinstance(data, list):
            for d in data:
                if isinstance(d, (dict, list)):
                    yield from self._traverse_data(d, match)
            return
        
        # dict
        for key, value in data.items():
            #print(key)
            # if key matches
            if key == match:
                yield value
            if isinstance(value, (dict, list)):
                yield from self._traverse_data(value, match)

    def _parse_videos(self, json_result):
        try:
            json_dict = json.loads(json_result)[1]

            #self.log.debug(json_dict)
            videos = []
            for v in self._traverse_data(json_dict, "videoRenderer"):
                vid = {}
                vid['title'] = v['title']['runs'][0]['text']
                vid['author'] = v['ownerText']['runs'][0]['text']
                vid['id'] = v["videoId"]
                vid['thumb'] = v['thumbnail']['thumbnails'][-1]['url'].split('?', maxsplit=1)[0]
                videos.append(vid)

            return videos
        except Exception as ex:
            self.log.debug(json_result)
            raise ex

    def search(self, query):
        if not isinstance(query, str):
            raise Exception("search query must be a string type")
        
        resp = self.req.get("https://www.youtube.com/results", params = {"search_query": query, "pbj": "1"})

        if resp.status_code != 200:
            self.log.debug(resp.text)
            raise Exception(f"error while getting search results page (status code {resp.status_code})")

        return self._parse_videos(resp.text)
