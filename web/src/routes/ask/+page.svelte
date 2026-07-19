<script lang="ts">
  import { onMount } from 'svelte';
  import Alert from '$lib/components/ui/Alert.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import ResultsTable from '$lib/components/ResultsTable.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import { ApiError, type AskHistoryItem, type AskResponse, askApi } from '$lib/api';
  import { auth } from '$lib/stores/auth.svelte';

  let question = $state('');
  let loading = $state(false);
  let error = $state<string | null>(null);
  let result = $state<AskResponse | null>(null);
  let history = $state<AskHistoryItem[]>([]);
  let copied = $state(false);

  onMount(async () => {
    if (!auth.isAuthenticated) return;
    try {
      history = await askApi.history();
    } catch {
      /* history is a nicety — never block the page on it */
    }
  });

  async function copyShareLink() {
    if (!result?.answer_id) return;
    const url = `${location.origin}/ask/a/${result.answer_id}`;
    try {
      await navigator.clipboard.writeText(url);
      copied = true;
      setTimeout(() => (copied = false), 2000);
    } catch {
      // Clipboard blocked (http, permissions) — show the URL for manual copy.
      prompt('Copy this link:', url);
    }
  }

  const examples = [
    'Who has the most wins in F1 history?',
    'Top 5 polesitters of 2023',
    'How many times has Verstappen won at Spa?',
    'Most podiums for Ferrari since 2010',
    'Who scored the most points in 2024?'
  ];

  /** Pull a useful message out of an ApiError. The /ask endpoint returns
   *  structured `{detail: {message, sql?}}` on every error path it controls,
   *  so prefer that. Fall back to status-based defaults for the rare cases
   *  where the message didn't come through (network drop, etc.). */
  function messageFromError(err: unknown): string {
    if (!(err instanceof ApiError)) return 'Something went wrong.';
    const raw = err.raw as { detail?: unknown } | null;
    const detail = raw?.detail;
    if (detail && typeof detail === 'object' && 'message' in detail) {
      const m = (detail as { message: unknown }).message;
      if (typeof m === 'string') return m;
    }
    if (typeof err.detail === 'string' && err.detail.trim()) return err.detail;
    if (err.status === 402) return 'Anthropic credits exhausted. Top up to keep asking.';
    if (err.status === 429) return 'Rate limit hit — try again in a minute.';
    if (err.status === 502) return 'Anthropic returned an error. Try again.';
    if (err.status === 503) return 'LLM upstream unavailable.';
    if (err.status >= 500) return `Server error (${err.status}). Try again.`;
    return `Request failed (${err.status}).`;
  }

  async function ask(q: string) {
    const trimmed = q.trim();
    if (!trimmed || loading) return;
    loading = true;
    error = null;
    result = null;
    try {
      result = await askApi.ask(trimmed);
      // Prepend to history optimistically — the server stored it already.
      if (auth.isAuthenticated && result.answer_id) {
        history = [
          { slug: result.answer_id, question: trimmed, created_at: new Date().toISOString() },
          ...history
        ].slice(0, 20);
      }
    } catch (err) {
      error = messageFromError(err);
    } finally {
      loading = false;
    }
  }

  function onSubmit(event: Event) {
    event.preventDefault();
    ask(question);
  }

  function tryExample(q: string) {
    question = q;
    ask(q);
  }

</script>

<svelte:head>
  <title>Ask — Sportsona</title>
</svelte:head>

<div class="space-y-8 max-w-4xl mx-auto">
  <header class="text-center space-y-2">
    <h1 class="text-3xl font-black italic tracking-tight">
      Ask<span class="text-accent">.</span>
    </h1>
    <p class="text-muted-foreground">
      Any F1 stats question. Answered with real data — never invented.
    </p>
  </header>

  <form onsubmit={onSubmit} class="flex gap-2">
    <input
      bind:value={question}
      type="text"
      placeholder="e.g. Who has the most wins at Monaco?"
      maxlength={500}
      autocomplete="off"
      disabled={loading}
      class="flex-1 h-12 rounded-md border border-input bg-background px-4 text-base placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
    />
    <Button type="submit" size="lg" disabled={loading || !question.trim()}>
      {#if loading}
        <Spinner size={16} />
      {/if}
      Ask
    </Button>
  </form>

  {#if !result && !loading && !error}
    <div class="space-y-3">
      <p class="text-sm text-muted-foreground text-center">Try one of these:</p>
      <div class="flex flex-wrap justify-center gap-2">
        {#each examples as ex (ex)}
          <button
            type="button"
            onclick={() => tryExample(ex)}
            class="text-sm rounded-full border border-input px-4 py-1.5 hover:border-accent hover:bg-accent/10 transition-colors"
          >
            {ex}
          </button>
        {/each}
      </div>
    </div>
  {/if}

  {#if error}
    <Alert variant="destructive">{error}</Alert>
  {/if}

  {#if result}
    <Card class="p-6 space-y-5">
      <div class="border-b pb-4 flex items-start justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-widest text-muted-foreground">You asked</p>
          <p class="text-lg font-medium">{result.question}</p>
        </div>
        {#if result.answer_id}
          <Button variant="outline" size="sm" onclick={copyShareLink}>
            {copied ? 'Copied!' : 'Share'}
          </Button>
        {/if}
      </div>

      {#if result.reasoning}
        <p class="text-sm italic text-muted-foreground">{result.reasoning}</p>
      {/if}

      {#if result.row_count === 0}
        <Card class="p-8 text-center text-muted-foreground bg-muted/20">
          <p class="text-sm">No rows matched that query.</p>
          <p class="text-xs mt-1">Try rephrasing — or peek at the SQL Claude wrote.</p>
        </Card>
      {:else}
        <ResultsTable
          columns={result.columns}
          rows={result.rows}
          footnote={result.truncated
            ? `Showing the first ${result.row_count} rows — more were truncated.`
            : undefined}
        />
      {/if}

      <details class="text-sm">
        <summary class="cursor-pointer text-muted-foreground hover:text-foreground select-none">
          Show the SQL Claude wrote
        </summary>
        <pre
          class="mt-3 rounded-md bg-muted/40 p-4 text-xs overflow-x-auto"><code>{result.sql}</code></pre>
      </details>

      <p class="text-xs text-muted-foreground border-t pt-3">
        {#if result.cached}
          instant — served from cache · {result.model}
        {:else}
          {result.model} · LLM {result.llm_latency_ms}ms · DB {result.db_latency_ms}ms
          {#if result.cache_read_tokens > 0}
            · cached {result.cache_read_tokens.toLocaleString()} prompt tokens
          {/if}
        {/if}
      </p>
    </Card>
  {/if}

  {#if auth.isAuthenticated && history.length > 0}
    <section class="space-y-3">
      <h2 class="text-sm font-semibold text-muted-foreground">Your recent questions</h2>
      <ul class="divide-y divide-border rounded-md border">
        {#each history as item (item.slug)}
          <li>
            <a
              href="/ask/a/{item.slug}"
              class="flex items-center justify-between gap-3 px-4 py-2.5 text-sm hover:bg-muted/40 transition-colors"
            >
              <span class="truncate">{item.question}</span>
              <span class="text-xs text-muted-foreground shrink-0">
                {new Date(item.created_at).toLocaleDateString()}
              </span>
            </a>
          </li>
        {/each}
      </ul>
    </section>
  {/if}
</div>
