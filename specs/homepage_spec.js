// spec.js
describe('AngularJS/Protractor Demo App Homepage', function() {

  it('should verify title', function() {
    browser.get('http://walmart.com/');

    var search = element(by.css('#search .js-searchbar-input'));
    search.click();
    search.sendKeys("Sennheiser HD 800");

    var submit = element(by.css('.searchbar-submit'));
    submit.click();
  });

});