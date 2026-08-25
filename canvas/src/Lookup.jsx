import { useEffect, useRef, useState } from 'react';

/** The hero, because it is montology's actual verb.
 *
 *  `monty onto check <name>` is the thing people run twenty times a day —
 *  before naming a class, a concept, a tag — and every version of this UI so
 *  far buried it inside an authoring panel. Here it is the first thing on the
 *  page, and it answers before you have finished the word.
 */
export default function Lookup({ words, onPick }) {
  const [q, setQ] = useState('');
  const [verdict, setVerdict] = useState(null);
  const box = useRef(null);

  // `/` focuses it from anywhere, the way every reference tool people already
  // use behaves.
  useEffect(() => {
    const key = (e) => {
      if (e.key === '/' && document.activeElement !== box.current) {
        e.preventDefault();
        box.current?.focus();
      }
      if (e.key === 'Escape') box.current?.blur();
    };
    window.addEventListener('keydown', key);
    return () => window.removeEventListener('keydown', key);
  }, []);

  useEffect(() => {
    const name = q.trim();
    if (!name) { setVerdict(null); return; }
    const t = setTimeout(async () => {
      try {
        const r = await fetch(`./api/check?name=${encodeURIComponent(name)}`);
        setVerdict({ name, findings: (await r.json()).findings ?? [] });
      } catch { /* the browse still works without the verdict */ }
    }, 160);
    return () => clearTimeout(t);
  }, [q]);

  const needle = q.trim().toLowerCase();
  const hits = needle
    ? words.filter((w) => w.label.toLowerCase().includes(needle)
        || (w.data.definition ?? '').toLowerCase().includes(needle)).slice(0, 8)
    : [];

  return (
    <div className="lookup">
      <input
        ref={box} className="mono" value={q} spellCheck="false"
        onChange={(e) => setQ(e.target.value)}
        placeholder="is this name taken?    /"
        aria-label="check a name against the vocabulary"
      />
      {verdict && (
        <p className={`verdict ${verdict.findings.length ? 'taken' : 'free'}`}>
          {verdict.findings.length
            ? <><b className="mono">{verdict.name}</b> is spoken for — {verdict.findings[0]}</>
            : <><b className="mono">{verdict.name}</b> is free. One word means one thing; keep it that way.</>}
        </p>
      )}
      {hits.length > 0 && (
        <ul className="hits">
          {hits.map((w) => (
            <li key={w.id}>
              <button onClick={() => { onPick(w); setQ(''); }}>
                <b className="mono">{w.label}</b>
                <span>{w.data.definition}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
