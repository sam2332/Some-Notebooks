import subprocess
import time
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

def _shell(cmd, debug=False, returns_POpen=False, close_fds=False):
    if debug:
        print(cmd)

    if returns_POpen:
        process = subprocess.Popen(cmd, close_fds=close_fds)
        return process

    process = subprocess.run(cmd, stdout=subprocess.PIPE)
    return process.stdout.decode("utf-8").strip().splitlines()


# In[ ]:


def run_command(cmd, debug=False, returns_POpen=False, close_fds=False):
    # This function runs adb commands on your connected device or emulator.
    if type(cmd) == str:
        cmd = cmd.split(" ")
    cmd = ["adb"] + cmd
    return _shell(cmd, debug=debug, returns_POpen=returns_POpen, close_fds=close_fds)


def TypeTextOnPhone(text):
    for ctext in list(str(text)):
        run_command(["shell", "input", "text", ctext.replace(" ", "%s")])
        time.sleep(0.1)
    run_command(["shell", "input", "keyevent", "66"])
    
def type_number(number):
    keymap = {"0":7,"1":8, "2":9, "3":10, "4":11, "5":12, "6":13, "7":14, "8":15, "9":16}
    for cnumber in list(str(number)):
        run_command(["shell", "input", "keyevent", str(keymap[cnumber])])
        time.sleep(0.5)
    run_command(["shell", "input", "keyevent", "66"])

class Toucher:
    def __init__(self,bh):
        pass
    def tap(self,x,y):
        run_command(f"shell input tap {x} {y}")
    def type(self,text):
        if type(text) ==str:
            TypeTextOnPhone(text)
        elif type(text) == int:
            type_number(text)  
        
class ImageSource():
    def generate(self):
        while True:
            s = time.time()
            run_command("shell screencap -p /sdcard/screen.png")
            run_command("pull /sdcard/screen.png ./game.png")
            run_command("shell rm /sdcard/screen.png")
            im = Image.open("game.png")
            im = im.convert("RGB")
            yield im