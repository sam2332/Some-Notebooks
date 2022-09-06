

import io
import json
import os
import random
import subprocess
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy
import pytesseract
import requests
from IPython.display import clear_output, display
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from tqdm import tqdm


# In[ ]:


import pyttsx3

tts_engine = pyttsx3.init()
tts_engine.setProperty("volume", 0.5)


def tts(s, volume=None):
    if volume is not None:
        old_volume = tts_engine.getProperty("volume")
        tts_engine.setProperty("volume", volume)
    print(f"{datetime.now().time()} - tts: {s}")
    tts_engine.say(s)
    tts_engine.runAndWait()
    if volume is not None:

        tts_engine.setProperty("volume", old_volume)



# In[ ]:


datetime.now().time()


# In[ ]:


import cv2
import numpy as np


# In[ ]:


from matplotlib import pyplot as plt


# In[ ]:


def shell(cmd, debug=False, returns_POpen=False, close_fds=False):
    if debug:
        print(cmd)

    if returns_POpen:
        process = subprocess.Popen(cmd, close_fds=close_fds)
        return process

    process = subprocess.run(cmd, stdout=subprocess.PIPE)
    return process.stdout.decode("utf-8").strip().splitlines()


# In[ ]:


def adb(cmd, debug=False, returns_POpen=False, close_fds=False):
    # This function runs adb commands on your connected device or emulator.
    if type(cmd) == str:
        cmd = cmd.split(" ")
    cmd = ["adb"] + cmd
    return shell(cmd, debug=debug, returns_POpen=returns_POpen, close_fds=close_fds)


def TypeTextOnPhone(text):
    adb(["shell", "input", "text", text.replace(" ", "%s")])
    adb(["shell", "input", "keyevent", "66"])


# In[ ]:


def sleep(num, print_time=False):
    s = random.choice([-1.75, -1, -0.5, 0, 0.5, 0.75, 1])
    num += s
    if print_time:
        print(f"sleeping for: {num}")
    time.sleep(num)


# In[ ]:


def pullPhoneScreen(resize_ratio=None, as_numpy=False, print_times=False):
    s = time.time()
    adb("shell screencap -p /sdcard/screen.png")
    adb("pull /sdcard/screen.png ./game.png")
    adb("shell rm /sdcard/screen.png")
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
        return numpy.array(im)
    return im


# In[ ]:


def PillowToCv2(img):
    img = np.array(img)
    if img.shape[-1] > 1:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img


# In[ ]:


class Beholder_Layer:
    def __init__(self, name, data, offsets=None):
        self.offsets = offsets
        self.name = name
        self.data = data

    def show(self):
        img = cv2.cvtColor(self.data, cv2.COLOR_BGR2RGB)
        display(Image.fromarray(img))

    def chop(self, new_name, x, y, h, w):
        return Beholder_Layer(
            name=new_name, data=self.data[y : y + h, x : x + w], offsets=(x, y)
        )


# In[ ]:


class Beholder_Layer_Chopper:
    def __init__(self, name):
        self.name = name

    def run(self, bh):
        pass


# In[ ]:


class Beholder_Matcher:
    def __init__(self, name, layer, enabled=False):
        self.enabled = enabled
        self.data = ""

    def show(self):
        img = cv2.cvtColor(self.data, cv2.COLOR_BGR2RGB)
        display(Image.fromarray(img))
    def run(self, bh):
        pass
    def __repr__(self):
        return f"Matcher: {self.name}"


# In[ ]:


class Beholder_Image_Matcher(Beholder_Matcher):
    def __init__(self, name, layer, filename, threshhold=None,
            sensitivity = None, convertToGray=True):
        self.name = name
        self.layer = layer
        self.data = ""
        if threshhold is None:
            threshhold = 0.8
        self.threshhold = threshhold
        if sensitivity is None:
            sensitivity = 60
        self.sensitivity = sensitivity
        if Path(filename).exists():
            self.data = PillowToCv2(Image.open(filename))
            if convertToGray:
                self.data = cv2.cvtColor(self.data, cv2.COLOR_BGR2GRAY)
        else:
            raise Exception(f"{filename} is missing")

    def run(self, bh):
        result = cv2.matchTemplate(
            bh.layers[self.layer].data, self.data, method=cv2.TM_CCOEFF_NORMED
        )
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        o={}
        if max_val > self.threshhold:
            height, width = self.data.shape[:2]
            layer_offset_y = 0
            layer_offset_x = 0
            if bh.layers[self.layer].offsets is not None:
                layer_offset_x, layer_offset_y = bh.layers[self.layer].offsets
            top_left = max_loc
            center = (
                (layer_offset_x + top_left[0] + (width / 2)),
                (layer_offset_y + top_left[1] + (height / 2)),
            )

            loc = np.where(result >= self.threshhold)

            f = set()
            for pt in zip(*loc[::-1]):
                f.add(
                    (
                        round(layer_offset_x + pt[0] / self.sensitivity),
                        layer_offset_y + round(pt[1] / self.sensitivity),
                    )
                )
            o[self.name]=BeholderMatch(self, center, f)
        return o

# In[ ]:

class BeholderMatch():
    def __init__(self,matcher,center,f):
        self.matcher = matcher
        self.center = center
        self.f = f
    



# In[ ]:


class Beholder:
    def __init__(self, videoFrameGenerator):
        self.generator = videoFrameGenerator
        self.matchers = {}
        self.layers = {}
        self.layer_modifiers = {}

    def addLayerModifer(self, ch: Beholder_Layer_Chopper):
        self.layer_modifiers[ch.name] = ch

    def addMatcher(self, m):
        self.matchers[m.name] = m

    def readNextImage(self):
        self.layers["image"] = Beholder_Layer(
            name="image", data=PillowToCv2(self.generator())
        )

    def digestImage(self):
        for m in self.layer_modifiers:
            if self.layer_modifiers[m].enabled:
                u = self.layer_modifiers[m].run(self)
                if u is not None:
                    self.layers.update(u)


    def findMatches(self, matchers=None):
        if matchers is None:
            matchers = self.matchers
        self.readNextImage()
        self.digestImage()
        matches = defaultdict(list)
        for m in matchers:
            m = matchers[m]
            mr = m.run(self)
            if mr is not None:
                matches.update(mr)

        return dict(matches)


# In[ ]:


class Beholder_Layer_Chopper_Grayscale(Beholder_Layer_Chopper):
    def __init__(self, name, from_layer, enabled=False):
        self.name = name
        self.from_layer = from_layer
        self.enabled = enabled

    def run(self, bh: Beholder):
        o = {}
        o[self.name] = Beholder_Layer(
            name=self.name,
            data=cv2.cvtColor(bh.layers[self.from_layer].data, cv2.COLOR_BGR2GRAY),
        )
        return o


# In[ ]:


class Beholder_Layer_Chopper_InRange(Beholder_Layer_Chopper):
    def __init__(self, name, from_layer, lbounds, ubounds, enabled=False):
        self.name = name
        self.from_layer = from_layer
        self.ubounds = ubounds
        self.lbounds = lbounds
        self.enabled = enabled

    def run(self, bh: Beholder):
        o = {}
        hsv = cv2.cvtColor(bh.layers[self.from_layer].data, cv2.COLOR_BGR2HSV)
        lower = np.array(self.lbounds)
        upper = np.array(self.ubounds)
        mask = cv2.inRange(hsv, lower, upper)
        o[self.name] = Beholder_Layer(
            name=self.name,
            data=cv2.bitwise_and(hsv, bh.layers[self.from_layer].data, mask=mask),
        )
        return o


# In[ ]:


class Beholder_Layer_TextExtract(Beholder_Layer_Chopper):
    def __init__(self, name, from_layer, threshhold, from_layer_is_bw, enabled=False):
        self.name = name
        self.from_layer = from_layer
        self.threshhold = threshhold
        self.from_layer_is_bw = from_layer_is_bw
        self.enabled = enabled

    def run(self, bh: Beholder):
        o = {}
        img = Image.fromarray(bh.layers[self.from_layer].data)
        if not self.from_layer_is_bw:
            img = img.convert("L")  # grayscale
        img = img.filter(ImageFilter.MedianFilter())  # a little blur
        img = img.point(lambda x: 0 if x < self.threshhold else 255)  # threshhold (binarize)

        txt = pytesseract.image_to_string(img)
        o[self.name] = txt.splitlines()


# In[ ]:


class Beholder_Layer_Chopper_AtCord(Beholder_Layer_Chopper):
    def __init__(self, name, from_layer, x, y, h, w, enabled=False):
        self.name = name
        self.from_layer = from_layer
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.enabled = enabled

    def run(self, bh: Beholder):
        o = {}
        o[self.name] = Beholder_Layer(
            name=self.name,
            data=bh.layers[self.from_layer].data[
                self.y : self.y + self.h, self.x : self.x + self.w
            ],
            offsets=(self.x, self.y),
        )
        return o


# In[ ]:


adb("wait-for-device")