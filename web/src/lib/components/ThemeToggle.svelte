<script lang="ts">
  import { themeStore } from '$lib/stores/theme.svelte';
  import { cn } from '$lib/utils';

  interface Props {
    class?: string;
  }
  let { class: className }: Props = $props();

  // Label cycles light → dark → system → light, matching themeStore.cycle().
  const label = $derived(
    themeStore.theme === 'light'
      ? 'Switch to dark mode'
      : themeStore.theme === 'dark'
        ? 'Switch to system theme'
        : 'Switch to light mode'
  );
</script>

<button
  type="button"
  aria-label={label}
  title={label}
  onclick={() => themeStore.cycle()}
  class={cn(
    'inline-flex h-9 w-9 items-center justify-center rounded-md',
    'text-muted-foreground hover:text-foreground hover:bg-muted',
    'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
    className
  )}
>
  {#if themeStore.theme === 'light'}
    <!-- Sun icon -->
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  {:else if themeStore.theme === 'dark'}
    <!-- Moon icon -->
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  {:else}
    <!-- "Auto" / system: half-filled disc — visually communicates "follow the OS." -->
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 3v18" />
      <path d="M12 3a9 9 0 0 0 0 18 z" fill="currentColor" />
    </svg>
  {/if}
</button>
