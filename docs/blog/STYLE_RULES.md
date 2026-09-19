# Blog style rules

Two goals, and they pull in the same direction:

1. A junior developer should understand every sentence.
2. Nothing should read like it came out of a chatbot.

Source for the second list: [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).
Only the parts that apply to a technical blog post are kept here. Content was rephrased for compliance
with licensing restrictions.

---

## Part 1 — Words and phrases that are banned outright

These words appear far more often in chatbot text than in human text. One of them is a slip. Five of them
and the post reads as generated.

**Verbs:** delve, underscore, highlight, showcase, emphasize, foster, enhance, leverage, garner, boast
(meaning "has"), utilize, align with.

**Adjectives:** crucial, pivotal, key, robust, vibrant, intricate, meticulous, seamless, comprehensive,
enduring.

**Nouns used abstractly:** landscape, tapestry, testament, interplay, ecosystem (when not literal),
insights.

**Sentence openers:** Additionally, Moreover, Furthermore, Notably, Ultimately.

**Whole phrases:** it's important to note, it's worth noting, valuable insights, a deep dive, at its
core, in today's world, that said.

Plain replacements, and they are almost always shorter:

| Banned | Write instead |
|---|---|
| this underscores / highlights | this shows |
| crucial / pivotal / key | important, or delete the word |
| delve into | look at |
| leverage | use |
| utilize | use |
| robust | reliable, or say what it survives |
| Additionally, ... | And, or just start the sentence |
| it's important to note that X | X |
| comprehensive | delete it |

---

## Part 2 — Sentence shapes that are banned

**"Not just X, but Y."** Also "It's not X, it's Y" and "Not only X but also Y". This is one of the
strongest chatbot tells. If you catch yourself writing it, split it into two sentences.

> Bad: *This is not just a bug, it's a design flaw.*
> Good: *This is a design flaw. The bug is what made it visible.*

**Rule of three.** Three adjectives or three short phrases in a row. Chatbots reach for this constantly
to sound thorough. Two is fine. Three is a tell.

> Bad: *The query is simple, atomic, and fast.*
> Good: *The query is one statement, so it looks atomic.*

**The trailing "-ing" clause that adds nothing.** A sentence that ends with `..., showing the importance
of X` or `..., making it a popular choice`. This is fake analysis stapled to a real fact. Delete it or
turn it into its own sentence with a real claim.

> Bad: *Both sessions got rowcount = 1, highlighting the danger of this pattern.*
> Good: *Both sessions got `rowcount = 1`. Neither got an error.*

**Avoiding the word "is".** Chatbots replace `is` with `serves as`, `stands as`, `represents`,
`functions as`, `marks`. Use `is`. Use `has` instead of `features` or `offers`.

> Bad: *The subquery serves as the target selector.*
> Good: *The subquery picks the row to update.*

**Vague attribution.** `Experts say`, `many developers`, `it is widely believed`, `some argue`. If you
cannot name who, delete the claim or say "I assumed" / "the docs say".

**"Despite its X, Y faces several challenges."** Chatbots end articles this way, often with a
"Future Outlook" heading. Do not write a challenges section. Do not write a future-work section.

**"In conclusion" / "In summary" / "Overall".** Never. The last paragraph should say something new, not
repeat what came before.

---

## Part 3 — Formatting that is banned

**Title Case Headings.** Chatbots capitalise every main word. Write headings in sentence case:
`How the plan explains it`, not `How The Plan Explains It`.

**Bold-header bullet lists.** The `- **Thing**: description` shape is the single most recognisable
chatbot output format. Use a real table, or write prose.

**Bold for emphasis, more than once or twice per section.** Bold the two or three sentences that a
skimmer must not miss. Nothing else.

**Em dashes with spaces around them ( — ).** Use a comma, a full stop, or brackets. A full stop is
almost always better. (Note: the chat messages that produced this plan are full of these. Do not copy
that style into the post.)

**Emoji anywhere.**

**A `---` divider between every section.** One or two in the whole post, at most.

**Curly quotes** (`"` `'`). Check that the editor has not converted straight quotes. Inside code blocks
this is not cosmetic, it breaks the code if someone copies it.

---

## Part 4 — Positive rules, because avoiding tells is not the same as writing well

**Short sentences.** If a sentence has two commas and an "and", split it.

**One idea per paragraph.** Three or four sentences. A ten-line paragraph will be skipped.

**Define a term the first time, inline, in under ten words.** `EvalPlanQual` needs a parenthetical, not
a paragraph.

**Every number carries its condition.** `1.25 s` alone means nothing. `1.25 s, with a 6 s lock held on
the oldest pending row` can be argued with.

**Say "I".** `I assumed this was atomic. It is not.` A chatbot does not have a wrong assumption to
report. This is the strongest thing a human writer has and it costs nothing.

**Narrows, not closes.** Never write `prevents`, `eliminates`, `guarantees`, `solves` about a mitigation
unless it is provably total. Use `narrows`, `reduces`, `makes smaller`.

**Say what you did not test.** One honest limitation paragraph is worth more than three confident ones.

---

## Part 5 — The self-check before publishing

Read the draft once looking only for these, in this order:

1. Ctrl-F every banned word from Part 1. Count them. Target is zero.
2. Ctrl-F for `not just`, `not only`, `rather than merely`. Target is zero.
3. Ctrl-F for ` — `. Replace each with a full stop or a comma.
4. Every heading: is it sentence case?
5. Every bold: is it one of the two or three sentences a skimmer must catch? If not, unbold it.
6. Every paragraph: more than five lines? Split it.
7. Read the last paragraph alone. Does it say something new, or does it summarise?
8. Read the first sentence alone. Does it state the finding, or set up context?
