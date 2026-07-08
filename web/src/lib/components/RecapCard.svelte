<script lang="ts">
  /**
   * Personalized race recap card. Fetches on demand (button click) because
   * first-time generation costs an LLM call (~15s); cached recaps resolve
   * instantly. Only render this for authenticated users.
   */
  import Card from '$lib/components/ui/Card.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import { ApiError, type RecapResponse, recapApi } from '$lib/api';

  interface Props {
    raceId: number;
    raceName?: string;
  }
  let { raceId, raceName }: Props = $props();

  let recap = $state<RecapResponse | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);

  // Reset when navigating between races (component instance is reused).
  $effect(() => {
    void raceId;
    recap = null;
    error = null;
    loading = false;
  });

  function messageFromError(err: unknown): string {
    if (!(err instanceof ApiError)) return 'Something went wrong.';
    const raw = err.raw as { detail?: unknown } | null;
    const detail = raw?.detail;
    if (detail && typeof detail === 'object' && 'message' in detail) {
      const m = (detail as { message: unknown }).message;
      if (typeof m === 'string') return m;
    }
    if (typeof err.detail === 'string' && err.detail.trim()) return err.detail;
    return `Request failed (${err.status}).`;
  }

  async function load() {
    if (loading) return;
    loading = true;
    error = null;
    try {
      recap = await recapApi.get(raceId);
    } catch (err) {
      error = messageFromError(err);
    } finally {
      loading = false;
    }
  }

  /** First line of the recap doubles as its headline. */
  const headline = $derived(recap ? recap.content.split('\n')[0] : '');
  const body = $derived(
    recap ? recap.content.split('\n').slice(1).join('\n').trim() : ''
  );
</script>

<Card class="p-6 space-y-4 border-accent/40">
  <div class="flex items-center justify-between gap-3">
    <h2 class="text-xs uppercase tracking-widest text-accent font-semibold">
      Your recap{raceName ? ` — ${raceName}` : ''}
    </h2>
    {#if recap}
      <span class="text-xs text-muted-foreground">{recap.model}</span>
    {/if}
  </div>

  {#if recap}
    <h3 class="text-lg font-bold leading-snug">{headline}</h3>
    <div class="text-sm leading-relaxed whitespace-pre-line">{body}</div>
  {:else if loading}
    <div class="flex items-center gap-3 py-4">
      <Spinner size={20} />
      <p class="text-sm text-muted-foreground">
        Writing your personalized recap — first time takes ~15 seconds…
      </p>
    </div>
  {:else if error}
    <p class="text-sm text-destructive">{error}</p>
    <Button variant="outline" size="sm" onclick={load}>Try again</Button>
  {:else}
    <p class="text-sm text-muted-foreground">
      A race story written for <em>you</em> — angled around the drivers and teams you follow.
    </p>
    <Button variant="accent" size="sm" onclick={load}>Get my recap</Button>
  {/if}
</Card>
