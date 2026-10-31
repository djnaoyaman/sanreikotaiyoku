const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'test-artifacts/launch-metadata');
fs.mkdirSync(output, { recursive: true });
(async () => {
  const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
  const results = [];
  for (const width of [320, 390, 1280]) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, javaScriptEnabled: false });
    await context.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.origin !== 'http://127.0.0.1:8765' || !url.pathname.startsWith('/sanreikotaiyoku/')) return route.abort();
      let relative = decodeURIComponent(url.pathname.slice('/sanreikotaiyoku/'.length));
      if (!relative || relative.endsWith('/')) relative += 'index.html';
      const file = path.resolve(root, relative);
      if (!file.startsWith(root + path.sep)) return route.abort();
      const exists = fs.existsSync(file) && fs.statSync(file).isFile();
      const target = exists ? file : path.join(root, '404.html');
      const type = target.endsWith('.svg') ? 'image/svg+xml' : target.endsWith('.css') ? 'text/css' : 'text/html';
      await route.fulfill({ status: exists ? 200 : 404, contentType: type, body: fs.readFileSync(target) });
    });
    const page = await context.newPage();
    const response = await page.goto('http://127.0.0.1:8765/sanreikotaiyoku/missing/nested/page');
    assert.equal(response.status(), 404);
    assert.equal(await page.title(), 'ページが見つかりません — 酸冷交代浴');
    assert.equal(await page.locator('h1').textContent(), 'ページが見つかりません。');
    assert(await page.locator('.brand img').evaluate(img => img.complete && img.naturalWidth > 0));
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.keyboard.press('Tab');
    assert.equal(await page.locator(':focus').getAttribute('aria-label'), '酸冷交代浴 トップページ');
    await page.keyboard.press('Tab');
    assert.equal(await page.locator(':focus').textContent(), 'トップページへ戻る');
    assert.equal(await page.locator(':focus').evaluate(el => getComputedStyle(el).outlineWidth), '3px');
    await page.screenshot({ path: path.join(output, `404-${width}.png`), fullPage: true });
    await page.keyboard.press('Enter');
    assert.equal(page.url(), 'http://127.0.0.1:8765/sanreikotaiyoku/');
    await page.goBack();
    assert.equal(await page.locator('h1').textContent(), 'ページが見つかりません。');
    results.push({ width, noOverflow: true, existingLogoLoaded: true, javascriptDisabled: true, keyboardReturnAndBack: true });
    await context.close();
  }
  fs.writeFileSync(path.join(output, 'report.json'), JSON.stringify({ scope: 'local project-path 404 simulation; not live Pages HTTP verification', results }, null, 2));
  await browser.close();
  console.log('PASS: 320/390/1280px custom 404, original wordmark, no overflow, visible keyboard focus, Return and Back without JavaScript');
})().catch(error => { console.error(error); process.exit(1); });
