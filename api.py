# -*- coding: utf-8 -*-
from typing import List, Tuple

import httpx
from lxml import etree

from decaptcha import decaptcha


class URPRequestException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

class XkNotOpenException(Exception):
    def __init__(self):
        super().__init__('非选课阶段不允许选课')


class URP:

    def __init__(self, username, password, host='jw3.yzu.edu.cn') -> None:
        self.username = username
        self.password = password
        self.host = host
        self.sess = httpx.Client(headers={'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 '
                                                         '(KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'),
                                          'Content-Type': 'application/x-www-form-urlencoded',
                                          'Connection': 'keep-alive',
                                          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                                          'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                                          'Accept-Encoding': 'gzip, deflate',
                                          'Upgrade-Insecure-Requests': '1'})
    
    def login(self) -> bool:
        try:
            captcha = self.sess.get(f'http://{self.host}/validateCodeAction.do')
        except httpx.HTTPError:
            raise URPRequestException('获取验证码时发生网络错误')

        try:
            login_result = self.sess.post(f'http://{self.host}/loginAction.do',
                                          data={'zjh1': '',
                                                'tips': '',
                                                'lx': '',
                                                'evalue': '',
                                                'eflag': '',
                                                'fs': '',
                                                'dzslh': '',
                                                'zjh': self.username,
                                                'mm': self.password,
                                                'v_yzm': decaptcha(captcha.content)})
        except httpx.HTTPError:
            raise URPRequestException('登录时发生网络错误')
        return '学分制综合教务' in login_result.text

    @staticmethod
    def _check_result(resp):
        if '数据库忙请稍候再试' in resp:
            return False, '课程冲突'
        elif '请您登录后再使用' in resp:
            return False, '登录失效'
        elif '选课成功' in resp:
            return True, '选课成功'
        elif '非选课阶段不允许选课' in resp:
            return False, '选课系统暂未开启'
        elif '没有课余量' in resp:
            return False, '没有课余量'
        elif '500 Servlet Exception' in resp:
            return False, '服务器返回500错误'
        elif '校任选课开课信息!' in resp:
            return False, '未检测到待选课程'
        elif '你已经选择了' in resp:
            return False, '你已经选中了此门课程'
        else:
            return False, '未知返回值!'

    def search_action(self, kc_id: str) -> List[Tuple]:
        url = f'http://{self.host}/xkAction.do'
        try:
            pre_action = self.sess.get(url)
            if '非选课阶段不允许选课' in pre_action.text:
                raise XkNotOpenException()
            pre_html = etree.HTML(pre_action.text)
            fajhh = pre_html.xpath('//input[@type="radio"]')[0].attrib['value']

            pre_action = self.sess.get(
                url,
                params={'actionType': '-1',
                        'fajhh': fajhh},
                headers={'Referer': str(pre_action.url)})
            
            search_result = self.sess.post(
                url,
                data={'kch': kc_id,
                    'kcm': '',
                    'actionType': '3',
                    'pageNumber': '-1'},
                headers={'Referer': str(pre_action.url)})
        except httpx.HTTPError:
            raise URPRequestException('搜索课程时发生错误')
        
        search_html = etree.HTML(search_result.text)
        trs = search_html.xpath('//table[@class="displayTag"]/tr')
        results = []
        for i, tr in enumerate(trs):
            tds = tr.xpath('./td')
            results.append((
                i + 1,
                tds[2].text.strip(),                          # kc_id
                (tds[3].xpath('./div/a/span')[0].text.strip()
                 if tds[3].xpath('./div/a/span')
                 else tds[3].xpath('./a')[0].text.strip()),   # name
                tds[4].text.strip(),                          # kc_no
                tds[8].text.strip(),                          # teacher
                tds[9].text.strip(),                          # remain
                tds[14].text.strip(),                         # week
                tds[17].text.strip()                          # district
            ))
        return results
        
    def xk_action(self, kc_id, kc_no) -> Tuple[bool, str]:
        '''
        This method must be called after calling `search_action`!
        '''
        try:
            req = self.sess.post(f'http://{self.host}/xkAction.do',
                                data={'actionType': '9',
                                    'kcId': f'{kc_id}_{kc_no}',
                                    'preActionType': '3'},
                                timeout=5)
        except httpx.HTTPError:
            raise URPRequestException('执行选课操作时发生网络错误')
        return self._check_result(req.text)
