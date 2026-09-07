import { readFileSync, writeFileSync, mkdirSync, realpathSync, statSync, lstatSync, existsSync, readdirSync, renameSync, unlinkSync } from 'node:fs';
import { resolve, relative, isAbsolute, dirname, join } from 'node:path';
import { createHash, randomUUID } from 'node:crypto';
import { createServer } from 'node:http';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';
import { Marked } from 'marked';

const templateRoot = fileURLToPath(new URL('../templates/report/', import.meta.url));
const MAX_DOCUMENT = 2 * 1024 * 1024;
const MAX_BUNDLE = 20 * 1024 * 1024;
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const hash = value => createHash('sha256').update(value).digest('hex');
function inside(root, path) {
  const rel = relative(root, path);
  return rel !== '..' && !rel.startsWith('..' + '/') && !rel.startsWith('..' + '\\') && !isAbsolute(rel);
}
function text(value, name) {
  if (typeof value !== 'string' || !value.trim() || value.length > 250) throw new Error(`${name} must be a nonempty string of at most 250 characters`);
  return value;
}
function slug(value, name) {
  if (typeof value !== 'string' || !/^[a-z0-9][a-z0-9-]{0,79}$/.test(value)) throw new Error(`${name} must use lowercase letters, numbers and hyphens`);
  return value;
}
function readBounded(path, limit) {
  if (!statSync(path).isFile() || statSync(path).size > limit) throw new Error(`File is not regular or exceeds size limit: ${path}`);
  return readFileSync(path, 'utf8');
}
function ownedDirectory(root, parts) {
  let path = root;
  for (const part of parts) {
    path = join(path, part);
    if (existsSync(path)) {
      if (lstatSync(path).isSymbolicLink() || !lstatSync(path).isDirectory()) throw new Error(`Report directory must not be a symlink: ${path}`);
    } else mkdirSync(path);
  }
  return path;
}
function regularOutput(path) {
  if (existsSync(path) && (lstatSync(path).isSymbolicLink() || !lstatSync(path).isFile())) throw new Error(`Unsafe report output: ${path}`);
}
export function loadManifest(target, manifestPath) {
  const root = realpathSync(target);
  const source = JSON.parse(readBounded(resolve(root, manifestPath), MAX_DOCUMENT));
  const result = { schemaVersion: 1, project: text(source.project, 'project'), title: text(source.title, 'title'), reportId: slug(source.reportId, 'reportId'), version: source.version, documents: [] };
  if (source.schemaVersion !== 1 || !Number.isSafeInteger(source.version) || source.version < 1) throw new Error('schemaVersion must be 1 and version must be a positive integer');
  if (!Array.isArray(source.documents) || !source.documents.length || source.documents.length > 100) throw new Error('documents must contain between 1 and 100 entries');
  const ids = new Set(); let size = 0;
  for (const doc of source.documents) {
    const id = slug(doc.id, 'document id');
    if (ids.has(id)) throw new Error(`Duplicate document id: ${id}`);
    ids.add(id);
    text(doc.path, 'document path');
    if (isAbsolute(doc.path) || !/\.md$/i.test(doc.path)) throw new Error('Document paths must be relative Markdown paths');
    const path = realpathSync(resolve(root, doc.path));
    if (!inside(root, path)) throw new Error(`Document is outside the target project: ${doc.path}`);
    const markdown = readBounded(path, MAX_DOCUMENT);
    size += Buffer.byteLength(markdown);
    if (size > MAX_BUNDLE) throw new Error('Document bundle exceeds 20 MiB');
    result.documents.push({ id, title: text(doc.title, 'document title'), path: doc.path, markdown, sha256: hash(markdown) });
  }
  return result;
}
export function renderMarkdown(markdown) {
  let index = 0; const headings = [];
  const parser = new Marked({ gfm: true, renderer: {
    html({ text }) { return escape(text); },
    image({ text }) { return `<span>[Image: ${escape(text)}]</span>`; },
    link({ href, tokens }) {
      const label = this.parser.parseInline(tokens);
      if (!/^(https?:\/\/|mailto:|#[a-zA-Z0-9_-]+$)/i.test(href)) return label;
      return `<a href="${escape(href)}" rel="noreferrer noopener">${label}</a>`;
    },
    heading({ tokens, depth }) {
      const label = this.parser.parseInline(tokens); const id = `section-${++index}`;
      headings.push(`<li><a href="#${id}">${label}</a></li>`);
      return `<h${depth} id="${id}">${label}</h${depth}>`;
    }
  }});
  const body = parser.parse(markdown);
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><style>${readFileSync(join(templateRoot,'document.css'),'utf8')}</style></head><body><details class="contents"><summary>On this page</summary><ol>${headings.join('')}</ol></details><article>${body}</article></body></html>`;
}
export function renderReport(snapshots) {
  const payload = snapshots.map(s => ({ ...s, documents: s.documents.map(d => ({ id: d.id, title: d.title, path: d.path, html: renderMarkdown(d.markdown) })) }));
  const data = JSON.stringify(payload).replace(/</g, '\\u003c');
  const script = `const snapshots = ${data};\n${readFileSync(join(templateRoot,'reader.js'),'utf8')}`;
  const digest = createHash('sha256').update(script).digest('base64');
  return readFileSync(join(templateRoot,'reader.html'),'utf8')
    .replace('<!--STYLE-->', `<style>${readFileSync(join(templateRoot,'reader.css'),'utf8')}</style>`)
    .replace('<!--CSP-->', `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'sha256-${digest}'; style-src 'unsafe-inline'; frame-src 'self' about:; base-uri 'none'; form-action 'none'">`)
    .replace('<!--SCRIPT-->', `<script>${script}</script>`);
}
export function generateReport(target, manifestPath) {
  const root = realpathSync(target);
  const snapshot = loadManifest(root, manifestPath);
  const directory = ownedDirectory(root, ['.toscanini','reports',snapshot.reportId]);
  const versions = ownedDirectory(directory, ['versions']);
  const lock = join(directory,'.generation-lock');
  writeFileSync(lock, '', {flag:'wx'});
  let temporary;
  try {
    const versionPath = join(versions, `${snapshot.version}.json`);
    if (existsSync(versionPath)) throw new Error(`Version ${snapshot.version} already exists; choose a new version`);
    const previous = readdirSync(versions).filter(n => /^\d+\.json$/.test(n)).map(name => {
      const path = join(versions,name); regularOutput(path);
      return JSON.parse(readBounded(path, MAX_BUNDLE * 2));
    });
    if (previous.some(s => s.reportId !== snapshot.reportId || s.project !== snapshot.project)) throw new Error('Report ID belongs to a different project');
    if (previous.some(s => s.version >= snapshot.version)) throw new Error('New version must be greater than every existing version');
    const all = [...previous, snapshot].sort((a,b) => b.version-a.version);
    if (Buffer.byteLength(JSON.stringify(all)) > MAX_BUNDLE * 2) throw new Error('Report history exceeds 40 MiB');
    const html = renderReport(all);
    const indexPath = join(directory,'index.html'); regularOutput(indexPath);
    temporary = join(directory, `.index-${randomUUID()}.tmp`);
    writeFileSync(temporary, html, {flag:'wx'});
    writeFileSync(versionPath, JSON.stringify(snapshot,null,2)+'\n', {flag:'wx'});
    renameSync(temporary,indexPath); temporary = undefined;
    return indexPath;
  } finally {
    if (temporary && existsSync(temporary)) unlinkSync(temporary);
    unlinkSync(lock);
  }
}
export function serveReport(path, port = 0) {
  const server = createServer((req,res) => {
    if (!['GET','HEAD'].includes(req.method) || req.url?.split('?')[0] !== '/') { res.writeHead(404); res.end(); return; }
    res.writeHead(200, {'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'});
    res.end(req.method === 'HEAD' ? undefined : readFileSync(path));
  });
  server.listen(port,'127.0.0.1');
  return server;
}
export async function reportCommand(args) {
  const {values} = parseArgs({args, options:{manifest:{type:'string'},target:{type:'string',default:'.'},serve:{type:'boolean',default:false},port:{type:'string',default:'0'},help:{type:'boolean',default:false}},strict:true});
  if (values.help) { console.log('toscanini report --manifest PATH [--target PATH] [--serve] [--port PORT]'); return; }
  if (!values.manifest) throw new Error('report requires --manifest PATH');
  const port = Number(values.port);
  if (!Number.isInteger(port) || port<0 || port>65535) throw new Error('port must be between 0 and 65535');
  const path = generateReport(values.target,values.manifest);
  console.log(`Report: ${path}`);
  if (values.serve) {
    const server = serveReport(path,port);
    await new Promise((resolve,reject)=>{server.once('listening',resolve);server.once('error',reject)});
    console.log(`Read report: http://127.0.0.1:${server.address().port}/`);
  }
}
