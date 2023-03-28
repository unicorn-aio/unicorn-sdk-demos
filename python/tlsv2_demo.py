import json
import os

import requests
from dotenv import load_dotenv
from loguru import logger

from unicornsdk import UnicornSdk, TlsSession

load_dotenv(verbose=True)
UnicornSdk.auth(os.environ.get("ACCESS_TOKEN"))

acess_token = os.environ.get("ACCESS_TOKEN")
cur_proxyuri = os.environ.get("PROXY_URI")

session = requests.Session()
headers = {
    "content-type": "application/json",
    "accept": "application/graphql+json, application/json",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjc2NjEyMjQyLCJpYXQiOjE2NzQwMjAyNDIsImp0aSI6Ijk0YTEwM2RjYTRhNzQyMTViN2Q3MTQ3NTU0YTUwOTU3IiwidXNlcl9pZCI6MTI3fQ.-n6QW-YylN1hhutgOocnxVf7p9mworZZYgRwQ7EKVdY",
    "origin": "https://sportsbet.io",
    "referer": "https://sportsbet.io/sports?c=home",
    "sec-ch-ua": "\"Not_A Brand\";v=\"99\", \"Brave\";v=\"109\", \"Chromium\";v=\"109\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-gpc": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "X-AUTHORIZATION": f"bearer {acess_token}",
    "X-TLS-URL": "https://sportsbet.io/graphql",
    "X-TLS-PROXY": cur_proxyuri,
    "X-TLS-NO-RET-JSON": "true",
}

resp = session.post(
    url="https://us.unicorn-bot.com/api/tls/forward_v2",
    headers=headers,
    data="{\"query\":\"query MyAllBalancesQuery($conversionCurrency: String!) {  banking {    id    myAllBalances(conversionCurrency: $conversionCurrency) {      edges {        node {          ...BalanceFragment          __typename        }        __typename      }      __typename    }    __typename  }}fragment BalanceFragment on BankingBalance {  id  currency  totalBalance  realBalance  convertedTotalBalance  __typename}\",\"operationName\":\"MyAllBalancesQuery\",\"variables\":{\"conversionCurrency\":\"USD\"}}"
)

logger.debug(resp.status_code)
logger.debug(json.dumps(resp.json(), indent=4))
