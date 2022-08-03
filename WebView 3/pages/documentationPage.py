from lib.MicroWebView import BasicApi, BasicPage
import os
from pages.frame_api import FrameApi


class DocumentationPage(BasicPage):
    route = "/documentation"
    template_file = "Documentation.html"
    template_args = {"files": []}
    renderOnArgUpdate = True

    def __init__(self):
        for file in os.listdir("Documentation"):
            name = file.split(".")
            name.pop(-1)
            name = ".".join(name)
            self.template_args["files"].append({"file": file, "name": name})

    class Api(FrameApi):
        def openFile(self, file):
            os.system(f"start './Documentation/{file}'")
