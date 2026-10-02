# GitHub Input

## Purpose

Fetch steps for SKILL.md Step 1 A and B. Load this file whenever the input is a GitHub URL, before running any command that uses part of the URL.

---

### Safe URL handling (A and B)

A GitHub URL is target content too (SKILL.md Rule 5). Git accepts refs such as `a;$(id)` and ``x`id` ``, and file paths can contain almost anything, so never paste URL text straight into a command.

1. **Validate each component before using it.** `{owner}` and `{repo}` must match `^[A-Za-z0-9._-]+$`. The ref and file path must match `^[A-Za-z0-9._/@+-]+$`; a file path may also contain spaces. If any component fails, stop and ask the user to confirm the target. Don't try to escape it.
2. **Pass components only as quoted variables.** Assign each validated value once in single quotes (`owner='…'`, `repo='…'`, `rest='…'`), then use `"$owner"`, `"$repo"`, `"$ref"`, and `"$file_path"` in every later command, including the clone URL.
3. **Split the ref from the path by resolving it.** Branch and tag names can contain `/` (`feature/auth`), so `blob/{ref}/{path}` and `tree/{ref}/{path}` can't be split on the first slash. Take everything after `blob/` or `tree/` (or, for a `raw.githubusercontent.com/{owner}/{repo}/…` URL, everything after `{repo}/`) as `$rest` and try its `/`-separated prefixes, longest first, until one resolves:

   ```bash
   candidate="$rest"
   while [[ -n "$candidate" ]]; do
     sha=$(gh api "repos/$owner/$repo/commits/$(jq -rn --arg r "$candidate" '$r|@uri')" --jq .sha 2>/dev/null) && break
     [[ "$candidate" == */* ]] && candidate="${candidate%/*}" || candidate=""
   done
   ref="$candidate"; file_path="${rest#"$ref"}"; file_path="${file_path#/}"
   ```

   The first prefix that resolves is the ref, and the remainder is the path. Record `$sha`; line references are only stable against a SHA. A 40-character hex ref resolves on the first try. If nothing resolves, report it under SKILL.md Failure modes (404 or private repo).
4. **URL-encode the file path for API and raw URLs:** `file_enc=$(jq -rn --arg p "$file_path" '$p|@uri | gsub("%2F"; "/")')`.
5. **Don't name a variable `path` in zsh.** zsh ties the `path` array to `$PATH`, so `path=…` breaks every later command lookup. The same goes for `fpath`, `cdpath`, and `manpath`.

### A. GitHub URL — single file

Patterns: `github.com/{owner}/{repo}/blob/{ref}/{path}` or `raw.githubusercontent.com/...`

1. Validate the URL components and resolve `$ref`, `$sha`, and `$file_path` as in **Safe URL handling**.
2. Fetch the content. Prefer `gh api -X GET "repos/$owner/$repo/contents/$file_enc" -f ref="$sha" --jq .content | base64 -d` when `gh` is available and authenticated, because it also works for private repos. Otherwise fetch the raw URL: `curl -fsSL "https://raw.githubusercontent.com/$owner/$repo/$sha/$file_enc"`.
3. If the file sources or calls sibling files (`source ./lib.sh`, `import helpers`, `run script file`), fetch those too, up to the scope limits in SKILL.md Step 2.

### B. GitHub URL — repo or directory

Patterns: `github.com/{owner}/{repo}` or `github.com/{owner}/{repo}/tree/{ref}/{path}`

1. Validate the URL components as in **Safe URL handling**. For a bare repo URL, use the default branch as `$ref` and resolve it to `$sha`.
2. Get repo metadata when `gh` is available: `gh repo view "$owner/$repo" --json name,description,defaultBranchRef,pushedAt,licenseInfo,isArchived`.
3. Get the file tree when `gh` is available: `gh api "repos/$owner/$repo/git/trees/$sha?recursive=1" --jq '.tree[] | select(.type=="blob") | .path'`.
4. If `gh` is unavailable, resolve refs without it before cloning:

   ```bash
   remote="https://github.com/$owner/$repo.git"
   default_ref=$(git ls-remote --symref "$remote" HEAD | awk '/^ref:/ { sub("refs/heads/", "", $2); print $2 }')
   ref="${ref:-$default_ref}"
   git ls-remote --exit-code "$remote" "$ref" "refs/heads/$ref" "refs/tags/$ref"
   ```

   If the URL is a `tree` URL and the ref/path split is still ambiguous without `gh`, clone the default branch into scratch first, then resolve the longest prefix that exists as a ref with `git -C "$scratch/$repo" rev-parse --verify "$candidate^{commit}"`; the remainder is the directory path. If no prefix resolves, fail explicitly under SKILL.md Failure modes instead of guessing.
5. Summarize the structure in 3–8 lines: languages, top-level layout, apparent entry points, and packaging (pkg scripts, Jamf, LaunchDaemons, CI).
6. Pick files to analyze using the entry-point heuristics in SKILL.md Step 2, then fetch them as in A.
7. Clone shallowly into a scratch directory (`git clone --depth 1 --branch "$ref" "https://github.com/$owner/$repo.git" "$scratch/$repo"`) and treat it as a local path when `gh` is unavailable, **or** when the repo is near or over the SKILL.md Step 2 limits, because you will grep across it repeatedly. `--branch` takes branch and tag names only; for a SHA ref, clone the default branch and `git fetch --depth 1 origin "$sha"` then `git checkout FETCH_HEAD`. Record the SHA with `git rev-parse HEAD`.
8. A shallow clone holds one commit, so `git log` is useless for ownership. Use `gh api "repos/$owner/$repo/contributors" --jq '.[] | "\(.contributions)\t\(.login)"'`, `gh api "repos/$owner/$repo/commits?per_page=5"`, and `gh api "repos/$owner/$repo/releases/latest"` instead. If `gh` is unavailable, say contributor/release metadata was not fetched.
