<script lang="ts">
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import ResultsTable from '$lib/components/ResultsTable.svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  const answer = $derived(data.answer);

  /** One-line summary for OG description: the first row, humanized. */
  const ogDescription = $derived.by(() => {
    if (!answer.rows.length) return 'Asked and answered with real F1 data on Sportsona.';
    const first = answer.rows[0].map((v) => String(v ?? '')).join(' · ');
    return `${first} — real data, never invented. Ask your own on Sportsona.`;
  });

  function formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString(undefined, {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  }
</script>

<svelte:head>
  <title>{answer.question} — Sportsona</title>
  <meta property="og:title" content={answer.question} />
  <meta property="og:description" content={ogDescription} />
  <meta property="og:type" content="article" />
  <meta name="description" content={ogDescription} />
</svelte:head>

<div class="space-y-8 max-w-4xl mx-auto">
  <header class="text-center space-y-2">
    <p class="text-xs uppercase tracking-widest text-muted-foreground">
      Shared answer · {formatDate(answer.created_at)}
    </p>
    <h1 class="text-2xl font-black italic tracking-tight leading-snug">
      {answer.question}<span class="text-accent">?</span>
    </h1>
  </header>

  <Card class="p-6 space-y-5">
    {#if answer.reasoning}
      <p class="text-sm italic text-muted-foreground">{answer.reasoning}</p>
    {/if}

    {#if answer.rows.length === 0}
      <p class="text-muted-foreground">No rows matched this question when it was asked.</p>
    {:else}
      <ResultsTable
        columns={answer.columns}
        rows={answer.rows}
        footnote={answer.truncated ? 'Truncated to the first rows.' : undefined}
      />
    {/if}

    <details class="text-sm">
      <summary class="cursor-pointer text-muted-foreground hover:text-foreground select-none">
        Show the SQL Claude wrote
      </summary>
      <pre
        class="mt-3 rounded-md bg-muted/40 p-4 text-xs overflow-x-auto"><code>{answer.sql}</code></pre>
    </details>

    <p class="text-xs text-muted-foreground border-t pt-3">
      Snapshot from {formatDate(answer.created_at)} · {answer.model}
    </p>
  </Card>

  <div class="text-center">
    <a href="/ask">
      <Button variant="accent" size="lg">Ask your own F1 question</Button>
    </a>
  </div>
</div>
