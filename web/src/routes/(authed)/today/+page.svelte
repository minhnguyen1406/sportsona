<script lang="ts">
  import { onMount } from 'svelte';
  import Alert from '$lib/components/ui/Alert.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import ResultsTable from '$lib/components/ResultsTable.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import { ApiError, type StatOfDayResponse, statApi } from '$lib/api';
  import { formatFullDate, parseUTC } from '$lib/date';

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
      {#if stat}{formatFullDate(stat.date)}{:else}Today{/if}
    </p>
    <h1 class="text-3xl font-black tracking-tight">
      Stat of the day<span class="text-rose-ink">.</span>
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
    <!-- The signature v3 hero: question + narration on a flat grape surface. -->
    <div
      class="rounded-[26px] p-8 space-y-3"
      style="background: var(--sp-grape-700); color: var(--sp-sand-100)"
    >
      <p class="text-[11px] font-extrabold uppercase tracking-[0.14em]" style="color: var(--sp-rose-400)">
        Stat of the day
      </p>
      <h2 class="text-2xl font-extrabold leading-snug" style="letter-spacing: -0.026em">
        {stat.question}
      </h2>
      <p class="text-[15px] leading-relaxed" style="color: var(--sp-grape-200)">
        {stat.narration}
      </p>
      {#if stat.reasons && stat.reasons.length > 0}
        <!-- "A number never travels alone": the evidence behind the headline. -->
        <div class="flex flex-col gap-2 pt-2">
          {#each stat.reasons as r, i (i)}
            <div class="grid grid-cols-[16px_1fr] gap-3 text-[14px] leading-snug" style="color: var(--sp-grape-200)">
              <span class="font-black" style="color: var(--sp-volt-500)">↑</span><span>{r}</span>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    {#if stat.rows.length > 0 || stat.sql}
      <Card class="p-6 space-y-6">
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
          {stat.model} · generated {parseUTC(stat.created_at).toLocaleString()}
        </p>
      </Card>
    {/if}
  {/if}
</div>
