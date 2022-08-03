from lib.MicroWebView import BasicApi, BasicPage


def checkLogin(user, password):
    users = {"demo": "demo"}
    if user in users:
        if password == users[user]:
            return True
    return "Bad Login"


class LoginPage(BasicPage):
    route = "/login"
    template_args = {"error": ""}
    template_file = "Login.html"
    renderOnArgUpdate = True

    class Api(BasicApi):
        def login(self, user, password):
            login = checkLogin(user, password)
            # login = True
            if login is True:
                self.window.ChangeRoute("/index")
            else:
                self.window.UpdateTemplateArgs({"message": login})
