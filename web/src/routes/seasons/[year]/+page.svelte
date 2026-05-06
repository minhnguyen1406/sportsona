<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import Alert from '$lib/components/ui/Alert.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import Skeleton from '$lib/components/ui/Skeleton.svelte';
  import {
    ApiError,
    type ConstructorStandingResponse,
    type DriverStandingResponse,
    type RaceResponse,
    f1Api
  } from '$lib/api';
  import { formatDate } from '$lib/date';

  type Tab = 'races' | 'drivers' | 'constructors';
  let tab = $state<Tab>('races');

  let races = $state<RaceResponse[]>([]);
  let driverStandings = $state<DriverStandingResponse[]>([]);
  let constructorStandings = $state<ConstructorStandingResponse[]>([]);

  let loading = $state(true);
  let error = $state<string | null>(null);

  $effect(() => {
    const year = Number($page.params.year);
    if (!Number.isFinite(year)) return;
    loading = true;
    error = null;

    Promise.allSettled([
      f1Api.listRacesBySeason(year),
      f1Api.driverStandings(year),
      f1Api.constructorStandings(year)
    ])
      .then(([racesR, dsR, csR]) => {
        // Race-not-found 404 means we still want to show standings if those exist;
        // collect a non-fatal error message but don't block the rest.
        if (racesR.status === 'fulfilled') races = racesR.value;
        else if (racesR.reason instanceof ApiError && racesR.reason.status !== 404) {
          error = racesR.reason.detail;
        }

        if (dsR.status === 'fulfilled') driverStandings = dsR.value;
        if (csR.status === 'fulfilled') constructorStandings = csR.value;
      })
      .finally(() => {
        loading = false;
      });
  });

  const year = $derived($page.params.year);
</script>

<div class="space-y-6">
  <header class="flex items-baseline justify-between">
    <div>
      <a href="/seasons" class="text-sm text-primary hover:underline">← All seasons</a>
      <h1 class="text-3xl font-bold tracking-tight mt-1">{year} Season</h1>
    </div>
  </header>

  <nav class="flex gap-1 border-b">
    {#each [['races', 'Races'], ['drivers', 'Driver standings'], ['constructors', 'Constructor standings']] as [t, label]}
      <button
        type="button"
        class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors"
        class:border-primary={tab === t}
        class:text-primary={tab === t}
        class:border-transparent={tab !== t}
        class:text-muted-foreground={tab !== t}
        onclick={() => (tab = t as Tab)}
      >
        {label}
      </button>
    {/each}
  </nav>

  {#if loading}
    <div class="space-y-2">
      {#each Array(8) as _, i (i)}<Skeleton class="h-12" />{/each}
    </div>
  {:else if error}
    <Alert variant="destructive">{error}</Alert>
  {:else}
    {#if tab === 'races'}
      {#if races.length === 0}
        <Card class="p-8 text-center text-muted-foreground">
          No races synced for {year}.
        </Card>
      {:else}
        <Card class="overflow-hidden">
          <table class="w-full text-sm">
            <thead class="bg-muted/50 text-left text-muted-foreground">
              <tr>
                <th class="px-4 py-2 font-medium">#</th>
                <th class="px-4 py-2 font-medium">Race</th>
                <th class="px-4 py-2 font-medium hidden md:table-cell">Circuit</th>
                <th class="px-4 py-2 font-medium hidden sm:table-cell">Date</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              {#each races as r (r.id)}
                <tr class="hover:bg-muted/30">
                  <td class="px-4 py-3 font-mono text-muted-foreground">{r.round}</td>
                  <td class="px-4 py-3">
                    <a href="/races/{r.id}" class="font-medium hover:text-primary">{r.name}</a>
                  </td>
                  <td class="px-4 py-3 hidden md:table-cell text-muted-foreground">
                    {r.circuit.name}
                  </td>
                  <td class="px-4 py-3 hidden sm:table-cell text-muted-foreground">
                    {formatDate(r.date)}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </Card>
      {/if}
    {:else if tab === 'drivers'}
      {#if driverStandings.length === 0}
        <Card class="p-8 text-center text-muted-foreground">
          No driver standings synced for {year}.
        </Card>
      {:else}
        <Card class="overflow-hidden">
          <table class="w-full text-sm">
            <thead class="bg-muted/50 text-left text-muted-foreground">
              <tr>
                <th class="px-4 py-2 font-medium">Pos</th>
                <th class="px-4 py-2 font-medium">Driver</th>
                <th class="px-4 py-2 font-medium hidden sm:table-cell">Wins</th>
                <th class="px-4 py-2 font-medium text-right">Points</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              {#each driverStandings as s (s.id)}
                <tr class="hover:bg-muted/30">
                  <td class="px-4 py-3 font-mono">{s.position}</td>
                  <td class="px-4 py-3">
                    <a
                      href="/drivers/{s.driver.driver_id}"
                      class="font-medium hover:text-primary"
                    >
                      {s.driver.given_name} {s.driver.family_name}
                    </a>
                  </td>
                  <td class="px-4 py-3 hidden sm:table-cell text-muted-foreground">{s.wins}</td>
                  <td class="px-4 py-3 text-right font-medium">{s.points}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </Card>
      {/if}
    {:else if tab === 'constructors'}
      {#if constructorStandings.length === 0}
        <Card class="p-8 text-center text-muted-foreground">
          No constructor standings synced for {year}.
        </Card>
      {:else}
        <Card class="overflow-hidden">
          <table class="w-full text-sm">
            <thead class="bg-muted/50 text-left text-muted-foreground">
              <tr>
                <th class="px-4 py-2 font-medium">Pos</th>
                <th class="px-4 py-2 font-medium">Team</th>
                <th class="px-4 py-2 font-medium hidden sm:table-cell">Wins</th>
                <th class="px-4 py-2 font-medium text-right">Points</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              {#each constructorStandings as s (s.id)}
                <tr class="hover:bg-muted/30">
                  <td class="px-4 py-3 font-mono">{s.position}</td>
                  <td class="px-4 py-3">
                    <a
                      href="/constructors/{s.constructor.constructor_id}"
                      class="font-medium hover:text-primary"
                    >
                      {s.constructor.name}
                    </a>
                  </td>
                  <td class="px-4 py-3 hidden sm:table-cell text-muted-foreground">{s.wins}</td>
                  <td class="px-4 py-3 text-right font-medium">{s.points}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </Card>
      {/if}
    {/if}
  {/if}
</div>
