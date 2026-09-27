const E = require('../engine.js'); const crypto = require('crypto');
const cases = require('./cases.json'); let bad = 0;
for (const c of cases) {
  const h = crypto.createHash('sha256').update(E.gatesCanonical(c.gates), 'utf8').digest('hex');
  const errs = [];
  if (h !== c.hash) errs.push('hash');
  let got;
  try {
    const r = E.applyGates(c.rows, c.gates); const f = E.funnel(r.entries, r.episodes, c.gates); const ep = c.gates.episode_column;
    got = { episodes: Object.fromEntries(r.episodes.map((e) => [e[ep], [e.final_status, e.level || '']])),
      problems: r.problems.map((p) => `${p.level}|${p.where}|${p.problem}`).sort(), funnel: f.map((x) => `${x.kind}|${x.count}|${x.n}`).sort() };
  } catch (e) { if (e instanceof E.StopError) got = { stop: e.message }; else throw e; }
  const X = c.expect;
  if (X.stop || got.stop) { if (!(X.stop && got.stop)) errs.push('stop mismatch ' + (X.stop || got.stop)); }
  else {
    if (JSON.stringify(Object.entries(X.episodes).sort()) !== JSON.stringify(Object.entries(got.episodes).sort())) errs.push('episodes');
    const pyP = X.problems.slice().sort(), jsP = got.problems.slice().sort();
    if (JSON.stringify(pyP) !== JSON.stringify(jsP)) { errs.push('problems'); console.log(pyP.filter(x=>!jsP.includes(x)).slice(0,3), jsP.filter(x=>!pyP.includes(x)).slice(0,3)); }
    const pyF = X.funnel.map(s=>s.replace(/\|(\d+)\.0$/,'|$1')).sort(), jsF = got.funnel.sort();
    if (JSON.stringify(pyF) !== JSON.stringify(jsF)) { errs.push('funnel'); console.log(pyF.filter(x=>!jsF.includes(x)), jsF.filter(x=>!pyF.includes(x))); }
  }
  if (errs.length) bad++;
  console.log((errs.length ? 'DIFF ' : 'OK   ') + c.name + (errs.length ? ' ' + errs.join(',') : ''));
}
console.log(bad ? `${bad} case(s) differ` : 'ALL CASES IDENTICAL');
