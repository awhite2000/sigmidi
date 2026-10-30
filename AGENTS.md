# Project rules

## Git

- Never run `git commit` and never `git push` until the user specifically requests it. Each request authorises only the action it names, once; after that, return to not committing or pushing.
- When explicitly asked to push, never push to `origin` without that explicit instruction. Keep all work local by default.

## Documentation

- Describe only the current design, parts, settings and assembly steps.
- Do not record design history, superseded components, comparisons with removed designs, or statements that obsolete parts are no longer needed. Keep change history in Git.
- Update documentation generators and packaged copies alongside their source documents.

<!-- CODEGRAPH_START -->
## CodeGraph

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), reach for it BEFORE grep/find or reading files when you need to understand or locate code:

- **MCP tool** (when available): `codegraph_explore` answers most code questions in one call — the relevant symbols' verbatim source plus the call paths between them, including dynamic-dispatch hops grep can't follow. Name a file or symbol in the query to read its current line-numbered source. If it's listed but deferred, load it by name via tool search.
- **Shell** (always works): `codegraph explore "<symbol names or question>"` prints the same output.

If there is no `.codegraph/` directory, skip CodeGraph entirely — indexing is the user's decision.
<!-- CODEGRAPH_END -->
