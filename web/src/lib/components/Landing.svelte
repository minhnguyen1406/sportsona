<script lang="ts">
  /**
   * Marketing landing for signed-out visitors. Committed grape ground
   * (Inspiration Study move 06) — depth from 900/800/700 steps, no borders.
   * Full-bleed: escapes the app container's padding with the 100vw trick.
   */
  import Logo from '$lib/components/Logo.svelte';

</script>

<div
  class="landing"
  style="width: 100vw; margin-left: calc(50% - 50vw); margin-top: -2rem; margin-bottom: -2rem; background: var(--sp-grape-900); color: var(--sp-sand-100)"
>
  <!-- ══ HERO ══ -->
  <section class="in hero" id="top">
    <p class="eyebrow">Every sport, one place</p>
    <h1 class="h1">You follow four sports. You check <em>nine apps</em>.</h1>
    <p class="qual big">
      Sportsona reads every league you care about and gives you one morning brief — the scores, the reason they happened, and where you stand.
      <b>Ask it anything and it shows you where the answer came from.</b>
    </p>
    <div class="hact">
      <a href="/register" class="btn btn--rose btn--lg">Get started free</a>
      <a href="#how" class="btn btn--ghost btn--lg">See how it works</a>
    </div>
    <p class="hnote">Free to use · No card · Follow as many sports as you like</p>

    <div class="surf">
      <div class="surf__hd"><span>Your Tuesday</span><span class="r">4 August · 8 followed</span></div>
      <div class="g2">
        <div class="tile" style="background: var(--sp-rose-500)">
          <p class="tile__k" style="color: #7a2038">Stat of the day</p>
          <div class="sp-stat" style="font-size: 64px; color: #3a0c1c">47<span style="font-size: 36px">%</span></div>
          <p class="tile__p" style="color: #5c1428">of <b style="color: #3a0c1c">Piastri's</b> points came from races he didn't start on the front row.</p>
        </div>
        <div class="tile">
          <p class="tile__k" style="color: var(--sp-teal-300)">Premier League · Final</p>
          <p class="tile__t">Late Ødegaard header settles the derby</p>
          <div style="display: flex; align-items: baseline; gap: 10px; margin-top: 12px">
            <span class="sp-stat" style="font-size: 30px">2–1</span>
            <span style="font-size: 12px; font-weight: 700; color: var(--sp-grape-200)">Arsenal · Chelsea</span>
          </div>
        </div>
        <div class="tile">
          <div class="surf__hd" style="margin-bottom: 8px"><span class="live">Live now</span><span class="r">3</span></div>
          <div class="row"><span class="n">Cincinnati · Sinner</span><span class="sp-fig s">6–4</span><span class="m">S3</span></div>
          <div class="row"><span class="n">Ashes · England</span><span class="sp-fig s">214/6</span><span class="m">D2</span></div>
          <div class="row"><span class="n">Inter Miami</span><span class="sp-fig s">1–1</span><span class="m">62'</span></div>
        </div>
      </div>
      <p class="illus">Illustrative — a real feed follows what you follow.</p>
    </div>
  </section>

  <!-- ══ THE STAT ══ -->
  <section class="in">
    <p class="eyebrow">Not just the number</p>
    <h2 class="claim claim--wide">A stat you can't argue with isn't worth much.</h2>
    <p class="qual">Anyone can show you a figure. Sportsona shows you the three things that produced it, so you can decide whether it means anything — and win the argument when it does.</p>
    <div class="surf">
      <div class="surf__hd"><span>Stat of the day</span><span class="r">Formula 1 · after Round 14</span></div>
      <div class="g2" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))">
        <div>
          <div class="scr"><span class="sp-stat n">47<span style="font-size: 40px">%</span></span><span class="vb">Outlier</span></div>
          <p class="tile__p" style="font-size: 15px; margin-top: 14px; max-width: 34ch">of Oscar Piastri's championship points came from races he didn't start on the front row.</p>
        </div>
        <div class="tile">
          <p class="tile__k">Why it's an outlier</p>
          <div class="rs">
            <div><i style="color: var(--sp-volt-500)">↑</i><span>Nine of his 14 point-scoring races started outside the top two</span></div>
            <div><i style="color: var(--sp-volt-500)">↑</i><span>Two wins from P5 or lower — more than anyone on the grid</span></div>
            <div><i style="color: var(--sp-grape-200)">→</i><span>His team-mate's figure over the same span: 21%</span></div>
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
        <p>Drivers, clubs, players, whole leagues. Four sports or fourteen — <b>the feed narrows to what you actually watch</b>, and everything after this point is built from that list.</p>
      </div>
      <div class="step__fig tile">
        <p class="tile__k">Who you follow · 8</p>
        <div class="row"><span class="n">Lando Norris</span><span class="sub">Formula 1</span></div>
        <div class="row"><span class="n">Arsenal</span><span class="sub">Premier League</span></div>
        <div class="row"><span class="n">Jannik Sinner</span><span class="sub">ATP</span></div>
        <div class="row"><span class="n">England</span><span class="sub">Test cricket</span></div>
      </div>
    </div>

    <div class="step">
      <span class="step__n sp-fig">02</span>
      <div>
        <h3>Read one brief instead of nine feeds.</h3>
        <p>A recap for every result that involved someone on your list, written to be read in three minutes — <b>with the reason it happened, not just the score.</b> Plus one stat each morning you didn't know.</p>
      </div>
      <div class="step__fig tile">
        <p class="tile__k" style="color: var(--sp-rose-400)">Formula 1 · Qualifying · Suzuka</p>
        <p class="tile__t">Verstappen finds two tenths nobody expected</p>
        <div class="sp-stat" style="font-size: 34px; margin-top: 14px">1:28.740</div>
        <p class="tile__p">Red Bull had been fourth quickest all weekend. <b>−0.181s</b> to Norris in P2, with McLaren admitting they had no answer on the softer compound.</p>
      </div>
    </div>

    <div class="step">
      <span class="step__n sp-fig">03</span>
      <div>
        <h3>Ask it the thing you were about to google.</h3>
        <p>Any question, across every sport, back to whenever the records start. <b>Every answer arrives with its sources attached</b> — and says plainly when something can't be confirmed.</p>
      </div>
      <div class="step__fig tile">
        <p class="tile__k">Ask</p>
        <p class="tile__t" style="font-size: 15.5px">How often does pole convert to a win at Suzuka?</p>
        <p class="tile__p">Since 2000, pole converted <b>14 times from 25 races</b> — about 56%, below the modern-era average of 61%.</p>
        <div class="g2" style="grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; margin-top: 14px">
          <div class="fg"><div class="sp-stat" style="font-size: 24px">14</div><div class="fg__k">Pole wins</div></div>
          <div class="fg"><div class="sp-stat" style="font-size: 24px; color: var(--sp-rose-500)">56%</div><div class="fg__k">Conversion</div></div>
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
        <div class="surf__hd"><span>Ask</span><span class="r">Updated today</span></div>
        <p class="tile__t" style="font-size: 20px; max-width: 34ch">How often does pole convert to a win at Suzuka?</p>
        <p class="tile__p" style="font-size: 15px; line-height: 1.68; max-width: 64ch; margin-top: 14px">Since 2000, pole has converted to victory <b>14 times from 25 races</b> at Suzuka — about <b>56%</b>, a little below the modern-era average of 61% across all circuits. The long opening sector gives the car behind a genuine run into Turn 1, and three of the last six races here were won from P2.</p>
        <div style="margin-top: 26px">
          <p class="tile__k" style="margin-bottom: 4px">Where this answer comes from</p>
          <div class="prov">
            <div class="pr"><span class="g" style="background: var(--sp-teal-500)"></span><span class="l">25 races at Suzuka since 2000</span><span class="s">Official results</span></div>
            <div class="pr"><span class="g" style="background: var(--sp-teal-500)"></span><span class="l">14 of them won from pole</span><span class="s">Official results</span></div>
            <div class="pr"><span class="g" style="background: var(--sp-teal-500)"></span><span class="l">Three of the last six won from P2</span><span class="s">Official results</span></div>
            <div class="pr"><span class="g" style="background: var(--sp-warning)"></span><span class="l">61% modern-era average across all circuits</span><span class="s">Derived by us</span></div>
            <div class="pr"><span class="g" style="background: var(--sp-sand-500)"></span><span class="l">Wet-weather subset — too few races to be meaningful</span><span class="s">Not available</span></div>
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

  <!-- ══ WHAT IT WATCHES ══ -->
  <section class="in" id="watch">
    <p class="eyebrow">What it follows</p>
    <h2 class="claim claim--wide">Four things worth knowing every morning.</h2>
    <p class="qual">Not a firehose. The feed answers the four questions you were going to look up anyway, for everyone on your list.</p>
    <div class="four">
      <div class="f">
        <span class="ic" style="background: var(--sp-rose-500)"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3A0C1C" stroke-width="2.4" stroke-linecap="round"><path d="M3 12h4l3-7 4 14 3-7h4"/></svg></span>
        <b>What happened</b><span>Every result involving someone you follow, recapped with the reason behind it.</span>
      </div>
      <div class="f">
        <span class="ic" style="background: var(--sp-teal-500)"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#04332C" stroke-width="2.4" stroke-linecap="round"><path d="M4 20V10M10 20V4M16 20v-7M22 20h-20"/></svg></span>
        <b>Where you stand</b><span>Standings, points, positions gained and lost — your people highlighted in every table.</span>
      </div>
      <div class="f">
        <span class="ic" style="background: var(--sp-volt-500)"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2E3A03" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/></svg></span>
        <b>What's live now</b><span>Scores as they move, only for the matches you'd actually have open.</span>
      </div>
      <div class="f">
        <span class="ic" style="background: var(--sp-sand-100)"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#211228" stroke-width="2.4" stroke-linecap="round"><path d="M4 5h16v11H9l-5 4z"/></svg></span>
        <b>Whatever you ask</b><span>Head-to-heads, records, historical context — sourced, and honest about the gaps.</span>
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
          <p class="q">I already have three sports apps. Why another?</p>
          <span class="lbl">Straight answer</span>
          <p class="a">Because none of them knows about the other two. <b>Sportsona's whole job is the overlap</b> — one brief covering every sport you follow, instead of three feeds each convinced it's the only one you read.</p>
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
    <p class="qual" style="font-size: 17px; max-width: 62ch">What we will do is get every number about your teams straight, in one place, with its source attached — and tell you plainly when the record doesn't go back far enough to say anything useful. <b>The point isn't to predict the sport. It's to know it well enough to argue from facts.</b></p>
  </section>

  <!-- ══ CTA ══ -->
  <section class="in cta" id="cta">
    <p class="eyebrow">Start free</p>
    <h2 class="claim">Follow everything. Check one place.</h2>
    <p class="qual">Pick your sports, pick your people, and read your first brief tomorrow morning.</p>
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
  .live { display: inline-flex; align-items: center; gap: 6px; color: var(--sp-rose-500); }
  .live::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--sp-rose-500); }
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
  .row .m { font-size: 11px; font-weight: 800; color: var(--sp-rose-500); width: 34px; text-align: right; font-variant-numeric: tabular-nums; }
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
