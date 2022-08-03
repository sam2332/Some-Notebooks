from lib.MicroWebView import BasicApi, PageMaster, BasicPage
from pages.loginPage import LoginPage
from pages.homePage import HomePage
from pages.searchPage import SearchPage
from pages.documentationPage import DocumentationPage
from pages.errorPage import ErrorPage
import atexit

pm = PageMaster("FrameWork", global_template_args={"navDisable": False})
pm.AddPage(LoginPage)
pm.AddPage(HomePage)
pm.AddPage(SearchPage)
pm.AddPage(DocumentationPage)
pm.AddPage(ErrorPage)

pm.setStartupPage(LoginPage)

pm.run()


def all_done():
    print("All done")


atexit.register(all_done)
