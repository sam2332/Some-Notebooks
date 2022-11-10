import cv2
import numpy as np
from python_vnc_client.vnc import Vnc

def green_blue_swap(image):
    # 3-channel image (no transparency)
    if image.shape[-1] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    # 4-channel image (with transparency)
    elif image.shape[-1] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
    return image 


class Toucher:
    def __init__(self,IMGSOURCE):
        self.vnc = IMGSOURCE.vnc
    def tap(self,x,y):
        vnc.mouse_event("Left",(x,y))
        
class ImageSource:
    def __init__(self,host,port=5900):
        self.vnc = Vnc(
            host,
            port,
        )
    def generate(self):
        try:
            self.vnc.connect()
            while True:

                try:
                    image = self.vnc.capture_screen(True)

                    data = np.array(image, dtype=np.uint8)
                    data = green_blue_swap(data)
                    yield data
                except Exception as e:
                    print(e)
        finally:
            self.vnc.close()