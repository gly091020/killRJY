# -*- coding: utf-8 -*-
import logging
import os.path
import re
import subprocess
from typing import List
import psutil
import winreg
import wmi

target = re.compile("^RC.*\.exe")
target_pid_list = []  # type:List[psutil.Process]
exe_name_list = ["RCManager.exe"]
dns = "123.125.81.6"
exe_path = ""

# 方法1：冻结程序
def freeze():
    if target_pid_list:
        for pid in target_pid_list:
            try:
                pid.suspend()
            except psutil.Error as e:
                logging.exception(e)
                continue
            else:
                logging.info("冻结%s成功" % pid.name())


def unfreeze():
    if target_pid_list:
        for pid in target_pid_list:
            try:
                pid.resume()
            except psutil.Error as e:
                logging.exception(e)
                continue
            else:
                logging.info("解冻%s成功" % pid.name())


def get_pid():
    global exe_path
    target_pid_list.clear()
    for pid in psutil.pids():
        try:
            p1 = psutil.Process(pid)
            if target.search(p1.name()):
                if p1.exe() and os.path.split(p1.exe())[1] == exe_name_list[0]:
                    exe_path = p1.exe()
                target_pid_list.append(p1)
        except psutil.NoSuchProcess:
            continue

# 方法2：劫持映像
def set_reg():
    try:
        for exe_name in exe_name_list:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{exe_name}")
            winreg.SetValueEx(key, "Debugger", False, winreg.REG_SZ, "null.exe")
    except OSError as e:
        logging.exception(e)
    else:
        logging.info("劫持成功")
    for exe_name in exe_name_list:
        subprocess.call("taskkill /im %s /f" % exe_name, creationflags=0x08000000)

def clear_reg():
    try:
        for exe_name in exe_name_list:
            winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{exe_name}")
    except OSError as e:
        logging.exception(e)
    else:
        logging.info("解劫持成功")
    if exe_path:
        subprocess.call(exe_path, creationflags=0x08000000)

# 方法3：恢复dns
def set_dns():
    wmi_service = wmi.WMI()
    col_nic_configs = wmi_service.Win32_NetworkAdapterConfiguration(IPEnabled=True)
    if len(col_nic_configs) < 1:
        logging.exception("没有找到可用的网络适配器")
    obj_nic_config = col_nic_configs[0]
    logging.info(f"修改{obj_nic_config}")
    arr_dns_servers = [dns]
    return_value = obj_nic_config.SetDNSServerSearchOrder(DNSServerSearchOrder=arr_dns_servers)
    subprocess.call("ipconfig /flushdns", creationflags=0x08000000)
    if return_value[0] == 0:
        logging.info("修改成功")
    else:
        logging.exception("修改失败")


# 要用的
def kill():
    set_reg()
    freeze()
    set_dns()

def un_kill():
    clear_reg()
    unfreeze()

