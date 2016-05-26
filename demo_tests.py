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

BUILD = os.environ.get('JOB_NAME') + ' #' + os.environ.get('BUILD_NUMBER')

sauce = SauceClient(USERNAME, ACCESS_KEY)

platforms = [{'deviceName': "Samsung Galaxy S4 Emulator",
              'platformName': "Android",
              'platformVersion': "4.4",
              'deviceOrientation': "portrait",
              'browserName': "browser",
              'appiumVersion': "1.5.2"
              },
             {'deviceName': "iPhone Simulator",
              'platformName': "iOS",
              'platformVersion': "9.2",
              'deviceOrientation': "portrait",
              'browserName': "Safari",
              'appiumVersion': "1.5.2"
              },
             {'platform': "Windows 10",
              'browserName': "chrome",
              'version': "latest"
              },
             {'platform': "OS X 10.11",
              'browserName': "safari",
              'version': "latest"
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

            p = platform.get('deviceName', platform.get('browserName'))
            if 'S4' in p:
                p = 'S4'
            elif 'iPhone' in p:
                p = 'iPhone'

            name = "%s_%s_%s" % (base_class.__name__, p, i + 1)
            module[name] = new.classobj(name, (base_class,), d)
    return decorator


@on_platforms(platforms)
class WalmartTests(unittest.TestCase):
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

    def test_search(self):
        self.driver.get('http://walmart.com/')
        search = self.driver.find_element_by_css_selector('.js-searchbar-input')
        search.click()
        search.send_keys("hot sauce")

        submit = self.driver.find_element_by_css_selector('.searchbar-submit')
        submit.click()
        spin_assert("wrong title", lambda: "hot sauce" in self.driver.title)
        cholula = self.driver.find_element_by_link_text('Cholula Original Hot Sauce, 12 fl oz')
        cholula.click()
        spin_assert("wrong comment",
                    lambda: ('FREE shipping on orders $50 +'
                             in self.driver.find_element_by_css_selector('.free-shipping-threshold-eligible').text))

    def test_basics(self):
        wd = self.driver
        wd.get("http://walmart.com/")
        wd.find_element_by_link_text("Tips & Ideas").click()
        spin_assert('no find it', lambda: "Find it fast" in wd.find_element_by_tag_name("html").text)
        wd.find_element_by_link_text("Food & Celebrations").click()
        wd.find_element_by_link_text("Food & Recipes").click()
        spin_assert('no special occasions', lambda: "Special Occasions" in wd.find_element_by_tag_name("html").text)

    def tearDown(self):
        print("Link to your job: https://saucelabs.com/jobs/%s" % self.driver.session_id)
        try:
            if sys.exc_info() == (None, None, None):
                sauce.jobs.update_job(self.driver.session_id, passed=True)
            else:
                sauce.jobs.update_job(self.driver.session_id, passed=False)
        finally:
            self.driver.quit()
