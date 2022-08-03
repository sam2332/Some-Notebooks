import os
import urllib.parse

os.environ["PYWEBVIEW_LOG"] = "debug"


import logging

logging.basicConfig(
    filename="myapp.log",
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.info("APP Started")
exlogger = logging.getLogger("Exception")

import sys


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    exlogger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ""

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass


log = logging.getLogger("Stdout")
sys.stdout = StreamToLogger(log, logging.INFO)
log = logging.getLogger("Stderr")
sys.stderr = StreamToLogger(log, logging.ERROR)

import inspect
import jinja2
from jinja2 import Environment, BaseLoader
import webview


class ApiMaster:
    window = None
    _pages = {}
    _apis = {}
    _currentRoute = ""
    _templateArgs = {}

    def __init__(self, pages, apis, startupRoute, templateArgs):
        self._pages = pages
        self._apis = {}
        self._templateArgs = templateArgs
        for page in self._pages:
            self._pages[page].template_args.update(self._templateArgs)

        for api in apis:
            self._apis[api] = apis[api](self)
            self._apis[api].template_args.update(self._pages[api].template_args)
        self._currentRoute = startupRoute

        for i in inspect.getmembers(self._apis[self._currentRoute]):
            if not i[0].startswith("_"):
                if inspect.ismethod(i[1]):
                    setattr(ApiMaster, i[0], i[1])
                    print(f"Adding Method {i[0]}")

    def RenderTemplateString(self, template, args={}):
        if "onBeforeRender" in [
            i[0] for i in inspect.getmembers(self._pages[self._currentRoute])
        ]:
            self._pages[self._currentRoute].onBeforeRender()
        self.window.load_html(jinga2TemplateString(template, args))

    def RenderTemplateFile(self, template, args={}):
        if "onBeforeRender" in [
            i[0] for i in inspect.getmembers(self._pages[self._currentRoute])
        ]:
            self._pages[self._currentRoute].onBeforeRender()
        self.window.load_html(jinga2Template(template, args))

    def ChangeTemplateFile(self, template):
        self._pages[self._currentRoute].template_file = template
        self.rerender()

    def ChangeRoute(self, new_route):
        args_update = None
        if "?" in new_route:
            new_route = new_route.split("?")
            args_update = dict(urllib.parse.parse_qsl(new_route[1]))
            new_route = new_route[0]
        if new_route in self._pages:
            if args_update is not None:
                self._pages[new_route].template_args.update(args_update)
                self._apis[new_route].template_args.update(args_update)

            if "onBeforeRender" in [
                i[0] for i in inspect.getmembers(self._pages[new_route])
            ]:
                self._pages[new_route].onBeforeRender()

            if "_onBeforeLeave" in [
                i[0] for i in inspect.getmembers(self._apis[self._currentRoute])
            ]:
                self._apis[self._currentRoute]._onBeforeLeave()

            for i in inspect.getmembers(self._apis[self._currentRoute]):
                if not i[0].startswith("_"):
                    if inspect.ismethod(i[1]):
                        delattr(ApiMaster, i[0])
                        print(f"Removing Method {i[0]}")

            self._currentRoute = new_route

            for i in inspect.getmembers(self._apis[self._currentRoute]):
                if not i[0].startswith("_"):
                    if inspect.ismethod(i[1]):
                        setattr(ApiMaster, i[0], i[1])
                        print(f"Adding Method {i[0]}")

            if "_onBeforeLoad" in [
                i[0] for i in inspect.getmembers(self._apis[new_route])
            ]:
                self._apis[new_route]._onBeforeLoad()

            self.window.load_html(
                jinga2Template(
                    self._pages[new_route].template_file,
                    self._pages[new_route].template_args
                    if self._pages[new_route].template_args
                    else None,
                )
            )

        else:
            exlogger.error(f"Page {new_route} does not exist")

    def UpdateTemplateArgs(self, args):
        self._pages[self._currentRoute].template_args.update(args)
        self._apis[self._currentRoute].template_args.update(args)
        if self._pages[self._currentRoute].renderOnArgUpdate:
            self.rerender()

    def GetTemplateArg(self, arg, default_return=False):
        if arg in self._pages[self._currentRoute].template_args:
            return self._pages[self._currentRoute].template_args
        return default

    def UpdateGlobalTemplateArgs(self, args):
        for p in self._pages:
            self._pages[p].template_args.update(args)
        if self._pages[self._currentRoute].renderOnArgUpdate:
            self.rerender()

    def rerender(self):
        if "onBeforeRender" in [
            i[0] for i in inspect.getmembers(self._pages[self._currentRoute])
        ]:
            self._pages[self._currentRoute].onBeforeRender()
        self.window.load_html(
            jinga2Template(
                self._pages[self._currentRoute].template_file,
                self._pages[self._currentRoute].template_args
                if self._pages[self._currentRoute].template_args
                else None,
            )
        )


class BasicApi:
    window = None
    template_args = {}

    def __init__(self, window):
        self.window = window


def jinga2TemplateString(TEMPLATE_STRING, args={}):
    print("RenderArgs", args)
    rtemplate = Environment(loader=BaseLoader).from_string(TEMPLATE_STRING)
    outputText = rtemplate.render(**args)
    with open("lastRender.html", "w") as f:
        f.write(outputText)
    return outputText


def jinga2Template(TEMPLATE_FILE, args={}):
    print("RenderArgs", args)
    templateLoader = jinja2.FileSystemLoader(searchpath="./Templates/")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(TEMPLATE_FILE)
    outputText = str(template.render(args))
    with open("lastRender.html", "w") as f:
        f.write(outputText)
    return outputText


class BasicPage:
    route = ""
    template_file = ""
    template_args = {}
    renderOnArgUpdate = False


class PageMaster:
    title = ""
    startupRoute = ""
    pages = {}
    apis = {}
    templateArgs = {}
    CApi = ApiMaster

    def __init__(self, title, global_template_args=None):

        self.title = title
        self.templateArgs["app_title"] = title
        if global_template_args is not None:
            self.templateArgs.update(global_template_args)

    def AddPage(self, pageObj):
        self.apis[pageObj.route] = type("CApi", (pageObj.Api, BasicApi), {})
        self.pages[pageObj.route] = pageObj()

    def makeApi(self):
        self.inst = self.CApi(
            self.pages, self.apis, self.startupRoute, self.templateArgs
        )
        return self.inst

    def setStartupPage(self, pageObj):
        self.startupRoute = pageObj.route

    def run(self):
        api = self.makeApi()
        html = jinga2Template(
            self.pages[self.startupRoute].template_file,
            self.pages[self.startupRoute].template_args
            if self.pages[self.startupRoute].template_args
            else None,
        )
        window = webview.create_window(
            self.title,
            html=html,
            js_api=api,
            resizable=True,
            confirm_close=True,
            width=900,
        )
        api.window = window
        webview.start(debug=True, gui="edgehtml")
