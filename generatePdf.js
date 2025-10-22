const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:8000/redoc/', {waitUntil: 'networkidle0'});
  await page.pdf({path: 'api-docs.pdf', format: 'A4'});
  await browser.close();
})();
