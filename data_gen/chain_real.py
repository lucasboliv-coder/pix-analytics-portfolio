"""
Real on-chain data for the Blockchain page — masked.

Unlike the rest of the Blockchain page (synthetic, see generator.py), the
figures below come from the real transaction records of the group's crypto
payments company, aggregated by month before anything left the source:

- Bridge activity for Jan-Jul 2025 and Dec 2025-Jan 2026 (Aug-Nov 2025 has
  no reliable record, so it is left as a gap rather than filled in).
- A Dec 2025-Jan 2026 snapshot of on-chain transfers: route split,
  direction, symbol mix and success rates.

Masking: every US$ volume and every transaction count was run through a
random mathematical operation, generated once and discarded — never
recorded anywhere, including here. Percentages (take rate, shares, success
rates) were computed from the real figures before masking, so they are the
real ones; absolute volumes and counts are not. Values are in US$ (USDT),
the currency the operation actually settles in. The group's own token is
shown under a fictional ticker, 'PFT'.
"""

BRIDGE_MONTHLY = [
    {'month': '2025-01', 'transactions': 44, 'volume_usd': 73100.0, 'take_rate_pct': 0.53},
    {'month': '2025-02', 'transactions': 121, 'volume_usd': 164000.0, 'take_rate_pct': 0.76},
    {'month': '2025-03', 'transactions': 152, 'volume_usd': 214000.0, 'take_rate_pct': 0.73},
    {'month': '2025-04', 'transactions': 80, 'volume_usd': 124000.0, 'take_rate_pct': 0.69},
    {'month': '2025-05', 'transactions': 52, 'volume_usd': 207000.0, 'take_rate_pct': 0.44},
    {'month': '2025-06', 'transactions': 60, 'volume_usd': 154000.0, 'take_rate_pct': 0.53},
    {'month': '2025-07', 'transactions': 47, 'volume_usd': 129000.0, 'take_rate_pct': 0.31},
    {'month': '2025-12', 'transactions': 150, 'volume_usd': 594000.0, 'take_rate_pct': 0.43},
    {'month': '2026-01', 'transactions': 176, 'volume_usd': 335000.0, 'take_rate_pct': 0.63},
]

BLOCKCHAIN_MONTHLY = [
    {'month': '2025-12', 'transactions': 2490, 'volume_usd': 5790000.0},
    {'month': '2026-01', 'transactions': 3842, 'volume_usd': 4630000.0},
]

SNAPSHOT_PERIOD = ("2025-12", "2026-01")
SNAPSHOT = {
    "bridge_share_of_usd_pct": 8.2,
    "blockchain_out_share_of_usd_pct": 58.3,
    "symbol_share_of_transactions_pct": {"USDT": 87.8, "PFT": 9.8, "BTC": 2.4},
    "success_rate_pct": {"BLOCKCHAIN": 99.4, "BRIDGE": 97.7},
}
