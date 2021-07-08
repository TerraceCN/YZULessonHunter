# -*- coding: utf-8 -*-
import json
from base64 import b64encode

import httpx

API_URL = 'http://20.89.45.35:8000/decaptcha'
ERROR_MSG = {
    -1: '验证码大小错误',
    -2: '验证码识别API出现错误'
}


class DecaptchaRequestException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg


def decaptcha(content):
    try:
        resp = httpx.post(API_URL, json={'content': b64encode(content).decode('ascii')})
    except httpx.HTTPError:
        raise DecaptchaRequestException('请求验证码识别API时发生错误')

    try:
        data = resp.json()
    except json.JSONDecodeError:
        raise DecaptchaRequestException('验证码识别API返回了错误的数据')

    if data['code'] == 0:
        return data['result']
    else:
        raise DecaptchaRequestException(ERROR_MSG[data['code']])
