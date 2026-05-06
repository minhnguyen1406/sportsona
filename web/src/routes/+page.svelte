<script lang="ts">
  import { onMount } from 'svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import { auth } from '$lib/stores/auth.svelte';
  import { authApi, ApiError } from '$lib/api';

  // If we have a token but no user yet, hydrate the profile so the header
  // shows the username after a refresh.
  onMount(async () => {
    if (auth.isAuthenticated && !auth.user) {
      try {
        const user = await authApi.me();
        auth.setUser(user);
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          auth.clear();
        }
      }
    }
  });
</script>

<div class="max-w-3xl mx-auto space-y-8">
  <section class="space-y-4 py-8">
    <h1 class="text-4xl font-bold tracking-tight">
      {#if auth.user}
        Welcome back, <span class="text-primary">{auth.user.username}</span>
      {:else}
        Your <span class="text-primary">sports</span>, your <span class="text-accent">persona</span>.
      {/if}
    </h1>
    <p class="text-lg text-muted-foreground">
      Follow drivers and teams. See your standings, your races, your results — all in one place.
      Starting with Formula 1, more sports coming.
    </p>
    <div class="flex gap-3">
      {#if !auth.isAuthenticated}
        <a href="/login">
          <Button size="lg">Sign in</Button>
        </a>
      {/if}
    </div>
  </section>

  <section class="grid gap-4 sm:grid-cols-3">
    <Card class="p-6">
      <div class="text-sm font-semibold text-primary mb-1">Live</div>
      <h3 class="font-semibold mb-1">Race calendar</h3>
      <p class="text-sm text-muted-foreground">
        Upcoming Grands Prix, sessions, and circuit info.
      </p>
    </Card>
    <Card class="p-6">
      <div class="text-sm font-semibold text-accent mb-1">Personalized</div>
      <h3 class="font-semibold mb-1">Followed drivers</h3>
      <p class="text-sm text-muted-foreground">
        Track your favorites' standings and recent results.
      </p>
    </Card>
    <Card class="p-6">
      <div class="text-sm font-semibold text-success mb-1">Historic</div>
      <h3 class="font-semibold mb-1">Every season since 1950</h3>
      <p class="text-sm text-muted-foreground">
        Browse races, results, and standings from F1's full history.
      </p>
    </Card>
  </section>
</div>
