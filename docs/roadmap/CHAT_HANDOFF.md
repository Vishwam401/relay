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
Read `CURRENT_WEEK.md`. First active phase is Week 0: async/blocking, signals, file descriptors/connections, TCP timeouts, and PostgreSQL transaction anomalies. Do not jump ahead until its Definition of Done passes.