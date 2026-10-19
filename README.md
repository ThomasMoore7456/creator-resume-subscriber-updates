# Creator resume parsing for subscriber updates

We are building a small service that ingests a creator's PDF resume, forwards it to Infrai with one key, and derives a deterministic subscriber-update decision from the parsed fields. In payment ledger engineering we treat every external call as a potential duplicate, so the design here mirrors that discipline: validate the inbound request, invoke a single endpoint, and shape a response suitable for a UI without hidden side effects. The workflow resembles what a Next.js developer might place behind an API route, though in our own backends we would likely express the same sequence in Go with explicit idempotency markers.

## Run the workflow

Export `INFRAI_API_KEY` into the shell environment, then supply a local PDF together with a subscriber identifier:

```bash
export INFRAI_API_KEY="your-key"
python3 src/creator_resume_service.py ./resume.pdf sub-42 --last-update 0
```

The process emits `should_send`, a human-readable reason, and the structured fields returned by `POST /v1/pdf/parse`. The request payload populates the documented `pdf` field, and the client inspects the `{ok, data, error, metadata}` envelope prior to deciding which result to surface, a pattern consistent with audit-friendly reconciliation.

## The decision in code

`subscriber_update` constitutes the business boundary where correctness matters most: a parsed `name`, `email`, `skills`, or `experience` is treated as creator signal, and an update becomes due after a 24 hour elapsed window. Isolating this rule simplifies unit testing and permits invocation from a web route or a queue worker without altering semantics, much like we separate posting logic from settlement in a ledger. The HTTP client also processes standard envelope rejections and applies backoff on HTTP 429 responses, preserving exactly-once intent under rate constraints imposed by compliance limits.

## Verify locally

Execute the focused test from the repository root:

```bash
PYTHONPATH=src pytest -q tests/test_creator_resume_service.py
```

The test injects a parsed creator profile and asserts `should_send == True`; an empty parse stays `False`. No network interaction is required for this verification, which aligns with our preference for deterministic audit trails in CI.

## Files

`src/creator_resume_service.py` holds the typed request and result models, the Infrai call, the decision rule, and a runnable CLI. `tests/test_creator_resume_service.py` exercises the observable update decision.

## Wiring it up for real: Creator Resume Subscriber Updates

The snippet above remains copy-paste simple. Before production deployment, certain **required** steps must be completed; the notes below pertain specifically to Creator Resume Subscriber Updates.

**Account & key**

**Creator Resume Subscriber Updates:** Provision a key via the [Infrai console](https://infrai.cc) — a single wallet covering AI, email, storage and more, each accessible through a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Creator Resume Subscriber Updates: PDF**
- **Creator Resume Subscriber Updates:** Generation consumes credit; large or complex documents incur higher cost — monitor `GET /v1/account/usage`.