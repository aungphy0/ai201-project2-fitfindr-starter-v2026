"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import config  # noqa: F401 — you'll use this in search_listings
from generate import generate
from utils.data_loader import load_listings

import re

# ── helpers for search_listings ──────────────────────────────────────────────

# Words that say nothing about the item. Without this list, "looking for a tee"
# would score every listing whose description contains "for" or "a".
_STOPWORDS = {
    "a", "an", "and", "the", "for", "with", "in", "on", "of", "to", "my", "me",
    "i", "im", "looking", "want", "need", "some", "something", "any", "size",
    "under", "below", "max", "please", "find",
}


def _words(text: str) -> list[str]:
    """Lowercase whole words (letters and digits), e.g. "Levi's 501" -> ["levi", "s", "501"]."""
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _keywords(description: str) -> set[str]:
    """The words in the query worth matching on: no filler words, no 1-letter words."""
    return {w for w in _words(description) if w not in _STOPWORDS and len(w) > 1}


def _size_matches(requested: str, listing_size: str) -> bool:
    """
    My size rule (it's in the README's Tool Inventory):
    every word of the requested size must be a whole word of the listing's size,
    after splitting on "/", spaces and brackets.

        "M"  matches "M", "S/M", "M/L"
        "S"  does NOT match "US 9"      (whole words, not substrings)
        "L"  does NOT match "XL"
        "One Size ..." listings match any request.
    """
    listing = (listing_size or "").lower()
    if listing.startswith("one size"):
        return True
    # Keep decimals together so "US 8" doesn't match "US 8.5".
    def size_words(text):
        return set(re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower()))

    wanted = size_words(requested or "")
    have = size_words(listing)
    return bool(wanted) and wanted <= have


def _score(listing: dict, keywords: set[str]) -> int:
    """
    Weighted keyword overlap. Each query keyword scores once, by the best place
    it appears:

        3  in the title
        2  in the style tags or category
        1  only in the description or colors

    Weighting matters: the mesh top's description says "great for layering
    under a graphic tee", which matched "graphic tee" as strongly as the
    actual graphic tees until title and tag matches counted for more.
    """
    def word_set(text: str) -> set[str]:
        words = set(_words(text))
        # Count "tee" in the query as a match for "tees" in the listing.
        return words | {w[:-1] for w in words if w.endswith("s")}

    title = word_set(listing.get("title", ""))
    tags = word_set(" ".join(listing.get("style_tags", [])) + " " + listing.get("category", ""))
    rest = word_set(listing.get("description", "") + " " + " ".join(listing.get("colors", [])))

    score = 0
    for k in keywords:
        forms = {k, k.rstrip("s")}
        if forms & title:
            score += 3
        elif forms & tags:
            score += 2
        elif forms & rest:
            score += 1
    return score



# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    keywords = _keywords(description)
    if not keywords:
        return []

    scored = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size and not _size_matches(size, listing["size"]):
            continue
        score = _score(listing, keywords)
        if score > 0:
            scored.append((score, listing))

    # Highest score first; on a tie, the cheaper item first.
    scored.sort(key=lambda pair: (-pair[0], pair[1]["price"]))
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    items = (wardrobe or {}).get("items") or []

    item_desc = (
        f"{new_item.get('title')} — {new_item.get('category')}, "
        f"colors: {', '.join(new_item.get('colors', []))}, "
        f"style: {', '.join(new_item.get('style_tags', []))}, "
        f"condition: {new_item.get('condition')}"
    )

    system = (
        "You are a friendly thrift stylist. Be concrete and brief. "
        "Plain text, no markdown headings."
    )

    if not items:
        # Empty wardrobe: general advice instead of an error or "".
        prompt = (
            f"Someone is thinking of buying this secondhand item:\n{item_desc}\n\n"
            "They haven't saved any clothes yet. Suggest one or two outfits built "
            "around it, describing the kinds of pieces, colors and shoes that would "
            "go with it. Keep it under 100 words."
        )
    else:
        wardrobe_lines = "\n".join(
            f"- {w.get('name')} ({w.get('category')}; colors: {', '.join(w.get('colors', []))})"
            for w in items
        )
        prompt = (
            f"Someone is thinking of buying this secondhand item:\n{item_desc}\n\n"
            f"These are the clothes they already own:\n{wardrobe_lines}\n\n"
            "Suggest one or two outfits that pair the new item with pieces from "
            "that list. Name each wardrobe piece exactly as it is written above. "
            "Only use pieces from the list. Keep it under 100 words."
        )

    answer = (generate(prompt, system=system) or "").strip()
    if not answer:
        return f"Try the {new_item.get('title')} with simple basics in neutral colors."
    return answer


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return "No outfit to caption — run suggest_outfit first."

    raw_price = float(new_item.get("price", 0))
    # "$24" for whole dollars, "$24.50" otherwise — never round a price.
    price = f"${raw_price:.0f}" if raw_price.is_integer() else f"${raw_price:.2f}"
    platform = new_item.get("platform", "")
    brand = new_item.get("brand")
    # 32 of 40 listings have no brand, so only mention it when there is one.
    brand_line = f"Brand: {brand}\n" if brand else ""

    prompt = (
        # "Write a caption for a social media post about a thrift find.\n\n"
        # f"Item: {new_item.get('title')}\n"
        # f"{brand_line}"
        # f"Price: {price}\n"
        # f"Platform: {platform}\n"
        ### changed ###
        "Write a caption for a social media post about a thrift find. "
        f"I just BOUGHT this item secondhand on {platform}; I am the buyer "
        "showing off what I found, not someone selling it.\n\n"
        f"Item: {new_item.get('title')}\n"
        f"{brand_line}"
        f"Price I paid: {price}\n"
        f"Bought on: {platform}\n"
        ### changed ###
        f"How I'm styling it: {outfit.strip()}\n\n"
        "Rules:\n"
        # "- 2 to 4 sentences, casual, first person, like a real post.\n"
        # f"- Mention the item, the price written exactly as {price}, and the "
        # f"platform written exactly as {platform} — once each.\n"
        # "- Be specific about the vibe of the outfit.\n"
        # "- No hashtag lists, no quotation marks around the caption."
        ### changed ###
        "- 2 to 4 sentences, casual, first person, like a real post.\n"
        f"- Mention the item, the price written exactly as {price}, and the "
        f"platform written exactly as {platform} — once each.\n"
        "- Be specific about the vibe of the outfit.\n"
        "- Write as the buyer. Never say I listed, uploaded, posted or am "
        "selling it, and never tell readers to buy or grab it.\n"
        "- No hashtag lists, no quotation marks around the caption."
        ### changed ###
    )

    return (generate(prompt) or "").strip()
