# ⚙️ Specialized Checks

## Contents
- Purpose
  - Bundle intake (SKILL.md Step 1 E)
  - Data scan (bundles and logs)
  - Collectors and archivers
  - Shared directories (app-owned paths and exploit targets)
  - Jamf parameter secrets
  - Per-user tools and home-directory secrets
  - Release pipelines
  - Destructive scope (Rule 14 overreach)

## Purpose

SKILL.md Step 1 E and Step 4 checks that apply only to some targets. Load this file when its trigger applies; each section's checks are then mandatory, like the rest of Step 4.

- **Bundle intake:** the input is a diagnostic or support bundle (SKILL.md Step 1 E).
- **Data scan:** the input is a bundle, or the code writes logs or reports meant to be shared.
- **Collectors and archivers:** the code gathers files into a bundle, report, or upload.
- **Shared directories:** root touches a file in an app-owned directory that non-root users can write, or a symlink primitive needs a high-value target.
- **Jamf parameter secrets:** a credential arrives through Jamf `$4`–`$11`.
- **Per-user tools:** the code never runs as root but stores credentials under the user's home.
- **Release pipelines:** release CI writes to a distribution channel (a Homebrew tap, a package repository, an update feed), or a distribution manifest in another repo defines the installed layout.
- **Destructive scope:** the code deletes, uninstalls, resets, or forgets package receipts.

---

### Bundle intake (SKILL.md Step 1 E)

1. List it with `unzip -l` and read entries with `unzip -p "$zip" "$entry"`, which also works in read-only or plan mode. Print plists with `plutil -p -`. Extract into the scratch directory only for scanning. Never run anything inside the bundle.
2. Find the generator: the app or script that builds the bundle (search its source for the bundle's file names). Ask one scope question if the user didn't say: bundle contents only, or bundle plus generator. In the second case the bundle is **evidence** and the generator is the **code under review**. Read any code that writes the sources the generator collects (shared log writers, permission setup) too, since the collector inherits their trust. The **Collectors and archivers** checks below apply to the generator.
3. Use bundle-relative paths as the location prefix (`metadata.txt:24`, `logs/app.log:993`), with line numbers from the extracted copy.
4. Scan the data with the **Data scan** below and fill the fact sheet's **Disclosure surface** row.
5. When the generator collects from host paths, record their real permissions on the analysis host (`ls -ld`, read-only) as observed host evidence, dated in Scope caveats.
6. End the report with a verdict on **this specific artifact**: whether it is safe to post as is, and exactly which lines or files to redact first.

---

### Data scan (bundles and logs)

For Step 1 E inputs, and for any shipped log the code writes, pattern-scan the text. It reads straight from the archive, so it works in read-only mode:

```bash
unzip -Z1 "$zip" '*.log' '*.txt' '*.json' '*.jsonl' '*.plist' 2>/dev/null |
while IFS= read -r entry; do
  unzip -p "$zip" "$entry" 2>/dev/null |
    grep -inE 'bearer|authorization:|token|secret|passw(or)?d|api[_-]?key|hooks\.slack\.com|webhook\.office\.com|logic\.azure\.com' |
    sed "s#^#$entry:#" | cut -c1-240
done | head -40

unzip -Z1 "$zip" '*.log' '*.txt' '*.json' '*.jsonl' '*.plist' 2>/dev/null |
while IFS= read -r entry; do unzip -p "$zip" "$entry" 2>/dev/null; done |
  grep -oE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' | sort | uniq -c | head
unzip -Z1 "$zip" '*.log' '*.txt' '*.json' '*.jsonl' '*.plist' 2>/dev/null |
while IFS= read -r entry; do unzip -p "$zip" "$entry" 2>/dev/null; done |
  grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b|\b([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b' | sort | uniq -c | head
unzip -Z1 "$zip" '*.log' '*.txt' '*.json' '*.jsonl' '*.plist' 2>/dev/null |
while IFS= read -r entry; do
  unzip -p "$zip" "$entry" 2>/dev/null |
    grep -inE 'serial|hostname|computername|udid|IOPlatform' |
    sed "s#^#$entry:#" | cut -c1-240
done | head -40
unzip -Z1 "$zip" '*.log' '*.txt' '*.json' '*.jsonl' '*.plist' 2>/dev/null |
while IFS= read -r entry; do unzip -p "$zip" "$entry" 2>/dev/null; done |
  grep -oE '/Users/[^/ ":]+' | sort | uniq -c
unzip -Z1 "$zip" '*.log' '*.txt' '*.json' '*.jsonl' '*.plist' 2>/dev/null |
while IFS= read -r entry; do unzip -p "$zip" "$entry" 2>/dev/null; done |
  grep -oE 'https?://[^ "<>]+\?[^ "<>]+' | sort -u | head -20   # query strings can carry tokens
unzip -Z1 "$zip" '*.log' '*.txt' '*.json' '*.jsonl' '*.plist' 2>/dev/null |
while IFS= read -r entry; do unzip -p "$zip" "$entry" 2>/dev/null; done |
  grep -oE '\[(DEBUG|INFO|NOTICE|WARNING|ERROR|FAULT)\]' | sort | uniq -c
```

Many hits are label or product names ("1password", "gitcredentialmanager"), so triage each one. Public vendor download URLs and UUIDs in them aren't secrets. Fill the **Disclosure surface** row with what remains, and credit redaction that worked (`<redacted>` in place of a webhook URL).

---

### Collectors and archivers

Code that gathers files into a bundle, report, or upload inherits the trust of every directory it reads.

- **Symlinks pull in other files.** `FileManager.copyItem`, `cp -R`, and `ditto` copy a symlink as a link, but `zip -r` without `-y` stores the link's *target*. A user who can write to a collected directory plants `x.log -> /Users/<victim>/.ssh/id_ed25519`, and the victim's next bundle includes the key. The finding is cross-user exfiltration, made worse when the bundle goes to a public issue. Check this tool behavior in isolation in the scratch directory (SKILL.md Rule 4), then cite the observed result.
- **Fix pattern:** skip anything that isn't a regular file (`lstat`, `URLResourceValues.isSymbolicLink`/`isRegularFile`, `find -type f`), require the expected owner for shared sources, and pass `zip -y` as a second layer.
- **Denylist redaction** (a fixed set of keys replaced with `<redacted>`) leaks any secret-bearing key added later, and logs or crash reports copied byte for byte are never scrubbed. Rate it Low when nothing leaks today. Recommend an allowlist export, a scrubber for webhook hosts, `Authorization`/`Bearer`, URL query strings, and `/Users/<name>`, plus a test that fails when a new key is in neither list.
  - **Test the key regexes against JSON form and other spellings.** A pattern shaped `(password\s*[:=]\s*["']?)…` redacts `password=hunter22` but leaves `"password": "hunter22"` intact, because the closing quote sits between the key and the colon. A pattern that does allow `["']?` after `api_key` still misses `"apiKey"` and `api-key:`, even case-insensitively (both checked in isolation with Python `re`). Run each secret pattern on the plain, JSON, camelCase, and kebab-case forms.
  - **Compare every export path.** Tools often chain two redactors for clipboard or log export and only one for the bundle, or seed inventory names in one path and not the other. List each path that writes shareable text and check it applies the same chain.
  - **Check the PII keys against real data.** A key list that names `deviceName` while the data source uses `name` never seeds the value. Count keys in the target's own fixtures or sample output to confirm coverage.
- **Public-posting exposure.** A bundle that the maintainers ask users to attach to public issues and that carries identity, group lists, inventory, or org schedules is a Low finding (Origin: Code + Deployment) when no credential is present. Recommend a "prepare for public posting" mode and a private upload path.
- **Disclosure.** When a High or Critical finding sits in third-party shipping code whose support process is public, add a Cross-cutting note recommending private vulnerability reporting before any public issue.

---

### Shared directories (app-owned paths and exploit targets)

Extends SKILL.md Step 4, Shared-directory trust.

- **App-owned directories that users can write.** A vendor directory such as `/Library/Application Support/<vendor>/logs` set to `root:staff 0775` or `root:admin 0775` so the GUI can share a log with the root daemon is as exposed as `/tmp`, and worse without the sticky bit. `staff` is every local account, and a group-writable directory without `+t` lets any member unlink root-owned files and put a symlink in their place. Root then running `chown`/`chmod` without `-h`, or `open()` without `O_NOFOLLOW`, on a file there is local privilege escalation, often at every daemon start. Read the code that sets the mode, and confirm the live mode on the analysis host with `ls -ld` (read-only; record it as dated host evidence). Recommend a root-only log for the daemon, `1775` if sharing is unavoidable, and `lstat` plus owner checks with `fchown`/`fchmod` on an `O_NOFOLLOW` descriptor.
- **High-value targets.** When you find a symlink primitive, name a concrete target the code itself creates. The best example is a script that a root LaunchDaemon runs, because taking ownership of it gives persistent root. Check the mode the primitive sets: a symlinked `chmod 0664` strips the execute bit, so a target that root executes directly becomes a denial of service, not code execution, when the attacker can't restore `+x`. In that case name a target root reads or sources instead (a config file, a shell startup file), and say which kind it is. Record the chain as observed code path plus inferred exploitability.
- **Root ownership changes over user-filled trees (hard links).** Root `chown -R "$user"` on a folder the user could write before or during the run — a backup or archive moved within their home, a folder restored from staging, a "fix permissions" step — changes the owner of every inode inside it. A hard link the user planted there is the system file itself, so they gain ownership of any root-owned file on the same volume that isn't SIP-protected or immutable. Unlike the symlink case, no race is needed, and neither symlink checks nor BSD `chown -R`'s default `-P` help. Check the platform fact in isolation (a non-root `ln` of a root-owned file into the scratch directory, removed immediately; `df` to show the volumes match) and record the side effect. Fix: drop the `chown` when the files already belong to the user (a rename within their home doesn't change owner), and do moves as the user (`launchctl asuser … sudo -u "$user" mv`). Also check the root `mv` that precedes such a `chown`: it resolves the source path again after any parent-symlink check.
- **A claimed fix for one operation isn't a fix for its siblings.** When a release moves one class of root operation on user-controlled paths into user context (for example, deletions), sweep the same paths for the other root operations (`mv`, `chown`, `chmod`, `cp`, `sqlite3`, `defaults write`): `grep -nE '\b(chown|chmod|cp|ditto|mv|mkdir|touch|ln)\b'` over the file, then filter for user-home or shared paths.

---

### Jamf parameter secrets

Extends SKILL.md Step 4, Secrets.

- Credentials passed in `$4`–`$11` (API secrets, SIEM ingest tokens, webhook URLs). They are visible in the Jamf Pro policy UI. Jamf also passes them as `argv` of the script process, which lives for the whole run.
  - **This exposure comes from the platform, not the target's code.** Jamf Pro delivers every policy parameter as a command-line argument, and macOS lets any local user read other processes' arguments. No script can hide a value once it arrives this way. Record the finding as **Origin: Platform + Deployment** (SKILL.md Rule 13), and say so in the finding's Impact.
  - On current macOS, any local user can read root processes' full `argv`. Confirm on the analysis host with `ps -axww -o user=,args= | awk '$1=="root"' | head` run as non-root; it has worked on Darwin 25.
  - Passing the secret to `curl` over stdin (`--config -`, `-K -`) protects only the `curl` child, not the parent script.
  - Name what the target already does about it: rejecting parameter-supplied secrets, reading them from a root-only file instead, warning in the log, or documenting the risk. Credit these in the finding, not only in the Low/Info roll-up.
  - Separate out any part the code does add, and label it **Code**. For example, a script that rejects a parameter secret but then runs every check before exiting keeps the value exposed for minutes with no benefit.
  - Rate the finding with **Credential severity** in `security.md`: a fleet-scoped secret is High **only while a policy actually populates the parameter**. Cite the observed `ps` check and give the rating both ways (SKILL.md Rule 11). If the target documents and supports a safer delivery (a root-only secrets file, Keychain), the headline uses that documented baseline and the populated-parameter rating is the alternate. If parameters are the only way the code accepts the secret, the exposure is part of the baseline and counts in the headline.

---

### Per-user tools and home-directory secrets

A tool that never runs as root still has a trust boundary: other local accounts and the network. Check where it keeps credentials (SMTP passwords, API tokens, webhook URLs).

- **Home directories aren't private on macOS.** On the Darwin 25 analysis host, home was `drwxr-x---+` with group `staff`, and every local account is in `staff`. `~/.config` was `0755`. A `0644` secrets file under `~` is therefore readable by every other local account. Confirm with `ls -ld ~ ~/.config` (read-only) and record the result as dated host evidence.
- **Setting a mode on create doesn't enforce it.** `os.open(path, O_CREAT | O_TRUNC, 0o600)` and `umask 077; > file` apply the mode only when they create the file. A file that already exists, or that the user wrote by hand from an example, keeps its old mode. Do not flag BSD/macOS `install -m 600` for this pattern; it applies the requested mode when replacing an existing destination. Check two things:
  - whether the loader checks `st_mode & 0o077` and the owner;
  - whether the docs or the success message claim "chmod 600" unconditionally. Check that claim against the code (SKILL.md Step 4, Secrets: "Verify the target's own security claims").
- **Severity:** Low at the documented baseline, when the tool's own setup command creates the file. Give Medium as the alternate when the docs also allow hand-writing the file and the Mac may have more than one local account (`security.md`, Credential severity: world-readable file, narrow scope).
- **Fix pattern:**
  - `mkdir(mode=0o700)` for the config directory;
  - `os.fchmod(fd, 0o600)` after opening, with `O_NOFOLLOW`;
  - a mode and owner check on load;
  - or the login Keychain, read with `security find-generic-password -w`, which keeps the secret out of argv.

---

### Release pipelines

Release CI that writes to a distribution channel (a Homebrew tap, a package repository, an update feed) is in scope (SKILL.md Step 2, item 7).

- **Rating.** A deploy token passed to a third-party action pinned to a mutable tag (`@v4`) is Low (Origin: Code + Deployment). Give Medium as the alternate when the token's scope is broader than that channel. Token scope is never visible in the repo, so put it in the Operator baseline.
- **Fix.** Pin to the full commit SHA, use a fine-grained token limited to the channel, and add Dependabot for `github-actions`.
- **CI without secrets.** CI jobs that hold no secrets and don't deploy, but use mutable tags, are Info and aren't scored.
- **Distribution manifests in other repos:** Homebrew tap formulae (`homebrew-<name>/Formula/*.rb`), pkg build repos, and Jamf script repos. They define the installed layout, the real invocation path, whether the shebang is rewritten, and which interpreter actually runs, which can differ from the one declared (for example, `depends_on "python@3.12"` with an unrewritten `#!/usr/bin/env python3`). Fetch them when that is cheap, record their SHA, and treat them as context: they are outside the target and aren't scored. If release CI writes to one, note which token it uses (see **Rating** above).

---

### Destructive scope (Rule 14 overreach)

A documented, admin-gated removal is not a finding. A removal that reaches past what its documentation says is one. Compare each deletion list with what else lives in the same namespace:

- **Parent-directory deletes in a vendor namespace.** `rm -rf "/Library/Application Support/<Vendor>"` or `/Library/Logs/<Vendor>` removes data that belongs to sibling products from the same vendor: for example an EDR agent, MDM agent logs, and updaters. A "remove the app suite" action that does this impairs security tooling nobody chose to remove. The code should delete the product-owned children, not the parent.
- **`pkgutil --forget` on sibling receipts.** Check whether the receipt list includes products that the tool offers as a separate action (for example, the EDR agent's receipt inside a "remove the app suite" action when EDR removal is its own action).
- **Parity isn't evidence.** A deletion list copied verbatim from an upstream or package-era script inherits that script's overreach. Say that it is inherited in the Origin line, but keep the severity.
- **Name what the other products store there, and label it inferred.** Vendor subpaths such as `/Library/Application Support/<Vendor>/<EDR product>` come from vendor documentation, not from the target's code.
- **Remove before download.** `rm -rf "$app"` followed by a download-and-install that can fail leaves the user with no app. Repairing a damaged bundle this way is defensible; replacing a working app is not.
- **Signature checks pin the publisher, not the version.** A Developer ID or Team ID check blocks foreign packages but still accepts an older, vulnerable build from the same vendor. When a manifest or feed chooses the package URL or version, check that every hop requires `https://` (not just the final URL) and that a minimum-version floor exists.

Check these even when a prior report didn't flag them. Removal lists are long and easy to skim past.
