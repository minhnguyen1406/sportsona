<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import Alert from '$lib/components/ui/Alert.svelte';
  import Badge from '$lib/components/ui/Badge.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import RecapCard from '$lib/components/RecapCard.svelte';
  import CommentThread from '$lib/components/CommentThread.svelte';
  import Skeleton from '$lib/components/ui/Skeleton.svelte';
  import {
    ApiError,
    type RaceResponse,
    type RaceResultResponse,
    type SprintResultResponse,
    type QualifyingResultResponse,
    f1Api
  } from '$lib/api';
  import { auth } from '$lib/stores/auth.svelte';
  import { formatLongDate } from '$lib/date';

  let race = $state<RaceResponse | null>(null);
  let results = $state<RaceResultResponse[]>([]);
  let sprint = $state<SprintResultResponse[]>([]);
  let qualifying = $state<QualifyingResultResponse[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);

  $effect(() => {
    const id = Number($page.params.id);
    if (!Number.isFinite(id)) {
      error = 'Race not found';
      loading = false;
      return;
    }
    loading = true;
    error = null;
    Promise.allSettled([
      f1Api.getRace(id),
      f1Api.getRaceResults(id),
      f1Api.getSprintResults(id),
      f1Api.getQualifyingResults(id)
    ])
      .then(([raceR, resultsR, sprintR, qualR]) => {
        if (raceR.status === 'fulfilled') race = raceR.value;
        else if (raceR.reason instanceof ApiError) error = raceR.reason.detail;
        if (resultsR.status === 'fulfilled') results = resultsR.value;
        if (sprintR.status === 'fulfilled') sprint = sprintR.value;
        if (qualR.status === 'fulfilled') qualifying = qualR.value;
      })
      .finally(() => (loading = false));
  });

</script>

<div class="space-y-6">
  {#if loading}
    <Skeleton class="h-24" />
    <Skeleton class="h-64" />
  {:else if error}
    <Alert variant="destructive">{error}</Alert>
  {:else if race}
    <header class="space-y-2">
      <a href="/seasons/{race.season}" class="text-sm text-primary hover:underline">
        ← {race.season} season
      </a>
      <div class="flex items-baseline gap-3 flex-wrap">
        <h1 class="text-3xl font-bold tracking-tight">{race.name}</h1>
        <Badge variant="accent">Round {race.round}</Badge>
      </div>
      <div class="text-muted-foreground">
        <a href="/circuits/{race.circuit.circuit_id}" class="hover:text-foreground">
          {race.circuit.name}
        </a>
        {#if race.circuit.country}
          · {race.circuit.country}
        {/if}
        · {formatLongDate(race.date)}
      </div>
    </header>

    {#if auth.isAuthenticated && results.length > 0}
      <RecapCard raceId={race.id} />
    {/if}

    {#if results.length > 0}
      <section class="space-y-2">
        <h2 class="text-lg font-semibold">Results</h2>
        <Card class="overflow-hidden">
          <table class="w-full text-sm">
            <thead class="bg-muted/50 text-left text-muted-foreground">
              <tr>
                <th class="px-4 py-2 font-medium">Pos</th>
                <th class="px-4 py-2 font-medium">Driver</th>
                <th class="px-4 py-2 font-medium hidden md:table-cell">Team</th>
                <th class="px-4 py-2 font-medium hidden sm:table-cell">Grid</th>
                <th class="px-4 py-2 font-medium text-right">Points</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              {#each results as r (r.id)}
                <tr class="hover:bg-muted/30">
                  <td class="px-4 py-3 sp-fig">
                    {r.position_text ?? (r.position ?? '—')}
                  </td>
                  <td class="px-4 py-3">
                    <a
                      href="/drivers/{r.driver.driver_id}"
                      class="font-medium hover:text-primary"
                    >
                      {r.driver.given_name} {r.driver.family_name}
                    </a>
                  </td>
                  <td class="px-4 py-3 hidden md:table-cell text-muted-foreground">
                    <a
                      href="/constructors/{r.constructor.constructor_id}"
                      class="hover:text-foreground"
                    >
                      {r.constructor.name}
                    </a>
                  </td>
                  <td class="px-4 py-3 hidden sm:table-cell text-muted-foreground">
                    {r.grid_position ?? '—'}
                  </td>
                  <td class="px-4 py-3 text-right font-medium">{r.points}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </Card>
      </section>
    {:else}
      <Card class="p-8 text-center text-muted-foreground">
        No race results yet — check back after the race weekend.
      </Card>
    {/if}

    {#if sprint.length > 0}
      <section class="space-y-2">
        <div class="flex items-baseline gap-2">
          <h2 class="text-lg font-semibold">Sprint</h2>
          <span class="text-xs text-muted-foreground">Saturday sprint race</span>
        </div>
        <Card class="overflow-hidden">
          <table class="w-full text-sm">
            <thead class="bg-muted/50 text-left text-muted-foreground">
              <tr>
                <th class="px-4 py-2 font-medium">Pos</th>
                <th class="px-4 py-2 font-medium">Driver</th>
                <th class="px-4 py-2 font-medium hidden md:table-cell">Team</th>
                <th class="px-4 py-2 font-medium hidden sm:table-cell">Grid</th>
                <th class="px-4 py-2 font-medium text-right">Points</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              {#each sprint as r (r.id)}
                <tr class="hover:bg-muted/30">
                  <td class="px-4 py-3 sp-fig">
                    {r.position_text ?? (r.position ?? '—')}
                  </td>
                  <td class="px-4 py-3">
                    <a
                      href="/drivers/{r.driver.driver_id}"
                      class="font-medium hover:text-primary"
                    >
                      {r.driver.given_name} {r.driver.family_name}
                    </a>
                  </td>
                  <td class="px-4 py-3 hidden md:table-cell text-muted-foreground">
                    <a
                      href="/constructors/{r.constructor.constructor_id}"
                      class="hover:text-foreground"
                    >
                      {r.constructor.name}
                    </a>
                  </td>
                  <td class="px-4 py-3 hidden sm:table-cell text-muted-foreground">
                    {r.grid_position ?? '—'}
                  </td>
                  <td class="px-4 py-3 text-right font-medium">{r.points}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </Card>
      </section>
    {/if}

    {#if qualifying.length > 0}
      <section class="space-y-2">
        <h2 class="text-lg font-semibold">Qualifying</h2>
        <Card class="overflow-hidden">
          <table class="w-full text-sm">
            <thead class="bg-muted/50 text-left text-muted-foreground">
              <tr>
                <th class="px-4 py-2 font-medium">Pos</th>
                <th class="px-4 py-2 font-medium">Driver</th>
                <th class="px-4 py-2 font-medium hidden md:table-cell">Team</th>
                <th class="px-4 py-2 font-medium hidden sm:table-cell">Q1</th>
                <th class="px-4 py-2 font-medium hidden sm:table-cell">Q2</th>
                <th class="px-4 py-2 font-medium hidden sm:table-cell">Q3</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              {#each qualifying as q (q.id)}
                <tr class="hover:bg-muted/30">
                  <td class="px-4 py-3 sp-fig">{q.position ?? '—'}</td>
                  <td class="px-4 py-3">
                    <a
                      href="/drivers/{q.driver.driver_id}"
                      class="font-medium hover:text-primary"
                    >
                      {q.driver.given_name} {q.driver.family_name}
                    </a>
                  </td>
                  <td class="px-4 py-3 hidden md:table-cell text-muted-foreground">
                    {q.constructor.name}
                  </td>
                  <td class="px-4 py-3 hidden sm:table-cell sp-fig text-xs">
                    {q.q1_time ?? '—'}
                  </td>
                  <td class="px-4 py-3 hidden sm:table-cell sp-fig text-xs">
                    {q.q2_time ?? '—'}
                  </td>
                  <td class="px-4 py-3 hidden sm:table-cell sp-fig text-xs">
                    {q.q3_time ?? '—'}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </Card>
      </section>
    {/if}

    <CommentThread raceId={race.id} />
  {/if}
</div>
