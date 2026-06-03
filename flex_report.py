import argparse
from collections import Counter
from datetime import date, timedelta

import credentials
from flex import (
    get_fortiflex_configurations,
    get_fortiflex_entitlement_points,
    get_fortiflex_entitlements,
    get_fortiflex_programs,
    get_oauth_token,
)


def print_separator(char="-", width=60):
    print(char * width)


# --- summary subcommand ---

def report_summary(token: str):
    programs = _get_programs(token)
    print_separator("=")
    print("FortiFlex Summary Report")
    print_separator("=")
    for program in programs:
        serial = program.get("serialNumber", "N/A")
        name = program.get("name", "Unnamed")
        start = program.get("startDate", "")
        end = program.get("endDate", "")
        print(f"\nProgram: {name}")
        print(f"  Serial: {serial}  |  Start: {start}  |  End: {end}")
        print_separator()
        _print_config_summary(token, serial)
    print()
    print_separator("=")


def _print_config_summary(token: str, program_serial: str):
    configs = get_fortiflex_configurations(token, program_serial).get("configs", [])
    if not configs:
        print("  No configurations found.")
        return
    for config in configs:
        config_id = config["id"]
        name = config.get("name", "Unnamed")
        status = config.get("status", "UNKNOWN")
        print(f"\n  Config: {name}  (ID: {config_id}, Status: {status})")
        entitlements = get_fortiflex_entitlements(token, program_serial, config_id).get("entitlements", [])
        if not entitlements:
            print("    No entitlements.")
            continue
        counts = Counter(e.get("status", "UNKNOWN") for e in entitlements)
        summary = ", ".join(f"{s}: {n}" for s, n in sorted(counts.items()))
        print(f"    Total: {len(entitlements)}  ({summary})")
        for ent in entitlements:
            serial = ent.get("serialNumber", "N/A")
            ent_status = ent.get("status", "UNKNOWN")
            description = ent.get("description", "")
            desc_str = f"  — {description}" if description else ""
            print(f"      {serial}  [{ent_status}]{desc_str}")


# --- points subcommand ---

def report_points(token: str, start_date: str, end_date: str):
    programs = _get_programs(token)
    print_separator("=")
    print(f"FortiFlex Point Usage Report  ({start_date}  →  {end_date})")
    print_separator("=")
    for program in programs:
        serial = program.get("serialNumber", "N/A")
        name = program.get("name", "Unnamed")
        print(f"\nProgram: {name}  (Serial: {serial})")
        print_separator()

        by_account = _collect_program_points(token, serial, start_date, end_date)

        program_total = sum(by_account.values())
        print(f"  Total:  {program_total:,.0f} pts\n")
        if by_account:
            print("  By account:")
            for acct_id, pts in sorted(by_account.items(), key=lambda x: -x[1]):
                print(f"    Account {acct_id}: {pts:>10,.0f} pts")

    print()
    print_separator("=")


def _collect_program_points(token: str, program_serial: str, start_date: str, end_date: str) -> dict[int, float]:
    configs = get_fortiflex_configurations(token, program_serial).get("configs", [])
    by_account: dict[int, float] = {}
    for config in configs:
        resp = get_fortiflex_entitlement_points(token, config["id"], start_date, end_date)
        for ent in resp.get("entitlements") or [] if resp else []:
            acct = ent.get("accountId", 0)
            by_account[acct] = by_account.get(acct, 0) + ent.get("points", 0)
    return by_account


# --- shared helpers ---

def _get_programs(token: str) -> list:
    programs = get_fortiflex_programs(token).get("programs", [])
    if not programs:
        print("No programs found.")
    return programs


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="FortiFlex usage reporting tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("summary", help="List all configurations and entitlement status counts")

    points_parser = subparsers.add_parser("points", help="Show point usage per tenant and configuration for a date range")
    today = date.today()
    points_parser.add_argument("--start", default=str(today - timedelta(days=30)), metavar="YYYY-MM-DD",
                               help="Start date (default: 30 days ago)")
    points_parser.add_argument("--end", default=str(today), metavar="YYYY-MM-DD",
                               help="End date (default: today)")

    args = parser.parse_args()

    token_resp = get_oauth_token(credentials.api_username, credentials.api_token, client_id="flexvm")
    token = token_resp["access_token"]

    if args.command == "summary":
        report_summary(token)
    elif args.command == "points":
        report_points(token, args.start, args.end)


if __name__ == "__main__":
    main()
