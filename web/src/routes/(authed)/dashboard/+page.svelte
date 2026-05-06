<script lang="ts">
  import { onMount } from 'svelte';
  import Badge from '$lib/components/ui/Badge.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import Skeleton from '$lib/components/ui/Skeleton.svelte';
  import { ApiError, type DashboardResponse, usersApi } from '$lib/api';
  import { auth } from '$lib/stores/auth.svelte';
  import { formatDate } from '$lib/date';

  let dashboard = $state<DashboardResponse | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);

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
</script>

<div class="space-y-8">
  <header class="space-y-1">
    <h1 class="text-3xl font-bold tracking-tight">
      Welcome back, <span class="text-primary">{auth.user?.username ?? '…'}</span>
    </h1>
    <p class="text-muted-foreground">Your followed drivers, teams, and the next race.</p>
  </header>

  {#if loading}
    <div class="grid gap-4 md:grid-cols-2">
      <Skeleton class="h-48" />
      <Skeleton class="h-48" />
    </div>
  {:else if error}
    <p class="text-destructive">{error}</p>
  {:else if dashboard}
    <!-- Next race -->
    <Card class="p-6">
      <div class="flex items-baseline justify-between mb-2">
        <h2 class="text-xs uppercase tracking-wider text-muted-foreground">Next race</h2>
        {#if dashboard.next_race}
          <Badge variant="accent">Round {dashboard.next_race.round}</Badge>
        {/if}
      </div>
      {#if dashboard.next_race}
        <a
          href="/races/{dashboard.next_race.id}"
          class="text-2xl font-semibold hover:text-primary transition-colors"
        >
          {dashboard.next_race.name}
        </a>
        <div class="text-sm text-muted-foreground mt-1">
          {dashboard.next_race.circuit.name}
          {#if dashboard.next_race.circuit.country}
            · {dashboard.next_race.circuit.country}
          {/if}
          · {formatDate(dashboard.next_race.date)}
        </div>
      {:else}
        <p class="text-muted-foreground">No upcoming races scheduled.</p>
      {/if}
    </Card>

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
        <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
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
  {/if}
</div>
