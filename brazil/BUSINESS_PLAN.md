# Business Plan: Media + Career Bot Flywheel

## The Thesis

Media coverage → audience → career bot users → affiliate revenue. The insight pills you already have are the content engine. A WhatsApp/web career bot is the monetization layer. Each fuels the other.

---

## Track A: Media Partnerships (weeks 1-3)

### What you ship
You already have 6 editorial-grade articles with charts. Package them for pitching.

### Target outlets (in priority order)
1. **Nexo Jornal** — data-driven, loves interactive embeds, educated audience. Perfect fit.
2. **Folha Dados / Folha de S.Paulo** — biggest reach, has a data team that would appreciate the methodology.
3. **Valor Econômico** — business audience, AI workforce angle resonates with executives.
4. **The Brazilian Report** — English-language, reaches international investors/policy people.
5. **Brasil de Fato** — progressive, would amplify the race/gender inequality angles hard.

### Pitch structure
- Email subject: "Dados inéditos: 626 profissões brasileiras analisadas por exposição à IA"
- Offer 3 formats:
  - **Embed** — they iframe your interactive map directly (you get the link back to your site)
  - **Data column** — monthly "Pílulas de IA e Emprego" column using your auto-generated insights
  - **One-off feature** — the gender gap story (37.7% vs 22.2%) is the strongest standalone piece
- Include 2-3 ready-to-publish insight pills as proof of quality
- Offer exclusive first-publish rights for 1 week to sweeten the deal

### What you need to build
Nothing new for the site. But prep materials:
- A 1-page media kit (PDF) explaining methodology, data sources, team
- 3 social-ready image cards (headline stat + mini chart) for Instagram/LinkedIn/Twitter
- A clean URL for the live site (if not already on a custom domain)

### Success metrics
- 1+ outlet publishes within 4 weeks
- Site traffic spike → capture emails for newsletter
- Social proof for Track B pitches

---

## Track B: Career Bot (weeks 2-6, parallel)

### Core idea
"Mande sua profissão e descubra seu risco de IA" — text your occupation, get back a personalized AI risk assessment with career transition suggestions and course recommendations.

### Channel: WhatsApp first
Why WhatsApp over a web app:
- 99% of Brazilians use WhatsApp. Zero download friction.
- Viral sharing is native ("manda pra um amigo que é contador")
- You can collect phone numbers for re-engagement
- The "send to group" mechanic is the growth loop

### User flow
```
User: "Sou auxiliar administrativo"
                ↓
Bot:  [matches to CBO 4110 — Agentes, assistentes e auxiliares administrativos]
                ↓
Bot:  "⚠️ Sua ocupação tem exposição ALTA à IA (7.8/10)

      📊 37.7% das mulheres nessa área estão em risco elevado
      💰 Salário mediano: R$ 2.100
      📈 Saldo CAGED: -3.200 (mais demissões que contratações)

      🔄 Transições sugeridas:
      1. Técnico em RH (exposição: 4.2, salário: R$ 3.800)
      2. Analista de dados jr (exposição: 3.5, salário: R$ 4.200)

      📚 Cursos recomendados:
      → Excel + Power BI (Alura) — 40h
      → Fundamentos de People Analytics (DIO) — 20h

      [Link para seu painel completo: site.com/painel?cbo=4110]"
```

### Tech stack
- **WhatsApp Business API** via Twilio or Meta's Cloud API (free tier: 1,000 conversations/month)
- **Backend**: Simple Python/FastAPI service that:
  1. Fuzzy-matches user text to CBO occupation titles (you have 626 slugs)
  2. Looks up pre-computed data from data.json
  3. Formats the response
  4. Logs anonymized usage stats
- **Hosting**: Railway/Fly.io free tier is enough to start
- **No LLM needed** for the bot itself — all data is pre-computed. Just template responses.

### Monetization: EdTech affiliates
- **Alura** — Brazil's largest online tech education platform. Has affiliate program (typically 20-30% commission on R$80-200/month subscriptions).
- **DIO** — Free-to-start with paid bootcamps. Good for career changers.
- **Coursera** — Has affiliate program, many courses have Portuguese subtitles.
- **Hotmart/Eduzz** — Marketplace for Brazilian course creators. Easy affiliate setup.

For each career transition suggestion, include a tracked affiliate link to a relevant course. At R$100 avg course price and 25% commission, you earn R$25 per conversion.

### Growth mechanics
- Every bot response ends with "Compartilhe com um colega → [share link]"
- Media articles link to the WhatsApp bot (Track A → Track B funnel)
- Weekly "profissão da semana" broadcast to opted-in users
- Instagram/TikTok shorts: "Sua profissão vai ser substituída? Manda mensagem pra descobrir" with QR code to WhatsApp

### Rough economics
| Metric | Conservative | Optimistic |
|--------|-------------|------------|
| Monthly bot users | 5,000 | 50,000 |
| Course click-through rate | 5% | 10% |
| Conversion rate | 3% | 5% |
| Avg commission | R$25 | R$40 |
| **Monthly revenue** | **R$187** | **R$10,000** |

The conservative case is modest, but it compounds — the real value is the audience and the data on what occupations people are worried about (which feeds back into better content and government sales pitches later).

---

## How the Flywheel Works

```
  Media articles (free)
       ↓ traffic
  Site visits + WhatsApp signups
       ↓ engagement
  Career bot responses + course recommendations
       ↓ affiliate $$
  Revenue funds more content + more media pitches
       ↓ credibility
  Government/enterprise contracts (later)
       ↓ data
  Better insights → better articles
       ↓
  [repeat]
```

---

## Implementation Order

### Week 1
- [ ] Prep media kit PDF (methodology, team, sample outputs)
- [ ] Create 3 social image cards from top insight pills
- [ ] Send pitch emails to Nexo + Folha + Valor
- [ ] Set up WhatsApp Business account + Twilio/Meta API

### Week 2-3
- [ ] Build WhatsApp bot backend (FastAPI + fuzzy CBO matching)
- [ ] Map 20-30 top occupations to specific course recommendations
- [ ] Set up affiliate accounts (Alura, DIO, Hotmart)
- [ ] Deploy bot, test with friends

### Week 4-5
- [ ] Launch bot publicly, link from site + media articles
- [ ] Post first social content (3x/week cadence)
- [ ] Start newsletter if media generates email signups
- [ ] Track: bot conversations, click-throughs, conversions

### Week 6+
- [ ] Analyze which occupations get the most queries (content signal)
- [ ] Add more insight templates based on demand
- [ ] Pitch government/SENAI with "X thousand workers used our tool" data
- [ ] Explore Instagram/TikTok short-form content

---

## What to Build Next (Technical)

The first coding tasks would be:

1. **WhatsApp bot backend** — FastAPI app with CBO fuzzy matching + templated responses
2. **Course mapping file** — JSON mapping top occupations → recommended courses with affiliate links
3. **Share/tracking infrastructure** — UTM links, basic analytics
4. **Landing page** — Simple page explaining the bot with WhatsApp QR code

The site itself is ready as-is. The Painel Pessoal already does 80% of what the bot needs — we'd just be wrapping it in a WhatsApp-friendly text format.

---

## Other Opportunities (Later)

These become viable once you have audience + credibility from Tracks A and B:

- **Government consulting** — Custom AI workforce reports for state governments, SENAI, SEBRAE (R$50-200K per engagement)
- **HR SaaS** — Companies upload CBO headcount, get AI exposure heatmap (R$2-10K/month recurring)
- **Union reports** — Custom analysis for CUT, Força Sindical (R$10-50K per report)
- **LatAm expansion** — Replicate the pipeline for Mexico (SINCO + IMSS), Colombia (CIUO + DANE), Argentina (CNO + SIPA)

## What Makes This Defensible

- **Data moat:** Nobody else has scored all 626 Brazilian occupations with AI exposure + demographics + regional + hiring trends.
- **Pipeline moat:** Scraping + scoring + visualization is automated. Monthly updates are trivial; a competitor starting from zero can't catch up quickly.
- **Editorial moat:** Insight pills generate press-ready content automatically. Media partnerships create a flywheel.
- **Network moat:** João's Brazilian connections + Sidney's technical execution.
