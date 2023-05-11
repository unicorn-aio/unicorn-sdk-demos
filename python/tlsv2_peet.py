import json
import os

import requests
from dotenv import load_dotenv
from loguru import logger

from unicornsdk import UnicornSdk, TlsSession

load_dotenv(verbose=True)
acess_token = os.environ.get("ACCESS_TOKEN")
cur_proxyuri = os.environ.get("PROXY_URI")

session = requests.Session()
headers = {
    "content-type": "application/json",
    "sec-ch-ua": "\"Not_A Brand\";v=\"99\", \"Brave\";v=\"109\", \"Chromium\";v=\"109\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "accept": "application/graphql+json, application/json",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "X-AUTHORIZATION": f"bearer {acess_token}",
    "X-TLS-URL": "https://tls.peet.ws/api/all",
    "X-TLS-PROXY": cur_proxyuri,
}

resp = session.get(
    url="https://us.unicorn-bot.com/api/tls/forward_v2/",
    headers=headers,
)

logger.debug(resp.status_code)
logger.debug(json.dumps(resp.json(), indent=4))
