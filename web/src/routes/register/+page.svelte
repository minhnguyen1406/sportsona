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
  let username = $state('');
  let password = $state('');
  let submitting = $state(false);
  let error = $state<string | null>(null);

  async function onSubmit(event: Event) {
    event.preventDefault();
    error = null;
    submitting = true;
    try {
      await authApi.register(email, username, password);
      // Auto-login on success — better UX than asking the user to log in again.
      const tokens = await authApi.login(email, password);
      auth.setTokens(tokens);
      try {
        auth.setUser(await authApi.me());
      } catch {
        /* /me hydrates lazily on home */
      }
      await goto('/dashboard');
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
      <h1 class="text-2xl font-semibold tracking-tight">Create your Sportsona account</h1>
      <p class="text-sm text-muted-foreground">Track your drivers, your teams, your races.</p>
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
        <Label for="username">Username</Label>
        <Input
          id="username"
          type="text"
          autocomplete="username"
          required
          minlength={3}
          maxlength={50}
          bind:value={username}
          placeholder="your_handle"
        />
      </div>

      <div class="space-y-2">
        <Label for="password">Password</Label>
        <Input
          id="password"
          type="password"
          autocomplete="new-password"
          required
          minlength={8}
          maxlength={72}
          bind:value={password}
          placeholder="at least 8 characters"
        />
      </div>

      <Button type="submit" class="w-full" disabled={submitting}>
        {submitting ? 'Creating account…' : 'Create account'}
      </Button>
    </form>

    <p class="mt-6 text-center text-sm text-muted-foreground">
      Already have an account?
      <a href="/login" class="text-primary hover:underline">Sign in</a>
    </p>
  </Card>
</div>
