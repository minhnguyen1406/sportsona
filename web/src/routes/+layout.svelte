<script lang="ts">
  import '../app.css';
  import Logo from '$lib/components/Logo.svelte';
  import ThemeToggle from '$lib/components/ThemeToggle.svelte';
  import SearchBox from '$lib/components/SearchBox.svelte';
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
    { href: '/connect', label: 'Connect' },
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

  const avatarInitial = $derived((auth.user?.username?.[0] ?? '?').toUpperCase());

  // Nav pill classes — idle grape-200, hover grape-600, active filled sand pill.
  const navBase =
    'px-4 py-2 rounded-full text-sm font-bold transition-colors';
  function navClass(active: boolean): string {
    return active
      ? `${navBase} bg-[var(--sp-sand-100)] text-[var(--sp-grape-700)]`
      : `${navBase} text-[var(--sp-grape-200)] hover:bg-[var(--sp-grape-600)] hover:text-[var(--sp-sand-100)]`;
  }
</script>

<div class="min-h-screen flex flex-col">
  <header
    class="sticky top-0 z-10 text-[var(--sp-sand-100)]"
    style="background: var(--sp-grape-700)"
  >
    <div class="container mx-auto flex h-[66px] items-center justify-between gap-6 px-4">
      <div class="flex items-center gap-6">
        <a href="/" class="flex items-center gap-2 shrink-0">
          <Logo variant="wordmark" size={30} />
        </a>
        <nav class="hidden md:flex items-center gap-1">
          {#each navLinks as link (link.href)}
            <a href={link.href} class={navClass(isActive(link.href, $page.url.pathname))}>
              {link.label}
            </a>
          {/each}
          {#if auth.isAuthenticated}
            {#each authedLinks as link (link.href)}
              <a href={link.href} class={navClass(isActive(link.href, $page.url.pathname))}>
                {link.label}
              </a>
            {/each}
          {/if}
        </nav>
      </div>

      <nav class="flex items-center gap-3">
        <div class="hidden lg:block"><SearchBox variant="header" /></div>
        <ThemeToggle />
        {#if auth.isAuthenticated}
          <button
            type="button"
            onclick={handleLogout}
            title="Sign out ({auth.user?.username ?? ''})"
            aria-label="Account — sign out"
            class="hidden md:grid h-9 w-9 place-items-center rounded-full font-extrabold text-sm"
            style="background: var(--sp-rose-500); color: var(--sp-on-rose)"
          >
            {avatarInitial}
          </button>
        {:else}
          <a
            href="/login"
            class="hidden md:inline text-sm font-bold text-[var(--sp-grape-200)] hover:text-[var(--sp-sand-100)]"
          >
            Sign in
          </a>
          <a href="/register" class="hidden md:inline">
            <Button variant="accent" size="sm">Get started</Button>
          </a>
        {/if}
        <!-- Mobile hamburger -->
        <button
          type="button"
          class="md:hidden inline-flex items-center justify-center h-10 w-10 rounded-full hover:bg-[var(--sp-grape-600)] transition-colors"
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

    <!-- Mobile menu drawer (also grape) -->
    {#if mobileOpen}
      <nav
        class="md:hidden px-4 py-3 space-y-1 text-sm border-t border-[var(--sp-grape-600)]"
        style="background: var(--sp-grape-700)"
      >
        {#each [...navLinks, ...(auth.isAuthenticated ? authedLinks : [])] as link (link.href)}
          <a
            href={link.href}
            class="block px-3 py-2.5 rounded-full font-bold transition-colors {isActive(link.href, $page.url.pathname)
              ? 'bg-[var(--sp-sand-100)] text-[var(--sp-grape-700)]'
              : 'text-[var(--sp-grape-200)] hover:bg-[var(--sp-grape-600)]'}"
          >
            {link.label}
          </a>
        {/each}
        <div class="border-t border-[var(--sp-grape-600)] pt-3 mt-2 flex items-center gap-3 px-3">
          {#if auth.isAuthenticated}
            <span class="text-[var(--sp-grape-200)]">{auth.user?.username ?? '…'}</span>
            <button
              type="button"
              onclick={handleLogout}
              class="ml-auto text-[var(--sp-rose-400)] font-bold"
            >Sign out</button>
          {:else}
            <a href="/login" class="text-[var(--sp-grape-200)] font-bold">Sign in</a>
            <a href="/register" class="ml-auto">
              <Button variant="accent" size="sm">Get started</Button>
            </a>
          {/if}
        </div>
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
