<script lang="ts">
  import { onMount } from 'svelte';
  import Alert from '$lib/components/ui/Alert.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import ResultsTable from '$lib/components/ResultsTable.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import { ApiError, type StatOfDayResponse, statApi } from '$lib/api';

  let stat = $state<StatOfDayResponse | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);

  function messageFromError(err: unknown): string {
    if (!(err instanceof ApiError)) return 'Something went wrong loading today’s stat.';
    const raw = err.raw as { detail?: unknown } | null;
    const detail = raw?.detail;
    if (detail && typeof detail === 'object' && 'message' in detail) {
      const m = (detail as { message: unknown }).message;
      if (typeof m === 'string') return m;
    }
    if (typeof err.detail === 'string' && err.detail.trim()) return err.detail;
    if (err.status === 402) return 'Anthropic credits exhausted — today’s stat can’t be generated.';
    if (err.status === 503) return 'LLM upstream unavailable — check back in a few.';
    if (err.status >= 500) return `Server error (${err.status}). Try refreshing.`;
    return `Request failed (${err.status}).`;
  }

  function formatDate(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  }

  onMount(async () => {
    try {
      stat = await statApi.today();
    } catch (err) {
      error = messageFromError(err);
    } finally {
      loading = false;
    }
  });
</script>

<svelte:head>
  <title>Today's stat — Sportsona</title>
</svelte:head>

<div class="space-y-8 max-w-4xl mx-auto">
  <header class="text-center space-y-2">
    <p class="text-xs uppercase tracking-widest text-muted-foreground">
      {#if stat}{formatDate(stat.date)}{:else}Today{/if}
    </p>
    <h1 class="text-3xl font-black italic tracking-tight">
      Stat of the day<span class="text-accent">.</span>
    </h1>
    <p class="text-muted-foreground">
      A fresh F1 angle each day, picked by Claude and grounded in the database.
    </p>
  </header>

  {#if loading}
    <Card class="p-12 flex flex-col items-center gap-3">
      <Spinner size={28} />
      <p class="text-sm text-muted-foreground">
        Generating today's stat… first request of the day takes a few seconds.
      </p>
    </Card>
  {:else if error}
    <Alert variant="destructive">{error}</Alert>
  {:else if stat}
    <Card class="p-6 space-y-6">
      <div>
        <p class="text-xs uppercase tracking-widest text-muted-foreground">Today's question</p>
        <h2 class="text-xl font-semibold mt-1">{stat.question}</h2>
      </div>

      <p class="text-base leading-relaxed border-l-4 border-accent pl-4 italic">
        {stat.narration}
      </p>

      {#if stat.rows.length > 0}
        <ResultsTable columns={stat.columns} rows={stat.rows} />
      {/if}

      <details class="text-sm">
        <summary class="cursor-pointer text-muted-foreground hover:text-foreground select-none">
          Show the SQL Claude wrote
        </summary>
        <pre
          class="mt-3 rounded-md bg-muted/40 p-4 text-xs overflow-x-auto"><code>{stat.sql}</code></pre>
      </details>

      <p class="text-xs text-muted-foreground border-t pt-3">
        {stat.model} · generated {new Date(stat.created_at).toLocaleString()}
      </p>
    </Card>
  {/if}
</div>
