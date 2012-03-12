import time
import ctypes
user32 = ctypes.windll.user32

keyPressFunc = user32.keybd_event
VK_LEFT = 0x25
VK_RIGHT = 0x27
VK_UP = 0x26

KEY_EVENT_EXTENDED_KEY = 0x1
KEY_EVENT_KEYUP = 0x2

def keyPress(key):
	keyPressFunc(key, 0, KEY_EVENT_EXTENDED_KEY, 0)
	keyPressFunc(key, 0, KEY_EVENT_KEYUP, 0)
	
def keyForward():
	keyPress(VK_RIGHT)
	
def keyBack():
	keyPress(VK_LEFT)
	
def test():
	for i in range(5):
		time.sleep(1)
		keyPress(VK_UP)
		
if __name__ == "__main__":
	test()