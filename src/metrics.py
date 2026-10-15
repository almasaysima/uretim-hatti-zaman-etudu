"""İstasyon özeti, takt zamanı, hat dengeleme ve Pareto metrikleri."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import config as cfg

HANDLING = "Elleçleme (alma/bırakma/yerleştirme)"


def station_summary(el: pd.DataFrame, st: pd.DataFrame) -> pd.DataFrame:
    """İstasyon bazında birim başına standart süre ve kalite göstergeleri."""
    g = el.groupby("station", sort=False)
    out = g.agg(
        n_elements=("seq", "count"),
        n_readings_total=("n_readings", "sum"),
        min_readings=("n_readings", "min"),
        mean_unit_s=("mean_unit_s", "sum"),
        fatigue_unit_s=("fatigue_s", lambda s: (s / el.loc[s.index, "batch"]).sum()),
        std_unit_s=("std_unit_s", "sum"),
        std_batch_s=("std_s", "sum"),
        sample_ok_share=("sample_ok", "mean"),
    )
    handling = el[el["category"] == HANDLING].groupby("station")["std_unit_s"].sum()
    out["handling_share"] = (handling.reindex(out.index).fillna(0) / out["std_unit_s"])
    out = out.reset_index().merge(st.drop(columns=["study_date"]), on="station")
    out["form_ceil_ok"] = [math.ceil(t - 1e-9) == f for t, f in zip(out["std_batch_s"], out["form_total_std"])]
    out["rank"] = out["std_unit_s"].rank(ascending=False, method="first").astype(int)
    return out.sort_values("rank").reset_index(drop=True)


def takt_time(available_s: float = cfg.AVAILABLE_TIME_PER_SHIFT_S,
              demand: float = cfg.DEMAND_PER_SHIFT) -> float:
    return available_s / demand


def add_takt_columns(summary: pd.DataFrame, available_s: float, demand: float) -> pd.DataFrame:
    s = summary.copy()
    takt = takt_time(available_s, demand)
    s["takt_s"] = takt
    s["load_vs_takt"] = s["std_unit_s"] / takt                          # >1 → takt'ı aşıyor
    s["capacity_per_shift"] = available_s / s["std_unit_s"]
    s["over_takt"] = s["std_unit_s"] > takt
    s["parallel_needed"] = np.ceil(s["load_vs_takt"] - 1e-9).astype(int)
    s["idle_vs_tmax_s"] = s["std_unit_s"].max() - s["std_unit_s"]
    return s


def balance_metrics(times: pd.Series, takt: float, label: str = "") -> dict:
    """Klasik hat dengeleme göstergeleri (her istasyon = 1 iş istasyonu varsayımı)."""
    t = times.astype(float)
    n, total, tmax = len(t), t.sum(), t.max()
    efficiency = total / (n * tmax)
    return {
        "Kapsam": label,
        "İstasyon sayısı (n)": n,
        "Toplam iş içeriği ΣTi (sn)": round(total, 2),
        "Darboğaz süresi Tmax (sn)": round(tmax, 2),
        "Hat dengeleme verimi LE (%)": round(100 * efficiency, 1),
        "Denge kaybı / verimsizlik BD (%)": round(100 * (1 - efficiency), 1),
        "Düzgünlük indeksi SI (sn)": round(float(np.sqrt(((tmax - t) ** 2).sum())), 1),
        "Takt (sn)": round(takt, 1),
        "Takt'a göre hat yükü ΣTi/(n·takt) (%)": round(100 * total / (n * takt), 1),
        "Teorik min. istasyon ⌈ΣTi/takt⌉": int(math.ceil(total / takt - 1e-9)),
        "Takt'ı aşan istasyon sayısı": int((t > takt).sum()),
    }


def balance_table(summary: pd.DataFrame, takt: float) -> pd.DataFrame:
    rows = [balance_metrics(summary["std_unit_s"], takt, f"Tüm istasyonlar ({len(summary)})")]
    main = summary[summary["branch"] == "Ana"]
    rows.append(balance_metrics(main["std_unit_s"], takt, f"Ana hat ({len(main)})"))
    return pd.DataFrame(rows)


def takt_sensitivity(summary: pd.DataFrame, available_s: float, scenarios=cfg.DEMAND_SCENARIOS) -> pd.DataFrame:
    rows = []
    for d in scenarios:
        takt = available_s / d
        over = summary[summary["std_unit_s"] > takt]
        rows.append({
            "Talep (adet/vardiya)": d,
            "Takt (sn)": round(takt, 1),
            "Takt'ı aşan istasyon": len(over),
            "Aşanlar": ", ".join(over["station"]) if len(over) else "-",
            "Ek kapasite ihtiyacı (paralel istasyon)": int((np.ceil(over["std_unit_s"] / takt - 1e-9) - 1).sum()),
            "Hat kapasitesi (adet/vardiya)": round(available_s / summary["std_unit_s"].max(), 0),
        })
    return pd.DataFrame(rows)


def pareto_table(df: pd.DataFrame, label: str, value: str, cutoff: float = cfg.PARETO_CUTOFF) -> pd.DataFrame:
    p = df[[label, value]].sort_values(value, ascending=False).reset_index(drop=True)
    p["share_pct"] = 100 * p[value] / p[value].sum()
    p["cum_pct"] = p["share_pct"].cumsum()
    p["vital_few"] = (p["cum_pct"] - p["share_pct"]) < cutoff * 100        # %80'e ulaşana dek
    return p


def element_table(el: pd.DataFrame) -> pd.DataFrame:
    e = el.copy()
    e["label"] = e["station"] + " › " + e["element"]
    return e


def branch_balance(summary: pd.DataFrame, takt: float) -> pd.DataFrame:
    """Hat kolu (Ana / -1 / -2 ...) bazında yük ve dengeleme göstergeleri."""
    rows = []
    for branch, g in summary.groupby("branch", sort=False):
        m = balance_metrics(g["std_unit_s"], takt, str(branch))
        rows.append({"Kol": branch, "İstasyon": m["İstasyon sayısı (n)"],
                     "ΣTi (sn)": m["Toplam iş içeriği ΣTi (sn)"], "Tmax (sn)": m["Darboğaz süresi Tmax (sn)"],
                     "LE (%)": m["Hat dengeleme verimi LE (%)"], "Takt'ı aşan": m["Takt'ı aşan istasyon sayısı"]})
    return pd.DataFrame(rows).sort_values("Tmax (sn)", ascending=False).reset_index(drop=True)
