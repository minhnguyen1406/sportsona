<script lang="ts">
  import { onMount } from 'svelte';
  import Alert from '$lib/components/ui/Alert.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import Skeleton from '$lib/components/ui/Skeleton.svelte';
  import { ApiError, type SeasonResponse, f1Api } from '$lib/api';

  let seasons = $state<SeasonResponse[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);

  onMount(async () => {
    try {
      seasons = await f1Api.listSeasons();
    } catch (err) {
      error = err instanceof ApiError ? err.detail : 'Failed to load seasons';
    } finally {
      loading = false;
    }
  });
</script>

<div class="space-y-6">
  <header>
    <h1 class="text-3xl font-bold tracking-tight">Seasons</h1>
    <p class="text-muted-foreground">Browse every F1 season since 1950.</p>
  </header>

  {#if loading}
    <div class="grid gap-3 grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8">
      {#each Array(20) as _, i (i)}
        <Skeleton class="h-16" />
      {/each}
    </div>
  {:else if error}
    <Alert variant="destructive">{error}</Alert>
  {:else if seasons.length === 0}
    <Card class="p-8 text-center text-muted-foreground">
      <p>No seasons synced yet.</p>
      <p class="text-sm mt-1">
        Run <code class="font-mono">poetry run python scripts/sync_f1_data.py</code> in the backend to populate data.
      </p>
    </Card>
  {:else}
    <div class="grid gap-3 grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8">
      {#each seasons as s (s.year)}
        <a
          href="/seasons/{s.year}"
          class="rounded-lg border bg-card p-4 text-center font-semibold hover:border-primary hover:text-primary transition-colors"
        >
          {s.year}
        </a>
      {/each}
    </div>
  {/if}
</div>
