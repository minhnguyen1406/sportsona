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

{#if variant === 'mark'}
  <svg
    width={size}
    height={size}
    viewBox="0 0 64 64"
    xmlns="http://www.w3.org/2000/svg"
    class={cn(className)}
    aria-label="Sportsona"
  >
    <rect width="64" height="64" rx="14" fill="#1A0F0A" />
    <text
      x="32"
      y="50"
      text-anchor="middle"
      font-family="Inter, system-ui, sans-serif"
      font-weight="900"
      font-size="56"
      fill="#F4ECD8"
      letter-spacing="-3"
    >S</text>
    <circle cx="52" cy="52" r="3.5" fill="#F47B3F" />
  </svg>
{:else}
  <div class={cn('inline-flex items-center gap-2', className)} aria-label="Sportsona">
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect width="64" height="64" rx="14" fill="#1A0F0A" />
      <text
        x="32"
        y="50"
        text-anchor="middle"
        font-family="Inter, system-ui, sans-serif"
        font-weight="900"
        font-size="56"
        fill="#F4ECD8"
        letter-spacing="-3"
      >S</text>
      <circle cx="52" cy="52" r="3.5" fill="#F47B3F" />
    </svg>
    <span
      class="font-black tracking-tight text-foreground"
      style="font-size: {wordmarkFontSize}px; line-height: 1; letter-spacing: -0.04em;"
    >
      Sportsona<span class="text-accent">.</span>
    </span>
  </div>
{/if}
