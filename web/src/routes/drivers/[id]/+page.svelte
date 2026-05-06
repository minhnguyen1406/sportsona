<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import Alert from '$lib/components/ui/Alert.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import FollowButton from '$lib/components/FollowButton.svelte';
  import Skeleton from '$lib/components/ui/Skeleton.svelte';
  import { ApiError, type DriverResponse, f1Api } from '$lib/api';
  import { auth } from '$lib/stores/auth.svelte';
  import { follows } from '$lib/follow.svelte';

  let driver = $state<DriverResponse | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);

  $effect(() => {
    const id = $page.params.id;
    if (!id) return;
    loading = true;
    error = null;
    f1Api
      .getDriver(id)
      .then((d) => (driver = d))
      .catch((err) => (error = err instanceof ApiError ? err.detail : 'Failed to load driver'))
      .finally(() => (loading = false));
  });

  onMount(() => {
    if (auth.isAuthenticated) follows.hydrate();
  });
</script>

<div class="max-w-3xl mx-auto space-y-6">
  <a href="/drivers" class="text-sm text-primary hover:underline">← All drivers</a>

  {#if loading}
    <Skeleton class="h-32" />
  {:else if error}
    <Alert variant="destructive">{error}</Alert>
  {:else if driver}
    <Card class="p-8">
      <div class="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 class="text-3xl font-bold tracking-tight">
            {driver.given_name} {driver.family_name}
          </h1>
          <dl class="mt-3 grid grid-cols-2 gap-x-8 gap-y-1 text-sm">
            <dt class="text-muted-foreground">Nationality</dt>
            <dd>{driver.nationality ?? '—'}</dd>
            <dt class="text-muted-foreground">Date of birth</dt>
            <dd>{driver.date_of_birth ?? '—'}</dd>
            <dt class="text-muted-foreground">Driver ID</dt>
            <dd class="font-mono text-xs">{driver.driver_id}</dd>
          </dl>
        </div>
        <FollowButton kind="driver" id={driver.driver_id} />
      </div>
    </Card>
  {/if}
</div>
