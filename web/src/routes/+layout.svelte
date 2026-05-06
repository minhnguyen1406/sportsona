<script lang="ts">
  import '../app.css';
  import Logo from '$lib/components/Logo.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import { auth } from '$lib/stores/auth.svelte';
  import { authApi } from '$lib/api';
  import { goto } from '$app/navigation';

  interface Props {
    children?: import('svelte').Snippet;
  }
  let { children }: Props = $props();

  async function handleLogout() {
    if (auth.refreshToken) {
      // Best-effort revoke; don't block UX if the network call fails.
      try {
        await authApi.logout(auth.refreshToken);
      } catch {
        /* ignore */
      }
    }
    auth.clear();
    goto('/login');
  }
</script>

<div class="min-h-screen flex flex-col">
  <header class="border-b bg-background">
    <div class="container mx-auto flex h-16 items-center justify-between px-4">
      <a href="/" class="flex items-center gap-2">
        <Logo variant="wordmark" size={32} />
      </a>
      <nav class="flex items-center gap-4 text-sm">
        {#if auth.isAuthenticated}
          <span class="text-muted-foreground">
            {auth.user?.username ?? '…'}
          </span>
          <Button variant="ghost" size="sm" onclick={handleLogout}>Sign out</Button>
        {:else}
          <a href="/login" class="text-primary hover:underline">Sign in</a>
        {/if}
      </nav>
    </div>
  </header>

  <main class="flex-1 container mx-auto px-4 py-8">
    {@render children?.()}
  </main>

  <footer class="border-t py-6 text-center text-sm text-muted-foreground">
    Sportsona — F1 first, more sports coming.
  </footer>
</div>
