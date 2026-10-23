# Python Checks

## Purpose

Language checks for Python targets, for SKILL.md Step 4. Load this file at the start of Step 4 when the fact sheet's Language(s) row lists Python code, before the manual checks. Each section names the view its hits usually feed; every hit still gets a ledger row (`scoring-procedure.md`).

---

### Security checks

- **`subprocess` with `shell=True`** and interpolated strings leads to injection. Prefer list arguments.
- **`os.system`, `os.popen`, `eval`, `exec`, `pickle.loads`, and `yaml.load` (without `SafeLoader`)** on untrusted data.
- **`requests` with `verify=False`,** or `ssl._create_unverified_context()`.
- **`tempfile.mktemp`** (racy) vs `mkstemp`/`NamedTemporaryFile`.
- **Secrets in source,** in `argparse` defaults, or written to logs through `logging.debug(f"{token}")`.
- **Python 2 `input()`** evaluates what it reads. Flag it if the script targets Python 2.
- **Missing interpreter:** macOS no longer bundles `/usr/bin/python3` without the CLT. Code that falls back to an arbitrary `python3` on `PATH` could run a user-installed interpreter as root.
- **The stdlib doesn't verify TLS for mail and FTP clients.** Called without `context=`, these use `ssl._create_stdlib_context()`, which is `CERT_NONE` with no hostname check (observed on 3.9.6 and 3.14.7):
  - `smtplib.SMTP_SSL` and `SMTP.starttls()`
  - `imaplib.IMAP4_SSL` and `IMAP4.starttls()`
  - `poplib.POP3_SSL` and `POP3.stls()`
  - `ftplib.FTP_TLS`

  A network attacker can present any certificate and receive the login. `urllib.request` and `http.client` do verify by default. Fix: create `ctx = ssl.create_default_context()` once and pass `context=ctx` to each constructor and to `starttls()`/`stls()`. A server without STARTTLS raises an error, so these clients fail closed against a downgrade. The risk is interception, not stripping. Rate the credential with **Credential severity** in `security.md` (unverified-TLS row).
- **Credit when present:** `subprocess` called with argument lists and never `shell=True`; values interpolated into an AppleScript string literal escaped for `\` and `"`; plist values passed through `xml.sax.saxutils.escape`.

### Engineer checks

- **Version:** check the shebang (`/usr/bin/python` is gone on macOS 12.3+), f-strings, and walrus operators. Python 2 syntax is a blocking issue on current macOS.
- **`subprocess`:** prefer `subprocess.run([...], check=True, capture_output=True, text=True)`. Flag `shell=True`, `os.system`, and unchecked `Popen`.
- **Exceptions:** flag bare `except:` and `except Exception: pass`. Suggest catching specific exceptions (`subprocess.CalledProcessError`, `FileNotFoundError`, `plistlib.InvalidFileException`).
- **Plists:** use `plistlib` rather than shelling out to `defaults read` and parsing text.
- **Paths:** use `pathlib.Path` and `Path.home()`. Note that `home` is root's when the script runs as root, which is a common bug in Jamf-run Python.
- **Mutable default args, globals as state, and `if __name__ == "__main__":` missing** (which makes the module untestable).
- **Secret parsing:** `value.strip().strip('"').strip("'")` and `getpass().strip()` silently change secrets that start or end with quotes or spaces, and the result shows up as a misleading auth failure. Strip only a matched pair of surrounding quotes, and don't strip `getpass` input.

### Manager checks

- Check for `requirements.txt`/`pyproject.toml`. Missing or unpinned dependencies are a fragility risk.
- Note the interpreter source: system `python3` needs the CLT, and a bundled one (such as MacAdmins Python) is a dependency to track.
- If tests exist (`tests/`, `pytest`), note coverage of the risky paths, not just their presence.
