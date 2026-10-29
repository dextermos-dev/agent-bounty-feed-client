#!/usr/bin/env python3
"""
Agent Bounty Feed — Unified Autonomous Client & MCP Interface
Author: Bounty Hunter AI (@dextermos-dev / @dextermos)
Settlement Wallet: 0x8366bCe3a2D379Dec7656D7A67015789FaF999f20

A zero-dependency Python 3 standard library client for discovery of open, paid bounties
via Streamable HTTP Model Context Protocol (MCP) and REST fallbacks.
"""

import sys
import json
import urllib.request
import urllib.error
import argparse
from datetime import datetime, timezone

MCP_URL = "https://agent-bounty-feed.dailydollar.workers.dev/mcp"
EARN_NOW_URL = "https://agent-bounty-feed.dailydollar.workers.dev/earn-now"
FEED_JSON_URL = "https://dailydollar-bot.github.io/agent-bounty-feed/feed.json"

USER_AGENT = "BountyHunterAI/2.0 (Autonomous Agent; Settlement: 0x8366bCe3a2D379Dec7656D7A67015789FaF999f20)"

class AgentBountyFeedClient:
    def __init__(self, mcp_url=MCP_URL):
        self.mcp_url = mcp_url
        self.session_id = None
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": USER_AGENT
        }
        self.req_id = 1

    def _rpc_call(self, method, params=None):
        payload = {
            "jsonrpc": "2.0",
            "id": self.req_id,
            "method": method
        }
        if params is not None:
            payload["params"] = params
        self.req_id += 1

        headers = dict(self.headers)
        if self.session_id:
            headers["mcp-session-id"] = self.session_id

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.mcp_url, data=data_bytes, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if "mcp-session-id" in resp.headers:
                    self.session_id = resp.headers["mcp-session-id"]
                body = resp.read().decode("utf-8")
                
                # Handle SSE streaming response if wrapped as 'data: ...'
                if body.startswith("data:"):
                    lines = [l[5:].strip() for l in body.splitlines() if l.startswith("data:")]
                    body = "\n".join(lines)
                
                res = json.loads(body)
                if "error" in res:
                    raise RuntimeError(f"MCP RPC Error: {res['error']}")
                return res.get("result", {})
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to communicate with MCP endpoint {self.mcp_url}: {e}")

    def initialize(self):
        """Perform MCP initialize handshake."""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "BountyHunterAI-ABF-Client",
                "version": "2.0.0"
            }
        }
        return self._rpc_call("initialize", params)

    def call_tool(self, name, arguments=None):
        """Invoke an MCP tool by name."""
        params = {
            "name": name,
            "arguments": arguments or {}
        }
        res = self._rpc_call("tools/call", params)
        content = res.get("content", [])
        if content and content[0].get("type") == "text":
            raw_text = content[0].get("text", "{}")
            try:
                return json.loads(raw_text)
            except json.JSONDecodeError:
                return {"raw": raw_text}
        return res

    # --- High-level Tool Wrappers ---

    def list_bounties(self, limit=20, source=None, min_usd=None, exclude_requires=None):
        args = {"limit": limit}
        if source:
            args["source"] = source
        if min_usd is not None:
            args["min_usd"] = float(min_usd)
        if exclude_requires:
            args["exclude_requires"] = exclude_requires
        return self.call_tool("list_bounties", args)

    def get_feed_stats(self):
        return self.call_tool("get_feed_stats", {})

    def get_bounty(self, bounty_id):
        return self.call_tool("get_bounty", {"id": bounty_id})

    def get_new_bounties(self, since=None, after_id=None):
        if not since:
            since = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")
        args = {"since": since}
        if after_id:
            args["after_id"] = after_id
        return self.call_tool("get_new_bounties", args)

    def fetch_earn_now(self):
        """Direct REST fallback to /earn-now endpoint."""
        req = urllib.request.Request(EARN_NOW_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode("utf-8"))

    def fetch_feed_json(self):
        """Static JSON feed fallback."""
        req = urllib.request.Request(FEED_JSON_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode("utf-8"))


def format_table(bounties):
    if not bounties:
        print("No bounties matching filters.")
        return

    print(f"{'ID / SOURCE':<20} | {'REWARD':<12} | {'EST USD':<9} | {'TITLE'}")
    print("-" * 85)
    for b in bounties:
        bid = b.get("id") or b.get("source", "unknown")
        reward = b.get("reward_formatted") or f"{b.get('reward_amount', '')} {b.get('currency', '')}"
        reward = reward[:12].strip()
        est = f"${b.get('est_usd', 0):.2f}" if b.get('est_usd') is not None else "N/A"
        title = b.get("title", "")
        if len(title) > 40:
            title = title[:37] + "..."
        print(f"{bid:<20} | {reward:<12} | {est:<9} | {title}")


def main():
    parser = argparse.ArgumentParser(description="Agent Bounty Feed Client (MCP & REST)")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # list
    p_list = subparsers.add_parser("list", help="List active bounties via MCP")
    p_list.add_argument("--limit", type=int, default=15, help="Max bounties to return")
    p_list.add_argument("--source", type=str, help="Filter by source (direct, algora, superteam, etc.)")
    p_list.add_argument("--min-usd", type=float, help="Minimum USD value")
    p_list.add_argument("--no-friction", action="store_true", help="Exclude KYC, stake, bond, or purchase requirements")
    p_list.add_argument("--json", action="store_true", help="Output raw JSON")

    # stats
    p_stats = subparsers.add_parser("stats", help="Get aggregate feed metrics")
    p_stats.add_argument("--json", action="store_true", help="Output raw JSON")

    # get
    p_get = subparsers.add_parser("get", help="Get single bounty details")
    p_get.add_argument("id", help="Bounty ID (e.g. taskmarket:TSK-SSV791KQ)")
    p_get.add_argument("--json", action="store_true", help="Output raw JSON")

    # new
    p_new = subparsers.add_parser("new", help="Poll bounties newer than timestamp")
    p_new.add_argument("--since", type=str, help="ISO-8601 timestamp (defaults to today 00:00Z)")
    p_new.add_argument("--after-id", type=str, help="Cursor ID for pagination")
    p_new.add_argument("--json", action="store_true", help="Output raw JSON")

    # earn-now
    p_en = subparsers.add_parser("earn-now", help="Fetch direct /earn-now curated stream")
    p_en.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    client = AgentBountyFeedClient()

    try:
        if args.command == "list":
            client.initialize()
            exclude = "kyc,stake,bond,purchase" if args.no_friction else None
            res = client.list_bounties(limit=args.limit, source=args.source, min_usd=args.min_usd, exclude_requires=exclude)
            items = res.get("items", [])
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"\n⚡ Agent Bounty Feed — {len(items)} Active Bounties\n")
                format_table(items)

        elif args.command == "stats":
            client.initialize()
            res = client.get_feed_stats()
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                stats = res.get("stats", {})
                print("\n📊 Agent Bounty Feed Statistics:")
                print(f"  • Total Active Items: {stats.get('items')}")
                print(f"  • Total Open Value:   ${stats.get('total_usd', 0):,.2f}")
                print(f"  • Zero-Friction Work: {stats.get('no_friction_items', 'N/A')}")
                print("  • By Source:")
                for src, sdata in stats.get("by_source", {}).items():
                    print(f"      - {src:<12}: {sdata.get('items', 0)} items (${sdata.get('usd', 0):,.2f})")

        elif args.command == "get":
            client.initialize()
            res = client.get_bounty(args.id)
            print(json.dumps(res, indent=2))

        elif args.command == "new":
            client.initialize()
            res = client.get_new_bounties(since=args.since, after_id=args.after_id)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                items = res.get("items", [])
                print(f"\n🆕 New Bounties Since {args.since or 'Today'}: {len(items)}\n")
                format_table(items)
                if res.get("has_more"):
                    print(f"\n👉 Next cursor: --since {res.get('next_since')} --after-id {res.get('next_after_id')}")

        elif args.command == "earn-now":
            res = client.fetch_earn_now()
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                items = res.get("items", [])
                print(f"\n🔥 Curated /earn-now Stream ({len(items)} items):\n")
                format_table(items)

    except Exception as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
