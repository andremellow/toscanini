import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, symlinkSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import { once } from 'node:events';
import { generateReport, renderMarkdown, serveReport } from '../scripts/report.mjs';
function fixture(t) {
  const root=mkdtempSync(join(tmpdir(),'tos-report-'));
  t.after(()=>rmSync(root,{recursive:true,force:true}));
  mkdirSync(join(root,'specs'));
  writeFileSync(join(root,'specs/spec.md'),'# Copy course\n\nPreserve title, description and modules.\n\n| Field | Copy |\n| --- | --- |\n| Title | Yes |\n\n- [ ] Test pending\n');
  writeFileSync(join(root,'specs/tests.md'),'# Test plan\n\nVerify each copied field.');
  const manifest={schemaVersion:1,reportId:'copy-course',project:'Learning',title:'Copy course',version:1,documents:[{id:'spec',title:'Specification',path:'specs/spec.md'},{id:'tests',title:'Test plan',path:'specs/tests.md'}]};
  const save=()=>writeFileSync(join(root,'report.json'),JSON.stringify(manifest));save();
  return {root,manifest,save};
}
test('CLI generates a self-contained report with arbitrary documents and packaged templates',t=>{
  const {root}=fixture(t);
  const output=execFileSync(process.execPath,[resolve('scripts/toscanini.mjs'),'report','--target',root,'--manifest','report.json'],{encoding:'utf8'});
  assert.match(output,/Report:/);
  const html=readFileSync(join(root,'.toscanini/reports/copy-course/index.html'),'utf8');
  assert.match(html,/sandbox=""/);assert.match(html,/sha256-/);
  assert.match(html,/Preserve title/);assert.match(html,/Verify each copied field/);
  assert.doesNotMatch(html,/<script[^>]+src=/);
});
test('versions snapshot source contents, preserve ordering and reject overwrite',t=>{
  const {root,manifest,save}=fixture(t);const path=generateReport(root,'report.json');
  const first=readFileSync(join(root,'.toscanini/reports/copy-course/versions/1.json'),'utf8');
  writeFileSync(join(root,'specs/spec.md'),'# Revised copy\n\nAlso preserve materials.');
  manifest.version=2;manifest.documents.reverse();save();generateReport(root,'report.json');
  assert.equal(readFileSync(join(root,'.toscanini/reports/copy-course/versions/1.json'),'utf8'),first);
  const html=readFileSync(path,'utf8');assert.match(html,/Preserve title/);assert.match(html,/preserve materials/);
  assert.equal(JSON.parse(readFileSync(join(root,'.toscanini/reports/copy-course/versions/2.json'))).documents[0].id,'tests');
  assert.throws(()=>generateReport(root,'report.json'),/already exists/);
  assert.equal(readFileSync(path,'utf8'),html);
});
test('invalid input does not write a partial version',t=>{
  const {root,manifest,save}=fixture(t);
  manifest.documents.push({id:'missing',title:'Missing',path:'specs/missing.md'});save();
  assert.throws(()=>generateReport(root,'report.json'),/ENOENT/);
  assert.equal(existsSync(join(root,'.toscanini/reports/copy-course')),false);
  manifest.documents.pop();manifest.documents[1].id='spec';save();
  assert.throws(()=>generateReport(root,'report.json'),/Duplicate/);
});
test('rejects traversal, input symlinks outside the project and output symlinks',t=>{
  const {root,manifest,save}=fixture(t);
  const external=mkdtempSync(join(tmpdir(),'tos-outside-'));t.after(()=>rmSync(external,{recursive:true,force:true}));
  writeFileSync(join(external,'secret.md'),'private');
  symlinkSync(join(external,'secret.md'),join(root,'specs/link.md'));
  manifest.documents[0].path='specs/link.md';save();assert.throws(()=>generateReport(root,'report.json'),/outside/);
  manifest.documents[0].path='specs/spec.md';manifest.reportId='../escape';save();assert.throws(()=>generateReport(root,'report.json'),/reportId/);
  manifest.reportId='copy-course';save();symlinkSync(external,join(root,'.toscanini'));assert.throws(()=>generateReport(root,'report.json'),/symlink/);
});
test('Markdown supports tables and code but disables raw HTML, scripts, images and unsafe links',()=>{
  const html=renderMarkdown('# Heading\n\n<script>alert(1)</script>\n\n[bad](javascript:alert(1))\n\n![tracking](https://example.com/pixel)\n\n| A | B |\n| --- | --- |\n| X | Y |\n\n```js\nconst x = 1;\n```');
  assert.match(html,/<table>/);assert.match(html,/<pre><code/);assert.match(html,/id="heading"/);
  assert.doesNotMatch(html,/<script|<img|href="javascript:/);assert.match(html,/&lt;script&gt;/);
});
test('server exposes only the generated HTML on loopback',async t=>{
  const {root}=fixture(t);const server=serveReport(generateReport(root,'report.json'));
  await once(server,'listening');t.after(()=>{server.closeAllConnections();server.close()});
  assert.equal(server.address().address,'127.0.0.1');const url=`http://127.0.0.1:${server.address().port}`;
  const response=await fetch(url);assert.equal(response.status,200);assert.match(await response.text(),/Specification/);
  assert.equal((await fetch(url+'/report.json')).status,404);
  assert.equal((await fetch(url,{method:'POST'})).status,404);
});

test('Markdown fragment links target stable headings, including duplicates and Unicode',()=>{
  const markdown = '[Scenarios](#scenarios) / [Again](#scenarios-1) / [Ações](#ações) / [Encoded](#a%C3%A7%C3%B5es)\n\n## Scenarios\n\n## Scenarios\n\n## Ações\n\n## **Copy** `course`\n';
  const html=renderMarkdown(markdown);
  for (const id of ['scenarios','scenarios-1','ações','copy-course']) {
    assert.ok(html.includes(`id="${id}"`));
    assert.ok(html.includes(`href="about:srcdoc#${id}"`));
  }
  assert.ok(html.includes('href="about:srcdoc#a%C3%A7%C3%B5es"'));
  const withEarlierHeading=renderMarkdown('# Introduction\n\n'+markdown);
  assert.ok(withEarlierHeading.includes('id="scenarios"'));
  assert.ok(renderMarkdown('## Scenarios').includes('id="scenarios"'));
});
