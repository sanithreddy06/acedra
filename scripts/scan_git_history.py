#!/usr/bin/env python3
"""Scan every commit's added lines, and every file name ever committed, for exposed credentials.

A dependency-free companion to the CI secret scanners (detect-secrets on the working tree, gitleaks on
history). Usage, from the repository root:

    python scripts/scan_git_history.py          # exit status 1 if anything is found

Known development placeholders (the built-in dev secret, the published demo passwords, example URLs)
are listed in ALLOWED and ignored.
"""
import re
import subprocess
import sys

PATTERNS = {
    "private key block": re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY"),
    "AWS access key id": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{60,}\b"),
    "Slack token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"),
    "Stripe key": re.compile(r"\b[sr]k_live_[0-9a-zA-Z]{20,}\b"),
    "LLM provider key": re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_\-]{32,}\b"),
    "JSON Web Token": re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"),
    "password in URL": re.compile(r"\b[a-z][a-z0-9+.\-]*://[^\s:/@'\"]+:([^\s@/'\"${}<>]{4,})@"),
    "assigned secret": re.compile(
        r"(?i)\b(?:secret_key|api_key|apikey|smtp_password|llm_api_key|embedding_api_key|postgres_password|"
        r"access_token|auth_token|client_secret)\b\s*[:=]\s*['\"]?([A-Za-z0-9+/_\-!@#%^&*.]{12,})"),
}
# Development and documentation placeholders that are meant to be public.
ALLOWED = re.compile(
    r"dev-only-insecure-secret-change-me|acedra-dev-password|acedra-ci|smart_campus|campus_secure_pwd|"
    r"REPLACE_WITH|change-this-in-production|user:pass@|u:p@|://acedra:\$|your[-_]|example|changeme|change-me|placeholder|x{8,}|\*{3,}|"
    r"k9Zr2mQx7LpT4vNc8WdY1sHb6JfG3aEu0RoXiMqV|settings\.|os\.environ|getenv|token_urlsafe|None\b|"
    r"secrets\.|create_access_token|payload|response|\.json\(\)|Optional\[|: str\b", re.I)
SENSITIVE_NAMES = re.compile(r"(^|/)(\.env(\.[^/]*)?|id_rsa|id_ed25519|.*\.pem|.*\.p12|.*\.pfx|.*\.key|credentials\.json)$")
ALLOWED_NAMES = re.compile(r"\.env(\.production)?\.example$")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, errors="replace").stdout


def main() -> int:
    findings = []
    commits = git("rev-list", "--all").split()
    for name in sorted(set(git("log", "--all", "--pretty=format:", "--name-only", "--diff-filter=A").split("\n"))):
        if name and SENSITIVE_NAMES.search(name) and not ALLOWED_NAMES.search(name):
            findings.append(("sensitive file name", name, "", ""))
    commit = path = ""
    for line in git("log", "--all", "-p", "--no-color", "--unified=0", "--pretty=format:@@commit %h").split("\n"):
        if line.startswith("@@commit "):
            commit = line.split()[1]
        elif line.startswith("+++ b/"):
            path = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            if path.endswith(("package-lock.json", "openapi.ts")) or len(line) > 2000:
                continue
            for label, pattern in PATTERNS.items():
                match = pattern.search(line)
                if match and not ALLOWED.search(line):
                    findings.append((label, path, commit, line[1:].strip()[:110]))
    print(f"Scanned {len(commits)} commits.")
    for label, path, commit, text in findings:
        print(f"  [{label}] {path} {commit} {text}")
    print(f"{len(findings)} finding(s).")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
