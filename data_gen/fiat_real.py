"""
Real fiat-rail and user data for the Users & Ticket and PIX Traded pages — masked.

Aggregated by month from the real records of the group's crypto-payments
company before anything left the source:

- USERS_MONTHLY: active users, Jan 2024 - Dec 2025.
- FIAT_MONTHLY: transactions, volume and average ticket (in / out) across the
  fiat rails (PIX, boleto, ATM), Jan 2024 - Dec 2025, in US$.
- FUNNEL_2025: new sign-ups and completed KYC, Jan-Jul 2025.
- METHOD_MIX_2025: each rail's share of volume and take rate, Jan-Jul 2025.
- SEP_2025: a four-week (Mon Sep 1 - Sun Sep 28, 2025) order-level snapshot —
  weekday pattern, refund rate, inbound share.

Masking: every count and every US$ figure was run through a random
mathematical operation, generated once and discarded — never recorded
anywhere, including here. Percentages, shares and rates were computed from
the real figures (or are ratios the masking cancels out of), so they're the
real ones; absolute counts and dollar amounts are not.
"""

USERS_MONTHLY = [
    {'month': '2024-01', 'active_users': 299},
    {'month': '2024-02', 'active_users': 341},
    {'month': '2024-03', 'active_users': 397},
    {'month': '2024-04', 'active_users': 407},
    {'month': '2024-05', 'active_users': 415},
    {'month': '2024-06', 'active_users': 482},
    {'month': '2024-07', 'active_users': 524},
    {'month': '2024-08', 'active_users': 524},
    {'month': '2024-09', 'active_users': 524},
    {'month': '2024-10', 'active_users': 672},
    {'month': '2024-11', 'active_users': 706},
    {'month': '2024-12', 'active_users': 739},
    {'month': '2025-01', 'active_users': 987},
    {'month': '2025-02', 'active_users': 1182},
    {'month': '2025-03', 'active_users': 1024},
    {'month': '2025-04', 'active_users': 1042},
    {'month': '2025-05', 'active_users': 1188},
    {'month': '2025-06', 'active_users': 1106},
    {'month': '2025-07', 'active_users': 1114},
    {'month': '2025-08', 'active_users': 1256},
    {'month': '2025-09', 'active_users': 1224},
    {'month': '2025-10', 'active_users': 1242},
    {'month': '2025-11', 'active_users': 1052},
    {'month': '2025-12', 'active_users': 1104},
]

FIAT_MONTHLY = [
    {'month': '2024-01', 'transactions': 1644, 'volume_usd': 308000.0, 'ticket_in_usd': 197.0, 'ticket_out_usd': 142.0},
    {'month': '2024-02', 'transactions': 2224, 'volume_usd': 494000.0, 'ticket_in_usd': 233.0, 'ticket_out_usd': 160.0},
    {'month': '2024-03', 'transactions': 2583, 'volume_usd': 538000.0, 'ticket_in_usd': 175.0, 'ticket_out_usd': 321.0},
    {'month': '2024-04', 'transactions': 2948, 'volume_usd': 477000.0, 'ticket_in_usd': 130.0, 'ticket_out_usd': 321.0},
    {'month': '2024-05', 'transactions': 3904, 'volume_usd': 976000.0, 'ticket_in_usd': 247.0, 'ticket_out_usd': 266.0},
    {'month': '2024-06', 'transactions': 4052, 'volume_usd': 1320000.0, 'ticket_in_usd': 334.0, 'ticket_out_usd': 255.0},
    {'month': '2024-07', 'transactions': 4233, 'volume_usd': 1710000.0, 'ticket_in_usd': 392.0, 'ticket_out_usd': 475.0},
    {'month': '2024-08', 'transactions': 5620, 'volume_usd': 5160000.0, 'ticket_in_usd': 490.0, 'ticket_out_usd': 2540.0},
    {'month': '2024-09', 'transactions': 5746, 'volume_usd': 4510000.0, 'ticket_in_usd': 427.0, 'ticket_out_usd': 2060.0},
    {'month': '2024-10', 'transactions': 6436, 'volume_usd': 4680000.0, 'ticket_in_usd': 409.0, 'ticket_out_usd': 2100.0},
    {'month': '2024-11', 'transactions': 6059, 'volume_usd': 6110000.0, 'ticket_in_usd': 560.0, 'ticket_out_usd': 3520.0},
    {'month': '2024-12', 'transactions': 6663, 'volume_usd': 5330000.0, 'ticket_in_usd': 508.0, 'ticket_out_usd': 2060.0},
    {'month': '2025-01', 'transactions': 7390, 'volume_usd': 5540000.0, 'ticket_in_usd': 557.0, 'ticket_out_usd': 1180.0},
    {'month': '2025-02', 'transactions': 8353, 'volume_usd': 4410000.0, 'ticket_in_usd': 384.0, 'ticket_out_usd': 876.0},
    {'month': '2025-03', 'transactions': 13756, 'volume_usd': 8380000.0, 'ticket_in_usd': 397.0, 'ticket_out_usd': 1400.0},
    {'month': '2025-04', 'transactions': 13607, 'volume_usd': 6380000.0, 'ticket_in_usd': 315.0, 'ticket_out_usd': 940.0},
    {'month': '2025-05', 'transactions': 16058, 'volume_usd': 7010000.0, 'ticket_in_usd': 274.0, 'ticket_out_usd': 1120.0},
    {'month': '2025-06', 'transactions': 18747, 'volume_usd': 6260000.0, 'ticket_in_usd': 213.0, 'ticket_out_usd': 849.0},
    {'month': '2025-07', 'transactions': 18127, 'volume_usd': 7120000.0, 'ticket_in_usd': 240.0, 'ticket_out_usd': 1090.0},
    {'month': '2025-08', 'transactions': 20953, 'volume_usd': 6900000.0, 'ticket_in_usd': 215.0, 'ticket_out_usd': 792.0},
    {'month': '2025-09', 'transactions': 15345, 'volume_usd': 7210000.0, 'ticket_in_usd': 303.0, 'ticket_out_usd': 1140.0},
    {'month': '2025-10', 'transactions': 13774, 'volume_usd': 8060000.0, 'ticket_in_usd': 387.0, 'ticket_out_usd': 1420.0},
    {'month': '2025-11', 'transactions': 12674, 'volume_usd': 6340000.0, 'ticket_in_usd': 322.0, 'ticket_out_usd': 1330.0},
    {'month': '2025-12', 'transactions': 25410, 'volume_usd': 7940000.0, 'ticket_in_usd': 177.0, 'ticket_out_usd': 1770.0},
]

FUNNEL_2025 = [
    {'month': '2025-01', 'new_users': 7133, 'kyc_completed': 628, 'kyc_rate_pct': 8.8},
    {'month': '2025-02', 'new_users': 7233, 'kyc_completed': 1325, 'kyc_rate_pct': 18.3},
    {'month': '2025-03', 'new_users': 2390, 'kyc_completed': 448, 'kyc_rate_pct': 18.7},
    {'month': '2025-04', 'new_users': 2350, 'kyc_completed': 472, 'kyc_rate_pct': 20.1},
    {'month': '2025-05', 'new_users': 2328, 'kyc_completed': 560, 'kyc_rate_pct': 24.1},
    {'month': '2025-06', 'new_users': 2523, 'kyc_completed': 504, 'kyc_rate_pct': 20.0},
    {'month': '2025-07', 'new_users': 2378, 'kyc_completed': 466, 'kyc_rate_pct': 19.6},
]

METHOD_MIX_2025 = {
    "PIX": {"share_of_volume_pct": 96.6, "take_rate_pct": 1.13},
    "Boleto": {"share_of_volume_pct": 3.1, "take_rate_pct": 2.05},
    "ATM": {"share_of_volume_pct": 0.3, "take_rate_pct": 3.17},
}

SEP_2025 = {
    "weekday_share_of_value_pct": {"Mon": 19.4, "Tue": 13.3, "Wed": 10.1, "Thu": 17.8, "Fri": 29.4, "Sat": 7.3, "Sun": 2.7},
    "refund_rate_pct": 2.5,
    "inbound_share_of_value_pct": 49.2,
}
