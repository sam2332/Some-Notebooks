
import cv2
import numpy as np
from matplotlib import pyplot as plt

import io
import json
import os
import random
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import numpy
import pytesseract
import requests
from tqdm import tqdm

from IPython.display import clear_output, display


from matplotlib import pyplot as plt
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



def secondsToTextDescription(time):
    day = time // (24 * 3600)
    time = time % (24 * 3600)
    hour = time // 3600
    time %= 3600
    minutes = time // 60
    time %= 60
    seconds = time

    out = []
    if day > 0:
        out.append(
            f"{day} Days",
        )
    if hour >0:
        out.append(
            f"{hour} Hours",
        )
    if minutes > 0:
        out.append(
            f"{minutes} Minutes",
        )
    if seconds > 0:
        out.append(
            f"{seconds} Seconds",
        )
    return " ".join(out)

# In[ ]:


def ImageSource_SingleFile(path, as_numpy=False):
    im = Image.open(path)
    im = im.convert("RGB")
    if as_numpy:
        return numpy.array(im)
    return im


def green_blue_swap(image):
    # 3-channel image (no transparency)
    if image.shape[-1] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    # 4-channel image (with transparency)
    elif image.shape[-1] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
    return image 


# In[ ]:


def PillowToCv2(img):
    img = np.array(img)
    
    return img


# In[ ]:


class Beholder_Layer:
    def __init__(self, name, data, offsets=None):
        self.offsets = offsets
        self.name = name
        self.data = data

    def show(self):
        img = self.data
        #img = cv2.cvtColor(self.data, cv2.COLOR_BGR2RGB)
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
    def __init__(
        self,
        name,
        layer,
        filename=None,
        batch_folder=None,
        threshhold=None,
        convertToGray=True,
        mask_filename=None,
    ):
        self.name = name
        self.layer = layer
        self.data = ""
        self.mask = None
        self.convertToGray = convertToGray
        if mask_filename is not None:
            self.mask = cv2.imread(mask_filename, cv2.IMREAD_UNCHANGED)
        if threshhold is None:
            threshhold = 0.8
        self.threshhold = threshhold
        if filename is not None:
            self.mode = "single"
            if Path(filename).exists():
                self.data = cv2.imread(filename)
                self.data = cv2.cvtColor(self.data, cv2.COLOR_RGB2BGR)
                if convertToGray:
                    self.data = cv2.cvtColor(self.data, cv2.COLOR_BGR2GRAY)
            else:
                raise Exception(f"{filename} is missing")
        elif batch_folder is not None:
            self.mode = "batch"
            self.data = []
            directory = Path(batch_folder)
            if directory.exists():
                for path in directory.iterdir():
                    if path.is_file():
                        data = cv2.imread(str(path))
                        data = cv2.cvtColor(data, cv2.COLOR_RGB2BGR)
                        if convertToGray:
                            data = cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)
                        self.data.append(data)
            else:
                raise Exception(f"{filename} is missing")

        else:
            raise Exception("ERROR LOADING MATCHER")

    def run(self, bh):
        if self.mode == "single":
            templates = [self.data]
        else:
            templates = self.data
        o = defaultdict(list)
        f = set()
        for template in templates:
            if self.convertToGray:
                result = cv2.matchTemplate(
                    bh.layers[self.layer].data,
                    template,
                    method=cv2.TM_CCOEFF_NORMED,
                    mask=self.mask,
                )
            else:
                result = cv2.matchTemplate(
                    bh.layers[self.layer].data[:, :, 0],
                    template[:, :, 0],
                    cv2.TM_SQDIFF_NORMED,
                )
            loc = np.where(result >= self.threshhold)

            layer_offset_y = 0
            layer_offset_x = 0
            if bh.layers[self.layer].offsets is not None:
                layer_offset_x, layer_offset_y = bh.layers[self.layer].offsets
            for pt in zip(*loc[::-1]):
                item = (
                    round(layer_offset_x + pt[0] / template.shape[1]),
                    round(layer_offset_y + pt[1] / template.shape[0]),
                )
                if item not in f:
                    f.add(item)

                    center = (layer_offset_x + pt[0], layer_offset_y + pt[1])
                    if type(self.name) == str:
                        o[self.name].append(
                            BeholderMatch(
                                self, self.layer, center, template_shape=template.shape
                            )
                        )
                    elif type(self.name) == list:
                        for name in self.name:
                            o[name].append(
                                BeholderMatch(
                                    self,
                                    self.layer,
                                    center,
                                    template_shape=template.shape,
                                )
                            )
        return o
# In[ ]:

class BeholderMatch():
    def __init__(self,matcher,layer,upper_right,template_shape):
        self.matcher = matcher
        self.layer = layer
        self.upper_right = upper_right
        self.template_shape = template_shape
        self.color = (255, 0, 0)
        self.thickness = 2
        self.center = (
            self.upper_right[0]+self.template_shape[1]/2,
            self.upper_right[1]+self.template_shape[0]/2
        )
    def show(self,bh):
        img = bh.layers[self.layer].data
        img = cv2.rectangle(
            img,
            (self.upper_right[0], self.upper_right[1]),
            (
                self.upper_right[0]+self.template_shape[1],
                 self.upper_right[1]+self.template_shape[0]
            ), 
            self.color,
            self.thickness
        )
        img = cv2.circle(img, self.center,radius=2,color =(255, 0, 0) , thickness=2)
        display(Image.fromarray(img))    



# In[ ]:


class Beholder:
    def __init__(self, ImageSource,toucher):
        self.image_source = ImageSource
        self.generator = self.image_source.generate()
        self.matchers = {}
        self.layers = {}
        self.layer_modifiers = {}
        self.toucher = toucher
    def tap(self,x,y):
        self.toucher.tap(x,y)

    def type(self,text):
        self.toucher.type(text)

    def addLayerModifer(self, ch: Beholder_Layer_Chopper):
        self.layer_modifiers[ch.name] = ch

    def addMatcher(self, m):
        if type(m.name) ==str:
            self.matchers[m.name] = m
        elif type(m.name) ==list:
            self.matchers['_'.join(m.name)] = m
        else:
            raise Exception("bad type str or list")

    def readNextImage(self):
        self.layers["image"] = Beholder_Layer(
            name="image", data=PillowToCv2(next(self.generator)),offsets=(0,0)
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
    def __init__(self, from_layer, enabled=False):
        self.name = from_layer+"_gray"
        self.from_layer = from_layer
        self.enabled = enabled

    def run(self, bh: Beholder):
        o = {}
        o[self.from_layer + "_gray"] = Beholder_Layer(
            name=self.name,
            data=cv2.cvtColor(bh.layers[self.from_layer].data, cv2.COLOR_BGR2GRAY),
            offsets=bh.layers[self.from_layer].offsets
        )
        return o

class Beholder_Layer_Chopper_PeakExtractor(Beholder_Layer_Chopper):
    def __init__(self, name, from_layer, threshhold, enabled=False, avg_fwd=1):
        self.name = name
        self.from_layer = from_layer
        self.threshhold = threshhold
        self.enabled = enabled
        self.avg_fwd = avg_fwd

    def run(self, bh: Beholder):
        o = {}
        frame = cv2.cvtColor(bh.layers[self.from_layer].data, cv2.COLOR_BGR2GRAY)
        finds = []
        in_range = False
        start = 0
        end = 0
        for c in range(0, frame.shape[1]):
            a = [f for f in range(c, c + self.avg_fwd)]
            avg = sum(a) / len(a)

            cell = frame[0][c]
            if cell > self.threshhold:
                if not in_range:
                    start = c
                    end = c
                    in_range = True
            else:
                if in_range:
                    end = c
                    finds.append((bh.layers[self.from_layer].offsets[0]+start, bh.layers[self.from_layer].offsets[0]+end))
                    in_range = False
        o[self.name] = finds
        return o

    
class Beholder_Layer_Chopper_ColorSplit(Beholder_Layer_Chopper):
    def __init__(self, from_layer, enabled=False):
        self.name = "RGB_splitter_" + from_layer
        self.from_layer = from_layer
        self.enabled = enabled

    def run(self, bh: Beholder):
        o = {}
        frame = bh.layers[self.from_layer].data
        height, width, layers = frame.shape
        zeroImgMatrix = np.zeros((height, width), dtype="uint8")
        # The OpenCV image sequence is Blue(B),Green(G) and Red(R)
        (B, G, R) = cv2.split(frame)
        # we would like to construct a 3 channel Image with only 1 channel filled
        # and other two channels will be filled with zeros
        B = cv2.merge([B, zeroImgMatrix, zeroImgMatrix])
        G = cv2.merge([zeroImgMatrix, G, zeroImgMatrix])
        R = cv2.merge([zeroImgMatrix, zeroImgMatrix, R])
        o[self.from_layer + "_B"] = Beholder_Layer(
            name=self.name,
            data=B,
            offsets=bh.layers[self.from_layer].offsets,
        )
        o[self.from_layer + "_G"] = Beholder_Layer(
            name=self.name,
            data=G,
            offsets=bh.layers[self.from_layer].offsets,
        )
        o[self.from_layer + "_R"] = Beholder_Layer(
            name=self.name,
            data=R,
            offsets=bh.layers[self.from_layer].offsets,
        )
        return o


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
            offsets=bh.layers[self.from_layer].offsets
        )
        return o

def sleep(num, print_time=False):
    s = random.choice([-0.1, 0, 0.5, 0.75, 1])
    num += s
    if print_time:
        print(f"sleeping for: {num}")
    if num <0:
        num = 0.1
    time.sleep(num)



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



