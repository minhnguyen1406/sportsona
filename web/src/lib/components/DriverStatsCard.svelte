<script lang="ts">
  import { onMount } from 'svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import { type FormGuide, type Progression, type Streak, type Streaks, statsApi } from '$lib/api';

  interface Props { driverId: string }
  let { driverId }: Props = $props();

  let form = $state<FormGuide | null>(null);
  let streaks = $state<Streaks | null>(null);
  let prog = $state<Progression | null>(null);

  onMount(async () => {
    const [f, s] = await Promise.allSettled([statsApi.form(driverId), statsApi.streaks(driverId)]);
    if (f.status === 'fulfilled') form = f.value;
    if (s.status === 'fulfilled') streaks = s.value;
    if (form) {
      try { prog = await statsApi.progression(driverId, form.season); } catch { /* optional */ }
    }
  });

  // Sparkline of cumulative points — prefix-sum curve as an SVG polyline.
  // Typed rows so the template's tuple destructuring narrows correctly.
  const streakRows = $derived<[string, Streak | null][]>(
    streaks
      ? [
          ['Win streak', streaks.longest_win_streak],
          ['Podium streak', streaks.longest_podium_streak],
          ['Points streak', streaks.longest_points_streak]
        ]
      : []
  );

  const sparkPoints = $derived.by(() => {
    if (!prog || prog.rounds.length < 2) return '';
    const xs = prog.rounds.map((_, i) => (i / (prog!.rounds.length - 1)) * 100);
    const max = Math.max(...prog.rounds.map((r) => r.cumulative), 1);
    return prog.rounds.map((r, i) => `${xs[i]},${30 - (r.cumulative / max) * 28}`).join(' ');
  });
</script>

{#if form || streaks}
  <Card class="p-5 space-y-4">
    <h3 class="text-sm font-extrabold tracking-tight">By the numbers</h3>

    {#if form}
      <div class="grid grid-cols-3 gap-3">
        <div>
          <div class="sp-stat text-3xl">{form.current_avg}</div>
          <div class="text-[10px] font-extrabold uppercase tracking-[0.08em] text-muted-foreground mt-1">Avg pts, last {form.window}</div>
        </div>
        <div>
          <div class="sp-stat text-3xl" class:text-success={form.momentum > 0} class:text-destructive={form.momentum < 0}>
            {form.momentum > 0 ? '+' : ''}{form.momentum}
          </div>
          <div class="text-[10px] font-extrabold uppercase tracking-[0.08em] text-muted-foreground mt-1">Momentum</div>
        </div>
        <div>
          <div class="sp-stat text-3xl">{form.season}</div>
          <div class="text-[10px] font-extrabold uppercase tracking-[0.08em] text-muted-foreground mt-1">Season</div>
        </div>
      </div>
    {/if}

    {#if prog && sparkPoints}
      <div>
        <svg viewBox="0 0 100 32" class="w-full h-10" preserveAspectRatio="none" aria-label="Cumulative points">
          <polyline points={sparkPoints} fill="none" stroke="currentColor" stroke-width="1.5" class="text-primary" vector-effect="non-scaling-stroke" />
        </svg>
        <div class="text-[11px] text-muted-foreground">Points progression · <span class="sp-fig">{prog.total}</span> total</div>
      </div>
    {/if}

    {#if streaks}
      <dl class="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        {#each streakRows as [label, s] (label)}
          <dt class="text-muted-foreground">{label}</dt>
          <dd class="sp-fig text-right">
            {#if s}{s.length} <span class="font-normal text-xs text-muted-foreground">({s.from.season}{s.from.season !== s.to.season ? `–${s.to.season}` : ''})</span>{:else}—{/if}
          </dd>
        {/each}
        <dt class="text-muted-foreground">Hottest stretch</dt>
        <dd class="sp-fig text-right">+{streaks.hottest_stretch.points_above_average} <span class="font-normal text-xs text-muted-foreground">vs own avg</span></dd>
      </dl>
    {/if}
  </Card>
{/if}
