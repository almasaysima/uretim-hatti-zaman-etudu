"""Ölçüm belirsizliği: Monte Carlo ile darboğaz ve kapasite sağlamlığı.

Sorun: Çoğu iş öğesi 1-3 okumaya dayanır; "darboğaz gerçekten bu istasyon mu?" sorusu
nokta tahminle cevaplanamaz. Çözüm: her iş öğesinin ortalamasını, okuma sayısına bağlı
standart hata ile (lognormal) yeniden örnekleyip sonuçları binlerce kez hesaplamak.

Model (yalnızca ÖRNEKLEME belirsizliği):
  * Öğenin değişkenlik katsayısı (CV) en az 3 okuması varsa kendi CV'si, yoksa
    ≥3 okumalı öğelerin medyan CV'si ("havuz CV") kullanılır.
  * Ortalamanın göreli standart hatası = CV / √n.
  * Çarpan ~ LogNormal(E=1, σ_rel); istasyon süresi = Σ(öğe std. süresi × çarpan).
Rating, yöntem farkı ve sistematik hata modellenmez.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FALLBACK_CV = 0.15      # ≥3 okumalı hiç öğe yoksa
MIN_READINGS_OWN_CV = 3


def pooled_cv(el: pd.DataFrame) -> float:
    ok = el.loc[el["n_readings"] >= MIN_READINGS_OWN_CV, "cv"].dropna()
    return float(ok.median()) if len(ok) else FALLBACK_CV


def relative_se(el: pd.DataFrame) -> np.ndarray:
    pool = pooled_cv(el)
    cv = np.where((el["n_readings"] >= MIN_READINGS_OWN_CV) & el["cv"].notna(), el["cv"], pool)
    return cv / np.sqrt(el["n_readings"].clip(lower=1))


def simulate(el: pd.DataFrame, available_s: float, takt: float, n_sims: int = 5000, seed: int = 42):
    """Döndürür: (istasyon_tablosu, kapasite_örnekleri).

    istasyon_tablosu: P(darboğaz), istasyon süresi p5/p50/p95 (birim başına sn).
    """
    rng = np.random.default_rng(seed)
    stations = list(dict.fromkeys(el["station"]))
    idx = {s: i for i, s in enumerate(stations)}
    onehot = np.zeros((len(el), len(stations)))
    onehot[np.arange(len(el)), el["station"].map(idx).to_numpy()] = 1.0

    sigma = np.sqrt(np.log1p(relative_se(el) ** 2))
    mult = np.exp(rng.normal(-0.5 * sigma ** 2, sigma, size=(n_sims, len(el))))
    times = (mult * el["std_unit_s"].to_numpy()) @ onehot            # (n_sims, n_stations)

    tmax = times.max(axis=1)
    bottleneck = times.argmax(axis=1)
    capacity = available_s / tmax
    p_bn = np.bincount(bottleneck, minlength=len(stations)) / n_sims

    out = pd.DataFrame({
        "station": stations,
        "p_bottleneck": p_bn,
        "time_p5": np.percentile(times, 5, axis=0),
        "time_p50": np.percentile(times, 50, axis=0),
        "time_p95": np.percentile(times, 95, axis=0),
        "p_over_takt": (times > takt).mean(axis=0),
    }).sort_values("p_bottleneck", ascending=False).reset_index(drop=True)
    return out, capacity


def capacity_interval(capacity: np.ndarray, lo: float = 5, hi: float = 95) -> tuple[float, float, float]:
    return tuple(float(np.percentile(capacity, q)) for q in (lo, 50, hi))
