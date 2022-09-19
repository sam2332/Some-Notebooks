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
    adb(["shell", "input", "text", text.replace(" ", "%s")])
    adb(["shell", "input", "keyevent", "66"])




def ScreenCap(resize_ratio=None, as_numpy=False, print_times=False):
    while True:
        s = time.time()
        run_command("shell screencap -p /sdcard/screen.png")
        run_command("pull /sdcard/screen.png ./game.png")
        run_command("shell rm /sdcard/screen.png")
        im = Image.open("game.png")
        im = im.convert("RGB")
        if resize_ratio is not None:
            im = im.resize(
                (int(im.width * resize_ratio), int(im.height * resize_ratio)),
                Image.Resampling.LANCZOS,
            )
        if print_times:
            print("pull image took ", time.time() - s)
        if as_numpy:
            im =  numpy.array(im)
        yield im