# Known limitations / next steps

A single consolidated list, pulled from each component's README, so nothing
is buried in a sub-directory.

## Backend

- Media answers (photo/audio/signature) store a `media_reference` string
  (a file path or object-storage key) rather than accepting binary uploads
  directly. A `POST /api/media/upload` endpoint backed by S3-compatible
  object storage is the natural next addition, with the Android app
  uploading captured files there and sending back the resulting key.
- The in-process rate limiter in `app/main.py` is per-instance. A
  multi-instance production deployment should swap it for a shared store
  (e.g. Redis).

## Web admin dashboard

- Question reordering uses simple up/down buttons instead of drag-and-drop,
  to avoid adding a drag-and-drop library as a dependency that couldn't be
  installed/tested in the authoring environment. Swap in something like
  `@dnd-kit/core` if true drag-and-drop is wanted.
- No CSV/Excel export button yet on the submissions page — the backend
  already returns everything needed via `GET /api/submissions`; adding an
  "Export" action is a small follow-up.
- No offline support (by design — offline-first is the Android app's job).

## Android app

- Same media-reference limitation as the backend: captured files are stored
  locally and referenced by path, not uploaded as binary data yet.
- `gradle/wrapper/gradle-wrapper.jar` (a binary) is not committed to the
  repository — run `gradle wrapper --gradle-version 8.7` once locally to
  generate it, or just use `gradle` directly (as CI does) instead of
  `./gradlew`.
- Manual dependency injection (`ServiceLocator`) is used instead of Hilt —
  a deliberate choice to avoid an annotation-processing build step that
  could not be verified in the authoring environment. This is a reasonable
  permanent choice for a project this size, not just a stopgap.
- Audio recording has no maximum duration or file-size cap.
- The signature pad captures reasonably fine strokes but has not been
  tuned for very large screens/tablets.

## Cross-cutting

- No end-to-end integration test exercises all three components together
  (e.g. a script that creates a survey via the web dashboard, downloads it
  on a simulated device, submits it, and confirms it appears in the
  submissions list). This would be a valuable addition once the individual
  pieces are confirmed to build and run correctly on their own.
