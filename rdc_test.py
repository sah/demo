import os
import sys
import new
import unittest
import time
import traceback
from selenium import webdriver
from sauceclient import SauceClient

USERNAME = os.environ.get('SAUCE_USERNAME')
ACCESS_KEY = os.environ.get('SAUCE_ACCESS_KEY')

BUILD = "RDC load %s" % int((time.time() - 1424998460) / 60.)

sauce = SauceClient(USERNAME, ACCESS_KEY)

platforms = [{'deviceName': "Samsung Galaxy S5 Device",
              'appium-version': "1.4",
              'platformName': "Android",
              'platformVersion': "4.4",
              'device-orientation': "portrait",
              'browserName': "Chrome"
              },
             {'platformName': "Windows 10",
              'browserName': "chrome"
              }]


class FailTestException(Exception):
    pass


def spin_assert(msg, test, timeout=30, args=[]):
    name = getattr(test, '__name__', 'unknown')
    last_e = None
    for i in xrange(timeout):
        try:
            if not test(*args):
                raise AssertionError(msg)
            if i > 0:
                print msg, "success on %s (%s)" % (i + 1, name)
            break
        except FailTestException:
            raise
        except Exception, e:
            if (str(e), type(e)) != (str(last_e), type(last_e)):
                print msg, "(try: %s):" % (i + 1), str(e), type(e)
                traceback.print_exc(file=sys.stdout)
            last_e = e
        time.sleep(1)
    else:
        print "%s fail (%s tries) (%s)" % (msg, i + 1, name)
        raise AssertionError(msg)


def on_platforms(platforms):
    def decorator(base_class):
        module = sys.modules[base_class.__module__].__dict__
        for i, platform in enumerate(platforms):
            d = dict(base_class.__dict__)
            d['desired_capabilities'] = platform

            p = platform['deviceName']
            if 'S4' in p:
                p = 'S4'
            elif 'S5' in p:
                p = 'S5'

            name = "%s_%s_%s" % (base_class.__name__, p, i + 1)
            module[name] = new.classobj(name, (base_class,), d)
    return decorator


@on_platforms(platforms)
class RdcLoadTest(unittest.TestCase):
    def setUp(self):
        self.desired_capabilities['name'] = self.id()
        self.desired_capabilities['build'] = BUILD
        self.desired_capabilities['idleTimeout'] = 600

        sauce_url = "http://%s:%s@ondemand.saucelabs.com:80/wd/hub"
        self.driver = webdriver.Remote(
            desired_capabilities=self.desired_capabilities,
            command_executor=sauce_url % (USERNAME, ACCESS_KEY)
        )
        self.driver.implicitly_wait(30)

    def test_sauce(self):
        self.driver.get('http://saucelabs.com/test/guinea-pig')
        spin_assert("wrong title", lambda: "I am a page title - Sauce Labs" in self.driver.title)
        comments = self.driver.find_element_by_id('comments')
        comments.send_keys('Hello! I am some example comments.'
                           ' I should be in the page after submitting the form')
        self.driver.find_element_by_id('submit').click()

        spin_assert("wrong comment",
                    lambda: ('Your comments: Hello! I am some example comments.'
                             ' I should be in the page after submitting the form'
                             in self.driver.find_element_by_id('your_comments').text))
        spin_assert('bad body', lambda: 'I am some other page content' not in self.driver.find_element_by_xpath('//body').text)
        self.driver.find_elements_by_link_text('i am a link')[0].click()

        spin_assert('bad content', lambda: 'I am some other page content' in self.driver.find_element_by_xpath('//body').text)

    def test_paste(self):
        wd = self.driver
        wd.get("http://codepad.org/")
        wd.find_element_by_xpath("//div[@id='editor']/form/table/tbody/tr[2]/td[1]/nobr[10]/label/input").click()
        wd.find_element_by_id("textarea").click()
        wd.find_element_by_id("textarea").clear()
        wd.find_element_by_id("textarea").send_keys("print \"hello\"")
        if not wd.find_element_by_name("private").is_selected():
            wd.find_element_by_name("private").click()
        wd.find_element_by_name("submit").click()
        spin_assert('no hello', lambda: "print \"hello\"" in wd.find_element_by_tag_name("html").text)

    def test_basics(self):
        wd = self.driver
        wd.get("http://codepad.org/")
        wd.find_element_by_link_text("login").click()
        spin_assert('no create', lambda: "Create Account:" in wd.find_element_by_tag_name("html").text)
        wd.find_element_by_link_text("about").click()
        spin_assert('no what it is', lambda: "What it is" in wd.find_element_by_tag_name("html").text)
        wd.find_element_by_link_text("codepad").click()
        spin_assert('no paste', lambda: "Paste your code" in wd.find_element_by_tag_name("html").text)

    def test_recent(self):
        wd = self.driver
        for i in xrange(20):
            wd.get("http://codepad.org/")
            wd.find_element_by_link_text("Recent Pastes").click()
            spin_assert('no recent', lambda: "Recent Pastes:" in wd.find_element_by_tag_name("html").text)
            wd.find_element_by_link_text("view").click()
            spin_assert('no create', lambda: "Create a new paste based on this one" in wd.find_element_by_tag_name("html").text)

    def test_projects(self):
        wd = self.driver
        wd.get("http://codepad.org/")
        wd.find_element_by_link_text("Get a Project Page").click()
        spin_assert('no create', lambda: "Create a Project:" in wd.find_element_by_tag_name("html").text)

    def no_test_create_account_requires_password(self):
        wd = self.driver
        wd.get("http://codepad.org/login")
        wd.find_element_by_xpath("//div/table/tbody/tr[2]/td/form/table/tbody/tr[1]/td[2]/input").click()
        wd.find_element_by_xpath("//div/table/tbody/tr[2]/td/form/table/tbody/tr[1]/td[2]/input").clear()
        wd.find_element_by_xpath("//div/table/tbody/tr[2]/td/form/table/tbody/tr[1]/td[2]/input").send_keys("nonesuch0237346")
        wd.find_element_by_xpath("//div/table/tbody/tr[2]/td/form/table/tbody/tr[3]/td/input").click()
        assert "Invalid password. Passwords must be at least 3 characters long." in wd.find_element_by_tag_name("html").text

    def no_test_login_requires_password(self):
        wd = self.driver
        wd.get("http://codepad.org/login")
        wd.find_element_by_xpath("//div/table/tbody/tr[1]/td/form/table/tbody/tr[1]/td[2]/input").click()
        wd.find_element_by_xpath("//div/table/tbody/tr[1]/td/form/table/tbody/tr[1]/td[2]/input").clear()
        wd.find_element_by_xpath("//div/table/tbody/tr[1]/td/form/table/tbody/tr[1]/td[2]/input").send_keys("nonesuch0237346")
        wd.find_element_by_xpath("//div/table/tbody/tr[1]/td/form/table/tbody/tr[3]/td/input").click()
        assert "Invalid password. Passwords must be at least 3 characters long." in wd.find_element_by_tag_name("html").text

    def tearDown(self):
        print("Link to your job: https://saucelabs.com/jobs/%s" % self.driver.session_id)
        try:
            if sys.exc_info() == (None, None, None):
                sauce.jobs.update_job(self.driver.session_id, passed=True)
            else:
                sauce.jobs.update_job(self.driver.session_id, passed=False)
        finally:
            self.driver.quit()
