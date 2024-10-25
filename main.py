# -*- coding: utf-8 -*-
import ctypes
import json
import math
import os.path
import re
import pynput.keyboard

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.abspath("platforms/")
import sys
import pygame.mixer
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPalette, QBrush, QPixmap, QTransform, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow
import function
import ui


settings = {
    "killCommand": "function.set_reg()\nfunction.freeze();\nfunction.set_dns()",
    "unKillCommand": "function.clear_reg()\nfunction.unfreeze()",
    "RJYRe": "^CM.*\.exe",
    "RJYEXEList": ["CMLauncher.exe", "CMService.exe", "CMApp.exe"],
    "killKey": "<ctrl>+<alt>+k",
    "targetDns": "123.125.81.6",
    "注释": "function.set_reg()函数属于毁灭性打击，可以彻底关闭锐捷，但是不能及时恢复\n"
            "function.freeze()函数同冻结程序，只是冻结，可以立即恢复，但冻结期间锐捷会未响应\n"
            "function.set_dns()函数可以解网，请在锐捷被打击期间使用"
}


def get_settings():
    global settings
    try:
        if os.path.isfile("config.json"):
            with open("config.json") as f:
                settings = json.loads(f.read())
        else:
            with open("config.json", "w+") as f:
                f.write(json.dumps(settings, ensure_ascii=False, indent=4))
    except json.JSONDecodeError:
        with open("config.json", "w+") as f:
            f.write(json.dumps(settings, ensure_ascii=False, indent=4))


def source_path(relative_path):
    # 是否Bundle Resource
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

get_settings()
cd = source_path('')
os.chdir(cd)

function.exe_name_list = settings["RJYEXEList"]
function.target = re.compile(settings["RJYRe"])
function.dns = settings["targetDns"]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.mouse_x, self.mouse_y = -1000, -1000
        self.is_click = False

    def mouseMoveEvent(self, a0):
        self.mouse_x, self.mouse_y = a0.x(), a0.y()

    def mousePressEvent(self, a0):
        self.is_click = True

    def mouseReleaseEvent(self, a0):
        self.is_click = False



if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    MainWindow = MainWindow()
    ui = ui.Ui_MainWindow()
    ui.setupUi(MainWindow)
    pygame.mixer.init()

    palette = QPalette()
    palette.setBrush(QPalette.Background, QBrush(QPixmap("data/background.png")))
    MainWindow.setPalette(palette)

    ui.title_bg.setPixmap(QPixmap("data/text_bg.png"))
    lever_1_texture = (QPixmap("data/lever_1.png"), QPixmap("data/lever_1_lit.png"))
    ui.lever_1.setPixmap(lever_1_texture[0])
    ui.desktop.setPixmap(QPixmap("data/desktop.png"))
    rounded_pixmap = QPixmap("data/lever_2.png")
    lever_sound = pygame.mixer.Sound("data/lever.wav")
    orb_sound = pygame.mixer.Sound("data/orb.wav")
    level_up_sound = pygame.mixer.Sound("data/level_up.wav")
    is_on = False
    run_on_main_thread_fun = None


    def get_direction_degree(x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        return angle_deg

    angle = int(get_direction_degree(ui.lever_2.pos().x() + ui.lever_2.width() / 2,
                                     ui.lever_2.pos().y() + ui.lever_2.height() / 2, MainWindow.mouse_x,
                                     MainWindow.mouse_y)) + 90
    o_angle = angle

    def look_mouse():
        global angle, o_angle, is_on, run_on_main_thread_fun
        angle = int(get_direction_degree(ui.lever_2.pos().x() + ui.lever_2.width() / 2, ui.lever_2.pos().y() + ui.lever_2.height() / 2, MainWindow.mouse_x, MainWindow.mouse_y)) + 90
        if angle > 45:
            angle = 45
        elif angle < -45:
            angle = -45
        if o_angle != angle:
            lever_sound.play()
        if not MainWindow.is_click:
            if angle == 45 and not is_on:
                level_up_sound.play()
                is_on = True
                exec(settings["killCommand"])
            elif angle == -45 and is_on:
                orb_sound.play()
                is_on = False
                exec(settings["unKillCommand"])
        o_angle = angle
        transform = QTransform().translate(rounded_pixmap.width() / 2, rounded_pixmap.height() / 2) \
            .rotate(angle) \
            .translate(-rounded_pixmap.width() / 2, -rounded_pixmap.height() / 2)
        ui.lever_2.setPixmap(rounded_pixmap.transformed(transform, mode=1))
        ui.lever_1.setPixmap(lever_1_texture[is_on])
        if run_on_main_thread_fun:
            run_on_main_thread_fun()
        run_on_main_thread_fun = None

    timer1 = QTimer()
    timer1.timeout.connect(look_mouse)
    timer1.start(100)
    MainWindow.setMouseTracking(True)

    def run_on_main_thread(fun: function):
        global run_on_main_thread_fun
        if run_on_main_thread_fun:
            return
        run_on_main_thread_fun = fun

    def key_fun():
        global is_on
        is_on = not is_on
        if is_on:
            exec(settings["killCommand"])
            MainWindow.mouse_x = 1000
            MainWindow.mouse_y = 0
        else:
            exec(settings["unKillCommand"])
            MainWindow.mouse_x = -1000
            MainWindow.mouse_y = 0
        orb_sound.play()
    h = pynput.keyboard.GlobalHotKeys({settings["killKey"]: lambda: run_on_main_thread(key_fun)})
    # 解网只能在主线程运行
    h.daemon = True
    h.start()

    MainWindow.setWindowIcon(QIcon(QPixmap("data/killRJY.png")))
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("RJYKill")
    MainWindow.setFixedSize(MainWindow.width(), MainWindow.height())

    function.get_pid()

    MainWindow.show()
    sys.exit(app.exec_())
