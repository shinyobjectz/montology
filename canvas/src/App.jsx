import { useCallback, useEffect, useMemo, useState } from 'react';
import Lookup from './Lookup.jsx';
import Entry from './Entry.jsx';
import Relations from './Relations.jsx';
import { index } from './lib.js';

/** The ontology as a reference work.
 *
 *  Rebuilt from the reader rather than from the data. Four jobs bring someone
 *  here — is this name taken, what is this system about, what needs a decision,
 *  and what did that word become — and the first is the one people do twenty
 *  times a day. So lookup is the hero and everything else is browsing.
 *
 *  One column, no rail. A lexicon has no table of contents; it has an order and
 *  a way to look things up, and both are cheaper than a permanent 236px of
 *  navigation next to a 66-character measure.
 */
export default function App() {
  const [raw, setRaw] = useState(null);
  const [error, setError] = useState('');
  const [area, setArea] = useState(null);

  useEffect(() => {
    fetch('./api/graph')
      .then((r) => (r.ok ? r.json() : r.json().then((e) => Promise.reject(e.error ?? r.statusText))))
      .then(setRaw)
      .catch((e) => setError(String(e)));
  }, []);

  const g = useMemo(() => (raw ? index(raw) : null), [raw]);

  const goTo = useCallback((node) => {
    document.getElementById(node.id)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, []);

  const attention = useMemo(() => {
    if (!g) return [];
    const s = g.stats ?? {};
    const unanswered = g.nodes.filter((n) => n.kind === 'question' && n.data.unanswered).length;
    // The count is rendered on its own, so the sentence must not carry it too.
    const s_ = (n, one, many = `${one}s`) => (n === 1 ? one : many);
    return [
      s.unnamed_verbs && { n: s.unnamed_verbs,
        say: `${s_(s.unnamed_verbs, 'verb')} performed on a word, that no word names`,
        fix: 'monty onto verbs' },
      s.collides && { n: s.collides,
        say: `${s_(s.collides, 'declaration')} wearing a word's name`,
        fix: 'monty lint' },
      s.candidates && { n: s.candidates,
        say: `${s_(s.candidates, 'name')} the code repeats that no word covers`,
        fix: 'monty scan --candidates' },
      unanswered && { n: unanswered,
        say: `${s_(unanswered, 'question')} no word answers`,
        fix: 'monty onto questions' },
    ].filter(Boolean);
  }, [g]);

  if (error) return <main className="page"><p className="error mono">{error}</p></main>;
  if (!g) return <main className="page"><p className="dim mono">reading the ontology…</p></main>;

  const shown = area ? g.areas.filter((a) => a.lead.label === area) : g.areas;

  return (
    <main className="page">
      <header className="masthead">
        <h1>{g.workspace}</h1>
        <p className="dim">
          {g.words.length} words
          {g.stats.relations ? `, ${g.stats.relations} relations` : ''}
          {g.stats.rulings ? `, ${g.stats.rulings} rulings` : ''}.
          Rendered from <code className="mono">.monty/ontology.db</code>, which is the truth —
          this is a reading of it.
        </p>
      </header>

      <Lookup words={g.words} onPick={goTo} />

      {attention.length > 0 && (
        <section className="attention">
          <h2>Wants a decision</h2>
          <ul>
            {attention.map((a) => (
              <li key={a.say}><b>{a.n}</b> {a.say}<code className="mono">{a.fix}</code></li>
            ))}
          </ul>
        </section>
      )}

      <Relations g={g} onPick={goTo} />

      <nav className="areas mono">
        <button className={area ? '' : 'on'} onClick={() => setArea(null)}>all</button>
        {g.areas.map((a) => (
          <button key={a.lead.id} className={area === a.lead.label ? 'on' : ''}
                  onClick={() => setArea(a.lead.label)}>
            {a.lead.label} <span>{a.words.length}</span>
          </button>
        ))}
      </nav>

      {shown.map((a) => (
        <section key={a.lead.id} className="chapter">
          <h2 className="mono">{a.lead.label}</h2>
          <Entry node={a.lead} g={g} onPick={goTo} />
          {a.words.map((w) => <Entry key={w.id} node={w} g={g} onPick={goTo} />)}
        </section>
      ))}

      {!area && g.loose.length > 0 && (
        <section className="chapter">
          <h2 className="mono">on their own</h2>
          {g.loose.map((w) => <Entry key={w.id} node={w} g={g} onPick={goTo} />)}
        </section>
      )}

      {!area && g.nodes.filter((n) => n.kind === 'doctrine').map((d) => (
        <section key={d.id} className="doctrine">
          <h2>{d.label}</h2>
          <p>{d.data.body}</p>
        </section>
      ))}
    </main>
  );
}
