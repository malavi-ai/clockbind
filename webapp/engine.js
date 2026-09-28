/* ClockBind engine — JavaScript port of phdstat `screen` (v0.3.2) apply_gates / funnel.
   Pure functions, no DOM. Parity-tested against the Python engine. */
(function (root) {
  const PASS = 'Pass', FAIL = 'Fail', HOLD = 'Hold', NA = 'n/a', CONFLICT = 'CONFLICT';

  class StopError extends Error {}

  const norm = (v) => (v === null || v === undefined || (typeof v === 'number' && isNaN(v))) ? '' : String(v).replace(/\s+/g, ' ').trim();
  const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
  const sortedSet = (arr) => [...new Set(arr)].filter((x) => x !== '').sort(cmp);
  const cf = (s) => s.toLowerCase();
  const pyList = (a) => '[' + a.map((x) => `'${x}'`).join(', ') + ']';

  const paths = (st) => (st.paths ? st.paths.map((p) => p.criteria) : [st.criteria]);
  const pathNames = (st) => (st.paths ? st.paths.map((p) => p.name) : [st.name]);
  const cols = (c) => (c.type === 'any_of' ? c.columns : [c.column]);
  const isGate = (c) => c.gate !== false;
  const vals = (g) => { const v = g.values || {}; return [v.pass || ['Y'], v.fail || ['N'], v.unknown || ['Unknown']]; };

  function criterionColumns(g, unit) {
    const out = [];
    for (const st of g.stages) {
      if (unit && (st.unit || 'episode') !== unit) continue;
      for (const crits of paths(st)) for (const c of crits) for (const col of cols(c)) if (!out.includes(col)) out.push(col);
    }
    return out;
  }

  function columnSpecs(g) {
    const [yes, no, unk] = vals(g);
    const spec = {};
    for (const st of g.stages) for (const crits of paths(st)) for (const c of crits) {
      const t = c.type || 'yn';
      let allowed;
      if (t === 'yn' || t === 'any_of') allowed = [...yes, ...no, ...unk];
      else if (t === 'in') allowed = [...new Set([...(c.scale || c.allowed), ...unk])];
      else allowed = null;
      for (const col of cols(c)) {
        if (spec[col] && spec[col][0] && allowed) spec[col] = [[...new Set([...spec[col][0], ...allowed])], c];
        else spec[col] = [allowed, c];
      }
    }
    return spec;
  }

  function criterionLabels(g) {
    const out = {};
    for (const st of g.stages) for (const crits of paths(st)) for (const c of crits) out[c.id] = c.label || c.id;
    return out;
  }

  // ---------------------------------------------------------------- hashing (matches Python json.dumps(sort_keys=True, ensure_ascii=False))
  function pyJson(v) {
    if (v === null || v === undefined) return 'null';
    if (typeof v === 'boolean') return v ? 'true' : 'false';
    if (typeof v === 'number') return Number.isInteger(v) ? String(v) : String(v);
    if (typeof v === 'string') return JSON.stringify(v).replace(/[\u007f]/g, (ch) => '\\u' + ch.charCodeAt(0).toString(16).padStart(4, '0'));
    if (Array.isArray(v)) return '[' + v.map(pyJson).join(', ') + ']';
    const keys = Object.keys(v).sort(cmp);
    return '{' + keys.map((k) => pyJson(k) + ': ' + pyJson(v[k])).join(', ') + '}';
  }
  function gatesCanonical(g) { const core = {}; for (const k of Object.keys(g)) if (k !== 'sha256') core[k] = g[k]; return pyJson(core); }

  // ---------------------------------------------------------------- cleaning
  function clean(rowsIn, g, problems) {
    const idc = g.id_column, ep = g.episode_column;
    const columns = rowsIn.length ? Object.keys(rowsIn[0]) : [];
    for (const col of [idc, ep]) if (rowsIn.length && !columns.includes(col)) throw new StopError(`Column '${col}' not found. Columns: ${columns.join(', ')}`);
    let rows = rowsIn.map((r) => { const o = {}; for (const k of Object.keys(r)) o[k] = norm(r[k]); return o; });
    rows = rows.filter((r) => (r[idc] || '') !== '');
    const seen = new Set(), dup = [];
    for (const r of rows) { const k = cf(r[idc]); if (seen.has(k) && !dup.includes(k)) dup.push(k); seen.add(k); }
    if (dup.length) throw new StopError(`Duplicate entry IDs (case-insensitive): ${dup.join(', ')}. Fix the sheet; no count is produced.`);
    const groups = new Map();
    for (const r of rows) { if (!r[ep]) continue; const k = cf(r[ep]); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(r); }
    for (const [, grp] of [...groups.entries()].sort((a, b) => cmp(a[0], b[0]))) {
      const forms = sortedSet(grp.map((r) => r[ep]));
      if (forms.length > 1) {
        problems.push({ level: 'ERROR', where: forms[0], problem: `Episode ID written in different forms ${pyList(forms)}; merged as '${forms[0]}'. Correct the sheet.` });
        for (const r of grp) r[ep] = forms[0];
      }
    }
    const spec = columnSpecs(g);
    for (const col of criterionColumns(g)) {
      if (!columns.includes(col)) {
        if (g.frozen) throw new StopError(`Frozen protocol requires column '${col}', which is missing from the data.`);
        problems.push({ level: 'ERROR', where: 'columns', problem: `Criterion column '${col}' is missing from the data (treated as Unknown; exploratory only)` });
        for (const r of rows) r[col] = '';
        continue;
      }
      const [allowed] = spec[col];
      if (allowed === null) {
        for (const r of rows) if (r[col] !== '' && isNaN(Number(r[col]))) { problems.push({ level: 'ERROR', where: r[idc], problem: `'${col}' = '${r[col]}' is not a number (treated as Unknown)` }); r[col] = ''; }
        continue;
      }
      const canon = {}; for (const a of allowed) canon[cf(a)] = a;
      for (const r of rows) {
        const v = r[col]; if (v === '') continue;
        if (canon[cf(v)] !== undefined) { r[col] = canon[cf(v)]; continue; }
        problems.push({ level: 'ERROR', where: r[idc], problem: `'${col}' = '${v}' is not an allowed value ${pyList(allowed)} (treated as Unknown)` });
        r[col] = '';
      }
    }
    return rows;
  }

  // ---------------------------------------------------------------- evaluation
  function evalCriterion(c, row, g) {
    const [yesA, noA, unkA] = vals(g); const yes = new Set(yesA), no = new Set(noA), unk = new Set(unkA);
    const t = c.type || 'yn';
    const vs = cols(c).map((col) => norm(row[col]));
    if (vs.some((v) => v === CONFLICT)) return HOLD;
    if (t === 'yn') { const v = vs[0]; return yes.has(v) ? PASS : no.has(v) ? FAIL : HOLD; }
    if (t === 'in') { const v = vs[0]; if (v === '' || unk.has(v)) return HOLD; return c.allowed.includes(v) ? PASS : FAIL; }
    if (t === 'any_of') { if (vs.some((v) => yes.has(v))) return PASS; return vs.every((v) => no.has(v)) ? FAIL : HOLD; }
    if (t === 'min') { const v = vs[0] === '' ? NaN : Number(vs[0]); return isNaN(v) ? HOLD : v >= c.value ? PASS : FAIL; }
    throw new StopError(`Unknown criterion type ${t}`);
  }

  function evalStage(stage, row, g) {
    const results = []; let best = null;
    const names = pathNames(stage), ps = paths(stage);
    ps.forEach((crits, i) => {
      const res = {}; for (const c of crits) res[c.id] = evalCriterion(c, row, g);
      const gates = crits.filter(isGate);
      const fails = gates.filter((c) => res[c.id] === FAIL).map((c) => c.id);
      const holds = gates.filter((c) => res[c.id] === HOLD).map((c) => c.id);
      const status = fails.length ? FAIL : holds.length ? HOLD : PASS;
      const out = { status, path: names[i], first_failed: fails[0] || '', first_held: holds[0] || '', failed: fails.join(';'), missing: holds.join(';'), scores: res };
      results.push(out);
      const rank = { [PASS]: 0, [HOLD]: 1, [FAIL]: 2 }[status];
      if (best === null || rank < best[0]) best = [rank, out];
    });
    const out = Object.assign({}, best[1]);
    if (results.length > 1) out.all_paths = results.map((r) => `${r.path}: ${r.status}` + (r.failed ? ` fail[${r.failed}]` : '') + (r.missing ? ` held[${r.missing}]` : '')).join(' || ');
    return out;
  }

  function stageCols(prefix, res, frame, multi) {
    frame.forEach((r, i) => {
      const x = res[i];
      r[`${prefix}_status`] = x ? x.status : NA;
      r[`${prefix}_path`] = x && x.status === PASS ? x.path : '';
      r[`${prefix}_first_failed`] = x ? x.first_failed : '';
      r[`${prefix}_first_held`] = x ? x.first_held : '';
      r[`${prefix}_failed`] = x ? x.failed : '';
      r[`${prefix}_missing`] = x ? x.missing : '';
      if (multi) r[`${prefix}_all_paths`] = x ? (x.all_paths || '') : '';
    });
  }

  function applyGates(rowsIn, g) {
    const idc = g.id_column, ep = g.episode_column;
    const problems = [];
    const rows = clean(rowsIn, g, problems);
    const entryStages = g.stages.filter((s) => (s.unit || 'episode') === 'entry');
    const epStages = g.stages.filter((s) => (s.unit || 'episode') === 'episode');

    for (const r of rows) r._state = PASS;
    for (const st of entryStages) {
      const res = rows.map((r) => (r._state === PASS ? evalStage(st, r, g) : null));
      stageCols(st.id, res, rows, !!st.paths);
      rows.forEach((r) => { const s = r[`${st.id}_status`]; if (s !== NA) r._state = s; });
    }
    for (const r of rows) if (r._state !== FAIL && r[ep] === '') problems.push({ level: 'ERROR', where: r[idc], problem: 'Entry is not excluded at Stage 0 but has no episode ID' });

    const entrySpecific = new Set();
    for (const st of entryStages) for (const crits of paths(st)) for (const c of crits) if (c.entry_specific) entrySpecific.add(c.id);
    const byEpSorted = new Map();
    for (const r of rows) { if (!r[ep]) continue; if (!byEpSorted.has(r[ep])) byEpSorted.set(r[ep], []); byEpSorted.get(r[ep]).push(r); }
    const epKeysSorted = [...byEpSorted.keys()].sort(cmp);
    for (const st of entryStages) for (const crits of paths(st)) for (const c of crits) {
      if (entrySpecific.has(c.id)) continue;
      for (const eid of epKeysSorted) {
        const vs = sortedSet(byEpSorted.get(eid).map((r) => r[c.column] || ''));
        if (vs.length > 1) problems.push({ level: 'ERROR', where: eid, problem: `Entries of this episode disagree on ${c.id} (${c.label || ''}): ${pyList(vs)}` });
      }
    }

    const epCols = criterionColumns(g, 'episode');
    const order = []; const groups = new Map();
    for (const r of rows) { if (!r[ep]) continue; if (!groups.has(r[ep])) { groups.set(r[ep], []); order.push(r[ep]); } groups.get(r[ep]).push(r); }
    const columns = rows.length ? Object.keys(rows[0]) : [];
    const extras = [...(g.carry_columns || []), ...[g.reason_column, g.claimed_status_column].filter(Boolean)];
    let eps = order.map((eid) => {
      const grp = groups.get(eid);
      const states = new Set(grp.map((r) => r._state));
      const s0 = states.has(PASS) ? PASS : states.has(HOLD) ? HOLD : FAIL;
      const usable = grp.filter((r) => r._state !== FAIL);
      const excl = grp.filter((r) => r._state === FAIL);
      const r = { [ep]: eid, S0_episode_status: s0, n_entries: grp.length,
        entries_used: usable.map((x) => x[idc]).join(';'), entries_excluded_S0: excl.map((x) => x[idc]).join(';'),
        entries_held_S0: grp.filter((x) => x._state === HOLD).map((x) => x[idc]).join(';') };
      if (g.round_column && columns.includes(g.round_column)) r.rounds = sortedSet(grp.map((x) => x[g.round_column])).join(';');
      for (const c of epCols) {
        const v = sortedSet(usable.map((x) => x[c] || ''));
        const ph = new Set(((g.values || {}).unknown || []).map(String));
        const dropped = sortedSet(excl.map((x) => x[c] || '')).filter((x) => !ph.has(x));
        if (dropped.length && !v.length && usable.length) problems.push({ level: 'ERROR', where: eid, problem: `'${c}' is coded only on entries excluded at Stage 0 (${r.entries_excluded_S0}); move it to a retained entry` });
        if (v.length > 1) problems.push({ level: 'ERROR', where: eid, problem: `Conflicting values for '${c}' across entries: ${pyList(v)} (episode held on this criterion)` });
        r[c] = v.length === 1 ? v[0] : (!v.length ? '' : CONFLICT);
      }
      for (const x of extras) if (columns.includes(x)) r[x] = sortedSet(grp.map((y) => y[x])).join(' | ');
      return r;
    });
    if (!eps.length) problems.push({ level: 'ERROR', where: 'episodes', problem: 'No episodes could be formed from the data' });

    let alive = eps.map((e) => e.S0_episode_status === PASS);
    for (const st of epStages) {
      const res = eps.map((e, i) => (alive[i] ? evalStage(st, e, g) : null));
      stageCols(st.id, res, eps, !!st.paths);
      const ids = []; for (const crits of paths(st)) for (const c of crits) if (!ids.includes(c.id)) ids.push(c.id);
      eps.forEach((e, i) => { for (const cid of ids) e[`${st.id}:${cid}`] = res[i] ? (res[i].scores[cid] || '') : ''; });
      alive = alive.map((a, i) => a && eps[i][`${st.id}_status`] === PASS);
    }

    const levels = g.levels;
    const final = (r) => {
      if (r.S0_episode_status === FAIL) return 'Outside analytic archive (S0)';
      if (r.S0_episode_status === HOLD) return 'Held at S0 (access/evidence)';
      for (const st of epStages) {
        const s = r[`${st.id}_status`];
        if (s === FAIL) return `Not passed ${st.id}`;
        if (s === HOLD) return `Held at ${st.id} (evidence missing)`;
      }
      const last = epStages[epStages.length - 1];
      return `Passed ${last.id}` + (last.paths ? ` (${r[last.id + '_path']})` : '');
    };
    const level = (r) => {
      if (r.S0_episode_status === FAIL) return 'Outside analytic archive';
      if (r.S0_episode_status === HOLD) return 'Held at S0 (not yet analysable)';
      let lab = levels[entryStages.length ? entryStages[entryStages.length - 1].id : 'base'] || 'Level 1';
      for (const st of epStages) {
        const s = r[`${st.id}_status`];
        if (s === PASS) { const bp = st.levels_by_path || {}; lab = bp[r[`${st.id}_path`]] || levels[st.id] || lab; continue; }
        if (s === HOLD) lab += ` (pending evidence at ${st.id})`;
        break;
      }
      return lab;
    };
    for (const e of eps) { e.final_status = final(e); if (levels) e.level = level(e); }

    const rc = g.reason_column;
    if (rc && eps.length && eps.some((e) => rc in e)) {
      const miss = eps.filter((e) => /^(Not passed|Outside)/.test(e.final_status) && !(e[rc] || '')).map((e) => e[ep]);
      if (miss.length) problems.push({ level: 'WARN', where: `${miss.length} episodes`, problem: 'No written reason for not reaching the next level: ' + miss.join(', ') });
    }
    const cs = g.claimed_status_column;
    if (cs && eps.length && eps.some((e) => cs in e)) {
      for (const r of eps) {
        const c = (r[cs] || '').trim(); if (!c) continue;
        if (levels && c.toLowerCase().startsWith('level')) {
          const got = r.level.split(' (')[0];
          const want = c.split(' (')[0].toLowerCase();
          if (!got.toLowerCase().startsWith(want) && !c.toLowerCase().startsWith(got.toLowerCase())) problems.push({ level: 'ERROR', where: r[ep], problem: `Hand-typed level '${c}' disagrees with the gates: '${r.level}'` });
        } else if (c.toLowerCase().includes('core') !== r.final_status.startsWith('Passed')) {
          problems.push({ level: 'ERROR', where: r[ep], problem: `Hand-typed status '${c}' disagrees with the gates: '${r.final_status}'` });
        }
      }
    }
    for (const r of rows) delete r._state;
    return { entries: rows, episodes: eps, problems };
  }

  // ---------------------------------------------------------------- funnel
  function valueCounts(arr) { const m = new Map(); for (const a of arr) m.set(a, (m.get(a) || 0) + 1); return [...m.entries()].sort((a, b) => b[1] - a[1]); }

  function funnel(entries, eps, g) {
    const lab = criterionLabels(g); const nested = !!g.levels; const rows = [];
    const add = (stage, kind, count, n) => rows.push({ stage, kind, count, n });
    add('entries', 'main', 'Source entries listed', entries.length);
    for (const st of g.stages.filter((s) => (s.unit || 'episode') === 'entry')) {
      const s = (r) => r[`${st.id}_status`];
      for (const [fc, n] of valueCounts(entries.filter((r) => s(r) === FAIL).map((r) => r[`${st.id}_first_failed`]))) add(st.id, 'side', `Entries excluded: ${lab[fc] || fc}`, n);
      for (const [fc, n] of valueCounts(entries.filter((r) => s(r) === HOLD).map((r) => r[`${st.id}_first_held`]))) add(st.id, 'side', `Entries held: ${lab[fc] || fc}`, n);
      add(st.id, 'main', `Entries passing ${st.id} (${st.name})`, entries.filter((r) => s(r) === PASS).length);
    }
    if (eps.length) {
      add('episodes', 'main', 'Distinct episodes (all entries)', eps.length);
      for (const [k, name] of [[FAIL, 'Episodes outside analytic archive'], [HOLD, 'Episodes held at S0 (access/evidence)']]) {
        const n = eps.filter((e) => e.S0_episode_status === k).length; if (n) add('episodes', 'side', name, n);
      }
      add('episodes', 'main', 'Episodes in analytic archive', eps.filter((e) => e.S0_episode_status === PASS).length);
      const verb = nested ? 'Remain at lower level' : 'Excluded';
      for (const st of g.stages.filter((s) => (s.unit || 'episode') === 'episode')) {
        const s = (e) => e[`${st.id}_status`];
        for (const [fc, n] of valueCounts(eps.filter((e) => s(e) === FAIL).map((e) => e[`${st.id}_first_failed`]))) add(st.id, 'side', `${verb}: ${lab[fc] || fc}`, n);
        for (const [fc, n] of valueCounts(eps.filter((e) => s(e) === HOLD).map((e) => e[`${st.id}_first_held`]))) add(st.id, 'side', `Pending evidence: ${lab[fc] || fc}`, n);
        if (st.paths) for (const [p, n] of valueCounts(eps.filter((e) => s(e) === PASS).map((e) => e[`${st.id}_path`]))) add(st.id, 'side', `Passing via path: ${p}`, n);
        add(st.id, 'main', `Episodes passing ${st.id} (${st.name})`, eps.filter((e) => s(e) === PASS).length);
      }
      if (nested) {
        const base = valueCounts(eps.map((e) => e.level.replace(/ \(pending.*\)$/, ''))).sort((a, b) => cmp(a[0], b[0]));
        for (const [lv, n] of base) add('levels', 'level', lv, n);
        const pend = valueCounts(eps.filter((e) => e.level.includes('pending')).map((e) => e.level)).sort((a, b) => cmp(a[0], b[0]));
        for (const [lv, n] of pend) add('levels', 'level', `  of which ${lv}`, n);
      }
    }
    return rows;
  }

  const api = { PASS, FAIL, HOLD, NA, StopError, applyGates, funnel, criterionLabels, criterionColumns, columnSpecs, gatesCanonical, paths, pathNames, cols, isGate, VERSION: '0.4.0' };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.ClockBindEngine = api;
})(typeof window !== 'undefined' ? window : globalThis);
