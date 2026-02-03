# GitHub Copilot Instructions — WhatsApp Bot (Python/FastAPI)

## 0) Project profile (read first)
You are assisting on a professional WhatsApp bot built with:
- **Python 3.12+**
- **FastAPI** (all endpoints must be `async`)
- **Pydantic v2** for schema validation
- **Twilio WhatsApp API** integration
- **Local RAG (Retrieval-Augmented Generation)** for semantic search + minimal LLM usage

Goal: produce correct, maintainable, production-grade changes with minimal files and explicit reasoning.

---

## 1) Repository structure rules (strict)
- **Do not create new files** without explicit user permission.
- Keep logic within the existing structure whenever possible.
- All technical documentation and usage instructions must live in **`README.md`** (keep it simple and clear).
- Folder responsibilities:
  - `config/`: **JSON only**. Contains bot flows, menus, and text content.
  - `src/`: main application code.

If you think a new file is necessary, stop and ask for approval with a short justification.

---

## 2) Configuration & text sources (no hardcoding)
Hardcoding is forbidden:
- **No API keys, tokens, URLs, phone numbers, or secrets** in code.
- **No menu text / flow logic** in code.

Required approach:
- Use **environment variables** for credentials and secrets (typically via `.env` in local dev).
- Extract **all bot text**, menu options, and flow logic from the **JSON files in `config/`**.
- When implementing features that depend on menus/flows, request or reference the relevant JSON file(s) via `@config/<file>.json` rather than duplicating content.

If a required value is missing from env/config, ask what the intended key/value name should be.

---

## 3) Python coding standards (professional)
### 3.1 Typing (mandatory)
- Use **type hints everywhere**: functions, methods, return types, class attributes when relevant.
- Prefer modern Python 3.12 typing:
  - `list[str]`, `dict[str, Any]`, `str | None`
  - `typing.TypedDict` / `pydantic` models when appropriate

### 3.2 Asynchrony (mandatory)
- All FastAPI endpoints must be `async def`.
- Any network calls (Twilio, LLM providers, external HTTP) must be async-friendly:
  - Prefer async clients (e.g., `httpx.AsyncClient`) or explicit async wrappers.
- Do not block the event loop with heavy CPU work. If unavoidable, isolate it (and explain trade-offs).

### 3.3 Pydantic v2 compatibility (mandatory)
- Use Pydantic v2 patterns (e.g., `BaseModel`, `field_validator` when needed).
- Ensure schema validation and serialization follow current v2 behavior.
- Avoid v1-only patterns.

### 3.4 Comments (useful only)
- Avoid narrating obvious code.
- Add comments where they clarify non-trivial logic, especially:
  - Local RAG pipeline decisions
  - Retrieval/scoring thresholds
  - Prompt construction constraints
  - Latency/cost optimizations

---

## 4) RAG + LLM usage rules
### 4.1 Local RAG first
- Prefer **local libraries** and local computation for semantic search and retrieval.
- Use LLM calls only where necessary and keep them minimal.

### 4.2 Minimal LLM consumption
When an LLM call is required:
- Optimize prompts for **brevity and determinism**.
- Provide only the minimum context needed (e.g., retrieved chunks, not entire documents).
- Avoid multi-turn prompt chains unless clearly justified.
- Always consider:
  - latency impact
  - cost impact
  - failure modes (timeouts, rate limits)

If an LLM is optional, propose a local alternative first.

---

## 5) Change protocol (how you work)
### 5.1 Planning before complex changes (required)
Before making complex or multi-file changes:
1) Provide a **brief plan** in chat:
   - which functions/modules will be touched
   - what will be added/modified
   - any config/env changes required
2) Wait for confirmation if the plan changes behavior or adds risk.

### 5.2 Keep diffs tight
- Prefer small, reviewable changes.
- Avoid broad refactors unless explicitly requested.
- Don’t rename things “for style”.

### 5.3 Validation requirements
Any proposed code must be compatible with:
- **Python 3.12**
- **FastAPI async patterns**
- **Pydantic v2**

When relevant, include:
- how to run formatting/lint/tests (if present in repo)
- how to validate endpoint behavior (example request/response)

---

## 6) Copilot CLI workflow recommendations (how to use you effectively)
When asked to implement bot behavior:
- Use **planning mode** (`/plan`) before writing code if new functionality is requested.
- To avoid hardcoding menus/flows, **reference JSON configs directly** in prompts using `@`:
  - Example: “Implement the response logic based on @config/bot_flow.json”

When generating code that depends on menus/text:
- Do not copy menus into Python constants.
- Parse/validate config JSON (and handle missing keys gracefully).

---

## 7) Security rules (non-negotiable)
- Never output or suggest committing secrets.
- Ensure `.env` is in `.gitignore` (if repo uses `.env`).
- Do not log sensitive data (Twilio auth, user phone numbers, message content) unless explicitly required and scrubbed.
- Prefer allow-lists and explicit validation for inbound webhook payloads.

If security and convenience conflict, choose security and explain the trade-off.

---

## 8) Output expectations (response format)
When responding with implementation guidance or code changes:
- Be concise and technical.
- Explain **why** a change is needed (cause → effect).
- Call out trade-offs explicitly when they exist (latency, cost, complexity, reliability).
- If you are missing critical information, ask targeted questions instead of guessing.