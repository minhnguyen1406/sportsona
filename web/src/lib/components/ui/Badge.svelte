<script lang="ts">
  import type { HTMLAttributes } from 'svelte/elements';
  import { cn } from '$lib/utils';

  type Variant = 'default' | 'secondary' | 'accent' | 'success' | 'destructive' | 'outline';

  interface Props extends HTMLAttributes<HTMLSpanElement> {
    variant?: Variant;
    class?: string;
    children?: import('svelte').Snippet;
  }

  let { variant = 'default', class: className, children, ...rest }: Props = $props();

  const variants: Record<Variant, string> = {
    default: 'bg-primary text-primary-foreground',
    secondary: 'bg-secondary text-secondary-foreground',
    accent: 'bg-accent text-accent-foreground',
    success: 'bg-success text-success-foreground',
    destructive: 'bg-destructive text-destructive-foreground',
    outline: 'border border-border text-foreground'
  };
</script>

<span
  {...rest}
  class={cn(
    'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold',
    variants[variant],
    className
  )}
>
  {@render children?.()}
</span>
