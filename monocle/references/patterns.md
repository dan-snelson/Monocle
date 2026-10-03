# 🔍 Pattern Quick Reference

## Purpose

A lookup table of common Jamf, macOS, and Python patterns, with why each matters and which views it usually feeds. Load it during SKILL.md Step 4 and while building the fact sheet in Step 3. Each hit belongs in the fact sheet with `file:line`. The table is a spotting aid, not a checklist: Step 4 stays mandatory, and every hit still needs confirming in the code.

---

| Pattern | Why it matters | Usual view(s) |
|---|---|---|
| Jamf policy script (runs as root, `$1`–`$3` reserved) | Every command runs with full privileges | Security, Engineer |
| `$4`–`$11` used for credentials | Visible in the Jamf UI, and in `ps` `argv` to every local user for the whole run, even when the script hands them to `curl` over stdin. Origin is Platform + Deployment (Rule 13): Jamf's delivery mechanism, not a code defect | Security |
| Wrapper or pkg `postinstall` runs the script without `"$@"` | Jamf params silently dropped; every default applies (for example, reporting stays in `test`) | Manager, Engineer |
| Script copies `${0:A}` into `/Library/…` plus a root LaunchDaemon | If any deploy path launches it from `/var/tmp` or another user-writable location, the persistent root copy is attacker-controlled | Security, Executive |
| Test / Development / Debug mode writes the same canonical report or cache as production | Synthetic results later uploaded as real compliance data | Security, Manager |
| Root `PATH` includes `/usr/local/bin`, or calls `/usr/local/bin/<tool>` | Intel Homebrew makes it user-owned; binary swap gives root | Security |
| `rm -f /var/tmp/prefix_*` glob in cleanup | Deletes concurrent instances' files (a Silent policy run alongside a Self Service run); their UI or state breaks mid-run. Not a security issue | Engineer |
| Webhook or API `curl` POST without `--fail` | HTTP errors logged as success | Engineer |
| README or CHANGELOG security claims ("no longer in process list") | Claims, not evidence; verify against code | Security |
| `loggedInUser=$(stat -f%Su /dev/console)` with no `loginwindow`/`_mbsetupuser` check | Breaks at the login window and during Setup Assistant | Engineer |
| `sudo -u "$user" command` without `launchctl asuser` | Runs in the wrong GUI session; UI and `defaults` calls may silently fail | Engineer |
| `curl … \| bash` / `sh -c "$(curl …)"` | Remote code execution as root; integrity depends on the remote host | Security, Executive |
| `curl -k` / `--insecure` | TLS verification disabled | Security |
| `/tmp/fixed-name` files | Predictable path; symlink attacks as root | Security |
| `/Library/Application Support/<vendor>/…` set `root:staff 0775` (no sticky bit), then root `chown`/`chmod` without `-h` at daemon start | Any local user swaps the shared file for a symlink; the next start hands them the target (LPE) | Security, Executive |
| Root log writer calls `open()` with `O_CREAT` and `O_APPEND` but no `O_NOFOLLOW` on a user-writable path | Root appends to, or creates, any file the symlink names | Security |
| Bundle generator: `copyItem`/`cp -R` from a user-writable directory, then `zip -r` without `-y` | Planted symlinks pull the generating user's private files into the archive | Security |
| Redaction via a fixed key denylist; logs copied unscrubbed | New secret-bearing keys and log lines leak by default | Security, Engineer |
| DEBUG always written to the shipped log, whatever the debug setting | Larger disclosure surface in every support bundle | Security, Engineer |
| Bundle metadata includes `NSUserName()` / `id -Gn` and is meant for public issues | Identity and privilege-group tiers published | Security |
| Root writes `/var/tmp/fixed`, then `chown "$loggedInUser"` it | The user can swap it for a symlink; the next `chown` gives them any root file (LPE) | Security, Executive |
| Root trusts a `/var/tmp` cache or report checked only by mtime or syntax | Users can forge results before upload or scoring | Security, Executive |
| `base64 -d > /var/tmp/x.zsh; zsh /var/tmp/x.zsh` (self-extracting wrapper) | Race between write and execute gives root | Security |
| `curl --header "Authorization: … ${token}"` | Token visible in `ps` for the whole request | Security |
| `[[ $4 == Debug ]] && set -x` | Every param, including secrets, lands in the Jamf policy log | Security |
| Script installs a copy of itself plus a root LaunchDaemon | Persistence; the copy becomes a privilege-escalation target | Security, Manager |
| Client copy built by `awk`/`sed` edits to its own source | Breaks silently when comments or list order change; check whether the substitution result is verified (`grep -qF`, `zsh -n`). Better fix: pass the mode as LaunchDaemon `ProgramArguments` and guard on an env var instead of editing the source | Manager, Engineer |
| Cache or self-update gated on the `scriptVersion=` string only | Edits without a version bump never deploy. It becomes permanent when the fast-path `exit` comes before the reinstall step and a nightly job keeps the cache fresh | Manager, Engineer |
| External check or EA runs `defaults write /Library/Preferences/.GlobalPreferences.plist` | Permanent, user-visible system change from a read-only-looking check. A "temporary" change restored only by `trap … EXIT` persists after SIGKILL, a crash, or power loss | Executive, Manager |
| pkg payload in `/usr/local/bin` that `postinstall` then runs | Root runs a file in a directory that may be user-owned (Intel Homebrew) | Security |
| `pgrep -a "Name"` then `kill "$pids"` | Substring match kills other tools' processes; several PIDs in one quoted argument give `kill: illegal pid`, so nothing is killed | Engineer |
| `pkill -9 'Sync'` / `pkill -9 'Agent'` (a short or generic name) without `-x` | Matches any process whose name contains the string, including other vendors' extensions | Engineer |
| `launchctl asuser … "$@"` with fallback to `sudo -u … "$@"` on any non-zero exit | Every legitimately failing command (for example, `security find-generic-password` returning 44) runs twice, the second time outside the GUI session; prompts and `open` can fire twice | Engineer |
| `is-at-least "$min" "$ver"` with `$ver` possibly empty | Inconsistent: `is-at-least 15.5 ""` is false but `is-at-least 2.0.0.100 ""` is true (zsh 5.9). Empty versions from an unreadable `Info.plist` pick the wrong branch, for example a legacy reinstall, or they pass a version gate | Engineer |
| `codesign -dv … \| awk '/TeamIdentifier/'` as a trust check | Displays the embedded Team ID without validating the signature; use `codesign --verify --strict -R='anchor apple generic and certificate leaf[subject.OU] = "TEAMID"'` | Security |
| Root `mkdir -p` inside the user's home or `~/Library/Containers/…`, then `chown` of only the leaf | Parent directories stay `root:wheel`; after deleting an app container, this rebuilds it without container metadata and may break the app's next launch | Engineer |
| `rm -rf "${TMPDIR}/…"` in a root script | Root's `TMPDIR` (or unset, giving `/…`), never the console user's; the cleanup silently does nothing | Engineer |
| Root `rm -rf` of a vendor parent directory (`/Library/Application Support/<Vendor>`, `/Library/Logs/<Vendor>`) | Deletes sibling products' data: EDR, MDM agent, and updaters (see `specialized-checks.md`, Destructive scope) | Security, Executive |
| Manifest or feed URL from preferences fetched without an `https://` check | Network attacker chooses the version or package; a publisher-only signature check still allows a downgrade | Security |
| `case` with `*)` falling through to `production` or another high-impact mode | A typo in a Jamf parameter enables production behavior | Engineer |
| Persistent job runs `networkQuality`, `softwareupdate --list`, or chained `jamf policy` nightly | Fleet-wide bandwidth and Jamf load within the jitter window, and again on wake | Executive, Manager |
| App bundle copied and re-signed ad hoc (`codesign --force --sign -`) | Loses its Team ID, so PPPC/TCC profiles keyed to the vendor stop matching | Engineer |
| JSON payload built by heredoc interpolation | A `"` in a hostname breaks the payload silently; prefer `jq -n --arg` | Engineer |
| Heavy discovery (`system_profiler`, disk-wide `mdfind`) before a root check or cache exit | Wasted runtime; noisy errors when not run as root | Engineer |
| `jamf recon` / `jamf policy -event` calls | Chained policies; hidden dependency and runtime | Manager, Engineer |
| `profiles`, `security`, `dscl`, `sysadminctl`, `fdesetup` | Identity, credential, or encryption changes | Security, Executive |
| `launchctl load` / `bootstrap` + plist write | Persistence | Security, Manager |
| `defaults write` on `/Library/Preferences/…` | System-wide config change | Manager |
| `killall`, `shutdown`, `reboot`, `softwareupdate -i -a --restart` | User disruption, data loss risk | Executive, Manager |
| `osascript -e 'display dialog'` from root without `asuser` | Dialog never appears or hangs | Engineer |
| Extension Attribute without `<result></result>` on all paths | Blank or incorrect inventory | Engineer, Manager |
| Hardcoded `jss.example.com` / org-specific URLs | Environment coupling | Manager |
| `swiftDialog` (`/usr/local/bin/dialog`) dependency | External binary; version drift | Manager, Engineer |
| `smtplib` / `imaplib` / `poplib` / `ftplib` TLS without `context=` | Python's default context is `CERT_NONE` with no hostname check, so credentials go to any server that answers (SKILL.md Step 4, Secrets: Library TLS defaults) | Security |
| Network call without a timeout in a scheduled job (`smtplib.SMTP(host, port)`, `urlopen(req)`, `curl` without `--max-time`) | Python's `smtplib`, `imaplib`, `ftplib`, raw `socket`, and `urlopen` without `timeout=` inherit `socket.getdefaulttimeout()`, which is `None`. A stalled server blocks forever; launchd won't start the next interval while the job is alive, so the schedule silently stops | Engineer, Manager |
| `os.open(path, O_CREAT, 0o600)` or `umask 077; > file` presented as "chmod 600" | The mode applies only on creation; an existing or hand-written file keeps `0644`, which other local accounts can read under a `staff`-group home | Security |
| Hardcoded launchd `PATH` without `/usr/local/bin` | Breaks Intel Homebrew; `brew doctor` fails on every scheduled run ("Homebrew's "bin" was not found in your PATH") | Engineer |
| Legacy `launchctl load` / `unload` | Exit status isn't a reliable success signal, so "schedule installed" can print when nothing loaded; use `bootstrap`/`bootout` against `gui/$UID` (or `system`) and verify with `launchctl print`. Label it inferred unless you observed the failure | Engineer |
| Release workflow passes a deploy token (tap, package repo, update feed) to a third-party action at a mutable tag | Repointed tag steals the token and ships code to every user; worse when the tool upgrades itself on a schedule | Security |
| `${(P)var}` or `printf -v "$var"` where `var` is built from user-controlled input (for example, the console user's language or another per-user preference read by root) | Subscript `$(…)` runs as root (`(P)` when the base variable is set, `printf -v` always); case folding doesn't stop it on case-insensitive APFS | Security |
| Root matches substrings in `/var/log/install.log` (or another syslog file) to decide state | Unprivileged `logger -p install.<level>` appends lines there; forged entries change what root decides and what inventory reports | Security, Engineer |
| Unified log `process ==` used as trust proof | Filters by executable name, not authenticated sender identity. Use it as one clue, not proof; prefer root-owned state or an API that exposes authenticated state | Security |
| `until <app is running>; do sleep …; done` with no counter in a scheduled root job that holds a PID lock | One stuck run blocks every later run until reboot, with no error | Engineer, Manager |
| Ignored exit code plus parse fallback to `{}` / `[]` | An outage reads as "nothing to do" and the run reports OK | Engineer, Manager |
