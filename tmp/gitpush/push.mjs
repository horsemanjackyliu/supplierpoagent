import git from 'isomorphic-git';
import http from 'isomorphic-git/http/node/index.cjs';
import fs from 'node:fs';
import path from 'node:path';

const dir = '/home/user/project';
const url = 'https://github.com/horsemanjackyliu/supplierpoagent.git';
const TOKEN = [REDACTED] author = { name: 'Joule Studio', email: 'joule-studio@sap.com' };

const IGNORE = new Set([
  'node_modules', '.next', '.git', 'build', '.npm', '.cache',
  '__pycache__', '.pytest_cache',
]);

function shouldIgnore(filepath) {
  return filepath.split(path.sep).some(p => IGNORE.has(p) || p.endsWith('.pyc'));
}

async function run() {
  console.log('=== Supplier PO Agent — GitHub Push ===\n');

  // 1. Init
  console.log('1. Initialising git repository...');
  await git.init({ fs, dir, defaultBranch: 'main' });
  console.log('   done');

  // 2. Stage
  console.log('\n2. Staging files...');
  const statusMatrix = await git.statusMatrix({ fs, dir });
  let staged = 0, skipped = 0;
  for (const [filepath, , workdir] of statusMatrix) {
    if (shouldIgnore(filepath)) { skipped++; continue; }
    if (workdir === 0) await git.remove({ fs, dir, filepath });
    else await git.add({ fs, dir, filepath });
    staged++;
  }
  console.log(`   ${staged} files staged, ${skipped} ignored`);

  // 3. Commit
  console.log('\n3. Creating commit...');
  const sha = await git.commit({
    fs, dir, author,
    message: [
      'feat: complete supplier PO agent with frontend and CF deployment',
      '',
      '- Agent: supplier-purchase-order-agent (Python A2A, v1.0.3)',
      '- MCP server: purchase-order-mcp-server (SAP CE_PURCHASEORDER_0001)',
      '- Frontend: supplier-po-frontend (Next.js 14, Tailwind, SAP Horizon)',
      '- CF manifests: python_buildpack (backend), nodejs_buildpack (frontend)',
      '- All assets v1.0.3, deployed to Joule Studio runtime (Job #13)',
    ].join('\n'),
  });
  console.log(`   commit: ${sha}`);

  // 4. Push
  console.log('\n4. Pushing to GitHub...');
  const tryPush = async (force) => git.push({
    fs, http, dir, url,
    ref: 'main', remoteRef: 'main', force,
    onAuth: () => ({ username: 'horsemanjackyliu', password: TOKEN }),
    onProgress: e => e.phase && process.stdout.write(`\r   ${e.phase} ${e.loaded ?? ''}/${e.total ?? ''}   `),
  });

  let result = await tryPush(false).catch(async err => {
    if (err.message?.includes('non-fast-forward') || err.message?.includes('rejected')) {
      console.log('\n   Remote has diverged — force-pushing...');
      return tryPush(true);
    }
    throw err;
  });

  process.stdout.write('\n');
  if (!result.ok) { console.error('   errors:', result.errors); process.exit(1); }
  console.log('   push ok');

  console.log('\n=== Done ===');
  console.log('URL  : https://github.com/horsemanjackyliu/supplierpoagent');
  console.log('SHA  :', sha);
}

run().catch(e => { console.error('\nFailed:', e.message ?? e); process.exit(1); });
