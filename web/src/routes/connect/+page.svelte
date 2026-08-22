<script lang="ts">
  /**
   * Six degrees of teammates. Pick two drivers; BFS over the teammate graph
   * returns the shortest chain of shared (season, team) links between them.
   */
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { replaceState } from '$app/navigation';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import SearchBox from '$lib/components/SearchBox.svelte';
  import { ApiError, type Connection, type GraphStats, type Suggestion, connectionsApi } from '$lib/api';

  let from = $state<Suggestion | null>(null);
  let to = $state<Suggestion | null>(null);
  let fromText = $state('');
  let toText = $state('');
  let result = $state<Connection | null>(null);
  let stats = $state<GraphStats | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);

  onMount(async () => {
    try { stats = await connectionsApi.stats(); } catch { /* cosmetic */ }
    // Deep link: /connect?from=max_verstappen&to=fangio runs immediately.
    const f = $page.url.searchParams.get('from');
    const t = $page.url.searchParams.get('to');
    if (f && t) run(f, t);
  });

  const examples: [string, string, string, string][] = [
    ['max_verstappen', 'Max Verstappen', 'fangio', 'Juan Fangio'],
    ['lewis_hamilton', 'Lewis Hamilton', 'senna', 'Ayrton Senna'],
    ['charles_leclerc', 'Charles Leclerc', 'michael_schumacher', 'Michael Schumacher'],
  ];

  async function run(fromId: string, toId: string) {
    if (loading) return;
    loading = true; error = null; result = null;
    try {
      result = await connectionsApi.connect(fromId, toId);
      // Keep the URL in sync so the chain can be shared/bookmarked.
      replaceState(`/connect?from=${encodeURIComponent(fromId)}&to=${encodeURIComponent(toId)}`, {});
      if (!fromText) fromText = result.path[0].name;
      if (!toText) toText = result.path.at(-1)?.name ?? '';
    } catch (e) {
      error = e instanceof ApiError ? e.detail : 'Something went wrong.';
    } finally {
      loading = false;
    }
  }

  function tryExample([fid, fname, tid, tname]: [string, string, string, string]) {
    from = { kind: 'driver', id: fid, label: fname, sublabel: '', href: '' };
    to = { kind: 'driver', id: tid, label: tname, sublabel: '', href: '' };
    fromText = fname; toText = tname;
    run(fid, tid);
  }
</script>

<svelte:head><title>Connect — Sportsona</title></svelte:head>

<div class="space-y-8 max-w-4xl mx-auto">
  <div class="rounded-[26px] p-8 space-y-5" style="background: var(--sp-grape-700); color: var(--sp-sand-100)">
    <div class="space-y-1">
      <p class="text-[11px] font-extrabold uppercase tracking-[0.14em]" style="color: var(--sp-rose-400)">Six degrees of teammates</p>
      <h1 class="text-3xl font-extrabold tracking-tight">Connect<span style="color: var(--sp-rose-500)">.</span></h1>
      <p class="text-[15px]" style="color: var(--sp-grape-200)">
        How is any driver linked to any other through the teammates they shared?
        {#if stats}<span class="opacity-80">· {stats.drivers} drivers, {stats.teammate_links} teammate links, all of F1 history.</span>{/if}
      </p>
    </div>

    <div class="grid gap-3 sm:grid-cols-[1fr_auto_1fr] items-center text-foreground">
      <SearchBox kind="driver" placeholder="From driver…" bind:value={fromText} onPick={(s) => (from = s)} />
      <span class="text-center font-extrabold hidden sm:block" style="color: var(--sp-grape-300)">→</span>
      <SearchBox kind="driver" placeholder="To driver…" bind:value={toText} onPick={(s) => (to = s)} />
    </div>

    <div class="flex flex-wrap items-center gap-2">
      <Button variant="accent" onclick={() => from && to && run(from.id, to.id)} disabled={loading || !from || !to}>
        {#if loading}<Spinner size={14} />{/if} Find the chain
      </Button>
      {#each examples as ex (ex[0] + ex[2])}
        <button type="button" onclick={() => tryExample(ex)}
          class="text-[12.5px] font-bold rounded-full px-4 py-2 transition-colors"
          style="background: var(--sp-grape-600); color: var(--sp-grape-200)">
          {ex[1].split(' ').at(-1)} → {ex[3].split(' ').at(-1)}
        </button>
      {/each}
    </div>
  </div>

  {#if error}
    <Card class="p-5 text-sm text-destructive">{error}</Card>
  {/if}

  {#if result}
    <Card class="p-6 space-y-5">
      <div class="flex items-baseline gap-3">
        <span class="sp-stat text-5xl text-rose-ink">{result.degrees}</span>
        <div>
          <p class="font-extrabold text-lg leading-tight">
            {result.degrees === 0 ? 'Same driver' : result.degrees === 1 ? 'degree — direct teammates' : 'degrees of separation'}
          </p>
          <p class="text-sm text-muted-foreground">{result.path[0].name} → {result.path.at(-1)?.name}</p>
        </div>
      </div>

      <ol class="relative border-l-2 border-border ml-3 space-y-4">
        {#each result.path as hop, i (hop.driver_id)}
          <li class="pl-5">
            <span class="absolute -left-[7px] mt-1.5 h-3 w-3 rounded-full" style="background: {i === 0 || i === result.path.length - 1 ? 'var(--sp-rose-500)' : 'var(--sp-grape-300)'}"></span>
            <a href="/drivers/{hop.driver_id}" class="font-extrabold hover:text-primary transition-colors">{hop.name}</a>
            {#if hop.via}
              <p class="text-sm text-muted-foreground">
                teammates with {result.path[i - 1].name} at
                <a href="/constructors/{hop.via.constructor_id}" class="font-semibold text-foreground hover:text-primary">{hop.via.constructor}</a>,
                <span class="sp-fig">{hop.via.season}</span>
              </p>
            {/if}
          </li>
        {/each}
      </ol>
    </Card>
  {/if}
</div>
