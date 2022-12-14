import json
import time
from collections import OrderedDict

from loguru import logger

from unicornsdk import UnicornSdk, Session

UnicornSdk.auth("your_access_token")

cur_proxyuri = "http://user:password@host:port"
proxies = {
    "http": cur_proxyuri,
    "https": cur_proxyuri,
}


session = Session()
session.config_for_kasada({
    'www.gamestop.ca': {
        'POST': [
            '/login_or_anything_blabla',
            '/api/auth/*'
        ]
    }
})

orgin = "https://www.gamestop.ca"

session.headers = {
    'cache-control': 'no-cache,no-store',
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    'content-type': 'application/json;charset=utf-8',
    'accept-encoding': 'gzip, deflate, br',
}

fp_url = f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp"

# check the challenge
resp = session.get(fp_url, proxies=proxies)
logger.debug(resp.status_code)
logger.debug(resp.text)

# now it should has been solved automatic

# now we try again
resp = session.get(fp_url, proxies=proxies)
logger.debug(resp.status_code)
logger.debug(resp.text)

