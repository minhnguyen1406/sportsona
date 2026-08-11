<script lang="ts">
  import { onMount } from 'svelte';
  import Badge from '$lib/components/ui/Badge.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import RecapCard from '$lib/components/RecapCard.svelte';
  import Skeleton from '$lib/components/ui/Skeleton.svelte';
  import { ApiError, type DashboardResponse, usersApi } from '$lib/api';
  import { auth } from '$lib/stores/auth.svelte';
  import { formatDate } from '$lib/date';

  let dashboard = $state<DashboardResponse | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);

  /** Most recent completed race across the user's followed drivers — the
   *  race their recap is most likely about. Derived from data already in
   *  the dashboard payload, no extra request. */
  const latestRace = $derived.by(() => {
    if (!dashboard) return null;
    let best: { race_id: number; race_name: string; date: string } | null = null;
    for (const fd of dashboard.followed_drivers) {
      for (const r of fd.recent_results) {
        if (!best || r.date > best.date) {
          best = { race_id: r.race_id, race_name: r.race_name, date: r.date };
        }
      }
    }
    return best;
  });

  onMount(async () => {
    try {
      dashboard = await usersApi.dashboard();
    } catch (err) {
      error = err instanceof ApiError ? err.detail : 'Failed to load dashboard';
    } finally {
      loading = false;
    }
  });

  function ordinal(n: number | null): string {
    if (n === null) return '—';
    const s = ['th', 'st', 'nd', 'rd'];
    const v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
  }

  /** Avatar initials: two names → their initials (LN); one name → first 3 (FER). */
  function initials(a: string, b?: string): string {
    if (b) return (a[0] + b[0]).toUpperCase();
    return a.slice(0, 3).toUpperCase();
  }
</script>

<div class="space-y-6">
  <header class="space-y-1">
    <p class="text-[11px] font-extrabold uppercase tracking-[0.14em] text-muted-foreground">
      Your season
    </p>
    <h1 class="text-3xl font-extrabold tracking-tight" style:letter-spacing="-0.032em">
      Welcome back, {auth.user?.username ?? '…'}<span class="text-rose-ink">.</span>
    </h1>
  </header>

  {#if loading}
    <div class="grid gap-4 md:grid-cols-2">
      <Skeleton class="h-48" />
      <Skeleton class="h-48" />
    </div>
  {:else if error}
    <p class="text-destructive">{error}</p>
  {:else if dashboard}
    <div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_322px] items-start">
      <!-- ── Main column ── -->
      <div class="space-y-6">
        <!-- Personalized recap of the latest race -->
        {#if latestRace}
          <RecapCard raceId={latestRace.race_id} raceName={latestRace.race_name} />
        {/if}

    <!-- Followed drivers -->
    <section class="space-y-3">
      <div class="flex items-baseline justify-between">
        <h2 class="text-lg font-semibold">Followed drivers</h2>
        <a href="/drivers" class="text-sm text-primary hover:underline">Browse drivers →</a>
      </div>
      {#if dashboard.followed_drivers.length === 0}
        <Card class="p-8 text-center text-muted-foreground">
          <p>You're not following any drivers yet.</p>
          <p class="text-sm mt-1">
            <a href="/drivers" class="text-primary hover:underline">Pick up to 3 drivers</a>
            to track their results here.
          </p>
        </Card>
      {:else}
        <div class="grid gap-4 sm:grid-cols-2">
          {#each dashboard.followed_drivers as fd (fd.driver.driver_id)}
            <Card class="p-5">
              <div class="flex items-start justify-between mb-2">
                <a
                  href="/drivers/{fd.driver.driver_id}"
                  class="font-semibold hover:text-primary transition-colors"
                >
                  {fd.driver.given_name} {fd.driver.family_name}
                </a>
                {#if fd.current_standing}
                  <Badge variant={fd.current_standing.position === 1 ? 'success' : 'secondary'}>
                    P{fd.current_standing.position}
                  </Badge>
                {/if}
              </div>
              {#if fd.driver.nationality}
                <div class="text-xs text-muted-foreground">{fd.driver.nationality}</div>
              {/if}
              {#if fd.current_standing}
                <div class="mt-3 text-sm">
                  <span class="font-medium">{fd.current_standing.points}</span>
                  <span class="text-muted-foreground"> pts · {fd.current_standing.wins} wins</span>
                </div>
              {/if}
              {#if fd.recent_results.length > 0}
                <ul class="mt-4 space-y-1 text-xs">
                  {#each fd.recent_results as r (r.race_id)}
                    <li class="flex justify-between gap-2">
                      <a
                        href="/races/{r.race_id}"
                        class="truncate text-muted-foreground hover:text-foreground"
                      >
                        {r.race_name}
                      </a>
                      <span class="font-medium">{ordinal(r.position)}</span>
                    </li>
                  {/each}
                </ul>
              {/if}
            </Card>
          {/each}
        </div>
      {/if}
    </section>

    <!-- Followed constructors -->
    <section class="space-y-3">
      <div class="flex items-baseline justify-between">
        <h2 class="text-lg font-semibold">Followed teams</h2>
        <a href="/constructors" class="text-sm text-primary hover:underline">Browse teams →</a>
      </div>
      {#if dashboard.followed_constructors.length === 0}
        <Card class="p-8 text-center text-muted-foreground">
          <p>You're not following any teams yet.</p>
          <p class="text-sm mt-1">
            <a href="/constructors" class="text-primary hover:underline">Pick up to 2 teams</a>
            to track them here.
          </p>
        </Card>
      {:else}
        <div class="grid gap-4 md:grid-cols-2">
          {#each dashboard.followed_constructors as fc (fc.constructor.constructor_id)}
            <Card class="p-5">
              <div class="flex items-start justify-between mb-2">
                <a
                  href="/constructors/{fc.constructor.constructor_id}"
                  class="font-semibold hover:text-primary transition-colors"
                >
                  {fc.constructor.name}
                </a>
                {#if fc.current_standing}
                  <Badge variant={fc.current_standing.position === 1 ? 'success' : 'secondary'}>
                    P{fc.current_standing.position}
                  </Badge>
                {/if}
              </div>
              {#if fc.constructor.nationality}
                <div class="text-xs text-muted-foreground">{fc.constructor.nationality}</div>
              {/if}
              {#if fc.current_standing}
                <div class="mt-3 text-sm">
                  <span class="font-medium">{fc.current_standing.points}</span>
                  <span class="text-muted-foreground"> pts · {fc.current_standing.wins} wins</span>
                </div>
              {/if}
            </Card>
          {/each}
        </div>
      {/if}
    </section>
      </div>
      <!-- /main -->

      <!-- ── Rail ── -->
      <aside class="space-y-6">
        <Card class="p-5">
          <p class="text-[11px] font-extrabold uppercase tracking-[0.14em] text-muted-foreground mb-2">
            Next race
          </p>
          {#if dashboard.next_race}
            <a
              href="/races/{dashboard.next_race.id}"
              class="text-lg font-extrabold hover:text-primary transition-colors"
              style:letter-spacing="-0.02em"
            >
              {dashboard.next_race.name}
            </a>
            <div class="text-sm text-muted-foreground mt-1">
              Round {dashboard.next_race.round} · {dashboard.next_race.circuit.name}
            </div>
            <div class="text-sm text-muted-foreground">{formatDate(dashboard.next_race.date)}</div>
          {:else}
            <p class="text-sm text-muted-foreground">No upcoming races scheduled.</p>
          {/if}
        </Card>

        {#if dashboard.followed_drivers.length + dashboard.followed_constructors.length > 0}
          <Card class="p-5">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-extrabold tracking-tight">Who you follow</h3>
              <span class="text-xs text-muted-foreground">
                {dashboard.followed_drivers.length + dashboard.followed_constructors.length}
              </span>
            </div>
            <div class="flex flex-col">
              {#each dashboard.followed_drivers as fd (fd.driver.driver_id)}
                <a
                  href="/drivers/{fd.driver.driver_id}"
                  class="flex items-center gap-3 py-2.5 border-b border-border last:border-0 group"
                >
                  <span
                    class="h-8 w-8 rounded-[10px] grid place-items-center text-[11px] font-extrabold shrink-0"
                    style="background: var(--sp-sand-200); color: var(--sp-sand-600)"
                  >{initials(fd.driver.given_name, fd.driver.family_name)}</span>
                  <span class="min-w-0 flex-1">
                    <span class="block text-sm font-bold truncate group-hover:text-primary transition-colors">
                      {fd.driver.given_name} {fd.driver.family_name}
                    </span>
                    <span class="block text-[11.5px] text-muted-foreground">
                      Formula 1{#if fd.current_standing} · P{fd.current_standing.position}{/if}
                    </span>
                  </span>
                  {#if fd.current_standing}
                    <span class="sp-fig text-sm ml-auto">{fd.current_standing.points}</span>
                  {/if}
                </a>
              {/each}
              {#each dashboard.followed_constructors as fc (fc.constructor.constructor_id)}
                <a
                  href="/constructors/{fc.constructor.constructor_id}"
                  class="flex items-center gap-3 py-2.5 border-b border-border last:border-0 group"
                >
                  <span
                    class="h-8 w-8 rounded-[10px] grid place-items-center text-[11px] font-extrabold shrink-0"
                    style="background: var(--sp-sand-200); color: var(--sp-sand-600)"
                  >{initials(fc.constructor.name)}</span>
                  <span class="min-w-0 flex-1">
                    <span class="block text-sm font-bold truncate group-hover:text-primary transition-colors">
                      {fc.constructor.name}
                    </span>
                    <span class="block text-[11.5px] text-muted-foreground">
                      Constructor{#if fc.current_standing} · P{fc.current_standing.position}{/if}
                    </span>
                  </span>
                  {#if fc.current_standing}
                    <span class="sp-fig text-sm ml-auto">{fc.current_standing.points}</span>
                  {/if}
                </a>
              {/each}
            </div>
          </Card>
        {/if}
      </aside>
    </div>
  {/if}
</div>
