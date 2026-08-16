# 8-Dimension Architecture Quality Framework

The single source of truth for the 8 quality dimensions used by both the review and design workflows in this skill.

## Scoring Rules (apply to every review)

- Score range: **0-5**. Meaning: 0 = absent/broken, 1 = barely present, 2 = weak, 3 = acceptable, 4 = good, 5 = exemplary.
- **Every score requires evidence** — a file path + line number, a concrete code snippet, or a direct observation made during recon. No evidence → write "not evaluated" instead of inventing a score.
- Only score dimensions selected by the user; others are marked "skipped".
- A dimension score is a judgment of the *current state*, not the roadmap. Remediation is listed separately.

---

## 1. Functional Correctness (功能正确性)

**Core question:** Can vague requirements be precisely implemented? (Can a fuzzy requirement be turned into a working, verifiable feature?)

### Evaluation questions
1. Where are requirements recorded (doc, ticket, comments), and can each feature be traced back to one?
2. Are acceptance criteria defined before implementation, or does "done" mean "the code ran once"?
3. When the user says "handle it flexibly" — what is the actual defined behavior at boundary cases (empty input, wrong format, timeout)?
4. Is there a single source of truth for business rules, or are they scattered across multiple modules?
5. Are error paths specified (what must happen when a step fails), or only the happy path?

### Evidence checkpoints
- Requirement docs vs. code: pick 2-3 features, verify a requirement → test → implementation chain
- TODOs, "magic" behavior decisions, comments like "temporary workaround"
- Exception/error handling coverage in the core flow
- Whether business rules appear duplicated with different values in different files

### Common anti-patterns
- Implementing based on assumptions without ever confirming requirements
- Acceptance = "it printed the expected output once"
- Boundary conditions handled as silent no-ops or generic exceptions
- Business rules copied into multiple places with drift between copies
- No record of *why* a behavior exists (no decision traceability)

### Remediation
| Cost | Action |
|---|---|
| Low | Write acceptance criteria retroactively for the 3 most important flows; add boundary-case tests |
| Medium | Centralize duplicated business rules into one module; add a requirements index (feature → files) |
| High | Set up requirement tracking (issue/ticket per feature) and a traceability table for new work |

---

## 2. Portability (可移植性)

**Core question:** If we switch platform/environment, how much code has to change?

### Evaluation questions
1. Are there hardcoded absolute paths, IPs, ports, or machine names in code or config?
2. Are environment differences (OS, paths, encodings, line endings) handled or assumed?
3. Is configuration externalized (env vars / config files), or compiled into code?
4. Are dependencies pinned (lock files) with known versions?
5. Does the app assume a specific working directory or file-system layout?
6. Are there platform-specific calls (Windows-only APIs, shell commands with unix syntax) without abstraction?

### Evidence checkpoints
- Grep for absolute paths, hardcoded `localhost:port`, `C:\` or `/home/` patterns
- Config files vs. constants in code; presence of `.env.example` / config templates
- Lock files (`requirements.txt` with pins, `package-lock.json`, `poetry.lock`, etc.)
- `os.path` vs `pathlib`, string-concatenated paths, `os.system` calls
- Encoding assumptions in file I/O (GBK vs UTF-8)

### Common anti-patterns
- Config values embedded in source files
- Paths built with hardcoded separators or relying on CWD
- No dependency pinning → "works on my machine"
- Windows-specific code with no fallback
- Default encodings assumed (breaks across OS locales)

### Remediation
| Cost | Action |
|---|---|
| Low | Extract hardcoded paths/IPs/ports into config; add `.env.example` |
| Medium | Switch to `pathlib.Path`; pin dependencies; add a devcontainer or setup script |
| High | Abstract platform-specific calls behind an interface; add CI on a second platform |

---

## 3. Maintainability / Extensibility (可扩展性 / 可维护性)

**Core question:** If a new feature or business change arrives, how many files must be touched?

### Evaluation questions
1. Are module boundaries aligned with business concepts, or with implementation convenience?
2. Can each module answer: what it does / how to use it / what it depends on — without reading internals?
3. Adding a new feature: which files need changes? (Answer should be "one module + its tests", not "5 scattered files")
4. Is there duplicated logic that must be kept in sync manually?
5. How large are the biggest files, and do they do more than one job?
6. Can internal implementation of a module change without touching its callers?

### Evidence checkpoints
- File sizes and class/function counts in the core package
- Copy-pasted code blocks across files (grep repeated signatures)
- Coupling smell: A module importing deeply into another's internals
- Names: modules named by layer (`utils.py`, `common.py`) vs. by business concept
- God objects: classes with 10+ responsibilities

### Common anti-patterns
- `utils.py` / `common.py` / `helpers.py` dumping grounds
- Feature addition requires editing 5+ unrelated files
- Business logic inside UI/entry-point code
- Copy-paste maintenance ("fix in one place, break the other")
- Tight coupling through shared mutable global state

### Remediation
| Cost | Action |
|---|---|
| Low | Split oversized files by responsibility; move duplicated constants to one source |
| Medium | Extract one module per business concept with a clear public API; move business logic out of entry points |
| High | Introduce explicit interfaces between modules; remove shared global state; dependency-injection for hard-coded dependencies |

---

## 4. Observability (可观测性)

**Core question:** If something breaks at 3 AM, how fast can the root cause be located?

### Evaluation questions
1. Does the system log at all? Are there structured logs (level, timestamp, context) or bare print statements?
2. Can a single request/business flow be traced end-to-end (request ID / trace ID)?
3. Are key metrics captured (latency, error rates, queue depth, resource usage)?
4. Is there any alerting, or does someone have to notice manually?
5. What happens to logs — rotated, retained, searchable, or written into a file nobody reads?
6. Can a failed task be distinguished from a slow one, a retried one, and a success?

### Evidence checkpoints
- Log statements: do they carry context (IDs, params), or only static strings?
- Logging setup: levels configurable via env? stdout vs. file? rotation?
- Presence of monitoring/alerting config (dashboards, alert rules)
- Error handling: is the error logged at the point of failure with the payload that caused it?
- Startup/error events logged, or silent?

### Common anti-patterns
- `print()`-only logging, or logging everything at INFO with no levels
- Errors swallowed (`except: pass`) or logged without the exception
- No request/transaction IDs across modules
- Logs without timestamps or with local-time-only timestamps
- Success and failure indistinguishable in logs
- No alerting — discovered by users

### Remediation
| Cost | Action |
|---|---|
| Low | Standardize log format (timestamp + level + logger + message); log exceptions with tracebacks |
| Medium | Add request IDs and thread them through the call chain; configure log rotation and retention |
| High | Structured logging + metrics endpoint + basic alert rules on error rate and latency |

---

## 5. Testability (可测试性)

**Core question:** How easy is it to test this feature in isolation?

### Evaluation questions
1. Can core logic run without external dependencies (DB, network, filesystem, time)?
2. Are dependencies injected, or instantiated inside the code being tested?
3. Do tests exist at unit / integration levels, or only manual testing?
4. Can a module be tested without first setting up a full environment?
5. Are tests deterministic (no time/randomness/network dependence) and fast?
6. Is the test pyramid respected (many fast unit tests, few slow integration tests)?

### Evidence checkpoints
- Test directory and coverage of core business logic
- Dependencies created inside functions vs. injected
- Test setup complexity (does a test require a running DB?)
- `time`, `random`, network calls inside business logic (hard to test)
- Test runtime (a test suite that takes 20 minutes discourages running it)

### Common anti-patterns
- Business logic entangled with I/O, so every test needs a real environment
- Zero tests for the core flow; "we test manually"
- Tests that depend on wall-clock time or random values
- Tests that pass/fail depending on run order or machine
- No test doubles in sight (mock/stub), full-stack tests only

### Remediation
| Cost | Action |
|---|---|
| Low | Add unit tests for the 3 most critical pure functions; pin a test command in README |
| Medium | Extract I/O boundaries so core logic accepts injected dependencies; add integration test setup |
| High | Refactor to dependency injection throughout; build a fast unit-test layer and CI test gate |

---

## 6. Usability / Onboarding (易用性)

**Core question:** Can a newcomer run the core flow within 10 minutes?

### Evaluation questions
1. Is there a README with: prerequisites, install steps, run steps, config explained?
2. Can the app be started with one documented command, including setup (deps, config, DB)?
3. Are there sample inputs/examples so the user can run the happy path immediately?
4. Are error messages actionable ("set env var X to Y") instead of cryptic traces?
5. Is sample data available for tests/demo without needing production data?
6. What's the first-run experience — clone → read → run, or a day of reverse engineering?

### Evidence checkpoints
- README completeness (setup/run/config sections)
- One-command setup (Makefile, script, package manager scripts)
- Default config that works out of the box vs. requires knowledge
- Example inputs in `input/` / `examples/`
- Error handling quality on the most common mistakes

### Common anti-patterns
- README missing or "it's obvious" one-liner
- Setup requires undocumented manual steps (create DB, set 10 env vars nobody knows)
- No sample data; first run requires production data or inventing data
- Errors show stack traces with no hint for the operator
- Prerequisites assumed (Python 3.9 vs 3.11, node version, DB version)

### Remediation
| Cost | Action |
|---|---|
| Low | Write the README setup/run sections; add one example input; fix the most confusing error message |
| Medium | Add a one-command setup script and sample data; document config options with defaults |
| High | Provide containerized/devcontainer setup; automated smoke test as an onboarding check |

---

## 7. Performance / Scalability (性能 / 可伸缩性)

**Core question:** If data volume or concurrency grows 10x, does the architecture deform?

### Evaluation questions
1. What happens at 10x current data: where are the bottlenecks (DB queries, loops, I/O)?
2. Are expensive operations obvious (N+1 queries, full-table scans, blocking calls in hot paths)?
3. Can compute/workers scale horizontally (stateless or partitioned), or is there a single point of contention?
4. Are there capacity numbers anywhere (expected users, rows, requests/sec)?
5. Does the design store data in ways that match access patterns (indexes, denormalization, caching)?
6. Is concurrency handled correctly (shared state, race conditions, connection pooling)?

### Evidence checkpoints
- Queries: loops calling DB/HTTP inside loops, missing indexes
- Synchronous blocking calls in request paths
- Global locks, single-worker assumptions, shared in-memory state without locking
- Batch jobs reading everything into memory
- Any documented capacity estimates or load tests

### Common anti-patterns
- "It works with my test data" with no load consideration
- N+1 queries in list/export flows
- Everything processed in memory for "simplicity"
- Single instance assumption baked in (local files, in-process state)
- No caching where data is hot and expensive to compute
- No capacity numbers anywhere — can't answer "what breaks first?"

### Remediation
| Cost | Action |
|---|---|
| Low | Fix obvious hotspots (indexes, N+1, add a cache for hot data); measure with a simple benchmark |
| Medium | Make workers stateless/partitioned; introduce queues for heavy work; add pagination/batching |
| High | Architectural changes (async processing, horizontal scaling, read replicas, caching layer) driven by measured bottlenecks |

---

## 8. Security (安全性)

**Core question:** If a breach or attack happens, how large is the blast radius?

### Evaluation questions
1. Where is sensitive data stored (secrets, credentials, PII), and who can access it?
2. Are all inputs validated (API params, file contents, user-provided strings) before use?
3. Are secrets in code, config committed to the repo, or properly managed?
4. What is the privilege model — least privilege per module/service, or one super-credential everywhere?
5. Is the attack surface known: which endpoints/files/commands accept external input?
6. What happens if one component is compromised — can it reach everything else?

### Evidence checkpoints
- Secrets/credentials in source, config files, or commit history
- Input validation on all external boundaries (API, CLI args, file parsing)
- AuthZ: are authorization checks present, or just authN?
- SQL/command construction: string interpolation vs. parameterized queries
- Sensitive data in logs (passwords, tokens, PII in log lines)
- Network exposure: what listens, what's accessible from where

### Common anti-patterns
- Passwords/API keys committed to the repo or hardcoded
- No input validation ("internal tool, no need")
- One shared admin credential used by all modules
- String-built SQL/shell commands from user input
- Logging sensitive payloads wholesale
- No concept of least privilege; everything runs as root/admin

### Remediation
| Cost | Action |
|---|---|
| Low | Move secrets to env/secret manager; remove hardcoded credentials; validate external inputs at boundaries |
| Medium | Parameterize queries/commands; redact sensitive fields in logs; scope credentials to least privilege |
| High | Introduce authZ model, secret rotation, input validation middleware, and a threat review of exposed surfaces |
