# Executive View

## Purpose

The Executive view tells a non-technical decision-maker, in under a minute of reading:

- What the script does for the business.
- What could go wrong, and how many people or devices it would affect.
- Whether to run, change, or stop it.

The reader will not read the code or the other views. Treat this view as the only part of the report they see.

---

## Structure and tone

Use exactly this structure:

```markdown
## Executive View

**In one sentence:** {What it does and why it exists, in business terms.}

- {Bullet 1}
- {Bullet 2}
- {Bullet 3}
- {… up to 6 bullets total}

**Monocle Score:** {n}/100 ({band}){, or {n2}/100 ({band2}) if {plain-language condition}}

**Recommendation:** {Approve | Approve with conditions | Hold | Do not run} — {one sentence explaining why, plus the conditions if any.}
```

Rules:

- **1–6 bullets.** Use as many as the real risks and facts need, and no more. Don't pad a low-risk view to reach a count (SKILL.md Rule 7).
- **Plain language.** Don't use jargon, command names, file paths, or line numbers. Write "administrator-level access to every Mac", not "runs as root via Jamf policy". Mention product names (Jamf, Okta, Slack) only when the reader would recognize them.
- **Lead with impact.** Each bullet states a consequence first and the cause second, if at all.
- **Quantify when possible.** "All managed Macs", "about 30 seconds per device", "requires a restart", "one person maintains it".
- **Neutral, confident tone.** Don't be alarmist, and don't hedge the point away. Use "could" only for real uncertainty.
- **One recommendation.** Always include one. Never write "it depends" without saying on what.
- **Monocle Score line.** Copy the score and band from the report header (SKILL.md, Step 5, Monocle Score). The first number assumes the tool is deployed as documented. Write the condition for the alternate as the administrator action it depends on, in plain language, for example "or 25/100 (Poor) if any Self Service policy offers every action". Leave the breakdown out of this view; it has its own section. The score line doesn't count toward the 1–6 bullets.
- **Powerful features are not defects.** When the tool can do something drastic on purpose, and administrators control whether users see it, say who controls it. Don't present it as a flaw. Write "Administrators choose which actions each policy offers; unless they do, users see all 20, including removing the security agent", not "The tool lets any user remove the security agent". Save risk language for what the code itself gets wrong (SKILL.md Rule 14).

Recommendation levels:

| Level | Use when |
|---|---|
| **Approve** | No Critical/High security findings; failure is low-impact and reversible |
| **Approve with conditions** | Safe to run once specific, named fixes or controls are in place (for example, "after failures are reported correctly", "pilot on 5% of devices first", or administrator configuration from the Operator baseline such as "once every Self Service policy limits the menu") |
| **Hold** | Material risk or unknowns that need an owner decision or more information before running |
| **Do not run** | A Critical security finding, likely data loss, or behavior that can't be verified (obfuscated or remote code) |

---

## Key questions the summary must answer

1. **What does it do for us?** State the business purpose, not the technical mechanism.
2. **Who or what does it touch?** Blast radius: one Mac, a group, or the whole fleet? Users, servers, or third-party services?
3. **What is the worst realistic outcome?** Data loss, outage, security exposure, user disruption, or compliance gap.
4. **How likely is that outcome?** Tie it to an observed cause, not a hypothetical one.
5. **Can we undo it?** Reversible, partly reversible, or permanent.
6. **Is anyone accountable for it?** Only when ownership is unclear or rests on one person.
7. **What should we do?** The recommendation.

Not every question needs its own bullet. Combine them where they fit naturally.

---

## Prioritization

Put bullets in this order:

1. The top risk from the Security view (Critical or High), if any.
2. User or business disruption (restarts, prompts, downtime, data loss).
3. Blast radius and reversibility.
4. Ownership or maintenance risk, if significant.
5. Positive notes (well-built, low-risk). Include at most one, and only if the view needs it for balance.

When there are no significant risks, say so plainly: "Low risk: it only reads settings and changes nothing."

---

## Good vs weak examples

### Weak

```markdown
**In one sentence:** This script is a zsh script that uses Jamf parameters and curl to do various things.

- The script uses root privileges.
- There are some security concerns that should be looked at.
- Error handling could be improved.
- Best practices should be followed.

**Recommendation:** Review further.
```

Why it's weak: it describes mechanism instead of purpose, uses jargon, makes vague claims, gives no blast radius, and recommends nothing.

### Good

```markdown
**In one sentence:** Sets up new Macs automatically at first login: it installs standard apps, applies security settings, and shows the user progress on screen.

- **Runs with full administrator access on every new Mac.** A mistake affects every device enrolled while it's active.
- **Contains a password for our device-management system written into the script itself.** Anyone who can read the script can copy it and use it to change settings across the fleet.
- **Failures are hidden.** If an app fails to install, the Mac still reports "success", so gaps show up later as help desk tickets.
- **Needs internet and one download site to be available.** If that site is down, setup stalls for new hires on day one.
- **Maintained by one person.** No documentation or tests exist outside their knowledge.

**Monocle Score:** 32/100 (Poor)

**Recommendation:** Do not run — the password in the script gives anyone who can read it control of the whole fleet; remove it and fix the false "success" reporting before the next hiring wave.
```

### Good (low-risk case)

```markdown
**In one sentence:** Reports each Mac's battery health to our inventory so we can plan replacements.

- **Low risk.** It only reads information and changes nothing on the device.
- **Runs in under a second, invisibly to users.**
- **May report "unknown" on desktop Macs,** which have no battery. That's expected, not an error.

**Monocle Score:** 100/100 (Excellent)

**Recommendation:** Approve — no changes needed.
```

---

## Language notes

The Executive view never names languages or constructs. Translate them into their business impact:

| Technical fact | Executive phrasing |
|---|---|
| Shell/Python/AppleScript runs as root | "Runs with full administrator access" |
| Jamf policy scoped to All Computers | "Runs on every managed Mac" |
| `curl … \| bash` | "Downloads and runs code from the internet without checking it" |
| Hardcoded API credentials | "Contains a stored password for {system}" |
| No `set -e`, `\|\| true`, bare `except` | "Failures are hidden or reported as success" |
| `shutdown -r`, `killall`, forced quit | "Restarts the Mac or closes apps, and users may lose unsaved work" |
| AppleScript `display dialog` | "Shows the user a pop-up" |
| Requires Python 3 / `jq` / swiftDialog | "Depends on extra software that must already be installed" |
| Writes a LaunchDaemon | "Installs something that keeps running in the background after restarts" |
| `profiles` / `fdesetup` / `sysadminctl` | "Changes security, encryption, or user-account settings" |
| Obfuscated or base64-encoded payload | "Contains hidden code that we can't verify" |
