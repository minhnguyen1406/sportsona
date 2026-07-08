<script lang="ts">
  import '../app.css';
  import Logo from '$lib/components/Logo.svelte';
  import ThemeToggle from '$lib/components/ThemeToggle.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import { auth } from '$lib/stores/auth.svelte';
  import { authApi } from '$lib/api';
  import { follows } from '$lib/follow.svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';

  interface Props {
    children?: import('svelte').Snippet;
  }
  let { children }: Props = $props();

  let mobileOpen = $state(false);

  // Close the mobile drawer on every navigation.
  $effect(() => {
    void $page.url.pathname;
    mobileOpen = false;
  });

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
    follows.reset();
    goto('/login');
  }

  const navLinks = [
    { href: '/ask', label: 'Ask' },
    { href: '/drivers', label: 'Drivers' },
    { href: '/constructors', label: 'Teams' },
    { href: '/seasons', label: 'Seasons' }
  ];

  const authedLinks = [
    { href: '/today', label: 'Today' },
    { href: '/dashboard', label: 'Dashboard' }
  ];

  function isActive(href: string, current: string): boolean {
    if (href === '/') return current === '/';
    return current === href || current.startsWith(`${href}/`);
  }
</script>

<div class="min-h-screen flex flex-col">
  <header class="border-b bg-background sticky top-0 z-10">
    <div class="container mx-auto flex h-16 items-center justify-between gap-6 px-4">
      <div class="flex items-center gap-8">
        <a href="/" class="flex items-center gap-2 shrink-0">
          <Logo variant="wordmark" size={32} />
        </a>
        <nav class="hidden md:flex items-center gap-1 text-sm">
          {#each navLinks as link (link.href)}
            <a
              href={link.href}
              class="px-3 py-1.5 rounded-md transition-colors hover:bg-muted"
              class:text-primary={isActive(link.href, $page.url.pathname)}
              class:font-medium={isActive(link.href, $page.url.pathname)}
            >
              {link.label}
            </a>
          {/each}
          {#if auth.isAuthenticated}
            {#each authedLinks as link (link.href)}
              <a
                href={link.href}
                class="px-3 py-1.5 rounded-md transition-colors hover:bg-muted"
                class:text-primary={isActive(link.href, $page.url.pathname)}
                class:font-medium={isActive(link.href, $page.url.pathname)}
              >
                {link.label}
              </a>
            {/each}
          {/if}
        </nav>
      </div>
      <nav class="flex items-center gap-3 text-sm">
        <ThemeToggle />
        {#if auth.isAuthenticated}
          <span class="text-muted-foreground hidden sm:inline">
            {auth.user?.username ?? '…'}
          </span>
          <span class="hidden md:inline">
            <Button variant="ghost" size="sm" onclick={handleLogout}>Sign out</Button>
          </span>
        {:else}
          <a href="/login" class="text-primary hover:underline hidden md:inline">Sign in</a>
          <a href="/register" class="hidden md:inline">
            <Button size="sm">Get started</Button>
          </a>
        {/if}
        <!-- Mobile hamburger -->
        <button
          type="button"
          class="md:hidden inline-flex items-center justify-center h-10 w-10 rounded-md hover:bg-muted transition-colors"
          aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={mobileOpen}
          onclick={() => (mobileOpen = !mobileOpen)}
        >
          {#if mobileOpen}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          {:else}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
              <path d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          {/if}
        </button>
      </nav>
    </div>

    <!-- Mobile menu drawer -->
    {#if mobileOpen}
      <nav class="md:hidden border-t bg-background px-4 py-3 space-y-1 text-sm">
        {#each navLinks as link (link.href)}
          <a
            href={link.href}
            class="block px-3 py-2.5 rounded-md transition-colors hover:bg-muted"
            class:text-primary={isActive(link.href, $page.url.pathname)}
            class:font-medium={isActive(link.href, $page.url.pathname)}
          >
            {link.label}
          </a>
        {/each}
        {#if auth.isAuthenticated}
          {#each authedLinks as link (link.href)}
            <a
              href={link.href}
              class="block px-3 py-2.5 rounded-md transition-colors hover:bg-muted"
              class:text-primary={isActive(link.href, $page.url.pathname)}
              class:font-medium={isActive(link.href, $page.url.pathname)}
            >
              {link.label}
            </a>
          {/each}
          <div class="border-t pt-2 mt-2 flex items-center justify-between px-3">
            <span class="text-muted-foreground">{auth.user?.username ?? '…'}</span>
            <Button variant="ghost" size="sm" onclick={handleLogout}>Sign out</Button>
          </div>
        {:else}
          <div class="border-t pt-3 mt-2 flex items-center gap-3 px-3">
            <a href="/login" class="text-primary hover:underline">Sign in</a>
            <a href="/register">
              <Button size="sm">Get started</Button>
            </a>
          </div>
        {/if}
      </nav>
    {/if}
  </header>

  <main class="flex-1 container mx-auto px-4 py-8">
    {@render children?.()}
  </main>

  <footer class="border-t py-6 text-center text-sm text-muted-foreground">
    Sportsona — F1 first, more sports coming.
  </footer>
</div>
