# -*- coding: utf-8 -*-
import os
import time
import traceback

import httpx
from prettytable import PrettyTable

from api import URP, URPRequestException

try:
    # 选择最优服务器
    print()
    hosts = ['jw1.yzu.edu.cn', 'jw2.yzu.edu.cn', 'jw3.yzu.edu.cn']
    best_host = None
    best_resp_time = 9999999999
    print('正在选择最优服务器')
    for h in hosts:
        t = 0
        try:
            for _ in range(10):
                stime = time.time()
                resp = httpx.get(f'http://{h}/validateCodeAction.do', timeout=5)
                etime = time.time()
                t += int((etime - stime) * 1000)
        except httpx.HTTPError:
            print(f'{h} 响应超时')
            continue
        if resp.status_code != 200:
            print(f'{h} 响应失败')
            continue
        resp_time = t / 10
        print(f'{h} 平均响应时间: {resp_time}ms')
        if best_resp_time > resp_time:
            best_resp_time = resp_time
            best_host = h
    if best_host is None:
        print('当前网络状况不佳，建议稍后再试')
        os.system('pause')
        exit(0)
    print(f'已选择 {best_host} 作为当前服务器')

    # 登录
    print('\n' + '=' * 20 + '\n')
    username = input('请输入用户名: ')
    password = input('请输入密码: ')

    urp = URP(username, password, best_host)
    if not urp.login():
        print('登录失败，请检查用户名或密码是否正确')
        os.system('pause')
        exit(0)
    print('登录成功')
    if username == password:
        print('警告: 您的用户名和密码相同，为了您的安全，建议修改密码!')

    # 搜索课程
    print('\n' + '=' * 20 + '\n')
    kc_id = input('请输入课程号: ').strip()
    print('正在搜索课程')
    table = PrettyTable(['编号', '课程号', '课程名', '课序号', '教师', '课余量', '星期', '校区'])
    search_result = urp.search_action(kc_id)
    table.add_rows(search_result)
    print(table)
    while True:
        try:
            index = int(input(f'请确认你要抢的课程并输入序号[1~{len(search_result)}]: ')) - 1
            if index < 0 or index >= len(search_result):
                print('请输入正确的序号!')
                continue
        except ValueError:
            print('请输入正确的序号!')
            continue
        break
    kc_no = search_result[index][3]
    kc_name = search_result[index][2]

    # 抢课
    print('\n' + '=' * 20 + '\n')
    print('开始抢课, Ctrl+C退出')
    cnt = 0
    while True:
        cnt += 1

        try:
            result, msg = urp.xk_action(kc_id, kc_no)
        except URPRequestException:
            print(f'执行选课操作时发生错误, 正在重试 <{cnt}>')
            time.sleep(1)
            continue

        if result:
            print(f'{kc_name}[{kc_id}_{kc_no}] 抢课成功! <{cnt}>')
            break
        else:
            if msg == '没有课余量':
                print(f'{kc_name}[{kc_id}_{kc_no}] 没有课余量, 正在重试 <{cnt}>')
                time.sleep(1)
                continue
            elif msg == '登录失效':
                print(f'登录失效，正在重新登录 <{cnt}>')
                urp.login()
                assert urp.login(), '重新登录失败'
                print('重新登录成功')
                urp.search_action(kc_id)
            elif msg == '服务器返回500错误':
                print(f'教务系统发生错误, 正在重试 <{cnt}>')
                time.sleep(1)
                continue
            elif msg == '响应超时':
                print('教务系统响应超时, 正在重试')
                continue
            else:
                raise RuntimeError(msg)
except KeyboardInterrupt:
    print('程序正在退出')
except Exception as e:
    traceback.print_exc()
    print('程序在运行时发生错误，建议你查看README以寻找解决方案\nhttps://github.com/TerraceCN/YZULessonHunter')
finally:
    os.system('pause')
    exit(1)
