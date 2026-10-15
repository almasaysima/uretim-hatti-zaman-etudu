"""En yavaş istasyonlar için 'What-If' kapasite senaryoları.

Hat kapasitesi = net süre / en yavaş istasyonun birim standart süresi (Tmax).
Bir istasyonu iyileştirmek kapasiteyi yalnızca bir sonraki darboğaza kadar artırır
("darboğaz kayması") - bu modül bunu açıkça gösterir.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as cfg

# (kod, ad, tür, değer)
SCENARIOS = [
    ("S1", "Süre −%10 (Kaizen)", "scale", 0.90),
    ("S2", "Süre −%20 (Kaizen)", "scale", 0.80),
    ("S3", "Süre −%30 (Kaizen)", "scale", 0.70),
    ("S4", "2. paralel istasyon (ideal, süre ÷2)", "scale", 0.50),
    ("S5", "Baskın iş öğesi −%25", "dominant", 0.75),
]


def _new_time(station: str, kind: str, value: float, summary: pd.DataFrame, el: pd.DataFrame) -> float:
    base = float(summary.loc[summary["station"] == station, "std_unit_s"].iloc[0])
    if kind == "scale":
        return base * value
    e = el[el["station"] == station]
    dom = e.loc[e["std_unit_s"].idxmax(), "std_unit_s"]
    return base - dom * (1 - value)


def _line_state(times: pd.Series, available_s: float, takt: float) -> dict:
    tmax = times.max()
    return {"bottleneck": times.idxmax(), "line_time_s": tmax,
            "line_capacity": available_s / tmax, "meets_takt": bool(tmax <= takt)}


def run_whatif(summary: pd.DataFrame, el: pd.DataFrame, available_s: float, takt: float,
               n_targets: int = cfg.N_BOTTLENECKS_FOR_WHATIF) -> pd.DataFrame:
    times = summary.set_index("station")["std_unit_s"]
    targets = list(summary.nsmallest(n_targets, "rank")["station"])
    base = _line_state(times, available_s, takt)
    rows = []
    for code, name, kind, value in SCENARIOS:
        # 1) her hedef istasyon tek başına
        for st_name in targets:
            t = times.copy()
            t[st_name] = _new_time(st_name, kind, value, summary, el)
            s = _line_state(t, available_s, takt)
            rows.append(_row(code, name, st_name, times[st_name], t[st_name], s, base))
        # 2) hedef istasyonların tamamı birlikte
        t = times.copy()
        for st_name in targets:
            t[st_name] = _new_time(st_name, kind, value, summary, el)
        s = _line_state(t, available_s, takt)
        rows.append(_row(code, name, f"İlk {n_targets} birlikte", np.nan, np.nan, s, base))
    return pd.DataFrame(rows)


def _row(code, name, target, old, new, s, base):
    return {
        "Senaryo": code, "Açıklama": name, "Hedef": target,
        "Eski süre (sn)": None if np.isnan(old) else round(old, 2),
        "Yeni süre (sn)": None if np.isnan(new) else round(new, 2),
        "Yeni darboğaz": s["bottleneck"],
        "Hat süresi Tmax (sn)": round(s["line_time_s"], 2),
        "Kapasite (adet/vardiya)": round(s["line_capacity"], 0),
        "Kapasite artışı (%)": round(100 * (s["line_capacity"] / base["line_capacity"] - 1), 1),
        "Takt sağlanıyor": "Evet" if s["meets_takt"] else "Hayır",
    }


def capacity_curves(summary: pd.DataFrame, available_s: float, max_cut: float = 0.5,
                    n_targets: int = cfg.N_BOTTLENECKS_FOR_WHATIF) -> pd.DataFrame:
    """Süre kısaltma yüzdesine karşı hat kapasitesi (grafik için)."""
    times = summary.set_index("station")["std_unit_s"]
    targets = list(summary.nsmallest(n_targets, "rank")["station"])
    cuts = np.linspace(0, max_cut, 26)
    rows = []
    for c in cuts:
        for st_name in targets:
            t = times.copy(); t[st_name] *= (1 - c)
            rows.append({"cut": c, "seri": st_name, "capacity": available_s / t.max()})
        t = times.copy()
        for st_name in targets:
            t[st_name] *= (1 - c)
        rows.append({"cut": c, "seri": f"İlk {n_targets} birlikte", "capacity": available_s / t.max()})
    return pd.DataFrame(rows)
