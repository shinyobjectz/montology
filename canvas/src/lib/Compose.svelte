<script>
  // Authoring, through the engine's own front door. This panel knows the SHAPE
  // of an intent (from /api/graph, which reports what the server accepts) and
  // nothing about what makes one valid — that lives in the laws, is checked
  // once, and comes back as text we display without rewording.
  let { intents, token, onwrote } = $props();

  let intent = $state('word.add');
  let fields = $state({});
  let answer = $state(null);
  let findings = $state([]);
  let checking = $state(false);

  const spec = $derived(intents.find((i) => i.intent === intent));
  // Whatever this intent calls the thing being named — that is the field the
  // check-first discipline applies to.
  const NAMED = ['name', 'word', 'term', 'dont_say', 'from_term', 'was'];
  const nameField = $derived(spec ? [...spec.required, ...spec.optional].find((f) => NAMED.includes(f)) : null);

  // Check-first, live. The CLI's discipline depends on the author REMEMBERING
  // to run `monty onto check`; here it is simply not possible to skip.
  let timer;
  $effect(() => {
    const value = nameField ? (fields[nameField] ?? '') : '';
    const wants = intent === 'word.add';        // only naming something NEW
    clearTimeout(timer);
    if (!wants || !value.trim()) { findings = []; return; }
    checking = true;
    timer = setTimeout(async () => {
      try {
        const r = await fetch(`./api/check?name=${encodeURIComponent(value)}`);
        findings = (await r.json()).findings ?? [];
      } finally { checking = false; }
    }, 220);
  });

  function pick(next) {
    intent = next;
    fields = {};
    answer = null;
    findings = [];
  }

  async function submit(e) {
    e.preventDefault();
    answer = null;
    const r = await fetch('./api/intent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Monty-Token': token },
      body: JSON.stringify({ intent, fields }),
    });
    answer = await r.json();
    if (answer.ok) { fields = {}; findings = []; onwrote?.(); }
  }

  const LABEL = {
    dont_say: 'do not say', say: 'say instead', their_meaning: 'what theirs means',
    from_term: 'route away from', to_word: 'say instead', genus: 'is a kind of',
    value: 'value', ruling: 'the ruling', was: 'was', now: 'is now',
  };
  const HELP = {
    register: 'code | surface | prose | all — a ruling with no register cannot gate',
    scope: 'a path glob. Without one, a register of "all" can never be enforced',
    pos: 'verb | noun | value — how a collision on this word gets judged',
    kind: 'core | inner | adopted | custom — whose word it is',
    code: 'dotted, and every prefix must resolve to a word',
    test: 'the one-line "is it one?" test',
  };
</script>

<h2>Author</h2>
<select class="mono" value={intent} onchange={(e) => pick(e.currentTarget.value)}>
  {#each intents as i}<option value={i.intent}>{i.intent}</option>{/each}
</select>

{#if spec}
  <form onsubmit={submit}>
    {#each spec.required as f}
      <label>
        <span>{LABEL[f] ?? f.replace(/_/g, ' ')} <em>required</em></span>
        {#if f === 'definition' || f === 'ruling' || f === 'why' || f === 'their_meaning'}
          <textarea class="mono" rows="3" bind:value={fields[f]}></textarea>
        {:else}
          <input class="mono" bind:value={fields[f]} spellcheck="false" />
        {/if}
        {#if HELP[f]}<small>{HELP[f]}</small>{/if}
      </label>
    {/each}

    {#if nameField && intent === 'word.add'}
      <p class="check" class:taken={findings.length}>
        {#if checking}checking…
        {:else if findings.length}
          <strong>{fields[nameField]} is spoken for</strong>
          {#each findings as f}<span>{f}</span>{/each}
        {:else if (fields[nameField] ?? '').trim()}
          {fields[nameField]} is free
        {:else}
          every name is checked before it is taken
        {/if}
      </p>
    {/if}

    {#each spec.optional as f}
      <label class="opt">
        <span>{LABEL[f] ?? f.replace(/_/g, ' ')}</span>
        <input class="mono" bind:value={fields[f]} spellcheck="false" />
        {#if HELP[f]}<small>{HELP[f]}</small>{/if}
      </label>
    {/each}

    <button class="go" type="submit">write it</button>
  </form>

  {#if answer}
    <p class="answer mono" class:bad={!answer.ok}>{answer.line}</p>
  {/if}
{/if}

<style>
  h2 { font-size: .8rem; margin: 0 0 .5rem; }
  select { width: 100%; padding: .3rem; font-size: .74rem; border-radius: 5px;
           border: 1px solid var(--line); background: var(--bg); color: var(--ink); }
  form { display: flex; flex-direction: column; gap: .5rem; margin-top: .7rem; }
  label { display: flex; flex-direction: column; gap: .18rem; }
  label span { font-size: .64rem; text-transform: uppercase; letter-spacing: .05em; color: var(--dim); }
  label em { font-style: normal; color: var(--term); font-size: .58rem; }
  label.opt span { opacity: .75; }
  input, textarea { width: 100%; padding: .3rem .4rem; font-size: .74rem; border-radius: 5px;
                    border: 1px solid var(--line); background: var(--bg); color: var(--ink);
                    resize: vertical; }
  small { font-size: .6rem; color: var(--dim); line-height: 1.35; }
  .check { font-size: .68rem; color: var(--surface); margin: -.1rem 0 0;
           display: flex; flex-direction: column; gap: .15rem; }
  .check.taken { color: var(--term); }
  .go { margin-top: .3rem; padding: .35rem; font-size: .74rem; cursor: pointer;
        border-radius: 5px; border: 1px solid var(--accent); background: var(--accent);
        color: white; font-weight: 600; }
  .answer { font-size: .7rem; line-height: 1.45; white-space: pre-wrap;
            border-left: 2px solid var(--surface); padding-left: .5rem; margin-top: .8rem; }
  .answer.bad { border-color: var(--term); color: var(--term); }
</style>
