import os
import cv2
import gc
import sys
import curses
import time
from ctypes import POINTER, WinDLL, Structure, sizeof, byref
from ctypes.wintypes import BOOL, SHORT, WCHAR, UINT, ULONG, DWORD, HANDLE
from playsound import playsound
from threading import Thread

LF_FACESIZE = 32
STD_OUTPUT_HANDLE = -11


class COORD(Structure):
    _fields_ = [
        ("X", SHORT),
        ("Y", SHORT),
    ]


class CONSOLE_FONT_INFOEX(Structure):
    _fields_ = [
        ("cbSize", ULONG),
        ("nFont", DWORD),
        ("dwFontSize", COORD),
        ("FontFamily", UINT),
        ("FontWeight", UINT),
        ("FaceName", WCHAR * LF_FACESIZE)
    ]


kernel32_dll = WinDLL("kernel32.dll")

get_last_error_func = kernel32_dll.GetLastError
get_last_error_func.argtypes = []
get_last_error_func.restype = DWORD

get_std_handle_func = kernel32_dll.GetStdHandle
get_std_handle_func.argtypes = [DWORD]
get_std_handle_func.restype = HANDLE

get_current_console_font_ex_func = kernel32_dll.GetCurrentConsoleFontEx
get_current_console_font_ex_func.argtypes = [HANDLE, BOOL, POINTER(CONSOLE_FONT_INFOEX)]
get_current_console_font_ex_func.restype = BOOL

set_current_console_font_ex_func = kernel32_dll.SetCurrentConsoleFontEx
set_current_console_font_ex_func.argtypes = [HANDLE, BOOL, POINTER(CONSOLE_FONT_INFOEX)]
set_current_console_font_ex_func.restype = BOOL

stdout = get_std_handle_func(STD_OUTPUT_HANDLE)
# Get current font characteristics
font = CONSOLE_FONT_INFOEX()
font.cbSize = sizeof(CONSOLE_FONT_INFOEX)
res = get_current_console_font_ex_func(stdout, False, byref(font))
font.dwFontSize.X = 10  # Changing X has no effect (at least on my machine)
font.dwFontSize.Y = 11
# Apply changes
res = set_current_console_font_ex_func(stdout, False, byref(font))
res = get_current_console_font_ex_func(stdout, False, byref(font))


cap = cv2.VideoCapture('Bad Apple_144p.mp4')
frameCount = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frameWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frameHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))


cmd = f'mode {frameWidth + 1}, {frameHeight + 1}'
os.system(cmd)

fps = 30
ms = 1 / fps
status = 0
videoHeight = frameHeight // 2


def generate_ascii():
    global fps
    fc = 0
    out = ''
    gscale = ".:-=+*#%@"
    temp = open("source.txt", "w")
    while cap.isOpened():
        ret, buf = cap.read()
        if not ret:
            break
        cv2.imshow('image', buf)
        k = cv2.waitKey(5)
        fc += 1
        os.system('cls')

        for i in range(videoHeight):
            for j in range(int(frameWidth)):
                R = buf[i * 2][j][0]
                G = buf[i * 2][j][1]
                B = buf[i * 2][j][2]
                gray = 0.2126 * R + 0.7152 * G + 0.0722 * B
                out += gscale[int(gray // 30)]

            out += "\n"
        temp.write(out)
        temp.write("\n")
        out = ''
        if k & 0xff == ord('q'):
            break
    temp.close()

    cap.release()
    cv2.destroyAllWindows()


# generate_ascii()

stdscr = curses.initscr()
stdscr.scrollok(True)
stdscr.timeout(1)
curses.curs_set(0)
curses.noecho()
curses.cbreak()
stdscr.keypad(True)

def play_music():
    playsound('./Bad Apple.mp3')


music_thread = Thread(target=play_music)
music_thread.start()
t0 = time.time()
frame = 1
with open("source.txt", 'r') as f:
    while True:
        t1 = time.time()
        new_frame = int((t1 - t0) * fps) + 1
        if new_frame == frame:
            continue
        frame = new_frame

        try:
            data = ""
            for i in range(videoHeight):
                data += f.readline()
            f.readline()
            stdscr.addstr(0, 0, data)
            # stdscr.addstr("Frame: %d" % i)
            stdscr.clrtoeol()
            stdscr.clearok(1)
            stdscr.refresh()
        except IOError:
            break

curses.curs_set(1)
curses.echo()
curses.nocbreak()
stdscr.keypad(False)

curses.endwin()
gc.collect()
sys.exit()
