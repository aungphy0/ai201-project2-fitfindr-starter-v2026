# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
<!-- Why 4 of 5 and not 5 of 5? Something about your search, probably —
     "my search is a plain keyword match and some phrasings will miss" is a
     real answer. -->

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
<!-- Why is 5 of 5 reasonable here when criterion 1 isn't? What's different
     about this path? -->

---

## 3. Something about state

Given a query that matches at least one listing, the `id` of
`session["selected_item"]` is the same `id` as the item that `suggest_outfit`
received and the item that `create_fit_card` received — in 5 of 5 tries.

**Why this target:**
The handoff from search to the next two tools is plain code with no model in
it, so it should behave identically every run; one miss means a bug, not bad
luck. I'm checking `id` rather than reading the outfit, because a wrong-item
bug (e.g. passing `results[1]` or a stale variable) still produces a
believable outfit — it just describes a different listing. Only comparing the
ids catches that.

---

## 4. Something about the fit card

Given a query that matches, the fit card states the selected item's price
(e.g. `$24`) and its platform (`depop`, `thredUp` or `poshmark`), and is no
longer than 4 sentences — in at least 4 of 5 tries.

**Why this target:**
Price and platform are what make the caption useful — they tell a reader what
it costs and where to buy it. The card is written by the model at temperature
0.9 with caching off during the eval, so the wording changes every run and it
will sometimes drop a detail or run long; 5 of 5 would be asking the model to
be deterministic. I didn't require the brand, because 32 of the 40 listings
have no brand, so a brand rule would fail for reasons that have nothing to do
with the caption.

---

## 5. Your choice — the price ceiling is respected

Given a query that includes a price ceiling ("under $X"), every listing in
`session["search_results"]` has `price` less than or equal to X — in 5 of 5
tries, using five different ceilings ($15, $20, $25, $30, $40).

**Why this target:**
A price ceiling is a hard limit for the user: showing a $38 item to someone
who said "under $30" is a wrong answer, not a weaker one. Both steps involved —
pulling X out of the query and filtering on it in `search_listings` — are code,
so 5 of 5 is achievable. The five ceilings span the data's price range ($12 to
$75), so a low ceiling like $15 checks that the filter works when only a few
listings qualify, not just when almost everything does.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
