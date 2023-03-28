import asyncio
import base64
import json
import os
import time
from datetime import datetime

import requests
import urllib3
from pathlib import Path
import sys
import re
import random

from aiohttp import ClientHttpProxyError, ServerDisconnectedError
from dotenv import load_dotenv
from requests.exceptions import ProxyError
from tenacity import stop_after_attempt, retry, retry_if_exception_type

urllib3.disable_warnings()

from requests_futures.sessions import FuturesSession
from loguru import logger
import brotli

from unicornsdk_async import UnicornSdkAsync, PlatForm

# set auth token for the sdk
load_dotenv(verbose=True)
UnicornSdkAsync.auth(os.environ.get("ACCESS_TOKEN"))
# UnicornSdkAsync.config_sdk(api_url="https://dev.unicorn-bot.com")
# UnicornSdkAsync.config_sdk(api_url="http://127.0.0.1:9000")
cur_proxyuri = os.environ.get("PROXY_URI", "http://user:password@host:port")


EXEC_DIR = Path(__file__).resolve().parent


def now_time_ms():
    return int(datetime.now().timestamp() * 1000)

def now_time_str():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


TIMEOUT = 15

orgin = "https://api.nike.com"
# orgin = "https://unite.nike.com"
# orgin = "https://accounts.nike.com"


class ErrProxyEmptyFP(Exception):
    pass

class ErrEmptyFP(Exception):
    pass

class ErrEmptyIPS(Exception):
    pass

class ErrEmptyTL(Exception):
    pass

class ErrCookieExpire(Exception):
    pass



class Task:
    PROXYS = []
    UAS = []

    def __init__(self, idx, model_id=None, ua=None, proxy="http://127.0.0.1:8888"):
        self.proxy = proxy
        self.device = None
        self.useragent = None
        self.idx = idx
        self.model_id = model_id
        self.ua = ua
        self.client = FuturesSession()
        self.accept_language = "en-GB,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,zh;q=0.6"
        self.platform = PlatForm.WINDOWS
        self.device_session = UnicornSdkAsync.create_device_session(idx, self.platform)
        self.kasada_api = self.device_session.kasada_api()
        self.ips_content = None
        self.fp_content = None


    def get_proxys(self):
        cur_proxyuri = self.proxy
        # cur_proxyuri = "http://127.0.0.1:8888"

        proxies = {
            "http": cur_proxyuri,
            "https": cur_proxyuri,
        }
        return proxies
        # return None


    async def init_device(self, **kwargs):
        logger.debug(f"testid_{self.idx} init session ...")
        device = await self.device_session.init_session(
            f"testid_{self.idx}",
            platform=self.platform,
            accept_language=self.accept_language,
            device_model=self.model_id,
            ua=self.ua,
            **kwargs
        )
        self.useragent = device["user_agent"]
        self.device = device
        logger.debug(self.useragent)

    @retry(reraise=True,
           stop=stop_after_attempt(3),
           retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ProxyError))
           )
    async def req_ipsjs(self, ips_url):
        logger.debug(f"testid_{self.idx} 请求 ips.js ...")
        resp = await asyncio.wrap_future(self.client.get(ips_url, headers={
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": self.accept_language,
            "referer": f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp",
            "user-agent": self.useragent,
        }, proxies=self.get_proxys(), verify=False, timeout=TIMEOUT))
        ipsjs = resp.content
        self.ips_content = ipsjs
        if len(ipsjs) == 0:
            raise ErrEmptyIPS()
        return ipsjs

    @retry(reraise=True,
           stop=stop_after_attempt(3),
           retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ProxyError))
           )
    async def req_tl(self, kpparam):
        logger.debug(f"testid_{self.idx} 请求 tl ...")
        tl_url = f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/tl"
        resp = await asyncio.wrap_future(self.client.post(
            tl_url,
            headers={
                "accept": "*/*",
                "content-type": "application/octet-stream",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": self.accept_language,
                "referer": f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp",
                "origin": orgin,
                "user-agent": self.useragent,
                "x-kpsdk-ct": kpparam["x_kpsdk_ct"]
            },
            data=kpparam["body"],
            proxies=self.get_proxys(), verify=False,
            timeout=TIMEOUT
        ))

        logger.debug(resp.status_code)
        logger.debug(resp.text)
        if not resp.text:
            raise ErrEmptyTL()
        return resp

    @retry(reraise=True,
           stop=stop_after_attempt(3),
           retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ProxyError))
           )
    async def req_fp(self, recheck=False):
        fp_url = f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp"
        logger.debug(f"testid_{self.idx} 请求 fp ... {fp_url}")
        resp = await asyncio.wrap_future(self.client.get(fp_url, headers={
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": self.accept_language,
            "user-agent": self.useragent,
        }, proxies=self.get_proxys(), verify=False, timeout=TIMEOUT))
        if not recheck:
            self.fp_content = resp.content
        logger.debug(resp.status_code)
        logger.debug(resp.text)
        if not resp.text:
            if not recheck:
                raise ErrProxyEmptyFP()
            else:
                raise ErrEmptyFP()
        if resp.status_code == 403:
            raise Exception(f"Fp:{resp.status_code}")
        return resp

    async def test_task(self):
        try:
            # 1 init a device session firstly
            # task.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
            await self.init_device()
            ua = self.useragent

            # 2 request /fp to check if we need to solve challenge
            resp = await self.req_fp()
            x_kpsdk_ct = None
            x_kpsdk_st = None
            st_diff = None

            if resp.status_code == 429:
                # 429 means we need to solve the ips challenge
                # get the ips url from the /fp resp
                ips_url = re.match(r".+src=\"(\S+)\".+", resp.text)[1]
                ips_url = f'{orgin}{ips_url}'

                # 3 request ips.js content
                ipsjs = await self.req_ipsjs(ips_url)

                # 4 gen tl payload with the ips content
                kpparam = await self.kasada_api.kpsdk_parse_ips(
                    ips_url, ipsjs,
                    # timezone_info="GMT-0700 (Pacific Daylight Time)",
                    timezone_info="GMT+0000 (Greenwich Mean Time)",
                    referrer="https://www.nike.com/"
                )

                # 5 post payload to /tl to get valid ct
                resp = await self.req_tl(kpparam)

                # save current timestamp st_diff
                # each task has a seperate st_diff / st
                x_kpsdk_ct = resp.headers["x-kpsdk-ct"]
                x_kpsdk_st = resp.headers["x-kpsdk-st"]
                st_diff = now_time_ms() - int(x_kpsdk_st)
                logger.debug(f"testid_{self.idx} x_kpsdk_ct: {x_kpsdk_ct}")
                logger.debug(f"testid_{self.idx} x_kpsdk_st: {x_kpsdk_st}")
                logger.debug(f"testid_{self.idx} st_diff: {st_diff}")

                # 6 everytime you need to request to your target endpoint, request a new cd
                # use st / st_diff to calc new cd

                # now you have ct & cd

                import requests, uuid

                ct = x_kpsdk_ct
                visitorid = str(uuid.uuid4())

                for i in range(0, 30):
                    kpparam = await self.kasada_api.kpsdk_answer(x_kpsdk_ct, x_kpsdk_st, st_diff)
                    # logger.debug(kpparam)
                    cd = kpparam["x_kpsdk_cd2"]

                    headers = {
                        'authority': 'api.nike.com',
                        'accept': 'application/json',
                        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,zh;q=0.6',
                        'appid': 'com.nike.commerce.nikedotcom.web',
                        'cache-control': 'no-cache',
                        'content-type': 'application/json; charset=UTF-8',
                        'origin': 'https://www.nike.com',
                        'pragma': 'no-cache',
                        'referer': 'https://www.nike.com/',
                        'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': '"Windows"',
                        'sec-fetch-dest': 'empty',
                        'sec-fetch-mode': 'cors',
                        'sec-fetch-site': 'same-site',
                        'user-agent': ua,
                        'x-b3-sampled': '1',
                        'x-b3-spanid': '9e2f9883862782fb',
                        'x-b3-spanname': 'undefined',
                        'x-b3-traceid': '9e2f9883862782fb',
                        'x-kpsdk-cd': cd,
                        'x-kpsdk-ct': ct,
                        'x-nike-visitid': '1',
                        'x-nike-visitorid': visitorid,
                    }

                    json_data = [
                        {
                            'op': 'add',
                            'path': '/items',
                            'value': {
                                'itemData': {
                                    'url': '/au/t/air-jordan-1-low-shoes-v2kdOZ/553558-136',
                                },
                                'skuId': '271d929f-6fab-5eb7-8f55-a66744904866',
                                'quantity': 1,
                            },
                        },
                    ]
                    try:
                        response = requests.patch(
                            'https://api.nike.com/buy/carts/v2/AU/NIKE/NIKECOM?modifiers=VALIDATELIMITS,VALIDATEAVAILABILITY',
                            headers=headers,
                            json=json_data,
                            timeout=15,
                        )
                        logger.debug(i)
                        logger.debug(response.status_code)
                        logger.debug(response.text)

                        if response.status_code == 429:
                            logger.error("429")
                            break
                        if response.status_code == 200 and len(response.text) == 0:
                            logger.error("200 empty!")
                            break
                        if response.status_code != 200:
                            break
                        await asyncio.sleep(1)

                        if "x-kpsdk-ct" in response.headers:
                            ct = response.headers["x-kpsdk-ct"]
                            logger.debug(f"change ct to {ct}")
                    except requests.exceptions.Timeout:
                        logger.debug("timeout ...")

            else:
                logger.debug(resp.status_code)
                logger.debug(resp.text)

        except (ErrEmptyFP, ErrProxyEmptyFP) as e:
            raise
        except ErrEmptyTL as e:
            raise
        except (ClientHttpProxyError, ServerDisconnectedError, ProxyError) as e:
            raise
        except Exception as e:
            logger.opt(exception=True).error(e)
            raise
        finally:
            # task.save_ips()
            pass


async def main():
    # init sdk
    await UnicornSdkAsync.init()

    task = Task("task_id_xxx", proxy=cur_proxyuri)
    await task.test_task()


    # deinitsdk
    await UnicornSdkAsync.deinit()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.2))
    loop.close()
