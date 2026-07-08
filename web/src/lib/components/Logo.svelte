<script lang="ts">
  import { cn } from '$lib/utils';

  interface Props {
    /** ``mark`` = just the square icon. ``wordmark`` = icon + "Sportsona." next to it. */
    variant?: 'mark' | 'wordmark';
    /** Side length (px) for the icon mark. Wordmark text scales relative to this. */
    size?: number;
    class?: string;
  }

  let { variant = 'mark', size = 40, class: className }: Props = $props();

  const wordmarkFontSize = $derived(Math.round(size * 0.7));
</script>

{#snippet markSvg()}
  <!--
    Sportsona mark — Warm Ink edition.
    - Background: cocoa gradient #3B1F12 → #150804 (carries the Sportsona
      warm palette: cream + ink + dreamsicle).
    - Italic Inter Black S in dreamsicle #F47B3F. x=28, y=51 baked from
      canvas TextMetrics (corrected for italic side-bearing asymmetry — note
      Chrome reports actualBoundingBoxLeft as a signed distance, so the
      italic S needed a 4-unit leftward correction vs the upright glyph).
    - Faint diagonal racing stripe behind for sport energy.
    - Dreamsicle #F47B3F dot at bottom-right = the "Sportsona." period
      accent. Rhymes with the orange period in the wordmark next to it.
  -->
  <svg
    width={size}
    height={size}
    viewBox="0 0 64 64"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden={variant === 'wordmark'}
    aria-label={variant === 'mark' ? 'Sportsona' : undefined}
    class="shrink-0"
  >
    <defs>
      <linearGradient id="sportsona-mark-bg" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#3B1F12" />
        <stop offset="1" stop-color="#150804" />
      </linearGradient>
    </defs>
    <rect width="64" height="64" rx="14" fill="url(#sportsona-mark-bg)" />
    <path d="M 4 56 L 60 8" stroke="#F47B3F" stroke-width="4" opacity="0.18" />
    <text
      x="28"
      y="51"
      text-anchor="middle"
      font-family="'Inter', system-ui, sans-serif"
      font-weight="900"
      font-style="italic"
      font-size="50"
      fill="#F47B3F"
    >S</text>
    <circle cx="52" cy="52" r="3.5" fill="#F47B3F" />
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
      class="font-black italic tracking-tight text-foreground"
      style:font-size="{wordmarkFontSize}px"
      style:line-height="1"
      style:letter-spacing="-0.04em"
    >Sportsona<span class="text-accent">.</span></span>
  </span>
{/if}
