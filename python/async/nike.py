"""
pyinstaller -F nike_ct_gen.py -n nike_ct_gen  --key L88V*7z$8x3pq6
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
import urllib3
from pathlib import Path
import sys
import re
import random

from dotenv import load_dotenv

urllib3.disable_warnings()

from requests_futures.sessions import FuturesSession
from loguru import logger
import brotli

from unicornsdk_async import UnicornSdkAsync, PlatForm

# set auth token for the sdk
load_dotenv(verbose=True)
UnicornSdkAsync.auth(os.environ.get("ACCESS_TOKEN"))

EXEC_DIR = Path(__file__).resolve().parent


def now_time_ms():
    return int(datetime.now().timestamp() * 1000)

def now_time_str():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


TIMEOUT = 10

# orgin = "https://api.nike.com"
# orgin = "https://unite.nike.com"
orgin = "https://accounts.nike.com"

UAS = [
    "Mozilla/5.0 (Linux; Android 10; Pixel 4 Build/QQ1D.200205.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/98.0.4758.101 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Pixel 3a Build/QQ1A.191205.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/96.0.4664.104 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Pixel 3 Build/QP1A.190711.019; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/98.0.4758.101 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Pixel 3 Build/QQ1A.200105.003; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/96.0.4664.104 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Pixel 3a Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/98.0.4758.101 Mobile Safari/537.36",
]


class Task:
    PROXYS = []

    def __init__(self, idx):
        self.proxy = self.get_proxy()
        self.proxies = None
        self.device = None
        self.useragent = None
        self.idx = idx
        self.client = FuturesSession()
        self.proxies = self.get_proxys(self.proxy)
        self.accept_language = "en-US,en;q=0.9"
        # zh-CN,zh;q=0.9,en;q=0.8
        self.platform = PlatForm.WINDOWS
        self.device_session = UnicornSdkAsync.create_device_session(idx, self.platform)
        self.kasada_api = self.device_session.kasada_api(self.proxies["http"])

    @classmethod
    def load_proxys(cls, proxyfile):
        with open(proxyfile) as f:
            for i in f:
                if i:
                    ip, port, user, passwd = i.strip().split(":")
                    cls.PROXYS.append((ip, port, user, passwd))
        pass

    @classmethod
    def remove_proxy(cls, proxy):
        cls.PROXYS.remove(proxy)

    @classmethod
    def get_proxy(cls):
        return cls.PROXYS.pop(0)

    @classmethod
    def put_proxy(cls, proxy):
        cls.PROXYS.append(proxy)

    def get_proxys(self, proxy):
        ip, port, user, passwd = proxy
        cur_proxyuri = f"http://{user}:{passwd}@{ip}:{port}"
        # cur_proxyuri = "http://127.0.0.1:8888"

        proxies = {
            "http": cur_proxyuri,
            "https": cur_proxyuri,
        }
        return proxies
        # return None


    async def init_device(self, **kwargs):
        ua = random.choice(UAS)
        logger.debug(f"testid_{self.idx} init session ...")
        device = await self.device_session.init_session(
            f"testid_{self.idx}",
            platform=self.platform,
            accept_language=self.accept_language,
            **kwargs
        )
        self.useragent = device["user_agent"]
        self.device = device
        logger.debug(self.useragent)

    def set_proxy(self, proxy):
        self.proxy = proxy
        self.proxies = self.get_proxys(proxy)

    async def req_ipsjs(self, ips_url):
        logger.debug(f"testid_{self.idx} 请求 ips.js ...")
        resp = await asyncio.wrap_future(self.client.get(ips_url, headers={
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": self.accept_language,
            "referer": f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp",
            "user-agent": self.useragent,
        }, proxies=self.proxies, verify=False, timeout=TIMEOUT))
        ipsjs = resp.content
        if len(ipsjs) == 0:
            raise Exception("ips.js 长度为 0！")
        # with open(f"z:/ips-{now_time_str()}.js", "wb") as f:
        #     f.write(ipsjs)
        return ipsjs

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
            proxies=self.proxies, verify=False,
            timeout=TIMEOUT
        ))

        logger.debug(resp.status_code)
        logger.debug(resp.text)
        if not resp.text:
            raise Exception("empty tl!")
        return resp

    async def req_fp(self):
        fp_url = f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp"
        logger.debug(f"testid_{self.idx} 请求 fp ... {fp_url}")
        resp = await asyncio.wrap_future(self.client.get(fp_url, headers={
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": self.accept_language,
            "user-agent": self.useragent,
        }, proxies=self.proxies, verify=False, timeout=TIMEOUT))
        logger.debug(resp.status_code)
        logger.debug(resp.text)
        return resp

    async def solve_ct(self):
        try:
            resp = await self.req_fp()
            x_kpsdk_ct = None
            x_kpsdk_st = None
            st_diff = None
            # if True:
            if resp.status_code == 429:
                # ct = resp.headers["x-kpsdk-ct"]
                # &x-kpsdk-v=i-1.4.0
                # ips_url = f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/ips.js?ak_bmsc_nke-2.3={ct}"
                ips_url = re.match(r".+src=\"(\S+)\".+", resp.text)[1]
                ips_url = f'{orgin}{ips_url}'

                ipsjs = await self.req_ipsjs(ips_url)

                kpparam = await self.kasada_api.kpsdk_parse_ips(
                    ips_url, ipsjs,
                    timezone_info="GMT-0700 (Pacific Daylight Time)",
                    referrer="https://www.nike.com/"
                )

                resp = await self.req_tl(kpparam)

                x_kpsdk_ct = resp.headers["x-kpsdk-ct"]
                x_kpsdk_st = resp.headers["x-kpsdk-st"]
                st_diff = now_time_ms() - int(x_kpsdk_st)
                logger.debug(f"testid_{self.idx} x_kpsdk_ct: {x_kpsdk_ct}")
                logger.debug(f"testid_{self.idx} x_kpsdk_st: {x_kpsdk_st}")
                logger.debug(f"testid_{self.idx} st_diff: {st_diff}")
                # kpparam = await sdk.kpsdk_answer(x_kpsdk_ct, x_kpsdk_st, st_diff)
                # logger.debug(kpparam)
            else:
                logger.debug(resp.status_code)
                logger.debug(resp.text)
        except Exception as e:
            logger.error(f"testid_{self.idx} {e}")
            raise e
        return x_kpsdk_ct, x_kpsdk_st, st_diff



async def main():
    # init sdk
    await UnicornSdkAsync.init()

    # 加载代理
    Task.load_proxys("./proxys.txt")

    task = Task(0)
    await task.init_device()
    await task.solve_ct()

    await asyncio.sleep(2)
    resp = await task.req_fp()
    # logger.debug(resp.status_code)
    # logger.debug(resp.text)

    for i in range(0, 1):
        await asyncio.sleep(10)
        resp = await task.req_fp()

    # deinitsdk
    await UnicornSdkAsync.deinit()
    sys.exit(0)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.2))
    loop.close()
