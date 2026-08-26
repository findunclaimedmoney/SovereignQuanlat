"""
Sovereign Quant — LICENSE SIGNING TOOL (seller-only, do NOT distribute)
========================================================================

This script is the other half of the license system in app.py. It is the
ONLY place that can mint a license key that app.py will accept, because it's
the only place that holds the private key.

DO NOT:
  - put this folder in the customer-facing build
  - commit `sovereign_quant_private_key.b64` to a public (or even private)
    git repo
  - email/upload/paste the private key file anywhere

If `sovereign_quant_private_key.b64` ever leaks, anyone who has it can mint
free "Institutional" licenses forever — the fix at that point is to generate
a brand new keypair, update PUBLIC_KEY_B64 in app.py, and treat every key
signed with the old private key as compromised (customers who already have
valid keys keep working since app.py only checks the signature; you'd just
stop trusting the leaked private key for anything new — for a hard cutover
you'd need to rev a "key version" field, which isn't implemented here).

Usage
-----
Generate a new keypair (only do this once — re-running invalidates every
key you've already issued, since old keys were signed with the old private
key and the app would need the new PUBLIC_KEY_B64 to trust them):

    python license_signing_tool.py generate-keypair

Issue a license key for a paying customer:

    python license_signing_tool.py issue --name "Jane Trader" --tier Professional --days 365

Verify a key locally before sending it to a customer (sanity check):

    python license_signing_tool.py verify "PAYLOAD_B64.SIGNATURE_B64"
"""
import argparse
import base64
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

KEY_FILE = Path(__file__).resolve().parent / "sovereign_quant_private_key.b64"
VALID_TIERS = ("Community", "Professional", "Institutional")


def cmd_generate_keypair(_args):
    if KEY_FILE.exists():
        confirm = input(
            f"{KEY_FILE.name} already exists. Overwriting it INVALIDATES every "
            f"license key you've issued so far (customers' keys are signed with "
            f"the current private key). Type 'yes' to proceed: "
        )
        if confirm.strip().lower() != "yes":
            print("Aborted.")
            return

    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()

    priv_bytes = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    KEY_FILE.write_text(base64.urlsafe_b64encode(priv_bytes).decode())
    pub_b64 = base64.urlsafe_b64encode(pub_bytes).decode()

    print(f"\nPrivate key saved to: {KEY_FILE}")
    print("Keep this file secret. Back it up somewhere safe (password manager, "
          "encrypted drive) — if you lose it, you can no longer issue license "
          "keys that match what's already been distributed.\n")
    print("Now update PUBLIC_KEY_B64 in app.py to:\n")
    print(f'    PUBLIC_KEY_B64 = "{pub_b64}"\n')


def _load_private_key() -> Ed25519PrivateKey:
    if not KEY_FILE.exists():
        sys.exit(f"No private key found at {KEY_FILE}. Run 'generate-keypair' first "
                  f"(only if you haven't already issued keys with an existing one!).")
    raw = base64.urlsafe_b64decode(KEY_FILE.read_text().strip())
    return Ed25519PrivateKey.from_private_bytes(raw)


def cmd_issue(args):
    if args.tier not in VALID_TIERS:
        sys.exit(f"--tier must be one of {VALID_TIERS}")

    priv = _load_private_key()
    payload = {
        "licensee": args.name,
        "tier": args.tier,
        "duration": int(args.days),
        "created_at": args.created_at,
    }
    payload_json = json.dumps(payload, sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")

    signature = priv.sign(payload_b64.encode())
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

    key = f"{payload_b64}.{signature_b64}"
    print("\nLicense key (send this to the customer to paste into "
          "'Activate New Licence Key' in the sidebar):\n")
    print(key)
    print()


def cmd_verify(args):
    from importlib import import_module
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        app_module_src = (Path(__file__).resolve().parent.parent / "app.py").read_text()
    except FileNotFoundError:
        sys.exit("Could not find ../app.py to read PUBLIC_KEY_B64 from.")

    marker = 'PUBLIC_KEY_B64 = "'
    start = app_module_src.find(marker)
    if start == -1:
        sys.exit("Could not find PUBLIC_KEY_B64 in app.py.")
    start += len(marker)
    end = app_module_src.find('"', start)
    pub_b64 = app_module_src[start:end]

    pub = Ed25519PublicKey.from_public_bytes(base64.urlsafe_b64decode(pub_b64))

    try:
        payload_b64, signature_b64 = args.key.split(".")
        padding = "=" * (-len(signature_b64) % 4)
        signature = base64.urlsafe_b64decode(signature_b64 + padding)
        pub.verify(signature, payload_b64.encode())
        padding = "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + padding))
        print("VALID key. Payload:", json.dumps(payload, indent=2))
    except (InvalidSignature, ValueError) as e:
        print("INVALID key:", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("generate-keypair", help="Create a new signing keypair (do this once).").set_defaults(func=cmd_generate_keypair)

    p_issue = sub.add_parser("issue", help="Sign a new license key for a customer.")
    p_issue.add_argument("--name", required=True, help="Licensee name, e.g. the customer's name or company.")
    p_issue.add_argument("--tier", required=True, choices=VALID_TIERS)
    p_issue.add_argument("--days", required=True, type=int, help="License duration in days.")
    p_issue.add_argument("--created-at", default="2026-08-26", help="ISO date stamp embedded in the key (informational only).")
    p_issue.set_defaults(func=cmd_issue)

    p_verify = sub.add_parser("verify", help="Check a key against this app's public key before sending it out.")
    p_verify.add_argument("key", help="The full license key string (payload.signature).")
    p_verify.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    args.func(args)
