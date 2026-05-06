<script lang="ts">
  import Button from '$lib/components/ui/Button.svelte';
  import { ApiError } from '$lib/api';
  import { follows } from '$lib/follow.svelte';
  import { auth } from '$lib/stores/auth.svelte';

  interface Props {
    kind: 'driver' | 'constructor';
    id: string;
    /** Show a compact button suitable for table rows (default: full width) */
    compact?: boolean;
    onerror?: (message: string) => void;
  }

  let { kind, id, compact = false, onerror }: Props = $props();

  const isFollowing = $derived(
    kind === 'driver' ? follows.isFollowingDriver(id) : follows.isFollowingConstructor(id)
  );

  let busy = $state(false);

  async function handle() {
    if (!auth.isAuthenticated) return;
    busy = true;
    try {
      if (kind === 'driver') await follows.toggleDriver(id);
      else await follows.toggleConstructor(id);
    } catch (err) {
      const detail =
        err instanceof ApiError ? err.detail : 'Could not update follow status';
      onerror?.(detail);
    } finally {
      busy = false;
    }
  }
</script>

{#if auth.isAuthenticated}
  <Button
    type="button"
    variant={isFollowing ? 'secondary' : 'default'}
    size={compact ? 'sm' : 'default'}
    disabled={busy}
    onclick={handle}
  >
    {isFollowing ? 'Following' : 'Follow'}
  </Button>
{/if}
