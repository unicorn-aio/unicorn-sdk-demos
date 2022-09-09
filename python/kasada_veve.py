import json
import os


from loguru import logger

from unicornsdk import UnicornSdk, Session

UnicornSdk.auth("your_access_token")

session = Session()
session.config_for_kasada({
    'mobile.api.prod.veve.me': {
        'POST': [
            '/graphql',
            '/api/auth/*'
        ]
    }
})

orgin = "https://mobile.api.prod.veve.me"
cur_proxyuri = "http://user:password@host:port"
proxies = {
    "http": cur_proxyuri,
    "https": cur_proxyuri,
}

session.headers = {
    'client-version': "1.0.619",
    'cache-control': 'no-cache,no-store',
    'client-name': 'veve-app-ios',
    'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
    'client-model': 'iphone 11 pro max',
    'pragma': 'no-cache',
    'client-brand': 'apple',
    'x-kpsdk-v': 'i-1.6.0',
    'accept-language': 'en-us',
    'expires': '0',
    'client-manufacturer': 'apple',
    'client-installer': 'appstore',
    'accept': 'application/json, text/plain, */*',
    'content-type': 'application/json;charset=utf-8',
    'accept-encoding': 'gzip, deflate, br',
    'client-id': "5c973397-8ba8-43a6-ab50-15e1f650e9ca",
    "referer": f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp",
}

fp_url = f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp"
session.get(fp_url, proxies=proxies)


response = session.post(
    'https://mobile.api.prod.veve.me/graphql',
    data=json.dumps(
        {
            'operationName': 'AppMetaInfo',
            'variables': {},
            'query': '''query AppMetaInfo { minimumMobileAppVersion featureFlagList { name enabled __typename }}'''
        },
        separators=(',', ':')
    ),
    headers={
        'Content-Type': 'application/json',
        'client-operation': 'AppMetaInfo'
    },
    proxies=proxies,
)
logger.debug(response.status_code)
logger.debug(response.text)
