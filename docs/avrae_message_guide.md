# Reading Avrae messages — general guide

Purpose
-------
This is a general guide for reading/parsing Avrae bot messages. Avrae is a widely used Discord bot that posts game outputs as embedded messages. Because Avrae (and similar bots) place most output inside embeds, robust readers must inspect embed parts, normalize text, and handle small Unicode/formatting differences.

Scope
-----
This guide covers common Avrae output patterns and provides general parsing strategies you can reuse for different Avrae commands (combat, downtime, rituals, checks, etc.). It's intentionally general — use the parsing rules here as a stable foundation and adapt to specific command variants when needed.

Typical structure of an Avrae reply
----------------------------------
- message.content: often empty or holds brief routing/attribution text; the bulk of the output is in embeds.
- embeds[i].title: short, user- or context-oriented headline. Often includes the character name and an action or event.
- embeds[i].description: the main multiline output (dice rolls, outcomes, log lines). Most human-readable lines live here.
- embeds[i].fields: structured name/value pairs for specific data (HP, status, totals, lists). Some Avrae commands use fields heavily.
- embeds[i].footer.text: attribution or command hints (e.g. server name, invocation string).
- embed author: sometimes used to show the character name/portrait; can contain formatted display strings.

General parsing principles
--------------------------
1. Inspect embeds first
   - Do not rely on `message.content` for Avrae outputs. Always iterate `message.embeds` and inspect `title`, `description`, and `fields`.

2. Prefer per-embed parsing
   - Treat each embed as a separate unit of information. Many Avrae replies use multiple embeds to separate sections.
   - Search `embed.description` and `embed.fields` for the target data before falling back to assembled `message.content`.

3. Ownership and bot filtering
   - Avrae messages are posted by a bot account (author.bot == True). Do NOT globally skip bot messages.
   - Skip only your bot's own messages (self.bot.user.id) so you don't process your deferred/followup echoes.
   - Optionally add an `avrae_only` filter (author.id == AVRAE_USER_ID) for faster, targeted scans.

4. Normalization is essential
   - Strip invisibles: remove U+200B (zero-width space) and similar characters before matching.
   - Normalize apostrophes (curly vs straight) — either normalize characters or make your regex accept both.
   - Trim leading/trailing whitespace and collapse multiple spaces when helpful.

5. Regex strategy
   - Use clear, tolerant patterns. Example for a phrase like `That's N contribution points`:

```python
POINTS_REGEX = re.compile(
    r"That[’']s\s+(?:only\s+)?\**\*?_?([0-9]{1,3}(?:,[0-9]{3})*)_?\*?\**\s+contribution\s+points",
    re.IGNORECASE,
)
```

   - After capturing numbers, strip commas and convert to int.
   - Consider a lowercase fallback (`text.lower()`) for robustness against mixed-case anomalies.

6. Key extraction patterns
   - Common rule: take the first meaningful token from `embed.title` (strip markdown bullets/prefixes and punctuation).
   - If `embed.title` is empty, fall back to the first token of `message.content`, then to the first field value/name, then to footer/author.

7. Aggregate and safety considerations
   - Maintain per-key aggregates and grand totals.
   - If processing message history, respect Discord API limits and cap `message_limit` (e.g. max 10k) to avoid long scans.
   - For diagnostics, include counts and small sample blobs (truncated to <= 1000 chars per embed field).

Common pitfalls and mitigations
------------------------------
- Skipping all bot messages: You must allow Avrae through — only skip your own bot.
- Invisible characters: Remove `\u200b`, `\u2060`, etc.
- Markdown-wrapped numbers: Allow for `*`, `**`, `_` wrappers around numbers (either in regex or by stripping formatting before match).
- Different apostrophes: Accept both straight `'` and curly `’` in regex.
- Fields overflow for diagnostics: Discord embed fields are limited; truncate to stay under 1024 characters.

Recommended parsing workflow (pseudocode)
---------------------------------------

1. Fetch recent messages newest-first (oldest_first=False).
2. For each message (skip only this bot's own messages):
   a. For each embed in message.embeds:
       i. desc = normalize(embed.description)
      ii. if POINTS_REGEX matches desc: extract points
     iii. key = extract_first_word(normalize(embed.title)) or fallback
      iv. add points to per_key[key]
   b. If no embed matched, scan `message.content` and `embed.fields` as fallback.

Normalization helper example
----------------------------

```python
def normalize_text(s: str) -> str:
    if not s:
        return ""
    for ch in ('\u200b', '\u2060'):
        s = s.replace(ch, '')
    # Optionally normalize curly apostrophe to straight
    s = s.replace('’', "'")
    return s.strip()
```

Tips for making parsing robust over time
--------------------------------------
- Add unit tests for representative embed descriptions and titles across the Avrae commands you use.
- Keep a short guide of the Avrae command variants you see on your server (some servers customize outputs).
- Consider adding a configuration entry for AVRAE_USER_ID so you can add a fast `avrae_only` mode when you need speed.
- When diagnosing misses, provide a small echo of the raw embed parts (we added `/contributions message_limit:1` to do this).

Appendix: examples and test cases
--------------------------------
- `embed.title`: "Ansa has begun adding their energy to the Mythal!" -> key `Ansa`
- `embed.description` contains: "That's 25 contribution points" -> capture `25`
- Variants:
  - "That’s 8 contribution points" (curly apostrophe)
  - "That's **25** contribution points" (markdown)
  - "That's 1,234 contribution points" (commas)

Follow-ups
----------
If you want, I can:
- Add an `avrae_only` flag to commands to speed scanning.
- Add unit tests for the regex and title-extraction helpers.
- Extend the normalization to remove other problematic Unicode if you encounter server-specific variants.

---
This guide is intentionally general; adapt it where a specific Avrae command exhibits a different layout.
