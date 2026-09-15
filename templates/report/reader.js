const byId = id => document.getElementById(id);
const versions = byId('version');
for (const snapshot of snapshots) {
  const option = document.createElement('option');
  option.value = String(snapshot.version);
  option.textContent = `v${snapshot.version}${snapshot === snapshots[0] ? ' · Latest' : ''}`;
  versions.append(option);
}
function render() {
  const params = new URLSearchParams(location.hash.slice(1));
  const snapshot = snapshots.find(s=>String(s.version)===params.get('version')) || snapshots[0];
  const selected = snapshot.documents.find(d=>d.id===params.get('document')) || snapshot.documents[0];
  versions.value = String(snapshot.version);
  byId('project').textContent = snapshot.project;
  byId('feature').textContent = snapshot.title;
  byId('title').textContent = selected.title;
  byId('path').textContent = selected.path;
  byId('version-label').textContent = `Version ${snapshot.version}`;
  document.title = `${selected.title} · Toscanini`;
  byId('documents').replaceChildren();
  for (const doc of snapshot.documents) {
    const button = document.createElement('button');
    button.textContent = doc.title;
    button.setAttribute('aria-pressed',String(doc.id===selected.id));
    button.onclick = ()=>{location.hash = new URLSearchParams({version:snapshot.version,document:doc.id}).toString()};
    byId('documents').append(button);
  }
  byId('document').srcdoc = selected.html;
}
versions.onchange = ()=>{const params=new URLSearchParams(location.hash.slice(1));params.set('version',versions.value);location.hash=params.toString()};
window.addEventListener('hashchange',render);
render();
