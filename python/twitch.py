import base64
import json
import os
import time

from dotenv import load_dotenv
from loguru import logger

from unicornsdk import UnicornSdk, Session, TlsSession

load_dotenv(verbose=True)
UnicornSdk.auth(os.environ.get("ACCESS_TOKEN"))
UnicornSdk.config_sdk(api_url="https://dev.unicorn-bot.com")
# UnicornSdk.config_sdk(api_url="http://localhost:9000")

# session = Session()
session = TlsSession()
session.config_tls(http2=False)
session.config_for_kasada({
    'gql.twitch.tv': {
        'POST': [
            '/gql',
            "/integrity",
        ]
    },
    "passport.twitch.tv": {
        "POST": [
            "/xxx"
        ]
    }
})

orgin = "https://gql.twitch.tv"
cur_proxyuri = os.environ.get("PROXY_URI")
proxies = {
    "http": cur_proxyuri,
    "https": cur_proxyuri,
}

session.headers = {
    'cache-control': 'no-cache,no-store',
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    'pragma': 'no-cache',
    'accept-language': 'en-US,en;q=0.9',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    "referer": f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp",
}

# check the challenge
fp_url = f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp"
resp = session.get(fp_url, proxies=proxies)
logger.debug(resp.status_code)
logger.debug(resp.text)

# now it should has been solved automatic
time.sleep(2)
resp = session.get(fp_url, proxies=proxies)
logger.debug(resp.status_code)
logger.debug(resp.text)

# check if cookie could last long
time.sleep(10)
resp = session.get(fp_url, proxies=proxies)
logger.debug(resp.status_code)
logger.debug(resp.text)

resp = session.post(
    "https://gql.twitch.tv/integrity",
    headers={
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.twitch.tv/",
        "Client-Id": "kimne78kx3ncx6brgo4mv6wki5h1ko",
        "X-Device-Id": "SFXAMVyKvxdRcutbG4JZUseUjWg4jzhn",
        "Client-Session-Id": "618d0eff052e1351",
        "Client-Version": "40aeca85-399f-45a8-9f12-30caf2c0f495",
        "x-kpsdk-ct": None,
        "x-kpsdk-cd": None,
        "Origin": "https://www.twitch.tv",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Content-Length": "0",
    },
    proxies=proxies
)
logger.debug(resp.status_code)
logger.debug(json.dumps(resp.json(), indent=4))



