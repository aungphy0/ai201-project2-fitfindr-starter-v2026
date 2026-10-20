# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr helps someone shop secondhand. You type what you're looking for in
plain language — like `'vintage graphic tee under $30, size M'` — and it
searches 40 thrift listings from Depop, thredUp and Poshmark for the best
match within your size and budget. It then suggests one or two outfits that
pair the find with clothes you already own, and writes a short caption you
could post about it. If nothing matches, it stops and tells you what to change
(a higher price, a different size, other keywords) instead of inventing a
result.

---

## Tool Inventory

### `search_listings`

- **What it does:** Filters the 40 listings by price ceiling and size, scores
  each remaining listing by keyword overlap with the query, and returns them
  best match first. Each keyword scores by the best place it appears: 3 in the
  title, 2 in the style tags or category, 1 only in the description or colors
  (ties go to the cheaper item). It does not call the model.
- **Inputs:**
  - `description` (str) — keywords from the query, e.g. `"vintage graphic tee"`.
    Matching is case-insensitive and on whole words, ignoring filler words
    like "a", "the", "for", "looking".
  - `size` (str or None) — e.g. `"M"`. `None` skips the size filter. A listing
    matches when every word of the requested size is one of the words in the
    listing's size, after splitting on `/`, spaces and brackets — so `"M"`
    matches `"M"`, `"S/M"` and `"M/L"`, but `"S"` does **not** match `"US 9"`
    and `"L"` does **not** match `"XL"`. Decimals stay together, so `"US 8"`
    does not match `"US 8.5"`. Listings sized "One Size" match any size.
  - `max_price` (float or None) — inclusive ceiling, e.g. `30.0` keeps a $30.00
    item. `None` skips the price filter.
- **Returns:** a list of up to 10 (`config.SEARCH_RESULT_LIMIT`) listing
  dicts, highest keyword score first. Each dict is a full listing: `id` (str),
  `title` (str), `description` (str), `category` (str), `style_tags`
  (list of str), `size` (str), `condition` (str), `price` (float), `colors`
  (list of str), `brand` (str **or None** — None on 32 of 40 listings) and
  `platform` (str).
- **When it has nothing:** returns an empty list `[]` — never `None`, never an
  exception. That happens when no listing passes the price and size filters,
  or when none of the survivors share a single keyword with the description.
  The loop checks for `[]` and stops.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits built around the
  thrifted item, using pieces from the user's wardrobe by name.
- **Inputs:**
  - `new_item` (dict) — one listing dict from `search_listings` (the
    `selected_item`).
  - `wardrobe` (dict) — `{"items": [...]}`, where each item has `id`, `name`,
    `category`, `colors` (list), `style_tags` (list) and an optional `notes`.
    The list may be empty.
- **Returns:** a non-empty string with one or two outfit suggestions. With a
  wardrobe, each outfit names at least one piece from the wardrobe by its
  `name` (e.g. "Baggy straight-leg jeans, dark wash").
- **When it has nothing:** if `wardrobe["items"]` is empty, it asks the model
  for general styling ideas for the item instead (what kinds of pieces and
  colors go with it) and returns those — still a non-empty string, never `""`
  and never an exception.

### `create_fit_card`

- **What it does:** Asks the model for a short, casual caption someone would
  post about the find.
- **Inputs:**
  - `outfit` (str) — the string returned by `suggest_outfit`.
  - `new_item` (dict) — the same listing dict that went into `suggest_outfit`.
- **Returns:** a 2–4 sentence caption (str) that mentions the item, its price
  (e.g. `$24`) and its platform once each, and describes the vibe of the
  outfit. The brand is mentioned only when `brand` is not `None`.
- **When it has nothing:** if `outfit` is empty or only whitespace, it does not
  call the model and returns the message `"No outfit to caption — run
  suggest_outfit first."` instead of raising.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, put a message in
`session["error"]` that names what the user searched for and what to change
(raise the price limit, try a different size or drop it, use broader
keywords), and stop — `suggest_outfit` and `create_fit_card` are never
called. Otherwise take the first (best-scoring) result as
`session["selected_item"]` and go on to `suggest_outfit`, then
`create_fit_card`.

**Where it lives:** `agent.py::run_agent`

The loop is a `while True` that looks at what the session already holds and
picks the next step: parse → search → outfit → fit card. Every pass calls
`trace.check_iterations()`, so a step that never fills in its field can't loop
forever (it stops at `config.MAX_ITERATIONS`).

**How the query is parsed:** regex, in `agent.py::parse_query`. It pulls out a
price ceiling ("under $30", "below 60", "less than $30", "up to $30",
"$40 max"), a size ("size M", "size S/M", "size US 8.5", "size W30 L30", or
"in a medium" → M), and whatever is left becomes the description. Example:
`'vintage graphic tee under $30, size M'` →
`{"description": "vintage graphic tee", "size": "M", "max_price": 30.0}`.

**What moves through the session:** in this order —

1. `query` — what the user typed
2. `parsed` — `description`, `size`, `max_price` from `parse_query`
3. `search_results` — the list from `search_listings` (the branch checks this)
4. `selected_item` — `search_results[0]`
5. `outfit_input_id` — the `id` of the item handed to `suggest_outfit`
6. `outfit_suggestion` — what `suggest_outfit` returned
7. `card_input_id` — the `id` of the item handed to `create_fit_card`
8. `fit_card` — what `create_fit_card` returned
9. `error` — set only when the run stopped early; then 4–8 stay `None`

Both tools read the item from `session["selected_item"]`, not from a local
variable, and record its `id` as they receive it. Fields 5 and 7 exist for
criterion 3: on a correct run both equal `selected_item["id"]`.

---

## Sample Run

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30, size M'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit 1:
Pair the Y2K Baby Tee with the baggy straight-leg jeans, black combat boots, and the black cropped zip hoodie for a cool, balanced contrast between fitted and loose. 

Outfit 2:
Style the Y2K Baby Tee with the wide-leg khaki trousers, chunky white sneakers, and the vintage black denim jacket to lean into that effortless, retro street style.

  Fit card: Just scored the cutest Y2K Baby Tee with a butterfly print for only $18 and I am obsessed. I'm listing it on depop, but first I had to style it two ways to show you the vision. You can wear it fitted with baggy jeans and combat boots for a cool contrast, or lean into retro street style with wide-leg trousers and sneakers.

2 model calls this session, 465 prompt + 160 output tokens

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_012', 'title': 'Oversized Crewneck Sweatshirt — Vintage Navy', 'description': 'Perfectly faded navy crewneck. Genuinely vintage — not manufactured distressed. Ribbed cuffs and hem. No graphics, clean.', 'category': 'tops', 'style_tags': ['vintage', 'basics', 'oversized', 'classic'], 'size': 'XL (fits oversized)', 'condition': 'good', 'price': 20.0, 'colors': ['navy'], 'brand': None, 'platform': 'thredUp'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"

Outfit 1:
White ribbed tank top tucked into the Vintage Levi's 501 Jeans — Medium Wash, layered with the Vintage black denim jacket, finished with Chunky white sneakers and the Black crossbody bag. 

Outfit 2:
Oversized grey crewneck sweatshirt worn over the Vintage Levi's 501 Jeans — Medium Wash, cinched with the Brown leather belt, and paired with Black combat boots and the Black crossbody bag.

```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"

Just scored these classic vintage Levi's 501 jeans on depop for only $38 and I am completely obsessed with the medium wash. I am keeping the rest of the outfit super effortless by pairing them with fresh white sneakers for that ultimate casual 90s off-duty vibe. Honestly, nothing beats finding a perfectly broken-in pair of denim that fits like a glove on the first try.

```

**The empty path** — the same loop on a query nothing matches:

```
$ python app.py ask 'designer ballgown size XXS under $5'

 No listings matched "designer ballgown", under $5, size XXS. To find something, raise your price limit, or try a different size or leave the size out, or use broader keywords (e.g. 'tee' instead of 'ballgown').

0 model calls this session

```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Same `id` through selected_item → suggest_outfit → create_fit_card | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card states price + platform, ≤ 4 sentences | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Price ceiling respected ($15 / $20 / $25 / $30 / $40) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Source: `results/run_2026-10-19_1743_before.md` (`python run_eval.py --label before`,
5 tries per scenario, caching off, temperature 0.9).

- **Criterion 5:** `run_eval.py` writes one row per scenario, and criterion 5
  has five scenarios, one per ceiling. Try 1–5 in the row above are the five
  ceilings in order ($15, $20, $25, $30, $40), each from its own try 1. All 25
  tries passed, not just those five. Search doesn't call the model, so every
  try at a given ceiling returned the same list.
- **The empty-wardrobe scenario** (`denim jacket under $50`, empty wardrobe) is
  a diagnostic run and isn't counted here. All 5 tries completed, and the
  outfit gave general styling advice instead of naming wardrobe pieces.

**Real output from one try** — criterion 1, try 1. Produced by
`run_eval.py::main` → `agent.py::run_agent`, with the search going through
`mcp_client.call_tool` → `mcp_server.py::search_listings`. The two model steps
are `tools.py::suggest_outfit` and `tools.py::create_fit_card`:

```
- Query: vintage graphic tee under $30
- stopped early: no
- selected_item: Vintage Band Tee — Faded Grey ($19.0, depop)
- search_results: 10

Outfit suggestion:
Outfit one:
Vintage Band Tee layered under the Black cropped zip hoodie, paired with the Baggy straight-leg jeans, dark wash. Finish with the Chunky white sneakers and the Black crossbody bag.

Outfit two:
Vintage Band Tee tucked into the Wide-leg khaki trousers, worn with the Brown leather belt. Add the Vintage black denim jacket and the Black combat boots for a grunge look.

Fit card:
Scored this faded grey vintage band tee for just $19 and I am already obsessed with how versatile it is. I listed it on depop, but honestly, styling it two completely different ways makes me want to keep it forever. You can go the effortless streetwear route with a cropped zip hoodie and chunky sneakers, or lean into a grungier aesthetic by tucking it into wide-leg khaki trousers with combat boots.
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Matching query completes all three tools | 4 of 5 | MET (5/5) | Every try had `stopped early: no` and a non-empty fit card, and its trace shows all five steps through `create_fit_card` |
| 2 | Impossible query stops before the second tool | 5 of 5 | MET (5/5) | Every trace ends at `[3] branch` with no `suggest_outfit` step, and the message names what to change (price, size, keywords) |
| 3 | Same `id` through all three tools | 5 of 5 | MET (5/5) | Both trace notes read `received id lst_002 · selected_item id lst_002` on every try |
| 4 | Fit card has price + platform, ≤ 4 sentences | 4 of 5 | MET (5/5) | All 5 cards contain `$42` and `poshmark`, and each is 3 sentences (counted on `.`, `!`, `?`) |
| 5 | Price ceiling respected | 5 of 5 | MET (5/5) | The search note's "highest price returned" was ≤ the ceiling every time: $15/$15, $20/$20, $25/$25, $26/$30, $40/$40 |

**Diagnoses**

No criterion missed, so there is no miss to diagnose. Reading all 45
completed fit cards turned up a failure my criteria don't cover, and two of
my checks turned out weaker than they look.

**1. The fit card is often written as if the user is the seller.** Place: the
model's output, caused by the prompt in `tools.py::create_fit_card`.
11 of the 45 cards say things like *"I listed it on depop"*, *"I uploaded it to
depop"*, *"Both pieces are up now on my depop if you want to snag them"* or
*"grab it before I change my mind and keep it for myself"*. That's the wrong
voice: the user is **buying** this item. The pattern is about the platform,
not about luck:

| Platform of selected item | Cards in seller voice |
|---|---|
| depop (band tee, Y2K tee, Levi's) | 10 of 20 |
| poshmark / thredUp | 1 of 25 |

Mechanism: the prompt passes `Platform: depop` as a bare label and says
"thrift find", but never says the user bought the item there. Depop is known
as an app where individuals post their own clothes to sell, so the model often
fills the gap with "I'm selling this." Criterion 4 still passes because it only
checks that the platform name *appears*, not what the sentence around it says.
The tool works; the prompt leaves out who is buying.

**2. Criterion 1 is easy to pass with this data.** All 5 tries used
one query, and `search_listings` counts a listing as a match if it shares any
single keyword. Common words like "vintage" are in many titles, so most queries
find something. "vintage jacket under $25" picked a *polo shirt*, and "vintage tee
under $15" picked a *leather belt*, because each shared only the word
"vintage" with the query.
The loop completes, but what it completes with isn't always what was asked
for. This is in the tool (`search_listings` scoring), not the loop.

**3. My criterion 3 evidence can't fail as written.** In `run_agent`,
`item = session["selected_item"]`, and the trace note compares `item["id"]` with
`session["selected_item"]["id"]`, which is the same object. It does show both
tools read from the session rather than a stale variable. A stronger check
would compare against `search_results[0]["id"]`, which also matched on every
try (lst_002 was the first result each time).


---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

Both traces are from `results/run_2026-10-19_1743_before.md`, printed by the
`trace.step()` calls in `agent.py::run_agent`. Step 2 is the MCP call.

**Happy path** — `vintage graphic tee under $30` (5 steps)

```
[1] parse_query
      in:  vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style, Y2K Baby Tee — Butterfly Print … +7 more
      →    ceiling 30.0 · highest price returned $26.0
[3] select_item
      out: Vintage Band Tee — Faded Grey ($19.0, depop)
[4] suggest_outfit
      in:  Vintage Band Tee — Faded Grey ($19.0, depop)
      out: Outfit one: Vintage Band Tee layered under the Black cropped zip hoodie, paired with the Baggy straight-leg je…
      →    received id lst_033 · selected_item id lst_033
[5] create_fit_card
      in:  Vintage Band Tee — Faded Grey ($19.0, depop)
      out: Scored this faded grey vintage band tee for just $19 and I am already obsessed with how versatile it is. I lis…
      →    received id lst_033 · selected_item id lst_033
```

**Empty search** — `designer ballgown size XXS under $5` (3 steps, stops at the branch)

```
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    ceiling 5.0 · highest price returned none (empty)
[3] branch
      →    search empty -> stopping, outfit and fit card skipped
```

**On the MCP move:** I registered `search_listings` in `mcp_server.py` with
`@mcp.tool()`, using typed inputs (`description: str`, `size: str | None`,
`max_price: float | None`). In `agent.py::run_agent`, I replaced the direct
`search_listings(...)` call with
`call_tool("search_listings", {"description": ..., "size": ..., "max_price": ...})`
from `mcp_client.py`. The direct call is left commented out above it. The output
did not change. `'vintage graphic tee under $30, size M'` still selects the
Y2K Baby Tee (lst_002) as in the Sample Run, and the impossible query still
comes back as `[]`, so the branch fires exactly as before. `call_tool` turns
the MCP response back into a Python list of dicts. The only visible difference is
speed: each search now starts a new server process, so it's slower.



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** One thing: the prompt in `tools.py::create_fit_card`.
Nothing in the tools' logic, the loop, the session or `scenarios.py` changed.
The original lines are commented out above the new ones.

1. The opening line now says who is buying: *"I just BOUGHT this item
   secondhand on {platform}; I am the buyer showing off what I found, not
   someone selling it."* The labels `Price:` and `Platform:` became
   `Price I paid:` and `Bought on:`.
2. I added one rule: *"Write as the buyer. Never say I listed, uploaded,
   posted or am selling it, and never tell readers to buy or grab it."*

**Which failure it was meant to fix:** Diagnosis 1, the fit cards written as
if the user were the seller (11 of 45 before, 10 of 20 on Depop items). The
diagnosis put the cause in the prompt: it named the platform but never said
the user bought the item there. So the fix was to add that missing fact to
the prompt.

### Run Log — After

Source: `results/run_2026-10-19_2223_after.md` (`python run_eval.py --label after`).
It used the same 10 scenarios, 5 tries each, caching off and temperature 0.9.
Criterion 5's row is scored the same way as before (one ceiling per column),
and again all 25 tries passed.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Same `id` through selected_item → suggest_outfit → create_fit_card | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card states price + platform, ≤ 4 sentences | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Price ceiling respected ($15 / $20 / $25 / $30 / $40) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Did it help, and how do I know:** Yes, for the failure it targeted. I
counted seller-voice cards the same way in both run logs: every completed fit
card (45 per run) checked for the same phrases ("listed it", "uploaded it",
"my depop", "up now on", "now live on", "grab it", "snag them", "head over
to", "keep it for myself", "before I change my mind", "selling", "for sale").

| | Before | After |
|---|---|---|
| Seller-voice cards, all items | 11 of 45 | **0 of 45** |
| Depop items only | 10 of 20 | **0 of 20** |
| poshmark / thredUp items | 1 of 25 | 0 of 25 |

The worst scenario before was "price ceiling $30" (the band tee on Depop),
with 5 of 5 cards in seller voice. After the change it had 0 of 5. Every card
there now reads like *"Scored this faded grey vintage band tee on depop for
only $19 and I am completely obsessed with it."* I also read all 20 Depop
cards by hand to catch seller phrasing the keyword list might miss. I didn't
find any.

The five criteria didn't change. They were 5/5 before and are 5/5 after. Every
card still has the right price and platform in 2–4 sentences, so the new rule
didn't push anything out.

There is one side effect. The cards became more alike: 37 of 45 now open with
"Score/Scored" (30 before), and 43 of 45 put the platform in the first
sentence (34 before). The "Bought on" framing seems to steer the model toward
one opening, "Scored X on {platform} for {price}." No criterion checks
variety, so this doesn't count as a miss, but it is a real cost of the fix.



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

No criterion is missed, before or after. These are the problems I know are
still there:

1. **Search accepts a match on a single common keyword** (`tools.py::search_listings`).
   "vintage jacket under $25" returns a polo shirt, and "vintage tee under $15"
   returns a leather belt, because "vintage" alone is enough to score. Criterion
   1 passes, but the item isn't always what was asked for. *What I'd do:*
   require the item-type word (tee, jacket, jeans…) to match the title or
   category, or give "vintage" less weight. I'd then add a criterion such as
   "the selected item's category matches the noun in the query". *Why I stopped:*
   Milestone 5 allows one change, and this one changes search ranking, which
   would affect criteria 1, 3 and 5 all at once.

2. **The criterion 3 check can't fail as written.** The trace note compares
   `item["id"]` with `session["selected_item"]["id"]`, which is the same
   object. *What I'd do:* compare `outfit_input_id` and `card_input_id`
   against `search_results[0]["id"]` instead, so that passing the wrong item
   would actually show up. It matched on every try in both runs, but the
   evidence should be able to show a failure if one happened.

3. **Fit cards are more formulaic after the fix.** 37 of 45 open with
   "Score/Scored". *What I'd do:* add a rule to vary the opening, then re-run
   and check that the seller-voice count stays at 0. *Why I stopped:* that
   would be a second change, and it would make it unclear which change caused
   the result.

4. **The seller-voice measurement is a keyword list plus a read-through, not a
   criterion.** Criterion 4 doesn't check voice, which is why it passed while
   11 cards were wrong. *What I'd do:* add a revision under criterion 4 in
   `criteria.md` (keeping the original line) that says "written as the buyer",
   so the next run scores voice directly.

5. **Criterion 1 is tested with only one query.** Five tries of the same query
   mostly test the model, not the search. *What I'd do:* use five different
   matching queries, as criterion 5 does with its ceilings.



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [x] criteria.md has five numbered criteria, each with a target
       [x] Each criterion has a reason underneath it
       [x] All five unit 3 sections above have real content
       [x] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [x] Planning Loop names the branch rule and agent.py::run_agent
       [x] Sample Run: one full query plus the three per-tool tests, as text
       [x] At least four new commits
       [x] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [x] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [x] Run Log — Before, five criteria, five tries each
       [x] Real output pasted underneath, naming file and function
       [x] A verdict on every criterion
       [x] A diagnosis for every miss, naming a place AND a mechanism
       [x] Loop Trace, with the MCP call visible in it
       [x] All three failure modes triggered and handled
       [x] One improvement, with Run Log — After in the same format
       [x] What's Still Broken
       [x] At least four new commits
       [x] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
