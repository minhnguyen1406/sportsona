<script lang="ts">
  /**
   * One comment plus its replies. The component renders `<svelte:self>` for
   * each reply, so the nested JSON tree draws as a nested UI tree — a DFS
   * pre-order traversal expressed as recursive markup.
   */
  import Button from '$lib/components/ui/Button.svelte';
  import Self from '$lib/components/CommentNode.svelte';
  import { ApiError, type CommentNode, commentsApi } from '$lib/api';
  import { auth } from '$lib/stores/auth.svelte';
  import { formatDate } from '$lib/date';

  interface Props {
    node: CommentNode;
    raceId: number;
    reload: () => void;
    /** Nesting depth — caps the indent so deep threads don't march off-screen. */
    depth?: number;
  }
  let { node, raceId, reload, depth = 0 }: Props = $props();

  let showReply = $state(false);
  let replyText = $state('');
  let busy = $state(false);
  let err = $state<string | null>(null);

  const isOwn = $derived(auth.user?.id === node.user_id && !node.is_deleted);
  const canReply = $derived(auth.isAuthenticated && !node.is_deleted);
  const indent = $derived(Math.min(depth, 6)); // stop indenting past 6 deep

  async function submitReply() {
    const body = replyText.trim();
    if (!body || busy) return;
    busy = true;
    err = null;
    try {
      await commentsApi.add(raceId, body, node.id);
      replyText = '';
      showReply = false;
      reload();
    } catch (e) {
      err = e instanceof ApiError ? e.detail : 'Could not post reply.';
    } finally {
      busy = false;
    }
  }

  async function remove() {
    if (busy) return;
    busy = true;
    try {
      await commentsApi.remove(node.id);
      reload();
    } catch {
      busy = false;
    }
  }
</script>

<div class="pt-4" style:margin-left="{indent > 0 ? 4 : 0}px">
  <div
    class="border-l-2 pl-4"
    class:border-border={depth > 0}
    class:border-transparent={depth === 0}
  >
    <div class="flex items-baseline gap-2 text-sm">
      <span class="font-bold" class:text-muted-foreground={node.is_deleted}>{node.author}</span>
      <span class="text-xs text-muted-foreground">{formatDate(node.created_at)}</span>
    </div>

    <p
      class="text-sm mt-1 whitespace-pre-wrap break-words"
      class:text-muted-foreground={node.is_deleted}
      class:italic={node.is_deleted}
    >
      {node.body}
    </p>

    {#if canReply || isOwn}
      <div class="flex items-center gap-3 mt-1.5 text-xs font-semibold">
        {#if canReply}
          <button class="text-muted-foreground hover:text-foreground" onclick={() => (showReply = !showReply)}>
            {showReply ? 'Cancel' : 'Reply'}
          </button>
        {/if}
        {#if isOwn}
          <button class="text-muted-foreground hover:text-destructive" onclick={remove} disabled={busy}>
            Delete
          </button>
        {/if}
      </div>
    {/if}

    {#if showReply}
      <div class="mt-2 space-y-2">
        <textarea
          bind:value={replyText}
          rows="2"
          maxlength={2000}
          placeholder="Add a reply…"
          class="w-full rounded-[14px] border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        ></textarea>
        {#if err}<p class="text-xs text-destructive">{err}</p>{/if}
        <Button variant="accent" size="sm" onclick={submitReply} disabled={busy || !replyText.trim()}>
          Reply
        </Button>
      </div>
    {/if}

    {#each node.replies as child (child.id)}
      <Self node={child} {raceId} {reload} depth={depth + 1} />
    {/each}
  </div>
</div>
