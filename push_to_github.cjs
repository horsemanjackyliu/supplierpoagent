const git  = require('/tmp/gitpush/node_modules/isomorphic-git');
const http = require('/tmp/gitpush/node_modules/isomorphic-git/http/node/index.cjs');
const fs   = require('fs');
const path = require('path');

const creds  = fs.readFileSync('/home/user/project/.github_token', 'utf8').trim().split('\n');
const pat    = creds[0];
const uname  = 'horsemanjackyliu';
const dir    = '/home/user/project';
const remote = 'https://github.com/horsemanjackyliu/supplierpoagent.git';
const author = { name: 'Joule Studio', email: 'joule-studio@sap.com' };

const IGNORE = new Set(['node_modules','.next','.git','build','.npm','.cache','__pycache__','.pytest_cache']);
function skip(fp) { return fp.split(path.sep).some(function(p){ return IGNORE.has(p)||p.endsWith('.pyc'); }); }
function getAuth() { return { username: uname, password: pat }; }

async function main() {
  console.log('=== GitHub Push ===  PAT len:', pat.length);
  await git.init({ fs, dir, defaultBranch: 'main' });
  console.log('1. init ok');

  const matrix = await git.statusMatrix({ fs, dir });
  let n=0, s=0;
  for (const [fp,,wd] of matrix) {
    if (skip(fp)) { s++; continue; }
    if (wd===0) await git.remove({ fs, dir, filepath: fp });
    else        await git.add({ fs, dir, filepath: fp });
    n++;
  }
  console.log('2. staged', n, 'skipped', s);

  const sha = await git.commit({
    fs, dir, author,
    message: 'feat: supplier PO agent + frontend + CF deploy v1.0.3',
  });
  console.log('3. commit', sha);

  const r = await git.push({
    fs, http, dir,
    url: remote,
    ref: 'main', remoteRef: 'main',
    force: true,
    onAuth: getAuth,
  });

  if (r.ok) {
    console.log('4. push ok\nDone => https://github.com/horsemanjackyliu/supplierpoagent\nsha:', sha);
  } else {
    console.error('push errors:', r.errors); process.exit(1);
  }
}

main().catch(function(e){ console.error('Error:', e.message||e); process.exit(1); });
