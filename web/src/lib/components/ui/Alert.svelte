<script lang="ts">
  import type { HTMLAttributes } from 'svelte/elements';
  import { cn } from '$lib/utils';

  type Variant = 'default' | 'destructive' | 'success';

  interface Props extends HTMLAttributes<HTMLDivElement> {
    variant?: Variant;
    class?: string;
    children?: import('svelte').Snippet;
  }

  let { variant = 'default', class: className, children, ...rest }: Props = $props();

  const variantClasses: Record<Variant, string> = {
    default: 'bg-background text-foreground border-border',
    destructive:
      'border-destructive/50 text-destructive bg-destructive/10 [&>svg]:text-destructive',
    success: 'border-success/50 text-success bg-success/10 [&>svg]:text-success'
  };
</script>

<div
  role="alert"
  {...rest}
  class={cn(
    'relative w-full rounded-lg border px-4 py-3 text-sm',
    variantClasses[variant],
    className
  )}
>
  {@render children?.()}
</div>
