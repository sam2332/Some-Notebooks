from lib.MicroWebView import BasicApi, BasicPage


class ErrorPage(BasicPage):
    route = "/error"
    template_file = "Error.html"
    template_args = {"type": "", "message": "", "retry_route": ""}

    class Api(BasicApi):
        def retry(self):
            self.window.ChangeRoute(self.template_args["retry_route"])
