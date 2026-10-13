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
  each remaining listing by how many of the query's keywords appear in its
  title, description, category, style tags and colors, and returns them best
  match first. It does not call the model.
- **Inputs:**
  - `description` (str) — keywords from the query, e.g. `"vintage graphic tee"`.
    Matching is case-insensitive and on whole words, ignoring filler words
    like "a", "the", "for", "looking".
  - `size` (str or None) — e.g. `"M"`. `None` skips the size filter. A listing
    matches when every word of the requested size is one of the words in the
    listing's size, after splitting on `/`, spaces and brackets — so `"M"`
    matches `"M"`, `"S/M"` and `"M/L"`, but `"S"` does **not** match `"US 9"`
    and `"L"` does **not** match `"XL"`. Listings sized "One Size" match any
    size.
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

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:**

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** <!-- regex, string splitting, or asking the model — say which -->

**What moves through the session:** <!-- which fields, in what order -->

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

```

```
$ python -c "from tools import suggest_outfit; ..."

```

```
$ python -c "from tools import create_fit_card; ..."

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
