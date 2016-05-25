// spec.js
describe('AngularJS/Protractor Demo App Homepage', function() {

  it('should verify title', function() {
    browser.get('http://walmart.com/');

    var title = element(by.css('body h1'));

    expect(title.getText()).toEqual('Title');
  });

});