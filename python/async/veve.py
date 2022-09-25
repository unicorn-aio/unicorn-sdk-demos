import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from requests_futures.sessions import FuturesSession

from unicornsdk import PlatForm, UnicornSdk
from unicornsdk_async import UnicornSdkAsync
from unicornsdk.utils import now_time_ms, now_time_str

load_dotenv(verbose=True)

UnicornSdkAsync.auth(os.environ.get("ACCESS_TOKEN"))


class Veve:
    """
    Ios version demo
    """

    def __init__(self, sessionid, *, cur_proxyuri="http://127.0.0.1:8888", origin="https://mobile.api.prod.veve.me"):
        self.sessionid = sessionid
        self.cur_proxyuri = cur_proxyuri
        self.x_kpsdk_ct = None
        self.x_kpsdk_st = None
        self.st_diff = None
        self.x_kpsdk_ct_expiretime = None
        self.orgin = origin
        self.client = FuturesSession()
        self.useragent = None
        self.x_kpsdk_v = "i-1.6.0"
        self.client_version = "1.0.619"
        self.client_name = "veve-app-ios"
        self.client_model = "iphone 11 pro max"
        self.client_user_id = str(uuid.uuid4())
        self.client_id = str(uuid.uuid4())
        self._login_cookie = None
        self.device_session = UnicornSdkAsync.create_device_session(self.sessionid, PlatForm.IOS)
        self.kasada_api = self.device_session.kasada_api()

    async def init_sesion(self):
        deviceinfo = await self.device_session.init_session(
            accept_language="en-gb",
            ua="Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        )
        self.useragent = deviceinfo["user_agent"]
        logger.debug(f"use {self.useragent}")

    def get_proxys(self):
        proxies = {
            "http": self.cur_proxyuri,
            "https": self.cur_proxyuri,
        }
        return proxies
        # return None

    def get_login_cookie(self):
        """
        the resp cookie when you logined
        :return:
        """
        # return ";".join([
        #     "veve=xxxxxxxxxxxxx",
        #     "Domain=web.api.prod.veve.me",
        #     "Path=/",
        #     "HttpOnly",
        #     "Secure",
        #     "SameSite=None, KP_UIDz-ssn=xxxxxxxx",
        #     "Max-Age=86400",
        #     "Path=/",
        #     "Expires=Wed, 02 Feb 2022 21:56:28 GMT",
        #     "HttpOnly",
        #     "Secure",
        #     "SameSite=None, KP_UIDz=xxxxxxxx",
        #     "Max-Age=86400",
        #     "Path=/",
        #     "Expires=Wed, 02 Feb 2022 21:56:28 GMT",
        #     "HttpOnly"
        # ])
        return self._login_cookie

    async def req_fp(self):
        orgin = self.orgin
        useragent = self.useragent
        fp_url = f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp"
        resp = await asyncio.wrap_future(self.client.get(fp_url, headers={
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br",
            "x-kpsdk-v": self.x_kpsdk_v,
            "accept-language": "en-gb",
            "user-agent": useragent,
        }, proxies=self.get_proxys(), verify=False))
        return resp

    async def do_web_ips(self):
        orgin = self.orgin
        useragent = self.useragent
        fp_url = f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp"
        resp = await self.req_fp()
        logger.debug(resp.status_code)
        logger.debug(resp.text)

        # if True:
        if resp.status_code == 429:
            ct = resp.headers["x-kpsdk-ct"]
            # &x-kpsdk-v=i-1.4.0
            ips_url = f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3" \
                      f"/ips.js?KP_UIDz={ct}&x-kpsdk-v={self.x_kpsdk_v}"

            resp = await asyncio.wrap_future(self.client.get(ips_url, headers={
                "accept": "*/*",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-gb",
                "referer": f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp",
                "user-agent": useragent,
            }, proxies=self.get_proxys(), verify=False))
            ipsjs = resp.content
            with open(f"z:/veve-ips-{now_time_str()}.js", "wb") as f:
                f.write(ipsjs)

            kpparam = await self.kasada_api.kpsdk_parse_ips(ips_url, ipsjs,
                                                     # timezone_info="GMT+0800 (中国标准时间)"
                                                     timezone_info="GMT-0700 (Pacific Daylight Time)"
                                                     )
            # logger.debug(json.dumps(kpparam, indent=4))

            tl_url = f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/tl"
            resp = await asyncio.wrap_future(self.client.post(
                tl_url,
                headers={
                    "accept": "*/*",
                    "content-type": "application/octet-stream",
                    "accept-encoding": "gzip, deflate, br",
                    "accept-language": "en-gb",
                    "referer": f"{orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp",
                    "origin": orgin,
                    "x-kpsdk-v": self.x_kpsdk_v,
                    "user-agent": useragent,
                    "x-kpsdk-ct": kpparam["x_kpsdk_ct"]
                },
                data=kpparam["body"],
                proxies=self.get_proxys(), verify=False,
            ))

            logger.debug(resp.status_code)
            logger.debug(resp.text)

            x_kpsdk_ct = resp.headers["x-kpsdk-ct"]
            x_kpsdk_st = resp.headers["x-kpsdk-st"]
            st_diff = now_time_ms() - int(x_kpsdk_st)
            logger.debug(f"x_kpsdk_ct: {x_kpsdk_ct}")
            logger.debug(f"x_kpsdk_st: {x_kpsdk_st}")
            logger.debug(f"st_diff: {st_diff}")

            self.x_kpsdk_st = x_kpsdk_st
            self.x_kpsdk_ct = x_kpsdk_ct
            self.st_diff = st_diff
            self.x_kpsdk_ct_expiretime = (datetime.now() + timedelta(hours=22)).timestamp()

        elif resp.status_code == 200:
            x_kpsdk_ct = resp.headers["x-kpsdk-ct"]
            self.refresh_ct(resp)
        else:
            raise Exception("???")

    async def get_answer(self):
        kpparam = await self.kasada_api.kpsdk_answer(self.x_kpsdk_ct, self.x_kpsdk_st, self.st_diff)
        logger.debug(kpparam)
        return kpparam

    def refresh_ct(self, resp):
        ct = resp.headers.get("x-kpsdk-ct")
        if ct:
            logger.debug(f"ct --> {ct}")
            self.x_kpsdk_ct = ct
            self.x_kpsdk_ct_expiretime = (datetime.now() + timedelta(hours=22)).timestamp()

    async def req_post_api_auth_totp_send(self, email="xxx@yahoo.com"):
        send_url = f"{self.orgin}/api/auth/totp/send"
        kpparam = await self.get_answer()
        resp = await asyncio.wrap_future(self.client.post(
            send_url,
            headers={
                "accept": "*/*",
                "content-type": "application/json",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-gb",
                "client-name": "veve-web-wallet",
                "client-version": "1.2.9",
                "referer": f"{self.orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp",
                "origin": "https://omi.veve.me",
                "user-agent": self.useragent,
                "x-kpsdk-ct": kpparam["x_kpsdk_ct"],
                "x-kpsdk-cd": kpparam["x_kpsdk_cd"],
            },
            json={"email": email},
            proxies=self.get_proxys(), verify=False,
        ))
        logger.debug(resp.status_code)
        logger.debug(resp.text)
        return resp

    async def req_post_graphql(self, ql, client_operation="MarketMultiplesQuery"):
        url = f"{self.orgin}/graphql"
        kpparam = await self.get_answer()
        # logger.debug(json.dumps(kpparam, indent=4))
        client = FuturesSession()

        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "content-type": "application/json",
            "client-version": self.client_version,
            # "referer": f"{self.orgin}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp",
            "origin": "https://omi.veve.me",
            "user-agent": self.useragent,
            "x-kpsdk-ct": kpparam["x_kpsdk_ct"],
            "x-kpsdk-cd": kpparam["x_kpsdk_cd"],
            "client-operation": client_operation,
            "client-name": self.client_name,
            "client-model": self.client_model,
            "client-brand": "apple",
            "client-manufacturer": "apple",
            "client-user-id": self.client_user_id,
            "client-id": self.client_id,
            "accept-language": "en-gb",
            "x-kpsdk-v": self.x_kpsdk_v,
            "client-installer": "appstore",
            "client-carrier": "unknown",
        }
        if self.get_login_cookie():
            headers["cookie"] = self.get_login_cookie()

        resp = await asyncio.wrap_future(client.post(
            url,
            headers=headers,
            data=json.dumps(ql, separators=(',', ':')),
            proxies=self.get_proxys(), verify=False,
        ))
        logger.debug(resp.status_code)
        logger.debug(resp.text)
        self.refresh_ct(resp)
        return resp

    def save_session(self):
        obj = {
            "x_kpsdk_ct": self.x_kpsdk_ct,
            "x_kpsdk_st": self.x_kpsdk_st,
            "st_diff": self.st_diff,
            "x_kpsdk_ct_expiretime": self.x_kpsdk_ct_expiretime,
            "login_cookie": self._login_cookie,
            "client_user_id": self.client_user_id,
            "client_id": self.client_id,
        }
        self.device_session.save_state(obj)
        with open(self.sessionid + ".json", "w", encoding="utf8") as f:
            json.dump(obj, f, indent=4, ensure_ascii=False)
        return obj

    async def refresh_ct_if_need(self):
        if self.x_kpsdk_ct and self.x_kpsdk_ct_expiretime and datetime.now().timestamp() < self.x_kpsdk_ct_expiretime:
            return
        logger.debug("we need refresh the ct from ips ...")
        await self.do_web_ips()

    def load_session(self):
        file = Path(self.sessionid + ".json")
        if file.exists():
            with open(file, encoding="utf8") as f:
                obj = json.load(f)
                self.client_user_id = obj.get("client_user_id")
                self.client_id = obj.get("client_id")
                self.x_kpsdk_ct = obj.get("x_kpsdk_ct")
                self.x_kpsdk_st = obj.get("x_kpsdk_st")
                self.st_diff = obj.get("st_diff")
                self.x_kpsdk_ct_expiretime = obj.get("x_kpsdk_ct_expiretime")
                self._login_cookie = obj.get("login_cookie")
                self.device_session.load_state(obj)
                self.useragent = self.device_session.device_info["user_agent"]
                return obj
        return None


async def test_if_ct_could_last_long(veve):
    """
    since i-1.6.0 update, test if our ct could last for a long time and not got empty respose
    :param veve:
    :return:
    """
    for idx, i in enumerate(range(10)):
        logger.debug(idx)
        resp = await veve.req_post_graphql({
            "operationName": "AppMetaInfo",
            "variables": {
                "client": "IOS"
            },
            "query": "query AppMetaInfo($client: SupportedClients!) {  minimumVersion(client: $client)  featureFlagList {    name    enabled    __typename  }}"
        }, client_operation="AppMetaInfo")
        if len(resp.text) == 0:
            break

        await asyncio.sleep(10)


async def test_AppMetaInfo(veve):
    resp = await veve.req_post_graphql({
            "operationName": "AppMetaInfo",
            "variables": {
                "client": "IOS"
            },
            "query": "query AppMetaInfo($client: SupportedClients!) {  minimumVersion(client: $client)  featureFlagList {    name    enabled    __typename  }}"
        }, client_operation="AppMetaInfo")


async def main():
    # init sdk
    await UnicornSdkAsync.init()

    veve = Veve("veve_testid", cur_proxyuri=os.environ.get("PROXY_URI"))

    if (not veve.load_session()):
        await veve.init_sesion()

    await veve.refresh_ct_if_need()

    # test get AppMetaInfo
    await test_AppMetaInfo(veve)
    # await test_if_ct_could_last_long(veve)

    veve.save_session()

    # deinitsdk
    await UnicornSdkAsync.deinit()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.5))
    loop.close()