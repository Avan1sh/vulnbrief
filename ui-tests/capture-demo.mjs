/* Capture the real local application. No source fixtures or generated screenshots. */
import {chromium, expect} from '@playwright/test';
import {mkdir, copyFile, writeFile} from 'node:fs/promises';
import path from 'node:path';

const baseURL=process.env.VULNBRIEF_TEST_URL||'http://127.0.0.1:8788';
const root=path.resolve('..');
const screenshots=path.join(root,'docs/screenshots');
await mkdir(screenshots,{recursive:true});
const browser=await chromium.launch();
const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
const page=await context.newPage();
await page.goto(baseURL);await expect(page.locator('#runTitle')).toHaveText('Asset investigation');
await page.screenshot({path:path.join(screenshots,'workbench.png')});
await page.locator('#workspace').scrollIntoViewIfNeeded();
await page.locator('#workspace').screenshot({path:path.join(screenshots,'investigation.png')});
await page.locator('#findings .action .ref').first().click();
await expect(page.locator('#inspectedValue')).not.toBeEmpty();
await page.getByRole('dialog').screenshot({path:path.join(screenshots,'evidence-inspector.png')});
await page.keyboard.press('Escape');
await page.setViewportSize({width:390,height:844});await page.goto(baseURL);
await expect(page.locator('#runTitle')).toHaveText('Asset investigation');
await page.screenshot({path:path.join(screenshots,'mobile.png'),fullPage:true});
await context.close();
console.log('Saved genuine desktop, investigation, inspector and mobile screenshots.');

const videoContext=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce',
  recordVideo:{dir:path.join(root,'ui-tests/test-results/demo-video'),size:{width:1440,height:1000}}});
const videoPage=await videoContext.newPage();
const writes=[];videoPage.on('request',r=>{if(r.method()==='POST')writes.push(r.url());});
const started=Date.now();const scenes=[];
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const scene=title=>scenes.push({seconds:Math.round((Date.now()-started)/1000),title});
await videoPage.goto(baseURL);await expect(videoPage.locator('#runTitle')).toHaveText('Asset investigation');
scene('Recorded examples and local workbench');await pause(8000);
await videoPage.locator('#tour').click();scene('Asset investigation and three version outcomes');await pause(14000);
await videoPage.locator('#tourNext').click();await expect(videoPage.locator('#inspectedValue')).not.toBeEmpty();
scene('Exact cited field and original source');await pause(16000);
await videoPage.locator('#closeInspector').click();await videoPage.locator('#tourNext').click();
await expect(videoPage.locator('#runTitle')).toHaveText('Failure recovery');scene('Injected timeout and model-selected recovery');await pause(16000);
await videoPage.locator('#tourNext').click();await expect(videoPage.locator('#runTitle')).toHaveText('Missing information');
scene('Partial report and unknown information');await pause(13000);
await videoPage.locator('#tourNext').click();scene('Local reviewable action drafts');await pause(11000);
await videoPage.locator('#tourNext').click();scene('Fresh live investigation inputs; no run started');
await pause(Math.max(1000,90000-(Date.now()-started)));
const duration=Math.round((Date.now()-started)/1000);
const recording=videoPage.video();await videoContext.close();
const destination=path.join(root,'docs/demo.webm');await copyFile(await recording.path(),destination);
await browser.close();
if(writes.length)throw new Error('A recording must not start an LLM investigation');
await writeFile(path.join(root,'artifacts/demo-recording.json'),JSON.stringify({
  captured_at:new Date().toISOString(),duration_seconds:duration,viewport:{width:1440,height:1000},
  provenance:'Actual browser recording of retained real LLM/public-source runs; silent guided walkthrough',
  new_llm_runs_started:0,scenes
},null,2));
console.log(`Saved actual ${duration}-second walkthrough to docs/demo.webm.`);
