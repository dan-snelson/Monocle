# Specialized Checks

## Purpose

Step 4 checks that apply only to some targets. Load this file when its trigger applies; each section's checks are then mandatory, like the rest of Step 4.

- **Data scan:** the input is a diagnostic or support bundle (SKILL.md Step 1 E), or the code writes logs or reports meant to be shared.
- **Destructive scope:** the code deletes, uninstalls, resets, or forgets package receipts.

---

### Data scan (bundles and logs)

For Step 1 E inputs, and for any shipped log the code writes, pattern-scan the text. It reads straight from the archive, so it works in read-only mode:

```bash
d() { unzip -p "$zip" '*.log' '*.txt' '*.json' '*.jsonl' '*.plist' 2>/dev/null; }
d | grep -inE 'bearer|authorization:|token|secret|passw(or)?d|api[_-]?key|hooks\.slack\.com|webhook\.office\.com|logic\.azure\.com' | cut -c1-200 | head -40
d | grep -oE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' | sort | uniq -c | head
d | grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b|\b([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b' | sort | uniq -c | head
d | grep -inE 'serial|hostname|computername|udid|IOPlatform' | cut -c1-200 | head
d | grep -oE '/Users/[^/ ":]+' | sort | uniq -c
d | grep -oE 'https?://[^ "<>]+\?[^ "<>]+' | sort -u | head -20   # query strings can carry tokens
d | grep -oE '\[(DEBUG|INFO|NOTICE|WARNING|ERROR|FAULT)\]' | sort | uniq -c
```

Many hits are label or product names ("1password", "gitcredentialmanager"), so triage each one. Public vendor download URLs and UUIDs in them aren't secrets. Fill the **Disclosure surface** row with what remains, and credit redaction that worked (`<redacted>` in place of a webhook URL).

---

### Destructive scope (Rule 14 overreach)

A documented, admin-gated removal is not a finding. A removal that reaches past what its documentation says is one. Compare each deletion list with what else lives in the same namespace:

- **Parent-directory deletes in a vendor namespace.** `rm -rf "/Library/Application Support/Microsoft"` or `/Library/Logs/Microsoft` removes data that belongs to sibling products from the same vendor: for example an EDR agent (Microsoft Defender), MDM agent logs (Intune), and updaters (Edge). A "remove the office suite" action that does this impairs security tooling nobody chose to remove. The code should delete the product-owned children, not the parent.
- **`pkgutil --forget` on sibling receipts.** Check whether the receipt list includes products that the tool offers as a separate action (for example, the EDR agent's receipt inside a "remove the office suite" action when EDR removal is its own action).
- **Parity isn't evidence.** A deletion list copied verbatim from an upstream or package-era script inherits that script's overreach. Say that it is inherited in the Origin line, but keep the severity.
- **Name what the other products store there, and label it inferred.** Vendor paths such as `/Library/Application Support/Microsoft/Defender` and `/Library/Logs/Microsoft/mdatp` come from vendor documentation, not from the target's code.
- **Remove before download.** `rm -rf "$app"` followed by a download-and-install that can fail leaves the user with no app. Repairing a damaged bundle this way is defensible; replacing a working app is not.
- **Signature checks pin the publisher, not the version.** A Developer ID or Team ID check blocks foreign packages but still accepts an older, vulnerable build from the same vendor. When a manifest or feed chooses the package URL or version, check that every hop requires `https://` (not just the final URL) and that a minimum-version floor exists.

Check these even when a prior report didn't flag them. Removal lists are long and easy to skim past.
