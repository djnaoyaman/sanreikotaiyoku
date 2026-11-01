const { chromium } = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
(async () => {
 const browser = await chromium.launch();
 fs.mkdirSync('test-artifacts/profile', { recursive: true });
 const results = [];
 try {
  for (const width of [320,390,1280]) {
   const page = await browser.newPage({viewport:{width,height:900}});
   await page.route('**/*', route => {
    const u = new URL(route.request().url());
    return u.hostname === '127.0.0.1' ? route.continue() : route.abort();
   });
   const errors=[]; page.on('pageerror', e=>errors.push(e.message));
   await page.goto('http://127.0.0.1:8765/#about', {waitUntil:'networkidle'});
   const ripple=page.locator('a[href="https://djnaoyaman.github.io/1minutes/sensory.html#ripple"]');
   assert.equal(await ripple.count(),1,'one contextual RIPPLE link');
   await ripple.scrollIntoViewIfNeeded();
   assert.ok(await ripple.isVisible(),'RIPPLE link visible');
   assert.match(await ripple.locator('..').innerText(),/入浴中ではなく、水辺を離れた場所/);
   await ripple.focus();
   assert.ok(await ripple.evaluate(el=>el===document.activeElement),'RIPPLE link keyboard focus');
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,'about no overflow');
   await page.screenshot({path:`test-artifacts/profile/ripple-${width}.png`});
   const indexAuthor=page.locator('footer a[href="profile.html"]');
   assert.match(await indexAuthor.innerText(),/作者・湯気文吾について/);
   for (const route of ['guide.html','quiz.html']) {
    await page.goto('http://127.0.0.1:8765/'+route, {waitUntil:'networkidle'});
    const author=page.locator('header a[href="profile.html"]');
    assert.equal(await author.innerText(),'作者について');
    assert.ok(await author.isVisible(),'author navigation visible');
    await author.focus();
    assert.ok(await author.evaluate(el=>el===document.activeElement),'author keyboard focus');
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,route+' no overflow');
    await page.screenshot({path:`test-artifacts/profile/${route}-${width}.png`});
   }
   await page.goto('http://127.0.0.1:8765/profile.html', {waitUntil:'networkidle'});
   await page.evaluate(async()=>{
    for(let y=0;y<document.body.scrollHeight;y+=500){scrollTo(0,y);await new Promise(r=>setTimeout(r,50));}
    scrollTo(0,0);
   });
   await page.waitForTimeout(800);
   const link=page.locator('a[href="https://djnaoyaman.github.io/profile.html"]');
   assert.ok(await link.count() >= 1,'central author link');
   await link.first().scrollIntoViewIfNeeded(); assert.ok(await link.first().isVisible(),'author link visible');
   const stamp=page.locator('footer time');
   assert.equal(await stamp.count(),1,'one visible footer date');
   assert.equal(await stamp.getAttribute('datetime'),'2026-10-31');
   assert.match(await stamp.innerText(),/2026\.10\.31/);
   const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
   const row={width,overflow,errors};results.push(row);
   await page.screenshot({path:`test-artifacts/profile/profile-${width}.png`,fullPage:true});
   assert.equal(overflow,false,'no horizontal overflow');
   assert.deepEqual(errors,[],'no JavaScript exceptions');
   await page.close();
  }
 } finally {
  fs.writeFileSync('test-artifacts/profile/results.json',JSON.stringify(results,null,2));
  await browser.close();
 }
})().catch(e=>{console.error(e);process.exit(1);});
