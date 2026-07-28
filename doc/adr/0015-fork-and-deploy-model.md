# 15. Fork-and-deploy model

Date: 2026-07-28

## Status

Accepted

## Context

Ataraxia will implement massive parallelization via cloud workers.  Local parallelization will also be enabled, but to process 1000s of shards in parallel, cloud is the default goto.

Serious quants who researched their alpha manually will not risk handing that strategy to a cloud platform.  Quantopian wound down after failing to build a business licensing strategies from independent quants, a model that requires the platform to actually see the strategy.  QuantConnect avoids this by shipping LEAN as OSS that runs locally instead of forcing everyone through their cloud.

The same trust problem already exists on the broker side.  In CFTC v. Coquest Inc., a broker quoted prices to customers while secretly taking the other side of those same trades through affiliated firms, using the customers' own confidential order information, without disclosure.  In practice this is B-booking: internalizing customer flow instead of routing it to market.  Case settled in 2023 via consent order, roughly $3M in disgorgement and penalties.  Different mechanism than a hosted backtest platform reading a quant's strategy code, but same shape of failure: someone in a privileged position has invisible access to something the other party can't verify isn't being used against them.

That's the actual risk with hosting Ataraxia as SaaS.  Encrypting strategies at rest with something like AWS KMS doesn't fix it.  KMS gives quants trust in AWS, not in whatever SaaS platform is built on top of AWS.  To run the strategy the platform still has to decrypt it to plaintext at execution time, and a quant has no way to verify that plaintext isn't logged or copied somewhere at that point.

## Decision

Ataraxia will not host and run strategies for users, even behind per-tenant KMS keys, since encryption at rest doesn't touch the plaintext-at-execution problem above.

Instead: fork the OSS repo into a private repo (can be local), then run locally or deploy to cloud infra the quant controls directly.

This isn't a permanent "no SaaS, ever."  It's "no SaaS until there's a way to prove the platform can't see the plaintext."  If verifiable execution, e.g. attested enclaves, gets good enough that even the operator provably can't access plaintext mid-execution, that's worth its own ADR.

## Consequences

- No recurring hosted revenue for now, which matters for any commercialization plan.
- Security patching is decentralized, every fork can silently drift behind upstream fixes.
- Onboarding has more friction than a SaaS competitor.
- All infra cost, management and operational security burden sits with the user, not Ataraxia.
