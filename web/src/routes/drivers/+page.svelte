<script lang="ts">
  import { onMount } from 'svelte';
  import Alert from '$lib/components/ui/Alert.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import FollowButton from '$lib/components/FollowButton.svelte';
  import Input from '$lib/components/ui/Input.svelte';
  import Skeleton from '$lib/components/ui/Skeleton.svelte';
  import { ApiError, type DriverResponse, f1Api } from '$lib/api';
  import { auth } from '$lib/stores/auth.svelte';
  import { follows } from '$lib/follow.svelte';

  const PAGE_SIZE = 25;

  let drivers = $state<DriverResponse[]>([]);
  let search = $state('');
  let offset = $state(0);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let followError = $state<string | null>(null);

  let debounceHandle: ReturnType<typeof setTimeout> | null = null;

  async function load() {
    loading = true;
    error = null;
    try {
      drivers = await f1Api.listDrivers({
        search: search || undefined,
        limit: PAGE_SIZE,
        offset
      });
    } catch (err) {
      error = err instanceof ApiError ? err.detail : 'Failed to load drivers';
    } finally {
      loading = false;
    }
  }

  function onSearchChange() {
    if (debounceHandle) clearTimeout(debounceHandle);
    debounceHandle = setTimeout(() => {
      offset = 0;
      load();
    }, 300);
  }

  function nextPage() {
    offset += PAGE_SIZE;
    load();
  }

  function prevPage() {
    offset = Math.max(0, offset - PAGE_SIZE);
    load();
  }

  onMount(() => {
    load();
    if (auth.isAuthenticated) follows.hydrate();
  });
</script>

<div class="space-y-6">
  <header class="flex items-center justify-between">
    <div>
      <h1 class="text-3xl font-bold tracking-tight">Drivers</h1>
      <p class="text-muted-foreground">Browse F1 drivers from 1950 to today.</p>
    </div>
  </header>

  <Card class="p-4">
    <Input
      type="search"
      placeholder="Search by name…"
      bind:value={search}
      oninput={onSearchChange}
    />
  </Card>

  {#if followError}
    <Alert variant="destructive">{followError}</Alert>
  {/if}

  {#if loading}
    <div class="space-y-2">
      {#each Array(8) as _, i (i)}
        <Skeleton class="h-14" />
      {/each}
    </div>
  {:else if error}
    <Alert variant="destructive">{error}</Alert>
  {:else if drivers.length === 0}
    <Card class="p-8 text-center text-muted-foreground">No drivers found.</Card>
  {:else}
    <Card class="overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-muted/50 text-left text-muted-foreground">
          <tr>
            <th class="px-4 py-2 font-medium">Driver</th>
            <th class="px-4 py-2 font-medium hidden sm:table-cell">Nationality</th>
            <th class="px-4 py-2 font-medium hidden md:table-cell">Born</th>
            <th class="px-4 py-2"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border">
          {#each drivers as d (d.driver_id)}
            <tr class="hover:bg-muted/30">
              <td class="px-4 py-3">
                <a href="/drivers/{d.driver_id}" class="font-medium hover:text-primary">
                  {d.given_name} {d.family_name}
                </a>
              </td>
              <td class="px-4 py-3 hidden sm:table-cell text-muted-foreground">
                {d.nationality ?? '—'}
              </td>
              <td class="px-4 py-3 hidden md:table-cell text-muted-foreground">
                {d.date_of_birth ?? '—'}
              </td>
              <td class="px-4 py-3 text-right">
                <FollowButton
                  kind="driver"
                  id={d.driver_id}
                  compact
                  onerror={(msg) => (followError = msg)}
                />
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </Card>

    <div class="flex items-center justify-between text-sm">
      <span class="text-muted-foreground">
        Showing {offset + 1}–{offset + drivers.length}
      </span>
      <div class="flex gap-2">
        <Button variant="outline" size="sm" disabled={offset === 0} onclick={prevPage}>
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={drivers.length < PAGE_SIZE}
          onclick={nextPage}
        >
          Next
        </Button>
      </div>
    </div>
  {/if}
</div>
