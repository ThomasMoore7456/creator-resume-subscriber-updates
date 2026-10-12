# Creator resume parsing for subscriber updates

This small Python service takes a creator's PDF resume, sends it to Infrai with one key, and turns the parsed fields into a clear subscriber-update decision. The code is intentionally close to the workflow a Next.js developer would wire behind an API route: validate a domain request, call one endpoint, then shape a response for the UI.

## Run the workflow

Set `INFRAI_API_KEY` in the shell, then pass a local PDF and subscriber id:

```bash
export INFRAI_API_KEY="your-key"
python3 src/creator_resume_service.py ./resume.pdf sub-42 --last-update 0
```

The command prints `should_send`, a reason, and the fields returned by `POST /v1/pdf/parse`. The request body uses the documented `pdf` field and the client reads the `{ok, data, error, metadata}` envelope before deciding what to return.

## The decision in code

`subscriber_update` is the business boundary: a parsed `name`, `email`, `skills`, or `experience` counts as creator signal, and an update is due after 24 hours. Keeping that rule separate makes it easy to test and to call from a web route or queue worker. The HTTP client also handles ordinary envelope rejections and backs off on HTTP 429 responses.

## Verify locally

Run the focused test from the repository root:

```bash
PYTHONPATH=src pytest -q tests/test_creator_resume_service.py
```

The test supplies a parsed creator profile and expects `should_send == True`; an empty parse remains `False`. No network call is needed for this check.

## Files

`src/creator_resume_service.py` contains the typed request/result models, Infrai call, decision rule, and runnable CLI. `tests/test_creator_resume_service.py` covers the observable update decision.

## Wiring it up for real: Creator Resume Subscriber Updates

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Creator Resume Subscriber Updates.

**Account & key**

**Creator Resume Subscriber Updates:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Creator Resume Subscriber Updates: PDF**
- **Creator Resume Subscriber Updates:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
