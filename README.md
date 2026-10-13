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
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

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
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
