<script lang="ts">
  /** Race comment section: the compose box + the rendered comment tree. */
  import { onMount } from 'svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import CommentNode from '$lib/components/CommentNode.svelte';
  import { ApiError, type CommentNode as Node, authApi, commentsApi } from '$lib/api';
  import { auth } from '$lib/stores/auth.svelte';

  interface Props {
    raceId: number;
  }
  let { raceId }: Props = $props();

  let nodes = $state<Node[]>([]);
  let loading = $state(true);
  let text = $state('');
  let busy = $state(false);
  let err = $state<string | null>(null);

  // Count every node in the forest (roots + all descendants) for the header.
  function countAll(list: Node[]): number {
    return list.reduce((sum, n) => sum + 1 + countAll(n.replies), 0);
  }
  const total = $derived(countAll(nodes));

  async function reload() {
    try {
      nodes = await commentsApi.list(raceId);
    } catch {
      /* leave the current tree on a transient failure */
    }
  }

  onMount(async () => {
    // Need the user's id to show delete on their own comments.
    if (auth.isAuthenticated && !auth.user) {
      try {
        auth.setUser(await authApi.me());
      } catch {
        /* ignore */
      }
    }
    await reload();
    loading = false;
  });

  async function submit() {
    const body = text.trim();
    if (!body || busy) return;
    busy = true;
    err = null;
    try {
      await commentsApi.add(raceId, body);
      text = '';
      await reload();
    } catch (e) {
      err = e instanceof ApiError ? e.detail : 'Could not post comment.';
    } finally {
      busy = false;
    }
  }
</script>

<section class="space-y-3">
  <div class="flex items-baseline gap-2">
    <h2 class="text-lg font-extrabold tracking-tight">Discussion</h2>
    {#if total > 0}<span class="sp-fig text-sm text-muted-foreground">{total}</span>{/if}
  </div>

  <Card class="p-5 space-y-4">
    {#if auth.isAuthenticated}
      <div class="space-y-2">
        <textarea
          bind:value={text}
          rows="3"
          maxlength={2000}
          placeholder="Share your take on the race…"
          class="w-full rounded-[14px] border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        ></textarea>
        {#if err}<p class="text-xs text-destructive">{err}</p>{/if}
        <div class="flex justify-end">
          <Button variant="accent" size="sm" onclick={submit} disabled={busy || !text.trim()}>
            Post comment
          </Button>
        </div>
      </div>
    {:else}
      <p class="text-sm text-muted-foreground">
        <a href="/login" class="text-primary font-semibold hover:underline">Sign in</a>
        to join the discussion.
      </p>
    {/if}

    {#if loading}
      <div class="flex items-center gap-2 py-4 text-sm text-muted-foreground">
        <Spinner size={16} /> Loading comments…
      </div>
    {:else if nodes.length === 0}
      <p class="text-sm text-muted-foreground py-2">No comments yet. Be the first.</p>
    {:else}
      <div class="divide-y divide-border">
        {#each nodes as node (node.id)}
          <CommentNode {node} {raceId} {reload} />
        {/each}
      </div>
    {/if}
  </Card>
</section>
