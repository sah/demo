import os
import unittest
import sys
from appium import webdriver
from sauceclient import SauceClient

USERNAME = os.environ.get('SAUCE_USERNAME')
ACCESS_KEY = os.environ.get('SAUCE_ACCESS_KEY')

sauce = SauceClient(USERNAME, ACCESS_KEY)

BUILD = os.environ.get('JOB_NAME') + ' #' + os.environ.get('BUILD_NUMBER')


class Selenium2OnSauce(unittest.TestCase):

    def setUp(self):
        desired_capabilities = {}
        desired_capabilities['build'] = BUILD
        desired_capabilities['name'] = 'Contact Manager Native Application Test on REAL S5'
        desired_capabilities['deviceName'] = "Samsung Galaxy S5 Device"
        #desired_capabilities['name'] = 'Contact Manager Native Application Test on REAL S4'
        #desired_capabilities['deviceName'] = "Samsung Galaxy S4 Device"
        #desired_capabilities['name'] = 'Contact Manager Native Application Test on FAKE S4'
        #desired_capabilities['deviceName'] = 'Samsung Galaxy S4 Emulator'
        desired_capabilities['appium-version'] = "1.4"
        desired_capabilities['platformName'] = "Android"
        desired_capabilities['platformVersion'] = "4.4"
        desired_capabilities['device-orientation'] = "portrait"

        desired_capabilities['app'] = 'http://saucelabs.com/example_files/ContactManager.apk'
        desired_capabilities["app-activity"] = ".ContactManager"
        desired_capabilities["app-package"] = "com.example.android.contactmanager"

        print desired_capabilities

        self.driver = webdriver.Remote(
            desired_capabilities=desired_capabilities,
            command_executor="http://%s:%s@ondemand.saucelabs.com/wd/hub" % (USERNAME, ACCESS_KEY)
        )
        print "driver init", self.driver.session_id
        self.driver.implicitly_wait(30)
        print "implicitly_wait"

    def test_app(self):
        self.driver.find_element_by_name('Add Contact').click()
        print "clicked Add Contact"
        for i in xrange(2):
            fields = self.driver.find_elements_by_class_name('android.widget.EditText')
            print fields
            fields[0].send_keys('My Name %s' % i)
            print "typed in name field"
            fields[2].send_keys('someone%s@somewhere.com' % i)
            print "typed in email field"
            fields = self.driver.find_elements_by_class_name('android.widget.EditText')
            self.assertTrue(('My Name %s' % i) in fields[0].text)

    def tearDown(self):
        print("Link to your job: https://saucelabs.com/jobs/%s" % self.driver.session_id)
        try:
            if sys.exc_info() == (None, None, None):
                sauce.jobs.update_job(self.driver.session_id, passed=True)
            else:
                sauce.jobs.update_job(self.driver.session_id, passed=False)
        finally:
            self.driver.quit()

if __name__ == '__main__':
    unittest.main()
