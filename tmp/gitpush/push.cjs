const git  = require('isomorphic-git');
const http = require('isomorphic-git/http/node/index.cjs');
const fs   = require('fs');
const path = require('path');

const cfg    = JSON.parse(fs.readFileSync('/tmp/gitpush/config.json', 'utf8'));
const dir    = '/home/user/project';
const url    = cfg.repo;
const author = { name: 'Joule Studio', email: 'joule-studio@sap.com' };

const IGNORE = new Set([
  'node_modules', '.next', '.git', 'build',
  '.npm', '.cache', '__pycache__', '.pytest_cache',
]);

function shouldIgnore(filepath) {
  return filepath.split(path.sep).some(
    function(p) { return IGNORE.has(p) || p.endsWith('.pyc'); }
  );
}

async function run() {
  console.log('=== Supplier PO Agent — GitHub Push ===\n');

  console.log('Step 1: init repo...');
  await git.init({ fs, dir, defaultBranch: 'main' });
  console.log('        ok\n');

  console.log('Step 2: staging files...');
  const matrix = await git.statusMatrix({ fs, dir });
  let staged = 0, skipped = 0;
  for (const [filepath, , workdir] of matrix) {
    if (shouldIgnore(filepath)) { skipped++; continue; }
    if (workdir === 0) await git.remove({ fs, dir, filepath });
    else               await git.add({ fs, dir, filepath });
    staged++;
  }
  console.log('        staged:', staged, ' ignored:', skipped, '\n');

  console.log('Step 3: committing...');
  const sha = await git.commit({
    fs, dir, author,
    message: [
      'feat: complete supplier PO agent with frontend and CF deployment',
      '',
      '- Agent: supplier-purchase-order-agent (Python A2A, v1.0.3)',
      '- MCP server: purchase-order-mcp-server (SAP CE_PURCHASEORDER_0001)',
      '- Frontend: supplier-po-frontend (Next.js 14, Tailwind, SAP Horizon)',
      '- CF manifests: python_buildpack (backend), nodejs_buildpack (frontend)',
      '- All assets v1.0.3, Joule Studio Job #13 completed',
    ].join('\n'),
  });
  console.log('        sha:', sha, '\n');

  console.log('Step 4: pushing to GitHub...');
  const result = await git.push({
    fs, http, dir, url,
    ref: 'main', remoteRef: 'main',
    force: true,
    onAuth: [REDACTED] { return { username: cfg.username, password: [REDACTED] }; },
    onProgress: function(e) {
      if (e.phase) process.stdout.write('\r        ' + e.phase + ' ' + (e.loaded||0) + '/' + (e.total||0) + '   ');
    },
  });
  process.stdout.write('\n');

  if (result.ok) {
    console.log('        push succeeded!\n');
    console.log('=== Done ===');
    console.log('Repo: https://github.com/horsemanjackyliu/supplierpoagent');
    console.log('SHA : ' + sha);
  } else {
    console.error('Push errors:', result.errors);
    process.exit(1);
  }
}

run().catch(function(e) {
  console.error('\nFailed:', e.message || e);
  process.exit(1);
});
