<script lang="ts">
  import { onMount } from 'svelte';
  import Alert from '$lib/components/ui/Alert.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import FollowButton from '$lib/components/FollowButton.svelte';
  import Skeleton from '$lib/components/ui/Skeleton.svelte';
  import { ApiError, type ConstructorResponse, f1Api } from '$lib/api';
  import { auth } from '$lib/stores/auth.svelte';
  import { follows } from '$lib/follow.svelte';

  const PAGE_SIZE = 25;

  let constructors = $state<ConstructorResponse[]>([]);
  let offset = $state(0);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let followError = $state<string | null>(null);

  async function load() {
    loading = true;
    try {
      constructors = await f1Api.listConstructors({ limit: PAGE_SIZE, offset });
    } catch (err) {
      error = err instanceof ApiError ? err.detail : 'Failed to load constructors';
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    load();
    if (auth.isAuthenticated) follows.hydrate();
  });
</script>

<div class="space-y-6">
  <header>
    <h1 class="text-3xl font-bold tracking-tight">Constructors</h1>
    <p class="text-muted-foreground">All F1 teams from 1950 to today.</p>
  </header>

  {#if followError}<Alert variant="destructive">{followError}</Alert>{/if}

  {#if loading}
    <div class="space-y-2">
      {#each Array(8) as _, i (i)}<Skeleton class="h-14" />{/each}
    </div>
  {:else if error}
    <Alert variant="destructive">{error}</Alert>
  {:else if constructors.length === 0}
    <Card class="p-8 text-center text-muted-foreground">No constructors found.</Card>
  {:else}
    <Card class="overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-muted/50 text-left text-muted-foreground">
          <tr>
            <th class="px-4 py-2 font-medium">Team</th>
            <th class="px-4 py-2 font-medium hidden sm:table-cell">Nationality</th>
            <th class="px-4 py-2"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border">
          {#each constructors as c (c.constructor_id)}
            <tr class="hover:bg-muted/30">
              <td class="px-4 py-3">
                <a href="/constructors/{c.constructor_id}" class="font-medium hover:text-primary">
                  {c.name}
                </a>
              </td>
              <td class="px-4 py-3 hidden sm:table-cell text-muted-foreground">
                {c.nationality ?? '—'}
              </td>
              <td class="px-4 py-3 text-right">
                <FollowButton
                  kind="constructor"
                  id={c.constructor_id}
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
        Showing {offset + 1}–{offset + constructors.length}
      </span>
      <div class="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={offset === 0}
          onclick={() => {
            offset = Math.max(0, offset - PAGE_SIZE);
            load();
          }}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={constructors.length < PAGE_SIZE}
          onclick={() => {
            offset += PAGE_SIZE;
            load();
          }}
        >
          Next
        </Button>
      </div>
    </div>
  {/if}
</div>
