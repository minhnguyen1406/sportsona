<script lang="ts">
  import { onMount } from 'svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import { type TitleMath, statsApi } from '$lib/api';

  interface Props { year: number }
  let { year }: Props = $props();
  let tm = $state<TitleMath | null>(null);

  onMount(async () => {
    try { tm = await statsApi.titleMath(year); } catch { /* no standings → hide */ }
  });
</script>

{#if tm && tm.leader}
  <Card class="p-5 space-y-3">
    <div class="flex items-baseline justify-between">
      <h3 class="text-sm font-extrabold tracking-tight">Title math</h3>
      <span class="text-xs text-muted-foreground">after round {tm.after_round} · {tm.remaining_rounds} to go</span>
    </div>
    {#if tm.clinched}
      <p class="text-sm"><span class="font-extrabold">{tm.leader.name}</span> has clinched the championship.</p>
    {:else}
      <p class="text-sm"><span class="sp-fig">{tm.still_alive}</span> drivers can still mathematically win. Max <span class="sp-fig">{tm.max_points_per_round}</span> pts per remaining round{#if tm.remaining_sprints > 0}, plus <span class="sp-fig">8</span> per sprint ({tm.remaining_sprints} left){/if}.</p>
      <ul class="divide-y divide-border text-sm">
        {#each tm.drivers.filter((d) => d.alive).slice(0, 6) as d (d.driver_id)}
          <li class="flex items-center gap-3 py-1.5">
            <span class="sp-fig w-5 text-muted-foreground">{d.position}</span>
            <span class="font-semibold flex-1 truncate">{d.name}</span>
            <span class="sp-fig">{d.points}</span>
            <span class="text-xs text-muted-foreground w-28 text-right">
              {d.needs_per_round === null ? 'leader' : d.needs_per_round <= 0 ? 'leading' : `needs ${d.needs_per_round}/rd`}
            </span>
          </li>
        {/each}
      </ul>
    {/if}
  </Card>
{/if}
