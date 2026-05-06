<script lang="ts">
  import { goto } from '$app/navigation';
  import Alert from '$lib/components/ui/Alert.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import Input from '$lib/components/ui/Input.svelte';
  import Label from '$lib/components/ui/Label.svelte';
  import Logo from '$lib/components/Logo.svelte';
  import { ApiError, authApi } from '$lib/api';
  import { auth } from '$lib/stores/auth.svelte';

  let email = $state('');
  let password = $state('');
  let submitting = $state(false);
  let error = $state<string | null>(null);

  async function onSubmit(event: Event) {
    event.preventDefault();
    error = null;
    submitting = true;
    try {
      const tokens = await authApi.login(email, password);
      auth.setTokens(tokens);
      // Hydrate the profile so the header updates immediately.
      try {
        auth.setUser(await authApi.me());
      } catch {
        /* ignore — token is set, /me hydrates lazily on home */
      }
      await goto('/');
    } catch (err) {
      if (err instanceof ApiError) {
        error = err.detail;
      } else {
        error = 'Network error — is the backend running on localhost:8000?';
      }
    } finally {
      submitting = false;
    }
  }
</script>

<div class="flex items-center justify-center py-12">
  <Card class="w-full max-w-md p-8">
    <div class="flex flex-col items-center gap-3 mb-6">
      <Logo size={56} />
      <h1 class="text-2xl font-semibold tracking-tight">Sign in to Sportsona</h1>
      <p class="text-sm text-muted-foreground">Welcome back. Enter your credentials below.</p>
    </div>

    {#if error}
      <Alert variant="destructive" class="mb-4">{error}</Alert>
    {/if}

    <form class="space-y-4" onsubmit={onSubmit}>
      <div class="space-y-2">
        <Label for="email">Email</Label>
        <Input
          id="email"
          type="email"
          autocomplete="email"
          required
          bind:value={email}
          placeholder="you@example.com"
        />
      </div>

      <div class="space-y-2">
        <Label for="password">Password</Label>
        <Input
          id="password"
          type="password"
          autocomplete="current-password"
          required
          bind:value={password}
          placeholder="••••••••"
        />
      </div>

      <Button type="submit" class="w-full" disabled={submitting}>
        {submitting ? 'Signing in…' : 'Sign in'}
      </Button>
    </form>

    <p class="mt-6 text-center text-sm text-muted-foreground">
      Don't have an account yet?
      <a href="/" class="text-primary hover:underline">Get in touch</a>
    </p>
  </Card>
</div>
