from lib.MicroWebView import BasicApi, BasicPage
from pages.frame_api import FrameApi


class HomePage(BasicPage):
    route = "/index"
    template_file = "Index.html"
    renderOnArgUpdate = True

    class Api(FrameApi):
        pass
