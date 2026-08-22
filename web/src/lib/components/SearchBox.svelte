<script lang="ts">
  /**
   * Autocomplete input backed by the Trie endpoint. Debounced 120ms so a
   * fast typist fires a few requests, not one per keystroke. Keyboard:
   * ↑/↓ to move, Enter to pick, Esc to close.
   */
  import { goto } from '$app/navigation';
  import { type Suggestion, searchApi } from '$lib/api';

  interface Props {
    placeholder?: string;
    /** Restrict to one kind (e.g. 'driver' for the connect pickers). */
    kind?: 'driver' | 'constructor';
    /** If given, called with the pick instead of navigating to its href. */
    onPick?: (s: Suggestion) => void;
    /** Visual style: 'header' renders on the grape bar; 'field' is a normal input. */
    variant?: 'header' | 'field';
    value?: string;
  }
  let { placeholder = 'Search drivers & teams', kind, onPick, variant = 'field', value = $bindable('') }: Props = $props();

  let items = $state<Suggestion[]>([]);
  let open = $state(false);
  let active = $state(-1);
  let timer: ReturnType<typeof setTimeout> | undefined;
  const listId = `sb-${Math.random().toString(36).slice(2, 8)}`;

  function schedule(q: string) {
    clearTimeout(timer);
    if (!q.trim()) { items = []; open = false; return; }
    timer = setTimeout(async () => {
      try {
        const all = await searchApi.suggest(q, 8);
        items = kind ? all.filter((s) => s.kind === kind) : all;
        open = items.length > 0;
        active = items.length ? 0 : -1;
      } catch { items = []; open = false; }
    }, 120);
  }

  function pick(s: Suggestion) {
    open = false;
    if (onPick) { value = s.label; onPick(s); return; }
    value = '';
    goto(s.href);
  }

  function onKey(e: KeyboardEvent) {
    if (!open) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); active = (active + 1) % items.length; }
    else if (e.key === 'ArrowUp') { e.preventDefault(); active = (active - 1 + items.length) % items.length; }
    else if (e.key === 'Enter' && active >= 0) { e.preventDefault(); pick(items[active]); }
    else if (e.key === 'Escape') { open = false; }
  }

  const inputClass = $derived(
    variant === 'header'
      ? 'w-56 h-9 rounded-full pl-9 pr-3 text-[13px] focus-visible:outline-none focus-visible:ring-2'
      : 'w-full h-11 rounded-full border border-input bg-background pl-10 pr-4 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
  );
  const inputStyle = $derived(
    variant === 'header'
      ? 'background: var(--sp-grape-800); border: 1px solid var(--sp-grape-600); color: var(--sp-sand-100); --tw-ring-color: var(--sp-rose-500)'
      : ''
  );
</script>

<div class="relative">
  <svg class="absolute left-3 top-1/2 -translate-y-1/2 opacity-60" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true">
    <circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>
  </svg>
  <input
    type="text"
    bind:value
    {placeholder}
    autocomplete="off"
    role="combobox"
    aria-expanded={open}
    aria-autocomplete="list"
    aria-controls={listId}
    class={inputClass}
    style={inputStyle}
    oninput={(e) => schedule((e.currentTarget as HTMLInputElement).value)}
    onkeydown={onKey}
    onfocus={() => { if (items.length) open = true; }}
    onblur={() => setTimeout(() => (open = false), 150)}
  />
  {#if open}
    <ul
      id={listId}
      role="listbox"
      class="absolute z-20 mt-2 w-full min-w-64 overflow-hidden rounded-[14px] border border-border bg-popover text-popover-foreground shadow-lg"
    >
      {#each items as s, i (s.kind + s.id)}
        <li role="option" aria-selected={i === active}>
          <button
            type="button"
            class="w-full text-left px-3 py-2 flex items-center gap-3 text-sm transition-colors {i === active ? 'bg-muted' : 'hover:bg-muted/60'}"
            onmousedown={(e) => e.preventDefault()}
            onclick={() => pick(s)}
          >
            <span class="font-semibold truncate">{s.label}</span>
            <span class="ml-auto text-xs text-muted-foreground whitespace-nowrap">{s.sublabel}</span>
          </button>
        </li>
      {/each}
    </ul>
  {/if}
</div>
