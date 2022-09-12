from loguru import logger

from unicornsdk import UnicornSdk, Session

access_token = "your_access_token"
UnicornSdk.auth(access_token)

captcha_api = UnicornSdk.captcha_api()
ret = captcha_api.image_ocr(image_path="../captcha_demo.png")
logger.debug(ret)
