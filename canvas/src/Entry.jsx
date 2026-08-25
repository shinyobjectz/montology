import { about, verbColor } from './lib.js';

/** One word, entire. Everything decided about it sits WITH it: a reader who
 *  has to look elsewhere to find out that a name was retired will not look. */
export default function Entry({ node, g, onPick }) {
  const d = node.data;
  const a = about(node, g);
  const unnamed = d.verbs_unnamed ?? [];
  const wrong = [];
  if (d.collides) wrong.push({
    text: `${d.collides} declaration${d.collides > 1 ? 's' : ''} in the code wear${d.collides > 1 ? '' : 's'} this name`,
    where: (d.at ?? []).slice(0, 3),
  });
  if (unnamed.length) wrong.push({
    text: `made to do ${unnamed.length} thing${unnamed.length > 1 ? 's' : ''} no word names`,
    where: unnamed,
  });

  const Link = ({ to }) => (
    <button className="link mono" onClick={() => onPick(to)}>{to.label}</button>
  );

  return (
    <article id={node.id}>
      <h3>
        <span className="mono name">{node.label}</span>
        <span className="grade mono">
          {d.word_kind}{d.pos ? ` · ${d.pos}` : ''}{d.code ? ` · ${d.code}` : ''}
        </span>
      </h3>

      <p className="def">{d.definition}</p>
      {d.test && <p className="test"><span>is it one?</span> {d.test}</p>}

      {(a.was.length > 0 || a.instead.length > 0 || a.ruled.length > 0) && (
        <ul className="decided">
          {a.was.map(({ other, e }) => (
            <li key={other.id}>
              <b className="retired mono">{other.label}</b> was retired in favour of this
              {e.data?.why && <em> — {e.data.why}</em>}
            </li>
          ))}
          {a.instead.map(({ other, e }) => (
            <li key={other.id}>
              do not say <b className="retired mono">{other.label}</b>
              {e.data?.register && e.data.register !== 'all' && <em> in {e.data.register}</em>}
              {e.data?.gates === false && <em className="weak"> — but this ruling cannot gate</em>}
            </li>
          ))}
          {a.ruled.map((r) => (
            <li key={r.id}>
              {r.data.ruling_kind === 'collision'
                ? <>contested with <b>{r.data.theirs}</b>, who mean “{r.data.their_meaning}”. {r.data.ruling}</>
                : <>a symbol may share this name in <code className="mono">{r.data.scope}</code> — {r.data.why}</>}
            </li>
          ))}
        </ul>
      )}

      <p className="ties">
        {a.inside && <span>inside <Link to={a.inside} /></span>}
        {a.genus.map((x) => <span key={x.id}>a kind of <Link to={x} /></span>)}
        {a.holds.length > 0 && (
          <span>holds {a.holds.map((h) => <Link key={h.id} to={h} />)}</span>
        )}
        {a.does.map(({ other, e }, i) => (
          <span key={`d${i}`}>
            <b style={{ color: verbColor(e.data.verb, e.data.defined !== false) }}>{e.data.verb}</b>
            {' '}<Link to={other} />
          </span>
        ))}
        {a.doneBy.map(({ other, e }, i) => (
          <span key={`b${i}`}>
            <Link to={other} />{' '}
            <b style={{ color: verbColor(e.data.verb, e.data.defined !== false) }}>{e.data.verb}</b> this
          </span>
        ))}
      </p>

      {wrong.length > 0 && (
        <ul className="wrong">
          {wrong.map((w, i) => (
            <li key={i}>
              {w.text}
              {w.where.length > 0 && <span className="mono where">{w.where.join('  ')}</span>}
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
