import {test, expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.beforeEach(async({page})=>{
  await page.goto('/');
  await expect(page.locator('#runTitle')).toHaveText('Asset investigation');
});

test('reviewer examples open actual retained outcomes without starting a run',async({page})=>{
  const writes=[];page.on('request',r=>{if(r.method()==='POST')writes.push(r.url());});
  await expect(page.locator('[data-demo]')).toHaveCount(3);
  await page.locator('[data-demo="v02-partial-final"]').click();
  await expect(page.locator('#statStatus')).toHaveText('partial');
  await expect(page.locator('#findings')).toContainText('CVE-2099-9999999');
  await page.locator('[data-demo="v02-recovery-final"]').click();
  await expect(page.locator('#timeline')).toBeVisible();
  await expect(page.locator('.error-event')).toContainText('deliberately injected');
  expect(writes).toEqual([]);
});

test('citation inspector shows the selected claim and exact supporting source value',async({page})=>{
  await page.locator('#findings .action .ref').first().click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.locator('.claim-context')).toContainText('Selected claim');
  await expect(page.locator('#inspectedValue')).not.toBeEmpty();
  await expect(page.locator('.evidence-meta')).toContainText('Retrieved at');
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(page.locator('#findings .action .ref').first()).toBeFocused();
});

test('tabs support arrow keys and history retains failed attempts',async({page})=>{
  await page.locator('#tab-findings').focus();await page.keyboard.press('ArrowRight');
  await expect(page.locator('#tab-evidence')).toHaveAttribute('aria-selected','true');
  await expect(page.locator('#evidence')).toBeVisible();
  await page.locator('#historyFilter').selectOption('failed');
  await expect(page.locator('#runList .run-item').first()).toBeVisible();
  const labels=await page.locator('#runList .badge').allTextContents();
  expect(labels.every(v=>['failed','interrupted'].includes(v))).toBeTruthy();
});

test('guided tour visits evidence, recovery and missing information without LLM calls',async({page})=>{
  const writes=[];page.on('request',r=>{if(r.method()==='POST')writes.push(r.url());});
  await page.locator('#tour').click();
  await expect(page.locator('#tourStep')).toContainText('1 / 6');
  await page.locator('#tourNext').click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.locator('#closeInspector').click();
  await page.locator('#tourNext').click();
  await expect(page.locator('#runTitle')).toHaveText('Failure recovery');
  await page.locator('#tourNext').click();
  await expect(page.locator('#runTitle')).toHaveText('Missing information');
  await page.locator('#closeTour').click();
  expect(writes).toEqual([]);
});

for(const width of [1440,768,390]){
  test(`layout and accessibility at ${width}px`,async({page})=>{
    await page.setViewportSize({width,height:1000});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
    const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
    expect(result.violations.map(v=>({id:v.id,description:v.description,nodes:v.nodes.map(n=>n.target)}))).toEqual([]);
  });
}

test('inspector is accessible and fits a phone viewport',async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await page.locator('#findings .action .ref').first().click();
  const box=await page.getByRole('dialog').boundingBox();expect(box.x).toBeGreaterThanOrEqual(0);expect(box.x+box.width).toBeLessThanOrEqual(390);
  const result=await new AxeBuilder({page}).include('#evidenceDialog').withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  expect(result.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))).toEqual([]);
});

test('failed KEV retrieval shows Unknown in the summary',async({page})=>{
  await page.route('**/api/runs/v02-reviewed',async route=>{
    const response=await route.fetch();const data=await response.json();
    data.report.evidence=data.report.evidence.filter(e=>e.tool!=='lookup_kev');
    await route.fulfill({json:data});
  });
  await page.reload();await expect(page.locator('#statKev')).toHaveText('Unknown');
});
