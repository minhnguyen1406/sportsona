<script lang="ts">
  import { cn } from '$lib/utils';

  interface Props {
    /** ``mark`` = just the icon. ``wordmark`` = icon + "Sportsona." next to it. */
    variant?: 'mark' | 'wordmark';
    /** Height (px) of the icon mark. Wordmark text scales relative to this. */
    size?: number;
    class?: string;
  }

  let { variant = 'mark', size = 40, class: className }: Props = $props();

  // Header lockup ratio from the brand guide: 30px mark : 21px wordmark.
  const wordmarkFontSize = $derived(Math.round(size * 0.7));
</script>

{#snippet markSvg()}
  <!--
    Sportsona mark — "The Rise". Three ascending bars where the tallest grows
    a head: a performance chart and a person are the same object.
    - The head is the trademark; it is ALWAYS rose and never closes the 5-unit
      gap to the bars (that air is what reads as a person, not a bar+bobble).
    - Bars take the contrast colour of the surface: Grape on light, Sand on
      dark. `currentColor` + a theme-aware text colour handles the flip.
    - No gradient, no outline, no stretching — see the brand guide.
  -->
  <svg
    width={size}
    height={size}
    viewBox="0 0 64 64"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden={variant === 'wordmark'}
    aria-label={variant === 'mark' ? 'Sportsona' : undefined}
    class="shrink-0 text-primary dark:text-foreground"
  >
    <g fill="currentColor">
      <rect x="13" y="39" width="9" height="14" rx="4.5" />
      <rect x="27" y="30" width="9" height="23" rx="4.5" />
      <rect x="41" y="25" width="9" height="28" rx="4.5" />
    </g>
    <circle cx="45.5" cy="14" r="6" class="fill-accent" />
  </svg>
{/snippet}

{#if variant === 'mark'}
  <span class={cn('inline-block', className)}>
    {@render markSvg()}
  </span>
{:else}
  <span class={cn('inline-flex items-center gap-2', className)} aria-label="Sportsona">
    {@render markSvg()}
    <span
      class="font-extrabold text-foreground"
      style:font-size="{wordmarkFontSize}px"
      style:line-height="1"
      style:letter-spacing="-0.028em"
    >Sportsona<span class="text-rose-ink">.</span></span>
  </span>
{/if}
