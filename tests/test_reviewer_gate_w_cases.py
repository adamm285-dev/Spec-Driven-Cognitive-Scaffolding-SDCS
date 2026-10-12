"""Gate W against secret formats it claims to block, and ledger prose it must not.

Written by the reviewing agent, 2026-09-22 (gate audit, batch 1). Of eight common secret
formats, v1.8.1's working copy caught one by rule (OpenAI `sk-`). A Slack token was also
"caught" -- as a PHONE NUMBER, because its digits happen to fit that pattern. Missed: the
Anthropic API key, Stripe, PEM private keys, Google OAuth client secrets, GitHub OAuth
tokens, JWTs. On three real ledgers (production decisions.md and CLAUDE.md, SDCS's own
decisions.md) it raised 0 false alarms, so the prose side is the population to protect.

Every secret below is FAKE and assembled at runtime from fragments, so no file in this
repo contains a secret-shaped literal for a push-protection scanner to trip on.
"""

from __future__ import annotations

import pytest

from sdcs.warehouse import scan_for_sensitive_data


def _fake(*parts: str) -> str:
    return "".join(parts)


SECRETS = {
    "anthropic_api_key": _fake("sk-", "ant-", "api03-", "A1b2C3d4" * 11, "-AAAA"),
    "stripe_live_key": _fake("sk", "_live_", "51Hx" * 6),
    "slack_bot_token": _fake("xo", "xb-", "1234567890-", "1234567890123-", "AbCd" * 6),
    "pem_private_key": _fake("-----BEGIN ", "RSA PRIVATE KEY-----"),
    "google_oauth_secret": _fake("GOC", "SPX-", "AbCdEfGh" * 3, "Ab12"),
    "github_oauth_token": _fake("gh", "o_", "A1b2" * 9),
    "jwt": _fake(
        "eyJhbGciOiJIUzI1NiJ9",
        ".",
        "eyJzdWIiOiIxMjM0NTYifQ",
        ".",
        "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
    ),
    "openai_key": _fake("sk-", "A1b2C3d4" * 6),
    # Added pass 3: held-out variants the pass-2 patterns missed. PKCS#8 is the header in
    # every Google service-account JSON; the pass-2 rule required a type word (RSA, EC).
    "pkcs8_private_key": _fake("-----BEGIN ", "PRIVATE KEY-----"),
    "stripe_restricted_key": _fake("rk", "_live_", "51Qz" * 6),
}

LEDGER_PROSE = [
    "34 failed / 2123 passed / 19 skipped in 1h38m, of which my engine changes caused NONE.",
    "p5 walls are 0.36:78% 1.32:18%, dimensions 0.48:100%.",
    "Shipped in c410d7a this morning, withdrawn the same day (v1.8.1, 2026-08-01).",
    "test_plan 11/4376.55  MAKI 19/3064.49  PA-Largo 5/1725.90",
    "Envelope of 123.4 x 82.8 ft on a 42x30 sheet; 544 commits, 538 windows.",
]


@pytest.mark.parametrize("name", sorted(SECRETS))
def test_gate_w_catches_the_secret_by_a_secret_rule(name):
    hits = scan_for_sensitive_data(f"config value = {SECRETS[name]}")
    by_secret_rule = [h for h in hits if h.get("type") not in ("phone", "email", "ipv4")]
    assert by_secret_rule, f"{name} passed Gate W (hits: {[h.get('label') for h in hits]})"


@pytest.mark.parametrize("line", LEDGER_PROSE)
def test_gate_w_passes_measurement_prose(line):
    assert scan_for_sensitive_data(line) == []
