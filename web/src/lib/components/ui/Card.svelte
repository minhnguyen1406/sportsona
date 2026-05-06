<script lang="ts">
  import type { HTMLAttributes } from 'svelte/elements';
  import { cn } from '$lib/utils';

  interface Props extends HTMLAttributes<HTMLDivElement> {
    class?: string;
    children?: import('svelte').Snippet;
  }

  let { class: className, children, ...rest }: Props = $props();
</script>

<div
  {...rest}
  class={cn('rounded-lg border bg-card text-card-foreground shadow-sm', className)}
>
  {@render children?.()}
</div>
