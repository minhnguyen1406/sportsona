<script lang="ts">
  /**
   * Renders an /ask or /today result set as a polished table.
   *  - Sticky header that survives horizontal scroll
   *  - Alternating row backgrounds + subtle hover
   *  - Monospace + right-aligned numeric cells
   *  - Snake_case → Title Case in headers
   *  - max-h container with internal scroll for tall results
   */
  interface Props {
    columns: string[];
    rows: unknown[][];
    /** Optional banner under the table (e.g. "Truncated to 100 rows"). */
    footnote?: string;
    /** Override the tallest the table can grow before internal scroll. */
    maxHeight?: string;
  }

  let { columns, rows, footnote, maxHeight = '32rem' }: Props = $props();

  function fmt(value: unknown): string {
    if (value === null || value === undefined) return '—';
    if (typeof value === 'number') {
      return Number.isInteger(value) ? String(value) : value.toFixed(2);
    }
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  }

  function isNumeric(value: unknown): boolean {
    return typeof value === 'number';
  }

  function prettyCol(c: string): string {
    return c.replace(/_/g, ' ').replace(/\b\w/g, (ch) => ch.toUpperCase());
  }

  // Detect numeric columns from the first non-null sample, so the whole column
  // can be right-aligned + tabular-num.
  const numericByCol = $derived.by(() => {
    return columns.map((_, j) => {
      for (const row of rows) {
        if (row[j] !== null && row[j] !== undefined) return isNumeric(row[j]);
      }
      return false;
    });
  });
</script>

<div class="space-y-2">
  <div
    class="overflow-auto rounded-md border bg-card"
    style:max-height={maxHeight}
  >
    <table class="w-full text-sm border-collapse">
      <thead class="bg-muted/60 sticky top-0 z-10 backdrop-blur supports-[backdrop-filter]:bg-muted/50">
        <tr>
          {#each columns as col, j (col)}
            <th
              class="px-4 py-2.5 text-xs font-semibold tracking-wide uppercase whitespace-nowrap border-b"
              class:text-right={numericByCol[j]}
              class:text-left={!numericByCol[j]}
            >
              {prettyCol(col)}
            </th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each rows as row, i (i)}
          <tr
            class="border-b last:border-b-0 even:bg-muted/20 hover:bg-muted/40 transition-colors"
          >
            {#each row as cell, j (j)}
              <td
                class="px-4 py-2 whitespace-nowrap"
                class:text-right={numericByCol[j]}
                class:font-mono={numericByCol[j]}
                class:tabular-nums={numericByCol[j]}
                class:text-muted-foreground={cell === null || cell === undefined}
              >
                {fmt(cell)}
              </td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
  {#if footnote}
    <p class="text-xs text-muted-foreground px-1">{footnote}</p>
  {/if}
</div>
