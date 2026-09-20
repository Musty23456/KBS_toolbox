# Verification notes

This project was built in a sandboxed environment with no network access
(no `pip install`, `npm install`, or Gradle dependency resolution possible)
and no Android SDK, emulator, or Kotlin compiler available. This document
says plainly what was and wasn't possible to check, per component, so you
know exactly how much to trust "it should work" versus "it has run."

## Backend (Python/FastAPI)

**Done:**
- Every `.py` file parsed successfully with Python's own `ast.parse`
  (catches syntax errors).
- Every internal `from app... import ...` was traced by hand against the
  actual module/symbol it names.
- A real bug was caught this way: survey API responses originally exposed
  only the version *number*, not the version *id* — but submissions need
  the id. Fixed in both the schema and the router.

**Not done:**
- `pytest` has never actually been run. ~30 tests exist across auth,
  surveys, submissions, sync, and the expression evaluator.
- No dependency was ever installed — a version conflict between pinned
  packages in `requirements.txt`, while unlikely (versions were chosen as
  known-compatible as of this writing), has not been ruled out by an
  actual `pip install`.

**First thing to run:** `pip install -r requirements.txt && pytest -v`

## Web dashboard (React/TypeScript/Vite)

**Done:**
- `tsc --noEmit --skipLibCheck` was run directly against the source files
  (bypassing the need for installed `node_modules`), which still catches
  real structural/type errors independent of missing packages. Zero real
  errors surfaced — the only errors were "module not found" (expected,
  since no packages are installed) and one expected false-positive around
  React's special `key` prop, which real `@types/react` resolves
  automatically and a bare interface check does not.

**Not done:**
- `npm install` and `npm run build` have never been run. No guarantee the
  pinned dependency versions in `package.json` resolve to a mutually
  compatible set until that actually happens.

**First thing to run:** `npm install && npm run build`

## Android app (Kotlin/Compose)

**Done:**
- Every `.kt` file's brackets/braces/parens were checked for balance with a
  string/comment-aware script (not just naive counting).
- Every Android XML resource file was parsed with `xml.etree.ElementTree`
  to confirm well-formedness.
- Every cross-file reference was traced by hand: constructor call sites
  against constructor signatures (arity and names), DAO/repository method
  calls against their declarations, DTO field names against their usage in
  (de)serialization call sites, and Compose function call sites against
  their signatures. All matched.
- The client-side expression evaluator was deliberately re-checked against
  the backend's Python implementation line-by-line for semantic parity
  (e.g., "any comparison against an unanswered question evaluates to
  false" — including `==` and `!=`, which is easy to get backwards).

**Not done — this is the big one:**
- **No compiler was ever run on this code.** Not `kotlinc`, not Gradle, not
  the Android Gradle Plugin, not the Room/KSP annotation processor. Nothing
  here has been type-checked by an actual Kotlin compiler. The checks above
  catch structural mistakes (typos, arity mismatches, unbalanced syntax)
  but **cannot** catch real type errors, incorrect Compose API usage,
  Room annotation misconfigurations, or Gradle dependency-resolution
  failures.
- `gradle/wrapper/gradle-wrapper.jar` is not included (binary, no network
  to fetch it) — see `android/README.md` for the two ways around this.
- Two JUnit test files exist (`ExpressionEvaluatorTest`,
  `AnswerValidatorTest`) but have never been run.

**First thing to run:** `cd android && gradle testDebugUnitTest
assembleDebug --stacktrace` — and expect to spend real time on the first
build's error output. This is genuinely the least-verified part of the
project; budget time accordingly.

## Bottom line

Treat this delivery as "written and carefully self-reviewed by someone who
could not compile or run any of it," not as "tested and working." The
backend and web dashboard are lower-risk (partial static verification was
possible for both). The Android app is the highest-risk piece — please
build it first and report back whatever surfaces.


## Phase 3 verification
- Repeatable group instance indexes added to Android persistence and sync payloads.
- Backend migration `0004_group_instance_index` added.
- Backend Python compilation passes in the available environment.
- Android Gradle compile could not be executed because the uploaded project does not contain `gradle-wrapper.jar`.
