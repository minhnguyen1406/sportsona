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

  // All proportions are derived from `size` so the mark scales cleanly.
  const radius = $derived(Math.round(size * 0.22));
  const sFontSize = $derived(Math.round(size * 0.85));
  const sLetterSpacing = $derived(Math.round(size * 0.047));
  const dotSize = $derived(Math.max(4, Math.round(size * 0.11)));
  const dotInset = $derived(Math.round(size * 0.14));
  const wordmarkFontSize = $derived(Math.round(size * 0.7));
</script>

{#snippet markBox()}
  <!-- HTML+flex centering: the S sits at the dead-center of the box without
       relying on font baseline math. The dot is absolutely positioned in
       the bottom-right corner. -->
  <span
    class="relative inline-flex items-center justify-center shrink-0"
    style:width="{size}px"
    style:height="{size}px"
    style:background="#1A0F0A"
    style:border-radius="{radius}px"
  >
    <span
      class="block"
      style:color="#F4ECD8"
      style:font-family="Inter, system-ui, sans-serif"
      style:font-weight="900"
      style:font-size="{sFontSize}px"
      style:line-height="1"
      style:letter-spacing="-{sLetterSpacing}px"
    >S</span>
    <span
      class="absolute"
      style:bottom="{dotInset}px"
      style:right="{dotInset}px"
      style:width="{dotSize}px"
      style:height="{dotSize}px"
      style:background="#F47B3F"
      style:border-radius="50%"
    ></span>
  </span>
{/snippet}

{#if variant === 'mark'}
  <span class={cn('inline-block', className)} aria-label="Sportsona">
    {@render markBox()}
  </span>
{:else}
  <span class={cn('inline-flex items-center gap-2', className)} aria-label="Sportsona">
    {@render markBox()}
    <span
      class="font-black tracking-tight text-foreground"
      style:font-size="{wordmarkFontSize}px"
      style:line-height="1"
      style:letter-spacing="-0.04em"
    >Sportsona<span class="text-accent">.</span></span>
  </span>
{/if}
