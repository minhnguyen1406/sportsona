<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { ApiError, authApi } from '$lib/api';
  import { auth } from '$lib/stores/auth.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';

  interface Props {
    children?: import('svelte').Snippet;
  }
  let { children }: Props = $props();

  let checking = $state(true);

  onMount(async () => {
    if (!auth.isAuthenticated) {
      await goto('/login');
      return;
    }
    // Hydrate the user profile if we don't have it. /me also serves as a
    // token-validity probe — if it 401s after a refresh attempt, we're out.
    if (!auth.user) {
      try {
        auth.setUser(await authApi.me());
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          auth.clear();
          await goto('/login');
          return;
        }
      }
    }
    checking = false;
  });
</script>

{#if checking}
  <div class="flex items-center justify-center py-24">
    <Spinner size={32} />
  </div>
{:else}
  {@render children?.()}
{/if}
