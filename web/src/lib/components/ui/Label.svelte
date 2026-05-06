<script lang="ts">
  import type { HTMLLabelAttributes } from 'svelte/elements';
  import { cn } from '$lib/utils';

  interface Props extends HTMLLabelAttributes {
    class?: string;
    children?: import('svelte').Snippet;
  }

  let { class: className, children, ...rest }: Props = $props();
</script>

<label
  {...rest}
  class={cn(
    'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
    className
  )}
>
  {@render children?.()}
</label>
