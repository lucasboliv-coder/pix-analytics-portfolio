"""
Deterministic synthetic data generator for PixFlow Analytics.

Nothing here comes from a real database: the whole dataset (users, PIX
transactions and on-chain transactions) is synthesized with numpy/pandas
from a fixed seed, so the numbers are always the same across runs and
visitors.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st

from data_gen.names import FIRST_NAMES_F, FIRST_NAMES_M, LAST_NAMES

START_DATE = dt.date(2024, 1, 1)
END_DATE = dt.date(2026, 3, 17)

DEFAULT_SEED = 42


def _date_range() -> pd.DatetimeIndex:
    return pd.date_range(START_DATE, END_DATE, freq="D")


def _weekly_seasonality() -> np.ndarray:
    # Monday=0 ... Sunday=6 — activity is stronger on business days
    return np.array([1.10, 1.15, 1.12, 1.08, 1.00, 0.62, 0.55])


def _apply_spikes(lam: np.ndarray, days: pd.DatetimeIndex, rng: np.random.Generator, n_spikes: int, intensity: tuple[float, float]) -> np.ndarray:
    """Simulates one-off activity spikes (campaigns, product launches)."""
    lam = lam.copy()
    spike_idx = rng.choice(len(days), size=n_spikes, replace=False)
    for idx in spike_idx:
        width = rng.integers(2, 5)
        factor = rng.uniform(*intensity)
        window = slice(max(0, idx - width), min(len(days), idx + width))
        lam[window] *= factor
    return lam


def _generate_users(rng: np.random.Generator) -> pd.DataFrame:
    days = _date_range()

    # growth trend: base rate climbs smoothly over the ~2-year window
    base = np.linspace(3, 22, len(days))
    weekly = np.tile(_weekly_seasonality(), len(days) // 7 + 1)[: len(days)]
    lam = base * weekly
    lam = _apply_spikes(lam, days, rng, n_spikes=6, intensity=(2.5, 4.5))

    signups_per_day = rng.poisson(lam=lam)

    signup_dates = np.repeat(days.values, signups_per_day)
    n = len(signup_dates)

    gender = rng.choice(["M", "F"], size=n, p=[0.52, 0.48])
    first_name = np.where(
        gender == "M",
        rng.choice(FIRST_NAMES_M, size=n),
        rng.choice(FIRST_NAMES_F, size=n),
    )
    last_name = rng.choice(LAST_NAMES, size=n)
    full_names = [f"{f} {l}" for f, l in zip(first_name, last_name)]

    wallets = [
        "0x" + "".join(rng.choice(list("0123456789abcdef"), size=40))
        for _ in range(n)
    ]

    segment = rng.choice(["Retail", "Premium"], size=n, p=[0.86, 0.14])

    df = pd.DataFrame(
        {
            "user_id": np.arange(1, n + 1),
            "wallet": wallets,
            "persona_name": full_names,
            "segment": segment,
            "signup_date": pd.to_datetime(signup_dates),
        }
    )
    return df.sort_values("signup_date").reset_index(drop=True)


def _generate_pix(rng: np.random.Generator, users: pd.DataFrame, direction: str) -> pd.DataFrame:
    days = _date_range()
    n_days = len(days)

    signups_per_day = users.groupby(users["signup_date"].dt.date).size()
    cumulative_active_users = signups_per_day.reindex(days.date, fill_value=0).cumsum().values

    # daily activity rate grows with the active user base
    base_rate = 0.9 if direction == "IN" else 0.75
    weekly = np.tile(_weekly_seasonality(), n_days // 7 + 1)[:n_days]
    lam = cumulative_active_users * (base_rate / 30) * weekly
    lam = _apply_spikes(lam, days, rng, n_spikes=5, intensity=(1.8, 3.0))
    lam = np.clip(lam, 0.5, None)

    tx_per_day = rng.poisson(lam=lam)
    dates = np.repeat(days.values, tx_per_day)
    n = len(dates)

    max_user_per_day = np.repeat(np.maximum(cumulative_active_users, 1), tx_per_day)
    user_idx = (rng.random(n) * max_user_per_day).astype(int)
    user_ids = users["user_id"].values[np.clip(user_idx, 0, len(users) - 1)]

    mu_log, sigma_log = (5.6, 1.0) if direction == "IN" else (5.4, 1.05)
    amount = rng.lognormal(mean=mu_log, sigma=sigma_log, size=n)
    amount = np.clip(amount, 20, 60_000).round(2)
    fee = np.clip(amount * rng.uniform(0.004, 0.012, size=n) + rng.uniform(0.5, 2.0, size=n), 0.5, None).round(2)

    status = rng.choice(
        ["CONFIRMED", "PENDING", "FAILED"], size=n, p=[0.93, 0.045, 0.025]
    )

    # timestamp within the day, slightly biased towards business hours
    seconds_in_day = rng.integers(6 * 3600, 23 * 3600, size=n)
    created_at = pd.to_datetime(dates) + pd.to_timedelta(seconds_in_day, unit="s")

    df = pd.DataFrame(
        {
            "user_id": user_ids,
            "direction": direction,
            "amount_brl": amount,
            "fee_brl": fee,
            "status": status,
            "created_at": created_at,
        }
    )
    return df.sort_values("created_at").reset_index(drop=True)


def _generate_chain(rng: np.random.Generator, pix_out: pd.DataFrame) -> pd.DataFrame:
    # on-chain activity follows (with noise) the PIX OUT withdrawal volume
    daily_volume = pix_out.groupby(pix_out["created_at"].dt.date)["amount_brl"].sum()
    days = _date_range()
    daily_volume = daily_volume.reindex(days.date, fill_value=0.0)

    lam = (daily_volume.values / 4000) + 1.5
    n_per_day = rng.poisson(lam=np.clip(lam, 0.5, None))
    dates = np.repeat(days.values, n_per_day)
    n = len(dates)

    tx_type = rng.choice(["BLOCKCHAIN", "BRIDGE"], size=n, p=[0.7, 0.3])
    symbol = rng.choice(
        ["BTC", "ETH", "USDT", "MATIC", "SOL"], size=n, p=[0.28, 0.24, 0.26, 0.13, 0.09]
    )

    value = rng.lognormal(mean=5.2, sigma=1.2, size=n)
    value = np.clip(value, 5, 80_000).round(2)
    tx_fee = np.clip(value * rng.uniform(0.001, 0.006, size=n), 0.1, None).round(3)
    fee_value = np.where(tx_type == "BRIDGE", np.clip(value * rng.uniform(0.002, 0.01, size=n), 0.1, None).round(3), 0.0)

    status = rng.choice(["CONFIRMED", "PENDING", "FAILED"], size=n, p=[0.95, 0.03, 0.02])

    tx_hash = [
        "0x" + "".join(rng.choice(list("0123456789abcdef"), size=64)) for _ in range(n)
    ]

    seconds_in_day = rng.integers(0, 24 * 3600, size=n)
    timestamp = pd.to_datetime(dates) + pd.to_timedelta(seconds_in_day, unit="s")

    df = pd.DataFrame(
        {
            "tx_hash": tx_hash,
            "type": tx_type,
            "symbol": symbol,
            "value": value,
            "tx_fee": tx_fee,
            "fee_value": fee_value,
            "status": status,
            "timestamp": timestamp,
        }
    )
    return df.sort_values("timestamp").reset_index(drop=True)


@st.cache_data(show_spinner="Generating synthetic dataset...")
def load_data(seed: int = DEFAULT_SEED) -> dict[str, pd.DataFrame]:
    """Single entry point: generates (and caches) the synthetic dataset."""
    rng = np.random.default_rng(seed)

    users = _generate_users(rng)
    pix_in = _generate_pix(rng, users, "IN")
    pix_out = _generate_pix(rng, users, "OUT")
    chain = _generate_chain(rng, pix_out)

    return {
        "users": users,
        "pix_in": pix_in,
        "pix_out": pix_out,
        "chain": chain,
    }
