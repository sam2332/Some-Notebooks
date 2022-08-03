from lib.MicroWebView import BasicApi, BasicPage
from pages.frame_api import FrameApi


def search(q):
    return [
        {
            "id": 1,
            "title": "Title1",
        },
        {
            "id": 0,
            "title": "Title2",
        },
    ]


class SearchPage(BasicPage):
    route = "/search"
    template_file = "Search.html"
    template_args = {"q": "", "results": []}
    renderOnArgUpdate = True

    def onBeforeRender(self):
        self.template_args["results"] = search(self.template_args["q"])

    class Api(FrameApi):
        def loadResult(self, book_id):
            self.window.ChangeRoute(f"/bookInfo?book_id={book_id}")
