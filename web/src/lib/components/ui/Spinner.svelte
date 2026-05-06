<script lang="ts">
  import { cn } from '$lib/utils';
  interface Props {
    size?: number;
    class?: string;
  }
  let { size = 20, class: className }: Props = $props();
</script>

<svg
  width={size}
  height={size}
  viewBox="0 0 24 24"
  xmlns="http://www.w3.org/2000/svg"
  class={cn('animate-spin text-muted-foreground', className)}
  aria-hidden="true"
>
  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" opacity="0.25" />
  <path
    fill="currentColor"
    d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4H4z"
  />
</svg>
