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


EXEC_DIR = Path(__file__).resolve().parent


def now_time_ms():
    return int(datetime.now().timestamp() * 1000)

def now_time_str():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


TIMEOUT = 15

# orgin = "https://api.nike.com"
# orgin = "https://unite.nike.com"
orgin = "https://accounts.nike.com"


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

    def __init__(self, idx, model_id=None, ua=None):
        self.proxy = None
        self.proxies = None
        self.device = None
        self.useragent = None
        self.idx = idx
        self.model_id = model_id
        self.ua = ua
        self.client = FuturesSession()
        self.proxies = None
        self.accept_language = "de-DE,de;q=0.9"
        # zh-CN,zh;q=0.9,en;q=0.8
        self.platform = PlatForm.WINDOWS
        self.device_session = UnicornSdkAsync.create_device_session(idx, self.platform)
        self.kasada_api = self.device_session.kasada_api()
        self.change_proxy()
        self.ips_content = None
        self.fp_content = None

    @classmethod
    def load_proxys(cls, proxyfile):
        with open(proxyfile) as f:
            for i in f:
                if i:
                    ip, port, user, passwd = i.strip().split(":")
                    cls.PROXYS.append((ip, port, user, passwd))
        r = random.shuffle(cls.PROXYS)
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

    def change_proxy(self, black=False):
        if not black and self.proxy:
            Task.put_proxy(self.proxy)
        self.proxy = self.get_proxy()
        self.proxies = self.get_proxys(self.proxy)
        self.kasada_api.proxy_uri = self.proxies["http"]
        # 重置 cookie
        self.client = FuturesSession()

    @classmethod
    def load_uas(cls, uas_file):
        with open(uas_file) as f:
            for i in f:
                if i:
                    ua = i.strip()
                    cls.UAS.append(ua)
        r = random.shuffle(cls.UAS)

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

    def set_proxy(self, proxy):
        self.proxy = proxy
        self.proxies = self.get_proxys(proxy)

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
        }, proxies=self.proxies, verify=False, timeout=TIMEOUT))
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
            proxies=self.proxies, verify=False,
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
        }, proxies=self.proxies, verify=False, timeout=TIMEOUT))
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

    async def solve_ct(self):
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
        return x_kpsdk_ct, x_kpsdk_st, st_diff

    def save_ips(self):
        if self.ips_content:
            with open(f"z:/ips-{self.platform}-{now_time_str()}_{self.idx}", "wb") as f:
                f.write(self.ips_content)

    def save_fp(self):
        with open(f"z:/fp-{self.platform}-{now_time_str()}.js", "wb") as f:
            f.write(self.fp_content)


async def single_task(task_id, model_id=None, ua=None):
    task = Task(task_id, model_id=model_id, ua=ua)

    await asyncio.sleep(random.randint(1, 5))
    retry = 3
    def continue_retry():
        nonlocal retry
        if retry > 0:
            retry -= 1
        else:
            raise

    while retry:
        try:
            await task.init_device()
            await task.solve_ct()
            break
        except (ErrEmptyFP, ErrProxyEmptyFP) as e:
            raise
        except ErrEmptyTL as e:
            raise
        except (ClientHttpProxyError, ServerDisconnectedError, ProxyError) as e:
            raise
        except Exception as e:
            logger.opt(exception=True).error(e)
            # continue_retry()
            task.save_fp()
            task.save_ips()
            raise
        finally:
            # task.save_fp()
            # task.save_ips()
            pass

    # try:
    #     for i in range(0, 1):
    #         await asyncio.sleep(10)
    #         resp = await task.req_fp(recheck=True)
    #         if resp.status_code != 200:
    #             raise ErrCookieExpire
    # except ErrEmptyFP as e:
    #     # task.save_ips()
    #     # task.save_fp()
    #     raise
    return True

async def muti_task_test(NUM, model_id=None):
    tasks = []
    for i in range(0, NUM):
        logger.debug(f"start task {i}")
        t = asyncio.create_task(single_task(i, model_id))
        tasks.append(t)

    rets = await asyncio.gather(*tasks, return_exceptions=True)
    success = [i for i in rets if not isinstance(i, Exception)]
    success_cnt = len(success)
    logger.debug(f"total: {len(rets)}, success: {success_cnt}")
    failed_cnt = len(rets) - success_cnt

    stats = {}
    for i in rets:
        if isinstance(i, Exception):
            desc = repr(i)
            stats[desc] = stats.get(desc, 0) + 1
    logger.debug(json.dumps(stats, indent=4, ensure_ascii=False))
    return success_cnt, failed_cnt

async def test_models(NUM):
    logger.debug("test models ...")
    modelids = [
    ]

    for idx, i in enumerate(modelids):
        i = i.split()[0]
        logger.info(f"idx: {idx} 测试 model id: {i}")
        success_cnt, failed_cnt = await muti_task_test(NUM, i)
        if success_cnt < 7:
            logger.error(f"idx: {idx} 太多错误！model id: {i}")
            raise Exception("停止测试！")
        logger.info((f"idx: [{idx}/{len(modelids)}] 成功数 {success_cnt} / {NUM}, model id: {i}"))
        time.sleep(3)

async def test_uas(NUM):
    Task.load_uas("./android_uas.txt")
    UAS = Task.UAS

    tasks = []
    for i in range(0, NUM):
        logger.debug(f"start task {i}")
        ua = random.choice(UAS)
        t = asyncio.create_task(single_task(i, ua=ua, model_id=None))
        tasks.append(t)

    rets = await asyncio.gather(*tasks, return_exceptions=True)
    success = [i for i in rets if not isinstance(i, Exception)]
    success_cnt = len(success)
    logger.debug(f"total: {len(rets)}, success: {success_cnt}")
    failed_cnt = len(rets) - success_cnt

    stats = {}
    for i in rets:
        if isinstance(i, Exception):
            desc = repr(i)
            stats[desc] = stats.get(desc, 0) + 1
    logger.debug(json.dumps(stats, indent=4, ensure_ascii=False))
    return success_cnt, failed_cnt


async def main():
    # init sdk
    await UnicornSdkAsync.init()

    # 加载代理
    Task.load_proxys("./proxys.txt")

    # await test_models(50)
    await single_task(0, ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")
    # await muti_task_test(50)
    # await test_uas(100)

    # deinitsdk
    await UnicornSdkAsync.deinit()
    sys.exit(0)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.2))
    loop.close()
