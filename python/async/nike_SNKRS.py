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
        self.accept_language = "de-DE;q=1.0"
        # zh-CN,zh;q=0.9,en;q=0.8
        self.platform = PlatForm.IOS
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
            await self.init_device()

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
                    timezone_info="GMT-0700 (Pacific Daylight Time)",
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
                kpparam = await self.kasada_api.kpsdk_answer(x_kpsdk_ct, x_kpsdk_st, st_diff)
                logger.debug(kpparam)

                # now you have ct & cd

                import requests

                cookies = {
                    'geoloc': 'cc=DE,rc=HE,tp=vhigh,tz=GMT+1,la=50.12,lo=8.68',
                    '_abck': 'F28BA0EA6C3C5A0873B1345B6F4ABB01~-1~YAAQrYUVArsMF+eFAQAAsulc8wl476pJaBhGhx+v0ONXwvmyog00GBeMj/gvXvyTJ6bvAbDEiOlAl98avkXdtmLAZVLfTZzMFo8rle+B6cigO4CFj5Rj1EQA8rVwpSKOiNeeT7S5gZ7SVpGsPjTldUakocC/IvNMjMQj4v8ASqI24WB4RtJMBOwU+OlAHKD06LyjhtuVPTa31/YLjt4qk0Hw6/rpVRlbE9Ti1wPgr71lDAOlEmTvPOw1492qJpdbGJn96eUJ/wJ7smJ4zRPEghHfKMk2j3CYPyl3cK9LwloXnbXmo9dUFPf4j5jeiQIX27EJGESQZ5fuj6/rSLohIgROXLtWsNgSeTpY4BySnSPvjldlhPloKcr2p73TErknWFJ8wi8xPOLVB5kyy3Fl/cvIsi/e3AkVjoWHfxbFJcSwzZGmnnB4kfOIXES6v51d1y+K7PrgimFswaa63jwPeqL9f8n1Z0j0orxrcXESBtJewn84iQ==~-1~-1~-1',
                    # 'akm_bmscz_c2': '02JQDtlckPsTrRR4mM4PbPGIGruQNICeEyfNBYeBBnPUidsJ8MNYhTKeWNhYPd5ulyKpscpZBFjWIBidJg2bsJQ3OyRC5RoczuAlhraCAQrx0uwPhjX775cFBuzpS0gVZz4JhLdZQxFqZ8Q8Tguf6ELXzBF',
                    # 'akm_bmscz_c2-ssn': '02JQDtlckPsTrRR4mM4PbPGIGruQNICeEyfNBYeBBnPUidsJ8MNYhTKeWNhYPd5ulyKpscpZBFjWIBidJg2bsJQ3OyRC5RoczuAlhraCAQrx0uwPhjX775cFBuzpS0gVZz4JhLdZQxFqZ8Q8Tguf6ELXzBF',
                    'bm_sv': 'C0859ADF72B2ADF3EA778A08F37CF7E5~YAAQH3vdWK0s48OFAQAA7oFc8xLFrXrV6bfVNBkQrr6xd2C4xmrKhFFm0f9EY9u3ldnZKWnYi957az08TEU4C6HJ/FegJ0vwqv8SuisTcliA0bL6AcpbEFf6/dY4CZD8PczT8tIWYETzokiTBK3sHtrvxpCO2Q0IBnNpUWVAKClgHKLHJMmJH+a3F5HLfJITpsOHbP/EmILhqexFgXuX/JJoLAXnAMokX5ASXEr9N5bghIEuQbjtjs9hy+G/qQ==~1',
                    'bm_sz': '054C53F0865D82904EF4FFF7C3A7EF27~YAAQjR0QAtZlL9iFAQAAGMg28xK6NWb04sJgaW3FeYHx7HCHeTgTNAmNFwNNulWY7GNP2ylhhDviiCenJ+tNiQzXIYiLszah++kq5uQs1b2s6zzzpA0Hp/HqIarTO5l37C5bR34pi8qFK1ASgtxW8s6WKvnvJbw6nKRA+vFCbeIczt+Sn6xMmMow8hSGqPdADce0rZcLCmV/zDelORcBo6sF2Joijzwap4pY2tP/s+eLzFNwpYZ/UzZ9cLXzHO0mMIDKne1hpbzlThRQ3Yg91BeQMGGjXbPTO6jXg9hOjUZ36mwTABuj0M97VZI9bdA1aIuqz5ETAKEK5autpCOv4njqOTjFMzgSnYRSxXNiE7Ly5x0sj7qouIstD9HEuoZMXQ==~4534596~3290168',
                    'ak_bmsc': '775A87762FD929AFAE4BBD417774B50F~000000000000000000000000000000~YAAQLXvdWLQ9eqeFAQAAOsQ28xJbcOKkNwyzhX3PC+KT1OJo1ZthjnEfEDtmuoJ24Nk3PbRW3tudjtGqcj4R9MlesbLoiLaHCZdBBDqwMVl8nYlWGhtbYfoyTmBrIpDHKUcaBrBM0Ftuy6A5l5dAJeYNhihv67o3CU1n/eo2+iJ3caNNeOCU02yF+IvbSXNlHgWDviDLY3dXQVVapEHfCu19dswAxGQWmAnt53Y9oixlXfBwZMy7FgpavCNW19m+71m/TG9niqadRrUVdCB7gbL8ogC1d9r+zuPXhohys4ezRuxDEpM8kKRjpVp2k9g5WOqt5ik8JLeiOMVHylBNgBE7jS3L/XT+r721GYM3Goj9VJ6VdIrvVWXBlugukMWDT2JefXmQ5XDBto64j0QE069Q/N2OYJBGRdSh2GU4Ggg=',
                }

                headers = {
                    'Host': 'api.nike.com',
                    # 'Cookie': 'geoloc=cc=DE,rc=HE,tp=vhigh,tz=GMT+1,la=50.12,lo=8.68; _abck=F28BA0EA6C3C5A0873B1345B6F4ABB01~-1~YAAQrYUVArsMF+eFAQAAsulc8wl476pJaBhGhx+v0ONXwvmyog00GBeMj/gvXvyTJ6bvAbDEiOlAl98avkXdtmLAZVLfTZzMFo8rle+B6cigO4CFj5Rj1EQA8rVwpSKOiNeeT7S5gZ7SVpGsPjTldUakocC/IvNMjMQj4v8ASqI24WB4RtJMBOwU+OlAHKD06LyjhtuVPTa31/YLjt4qk0Hw6/rpVRlbE9Ti1wPgr71lDAOlEmTvPOw1492qJpdbGJn96eUJ/wJ7smJ4zRPEghHfKMk2j3CYPyl3cK9LwloXnbXmo9dUFPf4j5jeiQIX27EJGESQZ5fuj6/rSLohIgROXLtWsNgSeTpY4BySnSPvjldlhPloKcr2p73TErknWFJ8wi8xPOLVB5kyy3Fl/cvIsi/e3AkVjoWHfxbFJcSwzZGmnnB4kfOIXES6v51d1y+K7PrgimFswaa63jwPeqL9f8n1Z0j0orxrcXESBtJewn84iQ==~-1~-1~-1; akm_bmscz_c2=02JQDtlckPsTrRR4mM4PbPGIGruQNICeEyfNBYeBBnPUidsJ8MNYhTKeWNhYPd5ulyKpscpZBFjWIBidJg2bsJQ3OyRC5RoczuAlhraCAQrx0uwPhjX775cFBuzpS0gVZz4JhLdZQxFqZ8Q8Tguf6ELXzBF; akm_bmscz_c2-ssn=02JQDtlckPsTrRR4mM4PbPGIGruQNICeEyfNBYeBBnPUidsJ8MNYhTKeWNhYPd5ulyKpscpZBFjWIBidJg2bsJQ3OyRC5RoczuAlhraCAQrx0uwPhjX775cFBuzpS0gVZz4JhLdZQxFqZ8Q8Tguf6ELXzBF; bm_sv=C0859ADF72B2ADF3EA778A08F37CF7E5~YAAQH3vdWK0s48OFAQAA7oFc8xLFrXrV6bfVNBkQrr6xd2C4xmrKhFFm0f9EY9u3ldnZKWnYi957az08TEU4C6HJ/FegJ0vwqv8SuisTcliA0bL6AcpbEFf6/dY4CZD8PczT8tIWYETzokiTBK3sHtrvxpCO2Q0IBnNpUWVAKClgHKLHJMmJH+a3F5HLfJITpsOHbP/EmILhqexFgXuX/JJoLAXnAMokX5ASXEr9N5bghIEuQbjtjs9hy+G/qQ==~1; bm_sz=054C53F0865D82904EF4FFF7C3A7EF27~YAAQjR0QAtZlL9iFAQAAGMg28xK6NWb04sJgaW3FeYHx7HCHeTgTNAmNFwNNulWY7GNP2ylhhDviiCenJ+tNiQzXIYiLszah++kq5uQs1b2s6zzzpA0Hp/HqIarTO5l37C5bR34pi8qFK1ASgtxW8s6WKvnvJbw6nKRA+vFCbeIczt+Sn6xMmMow8hSGqPdADce0rZcLCmV/zDelORcBo6sF2Joijzwap4pY2tP/s+eLzFNwpYZ/UzZ9cLXzHO0mMIDKne1hpbzlThRQ3Yg91BeQMGGjXbPTO6jXg9hOjUZ36mwTABuj0M97VZI9bdA1aIuqz5ETAKEK5autpCOv4njqOTjFMzgSnYRSxXNiE7Ly5x0sj7qouIstD9HEuoZMXQ==~4534596~3290168; ak_bmsc=775A87762FD929AFAE4BBD417774B50F~000000000000000000000000000000~YAAQLXvdWLQ9eqeFAQAAOsQ28xJbcOKkNwyzhX3PC+KT1OJo1ZthjnEfEDtmuoJ24Nk3PbRW3tudjtGqcj4R9MlesbLoiLaHCZdBBDqwMVl8nYlWGhtbYfoyTmBrIpDHKUcaBrBM0Ftuy6A5l5dAJeYNhihv67o3CU1n/eo2+iJ3caNNeOCU02yF+IvbSXNlHgWDviDLY3dXQVVapEHfCu19dswAxGQWmAnt53Y9oixlXfBwZMy7FgpavCNW19m+71m/TG9niqadRrUVdCB7gbL8ogC1d9r+zuPXhohys4ezRuxDEpM8kKRjpVp2k9g5WOqt5ik8JLeiOMVHylBNgBE7jS3L/XT+r721GYM3Goj9VJ6VdIrvVWXBlugukMWDT2JefXmQ5XDBto64j0QE069Q/N2OYJBGRdSh2GU4Ggg=',
                    'user-agent': 'SNKRS/5.1.1 (prod; 2210101445; iOS 16.0; iPhone13,1)',
                    'x-nike-caller-id': 'nike:snkrs:ios:5.1',
                    'newrelic': 'ewoiZCI6IHsKImFjIjogIjEwMTU4MTAiLAoiYXAiOiAiMzUxMzExMTAiLAoiaWQiOiAiMjQ5MjNlZDI0ZTY0ZDg3ZCIsCiJ0aSI6IDE2NzQ4MjUyNDg1MjYsCiJ0ciI6ICJkN2Y4MjczNGFmYmU0MWU3MDEzNzZiNGU3YjBlMWNkNiIsCiJ0eSI6ICJNb2JpbGUiCn0sCiJ2IjogWwowLAoyCl0KfQ==',
                    'x-kpsdk-ct': x_kpsdk_ct,
                    'x-kpsdk-cd': kpparam["x_kpsdk_cd2"],
                    'x-b3-traceid': '226e28a541c8d3fc',
                    'authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImVkZmY4YTAyLWIyZGEtNDhkZC1iOGVjLThhMmM1MGE2YTM0MnNpZyJ9.eyJpYXQiOjE2NzQ4MjI3MzEsImV4cCI6MTY3NDgyNjMzMSwiaXNzIjoib2F1dGgyYWNjIiwianRpIjoiYTI0YmIyY2EtZmMzMy00MmU0LTg3MTUtYzI4ZTI5OGI5ZWFlIiwiYXVkIjoiY29tLm5pa2UuZGlnaXRhbCIsInNidCI6Im5pa2U6YXBwIiwidHJ1c3QiOjEwMCwibGF0IjoxNjc0Nzc3ODM4LCJzY3AiOlsibmlrZS5kaWdpdGFsIl0sInN1YiI6ImNvbS5uaWtlLmNvbW1lcmNlLnNua3JzLmlvcyIsInBybiI6IjkxNTE4ZGYwLTRhMTYtNDZlZS1hZmZhLWI0NjZkODcxMjgxNiIsInBydCI6Im5pa2U6cGx1cyIsImxyc2NwIjoib3BlbmlkIHByb2ZpbGUgZW1haWwgcGhvbmUgZmxvdyBvZmZsaW5lX2FjY2VzcyBuaWtlLmRpZ2l0YWwifQ.b-KWDSK6p0V4K7aO4scV1OGK-7hvnbWyQntZbeAN5Z3I3YTYZd3xYa0Lv2leleDxWA_up7niwHSwFz5_FdzD31eFhsOPD3l4UokGy6ntvMA9bH9ko-nqpYuX1-wPVefVK9D0MLftgascV3h8QlrStDIG6KL9bFPBViFZ-eOqAa9Jrh1pEShLXVKoYUnVGTF7BpUdV3kjgQ0-JRMdEWvWTpXsRUzmwYmxjg7EukKqD1htonxkVBUQEVuiei8nA4f-rKGxvAlT62gtOAX4M22MtSuANiAtGOvkspkBoVJeKoxNsBTeTN45qS_gWbzS4XHOIBmmDiTa7qjxnXmb2RlgXQ',
                    'tracestate': '@nr=0-2-1015810-35131110-24923ed24e64d87d--0--1674825248526',
                    'x-acf-sensor-data': '2,i,CpOTxOf5gvwq72u8K/gjXaLuJEwz74Pq0A1YOp7utEf5/vxscjNB8a7L4db4dDoWu5e1enpoE0E8mdJz8W7/1ipp4ea/mWsLc1kzq+OoZz6lWN8YShBds7kktJhOcSwZ+d2aEQByHkA6GAlnqr+PzafuUEn01XmyU5Cr4r0PAXI=,g74CEGj+4T1JJfrEesFUuPgRMHJc2U3BaySqCTz+P9JGujbDsrxLTmv8M8kbPBPm6EU1tROA6MQdgCYmJMSVXvuqvNuCeyhVvSS3qpvuDagS5uvrsVBXvYZdq8jVoT1X8TYv89cI4qTX0ApfAsJ/TCOAxQgaIsU0BzIMWRsqOsw=$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$13,6,35$C9A06C3F-5920-49F0-A6E4-F047858FE871;1674825230783;7b5b81ca5a3468a99307aa122c294130;6000;plZOYrqrJnnp8nYr0KarVLL9+fqpzrcyzvodtwI0bDW/dNL9ryX8T389SULaZrMigmdvECJTF1VfFqToltWIhFyQ==;0.349829007254,0.586708327892,0.648695944261,0.354002446484,0.705647816813,0.893674116091,0.726457106584,0.456377145009,0.128523409862,0.442555341041;1351,168,173,166,120,112,113,150,212,210;27700,3738,8677,2162,658,624,1057,8162,12135,7700$',
                    'accept-language': 'de-DE;q=1.0',
                    'x-kpsdk-v': 'i-1.6.1',
                    'accept': 'application/json',
                    'content-type': 'application/json',
                    'x-newrelic-id': 'VQYGVF5SCBADUVBRBgAGVg==',
                    'traceparent': '00-d7f82734afbe41e701376b4e7b0e1cd6-24923ed24e64d87d-00',
                }

                json_data = {
                    'request': {
                        'email': 'jdsfghjhre@gmail.com',
                        'channel': 'SNKRS',
                        'country': 'DE',
                        'currency': 'EUR',
                        'clientInfo': {
                            'client': 'com.nike.commerce.snkrs.ios',
                            'deviceId': '0610kWVVHQsCG7jYstjuu+ZgH5OFLmIM74GTV5MPVbnmRe1UcUatwsGD13vjErOWRLS4Tff7kHSjoMz7qqFcoJw5Xw75IvcHFVKuUV+QThODnM8535hXN1Hnqc+ZDThwnoMv3WRMqvrzigF/CHIU3sBGd67eLTWDAZ3FV4WFdGNrbuVVIded9LgeYiQjJrpmPbwNzcosHq4wFDMZ708hqXOzEkIJCFFGknzBbcq4+GntS3GRaND/w+PyzD4jzlmLDCZXJC9uZuMFhR6ISu/d65ZL6gRZ400dd1ZXOid92NRiINej8tx5kq4MsrBXltmhsde2CFb5/Ruas/TsKg2E7saVCn3OXuS2NT8jk08L5KYYOAuIgdmY3qFdEgRfJCdQh+nfTbEsgLkd4D/ObkNFlXG//bKEDELRAFN2VKqob/MCiiN+ATJd7PPfj6Byh9e166k0dy0ziuoJ726CZSh4f0of/SQJ0/myazh7V1qeWvl6GgMs1Lygpi1iE6TC4KW1gcxry9vzPSpW08dOKRonrFkiQWFGBR8DgG0ScYznXd0XHHyrUV4PCowMEf7JdWQoRyofExtotfT5f0DPLCeVRk2kuKiqCwObWSYWLpTVeDRqiqS216Kg8pus29mUBCTb2psETYSjNiUUVpEmP2n6ka8GZ8iClDmcFIOtWnnqOr2oBRDTa8jJLB6sCbg0vwp7pMxwtESJzE5hwxbryj5KMwkTKKownJyIaedyflzqlw95wYulrZv1S0VG17xaEKSCLYQD74efm01EVxuwB5CipD30A/f/7OFaN53WMj0PoxWa3nn1+sVFpee0jGT6znEBD8kFzuq9qSPnGD4TSTAI2lhS8J+oB5LcpvPnnXfhQAiXO/j95J4kEUbnU3yC/gr8Y9Ik2TdtGa/bJjIpgNMznEX4aB2yhqB9sNStDO9gEks4I9F4s6wMkPVJIpub4Mfq4KxLyprIMOn3yvL5MEMSyeQ3SRDcyF+o4g3fpg33HC7WeZjTLDvALL5EYYIznoE0nF8M7mkX2nw5+ja5StOQ08G064S4x/GIEG4dBqvgi8Qj9+fCPof5cHup7XKsaYffyxVLnPHqa/gD9wCRvS5pSAuCnitSWCMCUdxnWhlIuqP01eLyS3v/Sq3EiALRJWlHYnbKeBZGzcltQ935BOG/ap9LCx5JTmDviI+2W1It8Ol5L1ItiVZ97R3TVI119zRUmr+lRkIW5rW8hoLZ9ZsfMQKApsf6roGhVdlX2GUfDdaaRzYTsFkt/oImDoXvA03A7PYnClhMaZxULhZkqfhXgaaG05kLm67HBdBaG11FyxzkglIMUVf1EVLtk7hjkmLO9B/g7O4IDCh5Erzscs62piQmuOFR2+oCh2CdM6G+bJ6DaUnifwrj4/tVzjVF/U9T85Cj70LA2qRxjrhHZCziqGPBkHkJIiTlmLWj2Z2Jx9Py/h9RqULDXwdS1q4HwuHazz2E5PjJZnyP8kwBTMk/x77hHUdPvdBa/mrLdB0HmB9tmL2UNuF2DpPgPSaFLQ+tHQSd2DR82kDtaQkXAlfwKIB59/QQ9N9oRph3UhRvpA0mvqs4juWAqWOdNUjsjnV7TIfEbLMdZz8I7LvftqjMFDL+j25WPMNp4rkJSVMBH6/yX6pfN1iLeqCgxDVF+0ohZ34WIKSzGiJ34AVqBGey3L1B8+KtZNZ9cnLaPd+ZaHWP/bbgoxGbK7eRh/it2x8KZziHMUGxSJrWI+qhD8FojkVT2ha1ElrlmXWvgCmTnETNdUIyHgN6SEU3k69Lv2QyJVlBV8ExaMWZ87eleXrVU7HIbjfIvmKMI7RZvwEm8BiIus0=',
                        },
                        'locale': 'de_DE',
                        'items': [
                            {
                                'quantity': 1,
                                'id': '2dd19d21-40cd-4e9b-961f-3e8cfd12a074',
                                'shippingMethod': 'GROUND_SERVICE',
                                'contactInfo': {
                                    'phoneNumber': '017623641664',
                                    'email': 'jdsfghjhre@gmail.com',
                                },
                                'skuId': '5cc9097a-e2f2-53cc-8ba6-6836680a5fed',
                                'recipient': {
                                    'lastName': 'Martini',
                                    'firstName': 'Ina',
                                },
                                'shippingAddress': {
                                    'country': 'DE',
                                    'city': 'Berlin',
                                    'address1': 'belzigerstr',
                                    'address2': '33',
                                    'postalCode': '10823',
                                },
                            },
                        ],
                    },
                }

                cookies["akm_bmscz_c2"] = x_kpsdk_ct
                cookies["akm_bmscz_c2-ssn"] = x_kpsdk_ct
                response = requests.put(
                    'https://api.nike.com/buy/checkout_previews/v2/397c1859-4acb-4395-99d7-0cc2fc4c1f09',
                    cookies=cookies,
                    headers=headers,
                    json=json_data,
                )
                logger.debug(response.status_code)
                logger.debug(response.text)
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
            # self.save_ips()
            pass

async def main():
    # init sdk
    await UnicornSdkAsync.init()

    useragent = "SNKRS/5.1.1 (prod; 2210101445; iOS 16.0; iPhone13,1)"
    task = Task("task_id_xxx", ua=useragent, proxy=cur_proxyuri)


    # deinitsdk
    await UnicornSdkAsync.deinit()
    sys.exit(0)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.2))
    loop.close()
