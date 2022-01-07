# -*- coding: utf-8 -*-
from os import system
from time import time, sleep
import traceback

import httpx
from prettytable import PrettyTable

from api import *


def choose_best_host():
    hosts = ['jw1.yzu.edu.cn', 'jw2.yzu.edu.cn', 'jw3.yzu.edu.cn']
    best_host = None
    best_resp_time = 9999999999

    print('正在选择最优服务器')

    for h in hosts:
        t = 0
        try:
            for _ in range(10):
                stime = time()
                resp = httpx.get(f'http://{h}/validateCodeAction.do', timeout=5)
                etime = time()
                t += int((etime - stime) * 1000)
        except httpx.HTTPError:
            print(f'{h} - 响应超时(5000ms)')
            continue

        resp_time = t / 10
        if resp.status_code != 200:
            print(f'{h} - 响应失败({resp_time}ms)')
            continue
        print(f'{h} - {resp_time}ms')

        if best_resp_time > resp_time:
            best_resp_time = resp_time
            best_host = h

    if best_host is None:
        return None
    return best_host


def input_account():
    while True:
        username = input('请输入用户名:\t')
        if username:
            break
        print('用户名不得为空')

    while True:
        password = input('请输入密码:\t')
        if password:
            break
        print('密码不得为空')
    return username, password


def pre_selection_mode():
    print('======== 预选模式 ========')
    kc_id = input('请输入课程号:\t').strip()
    kc_no = input('请输入课序号:\t').strip()
    return kc_id, kc_no, None


def block_mode(urp):
    try:
        while True:
            system('cls')
            print('======== 截胡模式 ========')
            kc_id = input('请输入课程号:\t').strip()
            print('正在搜索课程')
            search_result = urp.search_action(kc_id)
            if len(search_result) != 0:
                break
            print('未搜索到相关结果, 请检查课程号是否正确')
            sleep(3)
            

    except XkNotOpenException:
        pre_sel = input('选课尚未开始，是否进入预选模式? (Y/n):')
        if pre_sel == 'y' or pre_sel == 'Y':
            system('cls')
            return pre_selection_mode(urp)
        else:
            print('操作取消, 退出抢课脚本')
            system('pause')
            exit(0)
    
    table = PrettyTable(['编号', '课程号', '课程名', '课序号', '教师', '课余量', '星期', '校区'])
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
    return kc_id, kc_no, kc_name


def loop_xk(urp, kc_no, kc_id, kc_name="未知"):
    cnt = 0
    while True:
        cnt += 1

        try:
            result, status = urp.xk_action(kc_id, kc_no)
            exception = None
        except URPRequestException as e:
            status = e
            exception = e
        except Exception as e:
            status = e
            exception = e

        system('cls')
        print('======== 抢课信息 ========')
        print(f'课程号:\t{kc_id}')
        print(f'课序号:\t{kc_no}')
        print(f'课程名:\t{kc_name if kc_name else "未知"}')
        print(f'抢课次数:\t{cnt}')
        print(f'抢课状态:\t{status}')
        print('====== Ctrl+C 退出 ======')

        if result:
            return
        elif status == '登录失效':
            print(f'登录失效, 正在重新登录 <{cnt}>')
            while not urp.login():
                print('重新登录失败, 正在重试')
            print('重新登录成功')
            continue
        elif status == '你已经选中了此门课程':
            return 
        elif status == '课程冲突':
            return 
        elif status == '未检测到待选课程':
            return 
        elif exception is not None:
            traceback.print_last()
        
        sleep(2)  


try:
    system('cls')
    # 选择最优服务器
    best_host = choose_best_host()
    if best_host is None:
        print('当前网络状况不佳，建议稍后再试')
        system('pause')
        exit(1)
    print(f'已选择 {best_host} 作为当前服务器')
    sleep(1)


    while True:
        system('cls')
        # 输入用户名密码
        username, password = input_account()

        # 登录
        urp = URP(username, password, best_host)
        if urp.login():
            print('登录成功')
            sleep(1)
            break
        print('登录失败，请检查用户名或密码是否正确')
        sleep(3)

    # 选择工作模式
    system('cls')
    while True:
        print('工作模式:')
        print('1. 截胡模式 (选课已开放, 但是无课余量, 可在他人退课后选课)')
        print('2. 预抢模式 (选课尚未开放, 可预先设置要抢的课程, 并在选课开放后选课)')
        mode = input('请选择工作模式[1/2]:\t')
        if mode == '1':
            system('cls')
            kc_id, kc_no, kc_name = block_mode(urp)
            break
        elif mode == '2':
            system('cls')
            kc_id, kc_no, kc_name = pre_selection_mode(urp)
            break
        else:
            print('输入的模式错误')
            time(3)
            system('cls')
            continue
    
    # 抢课
    system('cls')
    loop_xk(urp, kc_no, kc_id, kc_name)

except KeyboardInterrupt:
    print('用户取消操作')
except Exception:
    traceback.print_last()
    print('程序在运行时发生错误，建议你查看README以寻找解决方案\nhttps://github.com/TerraceCN/YZULessonHunter')
finally:
    system('pause')
    exit(1)
