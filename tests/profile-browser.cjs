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
   assert.equal(await page.locator('footer time').getAttribute('datetime'),'2026-11-06');
   const partners=page.locator('#partners .partner-card');
   assert.equal(await partners.count(),2,'two cooperating facilities, separate from recommendations');
   assert.equal(await partners.nth(0).getAttribute('id'),'partner-kashima-suisyun','existing partner preserved');
   const himewako=page.locator('#partner-himewako');
   assert.equal(await himewako.locator('h3').innerText(),'土佐望月温泉 姫若子の湯');
   assert.match(await himewako.innerText(),/高知県高知市海老ノ丸12-2/);
   assert.equal(await himewako.getAttribute('aria-labelledby'),'partner-himewako-title');
   const official=himewako.locator('a.official-link');
   assert.equal(await official.getAttribute('href'),'https://www.himewako.jp/');
   assert.equal(await official.getAttribute('target'),'_blank');
   assert.equal(await official.getAttribute('rel'),'noopener noreferrer');
   assert.equal(await official.getAttribute('data-facility-id'),'himewako');
   assert.equal(await official.getAttribute('data-placement'),'cooperating_facility');
   await official.scrollIntoViewIfNeeded();
   assert.ok(await official.isVisible(),'new official link visible');
   await official.focus();
   assert.ok(await official.evaluate(el=>el===document.activeElement),'new official link keyboard focus');
   const firstBox=await partners.nth(0).boundingBox();
   const secondBox=await himewako.boundingBox();
   assert.ok(firstBox && secondBox && secondBox.y>=firstBox.y+firstBox.height+23,'partner cards separated');
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,'partners no horizontal overflow');
   await page.screenshot({path:`test-artifacts/profile/partners-${width}.png`});
   const indexAuthor=page.locator('footer a[href="profile.html"]');
   assert.match(await indexAuthor.innerText(),/作者・湯気文吾について/);
   for (const route of ['guide.html','quiz.html']) {
    await page.goto('http://127.0.0.1:8765/'+route, {waitUntil:'networkidle'});
    assert.equal(await page.locator('footer time').getAttribute('datetime'),'2026-11-02');
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
