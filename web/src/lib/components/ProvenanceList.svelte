<script lang="ts">
  /** "Where this answer comes from" — the three-state evidence list from the
   *  brand guide. Colour mapping: teal = confirmed in the record, warning
   *  amber = derived by us, sand = not available. Danger-adjacent states
   *  always carry the word, never colour alone. */
  import type { Provenance } from '$lib/api';

  interface Props { items: Provenance[] }
  let { items }: Props = $props();

  const dot: Record<Provenance['state'], string> = {
    confirmed: 'var(--sp-teal-500)',
    derived: 'var(--sp-warning)',
    unavailable: 'var(--sp-sand-500)'
  };
</script>

{#if items.length > 0}
  <div>
    <p class="text-[10.5px] font-extrabold uppercase tracking-[0.14em] text-muted-foreground mb-1">
      Where this answer comes from
    </p>
    <div class="flex flex-col">
      {#each items as it, i (i)}
        <div class="grid grid-cols-[16px_1fr_auto] items-center gap-3 py-2 border-b border-border last:border-0 text-[13.5px]">
          <span class="h-[9px] w-[9px] rounded-full" style="background: {dot[it.state]}"></span>
          <span class="text-foreground/90">{it.label}</span>
          <span class="text-[11.5px] font-bold text-muted-foreground">{it.source}</span>
        </div>
      {/each}
    </div>
    <div class="flex flex-wrap gap-4 mt-3 pt-3 border-t border-border text-[11.5px] font-bold text-muted-foreground">
      <span class="flex items-center gap-2"><i class="h-2 w-2 rounded-full" style="background: var(--sp-teal-500)"></i>Confirmed in the record</span>
      <span class="flex items-center gap-2"><i class="h-2 w-2 rounded-full" style="background: var(--sp-warning)"></i>Derived by us</span>
      <span class="flex items-center gap-2"><i class="h-2 w-2 rounded-full" style="background: var(--sp-sand-500)"></i>Not available</span>
    </div>
  </div>
{/if}
