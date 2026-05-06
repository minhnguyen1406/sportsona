<script lang="ts">
  import { cn } from '$lib/utils';

  interface Props {
    /** Just the icon mark (default), or wordmark */
    variant?: 'mark' | 'wordmark';
    size?: number;
    class?: string;
  }

  let { variant = 'mark', size = 40, class: className }: Props = $props();
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
    <rect width="64" height="64" rx="14" class="fill-primary" />
    <path
      d="M44 22c-3-4-9-5-13-5-7 0-11 4-11 9 0 5 3 7 12 8s11 3 11 8-4 9-12 9c-4 0-9-1-12-5"
      stroke="hsl(var(--primary-foreground))"
      stroke-width="5"
      stroke-linecap="round"
      fill="none"
    />
    <circle cx="50" cy="50" r="5" class="fill-accent" />
  </svg>
{:else}
  <div class={cn('inline-flex items-center gap-2', className)}>
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect width="64" height="64" rx="14" class="fill-primary" />
      <path
        d="M44 22c-3-4-9-5-13-5-7 0-11 4-11 9 0 5 3 7 12 8s11 3 11 8-4 9-12 9c-4 0-9-1-12-5"
        stroke="hsl(var(--primary-foreground))"
        stroke-width="5"
        stroke-linecap="round"
        fill="none"
      />
      <circle cx="50" cy="50" r="5" class="fill-accent" />
    </svg>
    <span class="text-2xl font-bold tracking-tight text-primary">Sportsona</span>
    <span class="text-2xl font-bold leading-none text-accent" aria-hidden="true">.</span>
  </div>
{/if}
