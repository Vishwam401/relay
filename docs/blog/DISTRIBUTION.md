# Distribution and comment prep

Reusable for every post in the series. Post 01 is the first run through it.

---

## Order matters

```
Hour 0    Hashnode published. Leave it alone for a few hours so it indexes first.
Hour 0    Add the link to the Relay README, near the top.
Hour 2-4  Hacker News. Then r/PostgreSQL. Stay available for comments.
Hour 4    LinkedIn pointer post.
Day 2     dev.to, with canonical_url pointing at the Hashnode URL.
Day 2     Suggest it to Postgres Weekly.
```

The gap before dev.to exists so search engines see the Hashnode URL as the original.

---

## Channel by channel

### Hacker News

Normal submission, not `Show HN`. `Show HN` is for things people can use; this is a finding.

Title rules there: no clickbait, no emoji, no "I". State the finding.

- Good: `Postgres: UPDATE ... WHERE id = (subquery) can claim the same job twice`
- Bad: `A subtle bug I found in my job queue`

Submit once. Do not ask anyone to upvote, it is detected and it gets accounts flagged. Weekday
morning US Eastern is the widest window. If it gets no traction, leave it. Resubmitting looks worse
than being ignored.

Be at the keyboard for the two hours after submitting. On HN the comments are the value, not the
points.

### r/PostgreSQL

Smaller than HN and better targeted. The most technically useful comments will come from here.

Do not drop a bare link. Write three or four lines in the post body: what the statement is, what
happened, and that it is reproducible in two minutes. Then the link.

r/ExperiencedDevs is a secondary option. Frame it around the measurement discipline rather than the
Postgres detail, because that audience is broader.

### Postgres Weekly

https://postgresweekly.com/ is hand-picked and lists query craft as a topic. There is a suggestion
link on the site. A mention in a curated newsletter outlasts a day on HN, because it stays in the
archive and people cite it later. This is the most under-used channel for exactly this kind of post.

### LinkedIn

A pointer, not the article. Four to six lines, one image, one link. LinkedIn's editor destroys code
blocks, and posting the full text there also splits the canonical URL.

The image should be the two `EXPLAIN` plans with the one differing line visible. That screenshot
carries the whole post.

Frame it around process, not cleverness. The people who hire care more that you reproduce failures
than that you know a Postgres internal.

### dev.to

Republish with `canonical_url` set to the Hashnode URL. Without it, search engines have to guess which
copy is the original, and it will not pick yours.

Expect it to underperform. The traffic there skews frontend and beginner, so a Postgres internals post
is not its audience. Post anyway, the cost is zero and the long tail from search is real.

### Skip

Medium, because the sign-in wall costs more readers than the reach gains. LinkedIn articles, for the
formatting reasons above. Lobste.rs would fit well but is invite only.

---

## Comment prep

The highest-value 20 minutes before submitting anywhere. Read these until the answers are yours.
Every answer is short on purpose, and every one is backed by something measured.

| Likely comment | Answer |
|---|---|
| "Just use `FOR UPDATE SKIP LOCKED`." | `SKIP LOCKED` removes waiting, not duplicates. The row lock plus the compare and set prevent the duplicate. Measured: two workers claiming different rows 6 ms apart with no `SKIP LOCKED` produced no duplicate |
| "My version has `AND status = 'pending'` and it works fine." | Correct, and that is version 2 in the post, which is called sound there. The broken one is the version without it. The whole difference is one condition |
| "So use `SERIALIZABLE`." | Measured: `REPEATABLE READ` and `SERIALIZABLE` both give `40001` instead of the duplicate. That is better, and it moves the expected case onto an error path, so every caller needs retry logic |
| "Why Postgres as a queue at all, use a broker." | Because the enqueue shares a transaction with the business write. With a broker, the order commits and the job does not exist, and nothing can detect it afterwards. The cost is that you own redelivery. `D-01` has both sides |
| "This is just a lost update, it is well known." | Agreed, and the post names it as one. The point is where it hides: the uncorrelated subquery turns the condition into a constant, and the only visible sign is one line in `EXPLAIN` |
| "Is this version specific?" | Measured on 16.14 only. Plan node names vary with table size and statistics. The invariant is the `InitPlan` and the absence of `status` in the outer condition |
| "`n = 1` is not evidence." | It is a mechanism demonstration, not a benchmark, and the post says so. It is deterministic and reproducible in two minutes |
| "What about advisory locks?" | Never measured, so no claim. The mechanism argument against it is that it serialises the whole claim path instead of one row |
| "Did you check a correlated subquery?" | Plan shape only, `Filter: (id = (SubPlan 1))` with cost `15968` against `27`. The recheck behaviour there was not measured |

### How to answer

State the measurement. Do not argue.

If someone corrects you and they are right, say so and fix the post. A visible correction raises
credibility more than being right the first time does. If someone is wrong, give them the reproduction
and let them run it.

Do not defend `n = 1` at length. One sentence, then move on.

---

## What to judge this by

Not views. Views on a first post are usually between a few hundred and a couple of thousand, and that
number says nothing.

Judge it by:

- Did one senior engineer leave a substantive comment? That is worth more than any traffic number,
  because it means someone checked the mechanism.
- Did anyone contradict it? That is a win either way. Correct means you learned something, incorrect
  means you now have a second measurement.
- Does post 02 do better than post 01? The series compounds, a single post does not.

Record what actually happened after publishing. Right now every reach number in this file comes from
published sources rather than from measurement. After post 01 there will be real numbers to plan
post 02 with.
