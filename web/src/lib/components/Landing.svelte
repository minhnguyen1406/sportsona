<script lang="ts">
  /**
   * Marketing landing for signed-out visitors — F1-first copy, every figure
   * real. Committed grape ground (Inspiration Study move 06). The standings
   * and next-race surface is LIVE (title-math + calendar endpoints), so the
   * page updates itself when the product does (move 04: the interface is the
   * illustration). Full-bleed via the 100vw trick.
   */
  import { onMount } from 'svelte';
  import Logo from '$lib/components/Logo.svelte';
  import { type RaceResponse, type TitleMath, f1Api, statsApi } from '$lib/api';
  import { formatDate } from '$lib/date';

  const SEASON = new Date().getFullYear();
  let tm = $state<TitleMath | null>(null);
  let next = $state<RaceResponse | null>(null);

  onMount(async () => {
    const [t, r] = await Promise.allSettled([statsApi.titleMath(SEASON), f1Api.listRacesBySeason(SEASON)]);
    if (t.status === 'fulfilled') tm = t.value;
    if (r.status === 'fulfilled') {
      const today = new Date().toISOString().slice(0, 10);
      next = r.value.find((x) => x.date > today) ?? null;
    }
  });
</script>

<div
  class="landing"
  style="width: 100vw; margin-left: calc(50% - 50vw); margin-top: -2rem; margin-bottom: -2rem; background: var(--sp-grape-900); color: var(--sp-sand-100)"
>
  <!-- ══ HERO ══ -->
  <section class="in hero" id="top">
    <p class="eyebrow">Formula 1 first · more sports coming</p>
    <h1 class="h1">You follow F1. You still check <em>five apps</em>.</h1>
    <p class="qual big">
      Sportsona reads every session and gives you one brief — the result, the reason it happened, and where your drivers stand.
      <b>Ask it anything about the record and it shows you where the answer came from.</b>
    </p>
    <div class="hact">
      <a href="/register" class="btn btn--rose btn--lg">Get started free</a>
      <a href="#how" class="btn btn--ghost btn--lg">See how it works</a>
    </div>
    <p class="hnote">Free to use · No card · Every race since 2010, entry lists back to 1950</p>

    <div class="surf">
      <div class="surf__hd">
        <span>The season right now</span>
        <span class="r">{#if tm}Championship after round {tm.after_round}{:else}Formula 1 · {SEASON}{/if}</span>
      </div>
      <div class="g2">
        <div class="tile" style="background: var(--sp-rose-500)">
          <p class="tile__k" style="color: #7a2038">Stat of the day</p>
          <div class="sp-stat" style="font-size: 64px; color: #3a0c1c">5</div>
          <p class="tile__p" style="color: #5c1428"><b style="color: #3a0c1c">Hamilton</b> owns Spa: five Belgian Grand Prix wins since 2010, spanning 2010 to 2024.</p>
        </div>
        <div class="tile">
          <p class="tile__k" style="color: var(--sp-teal-300)">Drivers' championship</p>
          {#if tm}
            {#each tm.drivers.slice(0, 4) as d (d.driver_id)}
              <div class="row"><span class="sp-fig" style="width: 18px; color: var(--sp-grape-200)">{d.position}</span><span class="n">{d.name}</span><span class="sp-fig s" style="font-size: 15px">{d.points}</span></div>
            {/each}
          {:else}
            <p class="tile__p">Live standings load here.</p>
          {/if}
        </div>
        <div class="tile">
          <p class="tile__k">Next up</p>
          {#if next}
            <p class="tile__t">{next.name}</p>
            <p class="tile__p">Round {next.round}{#if next.circuit.country} · {next.circuit.country}{/if} · {formatDate(next.date)}</p>
          {:else}
            <p class="tile__t">Season complete</p>
          {/if}
          {#if tm && !tm.clinched}
            <div style="display: flex; align-items: baseline; gap: 10px; margin-top: 14px">
              <span class="sp-stat" style="font-size: 30px; color: var(--sp-rose-500)">{tm.still_alive}</span>
              <span style="font-size: 12px; font-weight: 700; color: var(--sp-grape-200)">drivers can still win · {tm.remaining_rounds} rounds left</span>
            </div>
          {:else if tm?.leader}
            <p class="tile__p" style="margin-top: 14px"><b>{tm.leader.name}</b> has clinched the title.</p>
          {/if}
        </div>
      </div>
      <p class="illus">Live from the record — the standings and calendar above are real, today.</p>
    </div>
  </section>

  <!-- ══ THE STAT ══ -->
  <section class="in">
    <p class="eyebrow">Not just the number</p>
    <h2 class="claim claim--wide">A stat you can't argue with isn't worth much.</h2>
    <p class="qual">Anyone can show you a figure. Sportsona shows you the things that produced it, so you can decide whether it means anything — and win the argument when it does.</p>
    <div class="surf">
      <div class="surf__hd"><span>Stat of the day</span><span class="r">Belgian Grand Prix · results since 2010</span></div>
      <div class="g2" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))">
        <div>
          <div class="scr"><span class="sp-stat n">5</span><span class="vb">Record</span></div>
          <p class="tile__p" style="font-size: 15px; margin-top: 14px; max-width: 34ch">Belgian Grand Prix wins for Lewis Hamilton since 2010 — the most of anyone in that span.</p>
        </div>
        <div class="tile">
          <p class="tile__k">Why it stands out</p>
          <div class="rs">
            <div><i style="color: var(--sp-volt-500)">↑</i><span>His five wins span a 14-year window, 2010 to 2024</span></div>
            <div><i style="color: var(--sp-volt-500)">↑</i><span>Verstappen's three all came in a tight run, 2021 to 2023</span></div>
            <div><i style="color: var(--sp-grape-200)">→</i><span>Vettel needed seven years (2011–2018) to collect his three</span></div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ══ HOW ══ -->
  <section class="in" id="how">
    <p class="eyebrow">How it works</p>
    <h2 class="claim claim--wide">Three steps, then it runs itself.</h2>

    <div class="step">
      <span class="step__n sp-fig">01</span>
      <div>
        <h3>Tell it who you follow.</h3>
        <p>Up to three drivers and two teams. <b>Your people glow in every standings table</b>, and everything after this point — recaps, the morning stat, your dashboard — is built from that list.</p>
      </div>
      <div class="step__fig tile">
        <p class="tile__k">Who you follow · 3</p>
        <div class="row"><span class="n">Charles Leclerc</span><span class="sub">Ferrari</span></div>
        <div class="row"><span class="n">Lando Norris</span><span class="sub">McLaren</span></div>
        <div class="row"><span class="n">Max Verstappen</span><span class="sub">Red Bull Racing</span></div>
      </div>
    </div>

    <div class="step">
      <span class="step__n sp-fig">02</span>
      <div>
        <h3>Read one recap instead of five feeds.</h3>
        <p>After every race, a recap written around <b>your</b> drivers — the reason it happened, not just the classification — in three minutes. Plus one stat each morning you didn't know.</p>
      </div>
      <div class="step__fig tile">
        <p class="tile__k" style="color: var(--sp-rose-400)">Monaco Grand Prix · your recap</p>
        <p class="tile__t">Leclerc's Monaco nightmare, but Hamilton drags Ferrari home</p>
        <div class="sp-stat" style="font-size: 34px; margin-top: 14px">P2</div>
        <p class="tile__p">Antonelli converted pole into his fifth win of the season. Hamilton launched from P3 to P2, <b>6.2s</b> back — Ferrari's best Sunday of the year. Leclerc, from P4 on the grid, didn't see the flag.</p>
      </div>
    </div>

    <div class="step">
      <span class="step__n sp-fig">03</span>
      <div>
        <h3>Ask it the thing you were about to google.</h3>
        <p>Any question about the record — results back to 2010, entry lists to 1950. <b>Every answer arrives with its sources attached</b>, and says plainly when something isn't in the database.</p>
      </div>
      <div class="step__fig tile">
        <p class="tile__k">Ask</p>
        <p class="tile__t" style="font-size: 15.5px">Who has the most Belgian Grand Prix wins since 2010?</p>
        <p class="tile__p">Hamilton, with <b>5</b> — ahead of Verstappen and Vettel on three each.</p>
        <div class="g2" style="grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; margin-top: 14px">
          <div class="fg"><div class="sp-stat" style="font-size: 24px">5</div><div class="fg__k">Hamilton</div></div>
          <div class="fg"><div class="sp-stat" style="font-size: 24px; color: var(--sp-rose-500)">3</div><div class="fg__k">Verstappen · Vettel</div></div>
        </div>
      </div>
    </div>
  </section>

  <!-- ══ ASK / PROVENANCE ══ -->
  <section class="band" id="ask">
    <div class="in" style="padding-top: 0; padding-bottom: 0">
      <p class="eyebrow">Every answer shows its work</p>
      <h2 class="claim claim--wide">An AI that admits what it doesn't know.</h2>
      <p class="qual">Most sports AI answers in one confident tone whether the number is documented or guessed. Sportsona separates the three cases and labels them, every time. <b>You should always be able to see which parts to trust.</b></p>
      <div class="surf" style="background: var(--sp-grape-900)">
        <div class="surf__hd"><span>Ask</span><span class="r">A real answer, with its real sources</span></div>
        <p class="tile__t" style="font-size: 20px; max-width: 34ch">Who has the most Belgian Grand Prix wins since 2010?</p>
        <p class="tile__p" style="font-size: 15px; line-height: 1.68; max-width: 64ch; margin-top: 14px">Lewis Hamilton, with <b>5</b> Belgian Grand Prix victories between 2010 and 2024. Max Verstappen and Sebastian Vettel share second on <b>3</b> apiece. The query read every Belgian GP classification in the record and counted the winners.</p>
        <div style="margin-top: 26px">
          <p class="tile__k" style="margin-bottom: 4px">Where this answer comes from</p>
          <div class="prov">
            <div class="pr"><span class="g" style="background: var(--sp-teal-500)"></span><span class="l">Official race results · 2010–2026</span><span class="s">FIA classification</span></div>
            <div class="pr"><span class="g" style="background: var(--sp-teal-500)"></span><span class="l">Race calendar</span><span class="s">Official schedule</span></div>
            <div class="pr"><span class="g" style="background: var(--sp-teal-500)"></span><span class="l">Driver records</span><span class="s">Official entry lists</span></div>
            <div class="pr"><span class="g" style="background: var(--sp-warning)"></span><span class="l">Totals computed by us from the rows above</span><span class="s">Derived by us</span></div>
            <div class="pr"><span class="g" style="background: var(--sp-sand-500)"></span><span class="l">Sprint race results — not in the database yet</span><span class="s">Not available</span></div>
          </div>
          <div class="leg">
            <span><i style="background: var(--sp-teal-500)"></i>Confirmed in the record</span>
            <span><i style="background: var(--sp-warning)"></i>Derived by us</span>
            <span><i style="background: var(--sp-sand-500)"></i>Not available</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ══ WHAT IT FOLLOWS ══ -->
  <section class="in" id="watch">
    <p class="eyebrow">What it follows</p>
    <h2 class="claim claim--wide">Four things worth knowing every race week.</h2>
    <p class="qual">Not a firehose. The feed answers the four questions you were going to look up anyway, for the drivers and teams on your list.</p>
    <div class="four">
      <div class="f">
        <span class="ic" style="background: var(--sp-rose-500)"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3A0C1C" stroke-width="2.4" stroke-linecap="round"><path d="M3 12h4l3-7 4 14 3-7h4"/></svg></span>
        <b>What happened</b><span>Every race, recapped around the drivers you follow — with the reason behind the result.</span>
      </div>
      <div class="f">
        <span class="ic" style="background: var(--sp-teal-500)"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#04332C" stroke-width="2.4" stroke-linecap="round"><path d="M4 20V10M10 20V4M16 20v-7M22 20h-20"/></svg></span>
        <b>Where you stand</b><span>Standings, points, who can still mathematically win — your drivers highlighted in every table.</span>
      </div>
      <div class="f">
        <span class="ic" style="background: var(--sp-volt-500)"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2E3A03" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/></svg></span>
        <b>What's worth knowing today</b><span>One stat each morning you didn't know, with the evidence behind it.</span>
      </div>
      <div class="f">
        <span class="ic" style="background: var(--sp-sand-100)"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#211228" stroke-width="2.4" stroke-linecap="round"><path d="M4 5h16v11H9l-5 4z"/></svg></span>
        <b>Whatever you ask</b><span>Records, head-to-heads, how Verstappen connects to Fangio in ten teammates — sourced, and honest about the gaps.</span>
      </div>
    </div>
  </section>

  <!-- ══ OBJECTIONS ══ -->
  <section class="band">
    <div class="in" style="padding-top: 0; padding-bottom: 0">
      <p class="eyebrow">Straight answers</p>
      <h2 class="claim claim--wide">The doubts you're having are reasonable.</h2>
      <div class="obj">
        <div class="o">
          <p class="q">I already have the official F1 app. Why another?</p>
          <span class="lbl">Straight answer</span>
          <p class="a">Because it doesn't know who you follow. <b>Sportsona's whole job is the personal layer</b> — a recap angled around your drivers, standings with your rows lit up, and a record you can actually question.</p>
        </div>
        <div class="o">
          <p class="q">Isn't this just an AI writing summaries?</p>
          <span class="lbl">Straight answer</span>
          <p class="a">The writing is the smallest part. The work is in the record behind it — <b>every number is traceable to a source</b>, and when something can't be confirmed the answer says so rather than smoothing over it.</p>
        </div>
        <div class="o">
          <p class="q">Will it tell me who's going to win?</p>
          <span class="lbl">Straight answer</span>
          <p class="a">No. See below — <b>that's a promise we won't make</b>, and anyone making it is guessing with a chart on top.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- ══ LIMITS ══ -->
  <section class="in" id="limits">
    <p class="eyebrow">What we won't do</p>
    <h2 class="claim claim--wide">We can't tell you who's going to win.</h2>
    <p class="qual" style="font-size: 17px; max-width: 62ch">Nobody can, and anyone selling you a prediction engine is selling you a coin flip with a chart on it. We won't offer tips, we won't rank your chances, and we won't dress up a guess as a model.</p>
    <p class="qual" style="font-size: 17px; max-width: 62ch">What we will do is get every number about your drivers straight, in one place, with its source attached — and tell you plainly when the record doesn't go back far enough to say anything useful. <b>The point isn't to predict the sport. It's to know it well enough to argue from facts.</b></p>
    <p class="qual" style="font-size: 17px; max-width: 62ch">And today that means Formula 1 — every race since 2010, entry lists back to 1950. <b>More sports are coming.</b> We'd rather do one properly first.</p>
  </section>

  <!-- ══ CTA ══ -->
  <section class="in cta" id="cta">
    <p class="eyebrow">Start free</p>
    <h2 class="claim">Follow the grid. Check one place.</h2>
    <p class="qual">Pick your drivers, pick your team, and read your first recap after the next race.</p>
    <div class="hact"><a href="/register" class="btn btn--rose btn--lg">Get started free</a></div>
    <p class="hnote">Free to use · No card · Cancel whenever</p>
  </section>

  <footer class="in foot">
    <span class="brand"><Logo variant="wordmark" size={26} /></span>
    <span class="c">© 2026 Sportsona</span>
    <span class="fl"><a href="#how">How it works</a><a href="#limits">What we won't do</a></span>
  </footer>
</div>

<style>
  .landing { font-family: 'Figtree', system-ui, sans-serif; -webkit-font-smoothing: antialiased; }
  .landing a { color: var(--sp-rose-400); text-decoration: none; }
  .landing a:hover { color: #f7b0c0; }
  .in { max-width: 1120px; margin: 0 auto; padding: 96px 40px; }
  @media (max-width: 720px) { .in { padding: 64px 24px; } }
  .band { background: var(--sp-grape-800); padding: 96px 0; }
  @media (max-width: 720px) { .band { padding: 64px 0; } }

  .btn { display: inline-flex; align-items: center; gap: 8px; font-size: 13.5px; font-weight: 800; border: 0; border-radius: 999px; padding: 12px 21px; cursor: pointer; transition: background .16s cubic-bezier(.2,.7,.3,1); }
  .landing .btn--rose { background: var(--sp-rose-500); color: #3a0c1c; } .landing .btn--rose:hover { background: var(--sp-rose-400); color: #3a0c1c; }
  .landing .btn--ghost { background: transparent; color: var(--sp-sand-100); box-shadow: inset 0 0 0 1px var(--sp-grape-600); } .landing .btn--ghost:hover { background: var(--sp-grape-800); color: var(--sp-sand-100); }
  .btn--lg { font-size: 15px; padding: 15px 26px; }

  .eyebrow { font-size: 11px; font-weight: 800; letter-spacing: .18em; text-transform: uppercase; color: var(--sp-rose-400); margin: 0; }
  .claim { font-size: 42px; font-weight: 800; letter-spacing: -.036em; line-height: 1.06; margin: 16px 0 0; max-width: 19ch; text-wrap: balance; }
  .claim--wide { max-width: 26ch; }
  .qual { font-size: 16px; line-height: 1.68; color: var(--sp-grape-200); margin: 18px 0 0; max-width: 56ch; text-wrap: pretty; }
  .qual b { color: var(--sp-sand-100); }
  .qual.big { font-size: 17.5px; max-width: 52ch; }
  @media (max-width: 720px) { .claim { font-size: 32px; max-width: none; } }

  .hero { padding-top: 104px; padding-bottom: 88px; }
  .h1 { font-size: 64px; font-weight: 800; letter-spacing: -.042em; line-height: 1.02; margin: 20px 0 0; max-width: 17ch; text-wrap: balance; }
  .h1 em { font-style: normal; color: var(--sp-rose-500); }
  @media (max-width: 720px) { .h1 { font-size: 40px; max-width: none; } }
  .hact { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 32px; }
  .hnote { font-size: 12.5px; font-weight: 600; color: var(--sp-grape-200); margin: 18px 0 0; }

  .surf { background: var(--sp-grape-800); border-radius: 26px; padding: 26px; margin-top: 48px; }
  .surf__hd { display: flex; align-items: center; gap: 10px; font-size: 10.5px; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; color: var(--sp-grape-200); margin-bottom: 18px; }
  .surf__hd .r { margin-left: auto; font-weight: 700; letter-spacing: .04em; text-transform: none; font-size: 11.5px; }
  .g2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(268px, 1fr)); gap: 16px; }
  .tile { background: var(--sp-grape-700); border-radius: 20px; padding: 20px; }
  .tile__k { font-size: 10px; font-weight: 800; letter-spacing: .15em; text-transform: uppercase; color: var(--sp-grape-200); margin: 0 0 10px; }
  .tile__t { font-size: 17px; font-weight: 800; letter-spacing: -.022em; line-height: 1.24; margin: 0; text-wrap: balance; }
  .tile__p { font-size: 13px; line-height: 1.55; color: var(--sp-grape-200); margin: 8px 0 0; }
  .tile__p b { color: var(--sp-sand-100); }
  .illus { font-size: 11px; font-weight: 700; color: var(--sp-grape-200); margin: 12px 0 0; font-style: italic; }

  .row { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid var(--sp-grape-600); }
  .row:last-child { border-bottom: 0; padding-bottom: 0; }
  .row .n { font-size: 13px; font-weight: 700; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--sp-sand-100); }
  .row .s { font-size: 16px; color: var(--sp-sand-100); }
  .row .sub { font-size: 11.5px; font-weight: 700; color: var(--sp-grape-200); }

  .scr { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; }
  .scr .n { font-size: 76px; color: var(--sp-rose-500); }
  .scr .vb { font-size: 11.5px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; padding: 6px 13px; border-radius: 999px; background: var(--sp-rose-500); color: #3a0c1c; }
  .rs { display: flex; flex-direction: column; gap: 9px; margin-top: 20px; }
  .rs div { display: grid; grid-template-columns: 16px 1fr; gap: 11px; font-size: 14px; line-height: 1.55; color: var(--sp-grape-200); }
  .rs i { font-style: normal; font-weight: 900; font-size: 13px; }

  .prov { display: flex; flex-direction: column; margin-top: 6px; }
  .pr { display: grid; grid-template-columns: 16px 1fr auto; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--sp-grape-600); font-size: 13.5px; }
  .pr:last-child { border-bottom: 0; }
  .pr .g { width: 9px; height: 9px; border-radius: 50%; }
  .pr .l { color: var(--sp-grape-200); }
  .pr .s { font-size: 11.5px; font-weight: 700; color: var(--sp-grape-200); }
  .leg { display: flex; gap: 18px; flex-wrap: wrap; margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--sp-grape-600); font-size: 11.5px; font-weight: 700; color: var(--sp-grape-200); }
  .leg span { display: flex; align-items: center; gap: 7px; }
  .leg i { width: 8px; height: 8px; border-radius: 50%; display: block; }

  .step { display: grid; grid-template-columns: 64px minmax(0, 1fr) minmax(0, 1.05fr); gap: 34px; align-items: start; padding: 44px 0; border-top: 1px solid var(--sp-grape-600); }
  @media (max-width: 900px) { .step { grid-template-columns: 44px minmax(0, 1fr); gap: 20px; } .step__fig { grid-column: 1 / -1; } }
  .step__n { font-size: 15px; font-weight: 900; letter-spacing: -.02em; color: var(--sp-rose-500); }
  .step h3 { font-size: 25px; font-weight: 800; letter-spacing: -.028em; line-height: 1.16; margin: 0; text-wrap: balance; }
  .step p { font-size: 14.5px; line-height: 1.66; color: var(--sp-grape-200); margin: 12px 0 0; text-wrap: pretty; }
  .step p b { color: var(--sp-sand-100); }
  /* Tile typography must win over the step's prose rule (.step p). */
  .landing .step .tile__k { font-size: 10px; font-weight: 800; letter-spacing: .15em; line-height: 1.4; color: var(--sp-grape-200); margin: 0 0 10px; }
  .landing .step .tile__p { font-size: 13px; line-height: 1.55; margin: 8px 0 0; }
  .landing .step .tile__t { font-size: 17px; }
  .fg { background: var(--sp-grape-800); border-radius: 10px; padding: 12px; }
  .fg__k { font-size: 9.5px; font-weight: 800; letter-spacing: .09em; text-transform: uppercase; color: var(--sp-grape-200); margin-top: 3px; }

  .four { display: grid; grid-template-columns: repeat(auto-fit, minmax(232px, 1fr)); gap: 16px; margin-top: 44px; }
  .f { background: var(--sp-grape-800); border-radius: 20px; padding: 24px; display: flex; flex-direction: column; gap: 9px; min-height: 168px; }
  .f .ic { width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center; margin-bottom: 4px; }
  .f b { font-size: 16.5px; font-weight: 800; letter-spacing: -.022em; }
  .f span:not(.ic) { font-size: 13.5px; line-height: 1.55; color: var(--sp-grape-200); margin-top: auto; }

  .obj { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-top: 44px; }
  .o { background: var(--sp-grape-700); border-radius: 20px; padding: 24px; display: flex; flex-direction: column; gap: 12px; }
  .o .q { font-size: 17px; font-weight: 800; letter-spacing: -.022em; line-height: 1.3; margin: 0; text-wrap: balance; }
  .o .a { font-size: 13.5px; line-height: 1.62; color: var(--sp-grape-200); margin: 0; }
  .o .a b { color: var(--sp-sand-100); }
  .o .lbl { font-size: 9.5px; font-weight: 900; letter-spacing: .15em; text-transform: uppercase; color: var(--sp-rose-400); }

  .cta { text-align: center; }
  .cta .claim { max-width: 24ch; margin-left: auto; margin-right: auto; font-size: 46px; }
  .cta .qual { margin-left: auto; margin-right: auto; max-width: 48ch; }
  .cta .hact { justify-content: center; }
  @media (max-width: 720px) { .cta .claim { font-size: 32px; } }

  .foot { border-top: 1px solid var(--sp-grape-600); padding-top: 36px; padding-bottom: 56px; display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
  .foot .brand { color: var(--sp-sand-100); }
  .foot .c { font-size: 12.5px; color: var(--sp-grape-200); }
  .foot .fl { margin-left: auto; display: flex; gap: 22px; }
  .foot .fl a { font-size: 12.5px; font-weight: 600; color: var(--sp-grape-200); }
  .foot .fl a:hover { color: var(--sp-sand-100); }
</style>
