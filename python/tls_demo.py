from loguru import logger

from unicornsdk import UnicornSdk, TlsSession

access_token = "your_access_token"
UnicornSdk.auth(access_token)

cur_proxyuri = "http://user:password@host:port"
proxies = {
    "http": cur_proxyuri,
    "https": cur_proxyuri,
}

session = TlsSession()
session.headers = {
    "host": "secure.louisvuitton.com",
    "connection": "keep-alive",
    "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "dnt": "1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "sec-fetch-site": "none",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,ru;q=0.7",
}

# resp = session.get("https://baidu.com/")
# logger.debug(resp.status_code)


resp = session.get("https://secure.louisvuitton.com", proxies=proxies)
logger.debug(resp.status_code)
logger.debug(resp.cookies)

params = {
    "storeLang": "fra-fr",
    "pageType": "storelocator_section",
    "skuIdList": "1A9JGQ",
    "_": "83375",
}

# this site need tls fp
resp = session.get("https://secure.louisvuitton.com/ajaxsecure/getStockLevel.jsp", params=params, proxies=proxies)
logger.debug(resp.status_code)
logger.debug(resp.text)
