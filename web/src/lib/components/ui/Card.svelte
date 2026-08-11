<script lang="ts">
  import type { HTMLAttributes } from 'svelte/elements';
  import { cn } from '$lib/utils';

  interface Props extends HTMLAttributes<HTMLDivElement> {
    class?: string;
    children?: import('svelte').Snippet;
  }

  let { class: className, children, ...rest }: Props = $props();
</script>

<!-- v3: 20px radius, flat (no shadow). Border on light; on dark the grape
     surface step separates, so the border goes transparent. -->
<div
  {...rest}
  class={cn(
    'rounded-[20px] border border-border dark:border-transparent bg-card text-card-foreground',
    className
  )}
>
  {@render children?.()}
</div>
