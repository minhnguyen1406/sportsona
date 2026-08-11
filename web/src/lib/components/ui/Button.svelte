<script lang="ts" module>
  import type { HTMLButtonAttributes } from 'svelte/elements';
  import { cn } from '$lib/utils';

  export type ButtonVariant =
    | 'default'
    | 'accent'
    | 'destructive'
    | 'outline'
    | 'secondary'
    | 'ghost'
    | 'link';

  export type ButtonSize = 'default' | 'sm' | 'lg' | 'icon';

  const variantClasses: Record<ButtonVariant, string> = {
    default: 'bg-primary text-primary-foreground hover:bg-primary/90',
    accent: 'bg-accent text-accent-foreground hover:bg-accent/90',
    destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
    outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
    secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
    // v3 ghost: transparent with a 1px inset ring, no fill until hover.
    ghost: 'bg-transparent shadow-[inset_0_0_0_1px_hsl(var(--border))] hover:bg-muted',
    link: 'text-primary underline-offset-4 hover:underline'
  };

  // v3 buttons are pills — 800 weight, snug padding. Icon stays square-ish.
  const sizeClasses: Record<ButtonSize, string> = {
    default: 'h-10 px-5 py-2',
    sm: 'h-9 px-4',
    lg: 'h-11 px-6 text-[15px]',
    icon: 'h-10 w-10'
  };

  export function buttonClasses(variant: ButtonVariant = 'default', size: ButtonSize = 'default') {
    const base =
      'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-[13px] font-extrabold ' +
      'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ' +
      'disabled:pointer-events-none disabled:opacity-50';
    return cn(base, variantClasses[variant], sizeClasses[size]);
  }
</script>

<script lang="ts">
  interface Props extends HTMLButtonAttributes {
    variant?: ButtonVariant;
    size?: ButtonSize;
    class?: string;
    children?: import('svelte').Snippet;
  }

  let {
    variant = 'default',
    size = 'default',
    class: className,
    children,
    ...rest
  }: Props = $props();
</script>

<button {...rest} class={cn(buttonClasses(variant, size), className)}>
  {@render children?.()}
</button>
