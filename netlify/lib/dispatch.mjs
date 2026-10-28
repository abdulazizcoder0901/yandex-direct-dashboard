// GitHub'dagi "Ma'lumotni yangilash" (update.yml) workflow'ini ishga tushiradi: u Yandex'dan ma'lumot olib,
// "data" branchiga yozadi. Token Netlify'ning muhit o'zgaruvchisida: GH_ACTIONS_TOKEN
// (GitHub fine-grained token, faqat shu repo, Actions: Read and write).
const REPO = 'abdulazizcoder0901/yandex-direct-dashboard';
const WORKFLOW = 'update.yml';

export async function dispatch(source) {
  const token = process.env.GH_ACTIONS_TOKEN;
  if (!token) return { ok: false, reason: 'GH_ACTIONS_TOKEN berilmagan' };
  const headers = {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': 'yandex-direct-dashboard'
  };
  const base = `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}`;
  // Ishlab turgan yoki hozirgina boshlangan bo'lsa, yangisini boshlamaymiz (tugma ketma-ket bosilsa ham bitta so'rov)
  const runs = await fetch(`${base}/runs?per_page=1`, { headers }).then(r => (r.ok ? r.json() : null)).catch(() => null);
  const last = runs && runs.workflow_runs && runs.workflow_runs[0];
  if (last && last.status !== 'completed') return { ok: true, started: false, running: true, run: last.id };
  if (last && Date.now() - Date.parse(last.created_at) < 60 * 1000) return { ok: true, started: false, recent: true, run: last.id };
  const r = await fetch(`${base}/dispatches`, { method: 'POST', headers, body: JSON.stringify({ ref: 'main' }) });
  if (r.status === 204) return { ok: true, started: true, source };
  return { ok: false, reason: `GitHub javobi ${r.status}` };
}
