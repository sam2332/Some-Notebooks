from lib.MicroWebView import BasicApi


class FrameApi(BasicApi):
    def searchBook(self, book_name):
        self.window.UpdateGlobalTemplateArgs({"search": book_name})
        self.window.ChangeRoute(f"/search?q={book_name}")

    def showMenu(self, page):
        self.window.ChangeRoute(f"/{page}")
