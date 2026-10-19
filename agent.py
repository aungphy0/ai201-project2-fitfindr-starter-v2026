"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from mcp_client import call_tool
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
        # Criterion 3 (state): the id of the item each later tool actually
        # received. Compare both against session["selected_item"]["id"].
        "outfit_input_id": None,     # id of the item passed to suggest_outfit
        "card_input_id": None,       # id of the item passed to create_fit_card
    }



# ── query parsing (regex) ─────────────────────────────────────────────────────

import re

# "under $30", "below 30", "less than $30", "max $30", "$30 max", "up to $30"
_PRICE_PATTERNS = [
    r"(?:under|below|less than|max|up to|no more than)\s*\$?\s*(\d+(?:\.\d+)?)",
    r"\$\s*(\d+(?:\.\d+)?)\s*(?:max|or less)",
]

# "size M", "size S/M", "size US 8.5", "size W30", "size W30 L30", "size XXS"
_SIZE_PATTERN = (
    r"\bsize\s*:?\s*("
    r"us\s*\d+(?:\.\d+)?"          # shoes: US 8.5
    r"|w\d+(?:\s*l\d+)?"            # jeans: W30, W30 L30
    r"|[a-z0-9]+(?:/[a-z0-9]+)?"     # letters: M, XXS, S/M
    r")"
)

# "in a medium", "a small" -> a letter size
_WORD_SIZES = {"small": "S", "medium": "M", "large": "L"}


def parse_query(query: str) -> dict:
    """
    Pull description, size and max_price out of a plain-language query, using
    regex. Whatever isn't a price or a size is left as the description.

        "vintage graphic tee under $30, size M"
        -> {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}
    """
    text = query.strip()
    max_price = None
    size = None

    for pattern in _PRICE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            max_price = float(m.group(1))
            text = text[: m.start()] + " " + text[m.end():]
            break

    m = re.search(_SIZE_PATTERN, text, re.IGNORECASE)
    if m:
        size = m.group(1).upper()
        text = text[: m.start()] + " " + text[m.end():]
    else:
        m = re.search(r"\b(?:in\s+)?(?:a\s+)?(small|medium|large)\b", text, re.IGNORECASE)
        if m:
            size = _WORD_SIZES[m.group(1).lower()]
            text = text[: m.start()] + " " + text[m.end():]

    description = re.sub(r"[^\w\s'/-]", " ", text)      # drop "$", commas, etc.
    description = re.sub(r"\s+", " ", description).strip()
    return {"description": description, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """Say what the user could change — not just "No results"."""
    tried = [f'"{parsed["description"]}"' if parsed["description"] else "no keywords"]
    tips = []
    if parsed["max_price"] is not None:
        tried.append(f"under ${parsed['max_price']:g}")
        tips.append("raise your price limit")
    if parsed["size"]:
        tried.append(f"size {parsed['size']}")
        tips.append("try a different size or leave the size out")
    tips.append("use broader keywords (e.g. 'tee' instead of 'ballgown')")
    return (
        f"No listings matched {', '.join(tried)}. "
        f"To find something, {', or '.join(tips)}."
    )

# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)

    # The loop: each pass looks at what's in the session so far and picks the
    # next step. It ends when a step sets "done" — either the fit card is
    # written, or the search came back empty (the branch).
    steps = 0
    while True:
        steps += 1
        trace.check_iterations(steps)

        # Step 1 — parse the query (regex, see parse_query above).
        if not session["parsed"]:
            session["parsed"] = parse_query(query)
            continue

        # Step 2 — search.
        if not session["search_results"] and session["selected_item"] is None:
            parsed = session["parsed"]
            # session["search_results"] = search_listings(
            #     parsed["description"],
            #     size=parsed["size"],
            #     max_price=parsed["max_price"],
            session["search_results"] = call_tool("search_listings", {
                "description": parsed["description"],
                "size": parsed["size"],
                "max_price": parsed["max_price"],
                }
            )

            # ⚠️ THE BRANCH: nothing came back -> explain what to change and
            # stop. suggest_outfit and create_fit_card are never called.
            if not session["search_results"]:
                session["error"] = _no_results_message(parsed)
                return session

            # Otherwise pick the best match and keep going.
            session["selected_item"] = session["search_results"][0]
            continue

        # Step 3 — outfit, built from the item stored in the session.
        if session["outfit_suggestion"] is None:
            item = session["selected_item"]
            session["outfit_input_id"] = item["id"]
            session["outfit_suggestion"] = suggest_outfit(item, session["wardrobe"])
            continue

        # Step 4 — fit card, from the outfit and the same item in the session.
        if session["fit_card"] is None:
            item = session["selected_item"]
            session["card_input_id"] = item["id"]
            session["fit_card"] = create_fit_card(session["outfit_suggestion"], item)
            continue

        # Everything is filled in.
        return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
