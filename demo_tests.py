import os
import sys
import new
import unittest
import time
import traceback
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from sauceclient import SauceClient

USERNAME = os.environ.get('SAUCE_USERNAME')
ACCESS_KEY = os.environ.get('SAUCE_ACCESS_KEY')

BUILD = os.environ.get('JOB_NAME') + ' #' + os.environ.get('BUILD_NUMBER')

sauce = SauceClient(USERNAME, ACCESS_KEY)


platforms = [{'deviceName': "iPhone Simulator",
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
             {'platform': "Windows 10",
              'browserName': "edge",
              'version': "latest"
              },
             {'platform': "OS X 10.11",
              'browserName': "safari",
              'version': "latest"
              },
             {'platform': "OS X 10.10",
              'browserName': "chrome",
              'version': "latest"
              }]
platforms = platforms * 2


class FailTestException(Exception):
    pass


def spin_assert(msg, test, timeout=5, args=[]):
    name = getattr(test, '__name__', 'unknown')
    last_e = None
    for i in xrange(timeout):
        try:
            if not test(*args):
                raise AssertionError(msg)
            if i > 0:
                print "success on try %s (%s(msg=%s args=%s))" % (i + 1, name, repr(msg), repr(args))
            break
        except FailTestException:
            raise
        except Exception, e:
            if (str(e), type(e)) != (str(last_e), type(last_e)):
                print "%s: %s (try: %s): %s %s" % (msg, repr(args), (i + 1), str(e), type(e))
                traceback.print_exc(file=sys.stdout)
            last_e = e
        time.sleep(1)
    else:
        print "%s: %s fail (%s tries) (%s)" % (msg, repr(args), i + 1, name)
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

        sauce_url = "http://%s:%s@ondemand.saucelabs.com:4499/wd/hub"
        self.driver = webdriver.Remote(
            desired_capabilities=self.desired_capabilities,
            command_executor=sauce_url % (USERNAME, ACCESS_KEY)
        )
        self.driver.implicitly_wait(300)

    def move_to_element(self, element):
        if not self.desired_capabilities['browserName'] in ['android', 'safari', 'firefox']:
            ActionChains(self.driver).move_to_element(element).perform()

    def test_search(self):
        self.driver.get('http://walmart.com/')
        #search = self.driver.find_element_by_css_selector('.js-searchbar-input')
        search = self.driver.find_element_by_css_selector('input#global-search-input.header-GlobalSearch-input')
        search.click()
        search.send_keys("hot sauce")

        #submit = self.driver.find_element_by_css_selector('.searchbar-submit')
        submit = self.driver.find_element_by_css_selector('button.header-GlobalSearch-submit')
        submit.click()

        def check_in_title(title_content):
            title = self.driver.title
            if title_content not in title:
                print "%s not in %s" % (repr(title_content), repr(title))
                return False
            return True

        spin_assert("wrong title", check_in_title, args=["hot sauce"])
        cholula = self.driver.find_element_by_link_text('Cholula Original Hot Sauce, 12 fl oz')
        cholula.click()
        spin_assert("wrong title", check_in_title, args=["Cholula Original"])

    def test_terms(self):
        wd = self.driver
        wd.get("http://walmart.com/")
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        terms = wd.find_element_by_link_text("Terms of Use")
        self.move_to_element(terms)
        terms.click()
        wd.find_element_by_link_text("Introduction").click()
        spin_assert('no acceptance',
                    lambda: "you accept this Agreement" in wd.find_element_by_tag_name("html").text)

    def tearDown(self):
        print("Link to your job: https://saucelabs.com/jobs/%s" % self.driver.session_id)
        try:
            if sys.exc_info() == (None, None, None):
                sauce.jobs.update_job(self.driver.session_id, passed=True)
            else:
                sauce.jobs.update_job(self.driver.session_id, passed=False)
        finally:
            self.driver.quit()
