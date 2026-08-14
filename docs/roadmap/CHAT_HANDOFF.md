# Conversation Handoff

## Goal
Become a strong backend engineer capable of joining a strong MNC or high-quality startup. Focus on architecture, correctness, failure behavior, operational thinking, and explicit tradeoffs.

## Decisions Already Made
- Alpha Commerce is finished; do not extend it.
- Portfolio: Alpha Commerce shows breadth; Relay will show depth.
- Relay is a developer-facing durable job execution service—a small Celery-like system built to understand queues rather than merely use them.
- Month 1 is backend fundamentals + Relay core.
- Months 2-3 may add AI/LLM execution: provider rate limits, token/cost accounting, budget caps, fallback, caching, and evaluations.
- Avoid generic RAG-chatbot projects; AI infrastructure is the intended domain angle.
- Do not chase Redis, RabbitMQ, Kafka, Kubernetes, microservices, or frameworks as buzzwords.

## Mental Model
For every dependency ask:
1. What does it guarantee, and what does it not?
2. If it fails, does the system degrade or die?
3. What happens if work executes twice?
4. If state exists in two places, how is it synchronized?
5. Under load, what fails first?

Learning is failure-driven: intentionally stop workers/databases, exhaust pools, create concurrent transactions, measure behavior, and document expected versus actual results.

## Reading Policy
- DDIA 1st edition is the core text, read on demand.
- Kurose is used mainly for transport/TCP fundamentals.
- Alex Xu is deferred until interview-preparation months.
- Building Microservices and Database Internals are optional/on-demand.

## Start Here
Read `CURRENT_WEEK.md` — it is a pointer to the active week's **plan** (`docs/planning/WEEK_NN.md`) and **log** (`docs/logs/WEEK_NN.md`). Those are always two separate files: the plan states intent, the log states measured outcome.

**Current position:** Week 0 is complete (async/blocking, signals, file descriptors/connections, TCP timeouts, PostgreSQL transaction anomalies — all reproduced with measurements). Week 1 is active and Din 1 is done: the `jobs` table and its first migration exist, with every column decision recorded in `docs/DECISIONS.md` as `D-03`..`D-08`. Next is Din 2 (`POST /jobs`, `GET /jobs/{id}`).

Do not jump ahead of the current day. Open items carried forward are listed at the bottom of `docs/LEARNING_LOG.md`.