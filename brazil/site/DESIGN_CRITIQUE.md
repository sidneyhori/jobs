Design Critique: index.html — Landing Page Transformation

  Anti-Patterns Verdict: Borderline pass

  The warm editorial palette is good — it doesn't scream "AI-generated." But the structure has tells:
  - Identical metric cards with icon + big number + label (the "hero metric layout" anti-pattern)
  - Everything wrapped in cards — .card, .metric-card, .salary-card, .state-card, .action-card,
  .demo-stat — cards inside cards inside views
  - System font stack only — no typographic personality at all
  - Uniform spacing — 20px/16px/12px everywhere with no rhythm or breathing room
  - Dark mode default with warm accents — better than cyan-on-black, but still the "safe AI" approach

  Overall Impression

  This is a data dashboard pretending to be a website. It launches directly into a dense treemap with 8
  stat blocks, 6 toggle buttons, and a wall of text — with zero onboarding. A first-time visitor has no
  idea what this is, why they should care, or where to start. The current structure is:

  ▎ Nav → (7 tabs that each show raw data)

  What it should be:

  ▎ Hero → "Why this matters" → Interactive previews of each tool → Full tools below or behind
  navigation

  The biggest opportunity is narrative framing — this data tells a compelling story about AI's impact on
   19 million Brazilian jobs. Right now it's a spreadsheet with a nice color scheme.

  What's Working

  1. The treemap itself is genuinely impressive — squarified layout, smooth hover, rich tooltips. It's
  the kind of visualization that makes people lean in. It just needs a better introduction.
  2. Theme system is solid — the CSS token architecture with --border, --overlay-soft, etc. is clean and
   will make the landing page redesign much easier. Light/dark toggle with localStorage persistence
  across pages works well.
  3. The "Perguntar" (Ask) tab is a killer feature — natural language queries over labor data is
  genuinely novel. It's buried as tab 7 of 7, which is criminal. This should be front-and-center.

  Priority Issues

  1. No Landing Experience — Users Are Dropped Into Raw Data

  What: The page opens directly to a dense treemap view with technical controls, two paragraphs of
  methodology, and 8 stat blocks. There's no hero, no value proposition, no narrative entry point.

  Why it matters: A first-time visitor (journalist, policymaker, worker worried about their job) bounces
   in 3 seconds. They see a colored rectangle grid and think "this isn't for me." The page needs to
  answer "What is this?" and "Why should I care?" before showing any data.

  Fix: Add a hero section above the nav-driven views:
  - A clear headline like "Como a IA vai transformar seu emprego?" (How will AI transform your job?)
  - A single compelling stat pulled from the data ("X million jobs at high risk")
  - A search bar for "Minha Ocupação" — the most personal, highest-engagement entry point
  - Scroll down to see curated sections introducing each tool

  Command: /frontend-design — this needs a full landing page structure designed from scratch, wrapping
  the existing views

  ---
  2. Navigation Is an Undifferentiated Tab Bar

  What: 7 equally-weighted tabs + "Insights →" + theme toggle, all in a flat horizontal bar. No
  hierarchy. No indication of what's most important. On mobile, these overflow off-screen with no
  affordance.

  Why it matters: A user scanning "Mapa | Risco x Oportunidade | Minha Ocupação | Demografia | Mapa
  Regional | Ranking | Perguntar" has no idea what path to take. Everything looks equally important,
  which means nothing is.

  Fix: For a landing page format, replace the tab bar with:
  - A slim top bar with site title/logo, theme toggle, and "Insights" link
  - Anchor navigation that highlights as you scroll through sections on the landing page
  - Each section on the landing page has a "Explore full view →" link that opens the deep-dive (the
  current tab views)
  - Consider a sticky side-nav or scroll-spy for the full-page flow

  Command: /distill — simplify the navigation to match a landing page mental model

  ---
  3. No Typographic Identity

  What: System font stack (-apple-system, BlinkMacSystemFont, 'Segoe UI') for everything. 26px h1, 20px
  h2, 14px body, 11px labels — a flat, utilitarian scale with no personality.

  Why it matters: This is editorial content about a socially important topic. System fonts signal
  "utility app" not "publication worth reading." The insights.html page has the same problem — both
  pages need a distinctive display font to create gravitas.

  Fix: Load a distinctive serif or editorial font for headlines (e.g., Fraunces, Playfair Display, or
  Source Serif 4) and keep the system stack for body/UI. Use a more dramatic type scale — the hero
  headline should be 40-48px, section titles 28-32px, creating real contrast.

  Command: /bolder — amplify the typographic hierarchy and visual impact

  ---
  4. Wall of Stats With No Narrative Structure

  What: The treemap view (the default landing) has a stats-row with 8 stat-section blocks dumped
  horizontally. Each view follows the same pattern: h2 → p.section-desc → [data dump]. There's no
  storytelling, no progressive disclosure.

  Why it matters: Data without narrative is noise. "Exposição média: 4,7" means nothing to someone who
  doesn't already understand the scoring system. The page needs to guide users from "here's what's
  happening" to "here's what it means for you."

  Fix: For the landing page format, structure each section as:
  1. Provocative question as section header ("Sua profissão está em risco?")
  2. One key insight in large text
  3. Interactive preview (miniature version of the full view)
  4. "Ver análise completa →" link to the full tab

  Command: /clarify — rewrite section headers and descriptions as narrative, not labels

  ---
  5. Cards Everywhere, Rhythm Nowhere

  What: Every piece of content is wrapped in a card (.card, .metric-card, .salary-card, .state-card,
  .action-card, .demo-stat, .demo-chart-box). All cards have the same border, same radius, same padding.
   The layout is a uniform grid with no visual rhythm.

  Why it matters: When everything is in a card, nothing stands out. The eye has nowhere to rest and no
  hierarchy to follow. A landing page needs sections that breathe — full-width moments, tight data
  clusters, and generous whitespace between major sections.

  Fix: For the landing page, use full-width sections with alternating backgrounds (--bg / --bg2) instead
   of cards. Reserve cards for genuinely contained data (the state grid, the ranking table). Use varied
  vertical spacing — 80px between major sections, 32px within sections, 12px between related items.

  Command: /distill — strip cards, flatten hierarchy, create rhythm through spacing

  ---
  Minor Observations

  - No <meta description> or OG tags — insights.html has them, index.html doesn't. Important for
  sharing.
  - The "Perguntar" feature should be elevated to hero-level prominence — a natural language search bar
  is the most engaging entry point for non-technical users.
  - No footer — no credits, no data source links, no methodology page. A landing page needs closure.
  - All view descriptions are methodology-focused ("Visualização de 626 ocupações da CBO...") — should
  be benefit-focused ("Descubra como a IA afeta sua profissão").
  - padding-bottom: 250px on #view-mapa is a hack — smells like a workaround for content overlap.
  - Inline styles on the Perguntar view (lines 802-807) — should be in the stylesheet.

  Questions to Consider

  - "What if the first thing visitors see is a search bar, not a treemap?" — "Digite sua profissão" is a
   more personal, lower-friction entry than parsing a complex visualization.
  - "What would this look like as a story with chapters?" — Each section revealing a facet of the
  AI-jobs story, scrolling vertically like a longform article, with the interactive tools embedded as
  the illustrations.
  - "Does this need 7 tabs?" — "Mapa" and "Mapa Regional" overlap conceptually. "Ranking" is a table
  view of the same data as the treemap. Could some of these be consolidated?
  - "What's the one thing you want someone to remember after visiting?" — Right now the answer is
  unclear. A landing page forces you to answer that question.