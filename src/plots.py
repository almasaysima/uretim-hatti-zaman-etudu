"""Matplotlib / Seaborn görselleştirmeleri (Türkçe etiketli, 200 dpi)."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import PercentFormatter

from . import config as cfg
from .metrics import HANDLING, pareto_table

RED, ORANGE, BLUE, GREY, NAVY = "#C0392B", "#E67E22", "#2E86C1", "#B0B7BF", "#1B2631"
CAT_COLORS = {"İşlem": "#2E86C1", "Test": "#C0392B", HANDLING: "#F5B041"}


def _style():
    sns.set_theme(style="whitegrid", context="notebook", font="DejaVu Sans")
    plt.rcParams.update({"axes.titleweight": "bold", "axes.titlesize": 13, "figure.dpi": 100,
                         "axes.spines.top": False, "axes.spines.right": False})


def _save(fig, out_dir: Path, name: str) -> Path:
    path = Path(out_dir) / name
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def plot_station_times(summary: pd.DataFrame, takt: float, out_dir) -> Path:
    _style()
    s = summary.sort_values("std_unit_s")
    top = s["rank"] <= cfg.N_BOTTLENECKS_FOR_WHATIF
    fig, ax = plt.subplots(figsize=(11, 10))
    bars = ax.barh(s["station"], s["std_unit_s"], color=[RED if t else BLUE for t in top])
    for bar, over in zip(bars, s["std_unit_s"] > takt):
        if over:
            bar.set_hatch("//")
            bar.set_edgecolor("white")
    for y, v in enumerate(s["std_unit_s"]):
        ax.text(v + 0.6, y, f"{v:.1f}", va="center", fontsize=8)
    ax.axvline(takt, color=NAVY, ls="--", lw=1.6)
    ax.text(takt + 0.8, len(s) - 0.4, f"Takt = {takt:.1f} sn", color=NAVY, fontsize=10, fontweight="bold")
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Birim başına standart süre (sn)  [ortalama + %10 yorgunluk payı, parti başına bölünmüş]")
    ax.set_title("İstasyon bazında birim standart süre ve darboğaz istasyonları")
    handles = [plt.Rectangle((0, 0), 1, 1, color=RED), plt.Rectangle((0, 0), 1, 1, color=BLUE),
               plt.Rectangle((0, 0), 1, 1, facecolor="grey", hatch="//", edgecolor="white")]
    ax.legend(handles=handles, labels=[f"İlk {cfg.N_BOTTLENECKS_FOR_WHATIF} darboğaz", "Diğer istasyonlar",
                                       "Takt'ı aşıyor (taralı)"], loc="center right")
    return _save(fig, out_dir, "01_istasyon_standart_sureleri.png")


def _pareto(df, label, value, title, xlabel, fname, out_dir, top_n=None, figsize=(12, 6.5)):
    _style()
    p = pareto_table(df, label, value)
    n_vital, n_total = int(p["vital_few"].sum()), len(p)
    if top_n:
        p = p.head(top_n)
    fig, ax = plt.subplots(figsize=figsize)
    colors = [RED if v else GREY for v in p["vital_few"]]
    ax.bar(range(len(p)), p[value], color=colors)
    ax.set_xticks(range(len(p)))
    ax.set_xticklabels(p[label], rotation=60, ha="right", fontsize=8)
    ax.set_ylabel(xlabel)
    ax.grid(axis="x", visible=False)
    ax2 = ax.twinx()
    ax2.plot(range(len(p)), p["cum_pct"], color=NAVY, marker="o", ms=4, lw=1.8)
    ax2.axhline(cfg.PARETO_CUTOFF * 100, color=NAVY, ls=":", lw=1.2)
    ax2.set_ylim(0, 105)
    ax2.yaxis.set_major_formatter(PercentFormatter())
    ax2.set_ylabel("Kümülatif pay")
    ax2.grid(False)
    ax2.spines["right"].set_visible(True)
    shown = f", grafikte ilk {top_n} gösteriliyor" if top_n else ""
    ax.set_title(f"{title}\nKırmızı = ilk %80'i oluşturan 'hayati az' ({n_vital}/{n_total} kalem{shown})")
    return _save(fig, out_dir, fname)


def plot_pareto_stations(summary, out_dir):
    return _pareto(summary, "station", "std_unit_s", "Pareto: istasyonların toplam standart süreye katkısı",
                   "Birim standart süre (sn)", "02_pareto_istasyon.png", out_dir)


def plot_pareto_elements(el, out_dir, top_n=20):
    d = el.assign(label=el["station"] + " › " + el["element"])
    return _pareto(d, "label", "std_unit_s", f"Pareto: iş öğesi bazında zaman kaybı (ilk {top_n})",
                   "Birim standart süre (sn)", "03_pareto_is_ogesi.png", out_dir, top_n=top_n,
                   figsize=(13, 7.5))


def plot_distribution(summary, out_dir) -> Path:
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw={"width_ratios": [1, 1.25]})
    v = summary["std_unit_s"]
    sns.histplot(v, bins=14, kde=True, kde_kws={"cut": 0}, color=BLUE, ax=axes[0])
    sns.rugplot(v, color=NAVY, ax=axes[0])
    axes[0].axvline(v.median(), color=RED, ls="--", label=f"Medyan = {v.median():.1f} sn")
    axes[0].axvline(v.mean(), color=ORANGE, ls="--", label=f"Ortalama = {v.mean():.1f} sn")
    axes[0].set_xlabel("Birim standart süre (sn)")
    axes[0].set_ylabel("İstasyon sayısı")
    axes[0].set_title("İstasyon süre dağılımı (sağa çarpık)")
    axes[0].legend()
    order = summary.groupby("branch")["std_unit_s"].max().sort_values(ascending=False).index
    sns.boxplot(data=summary, y="branch", x="std_unit_s", order=order, color="#D6EAF8", ax=axes[1], fliersize=0)
    sns.stripplot(data=summary, y="branch", x="std_unit_s", order=order, color=NAVY, size=6, ax=axes[1])
    axes[1].set_xlabel("Birim standart süre (sn)")
    axes[1].set_ylabel("Hat kolu (ürün kodu eki)")
    axes[1].set_title("Hat kollarına göre dağılım")
    return _save(fig, out_dir, "04_sure_dagilimi.png")


def plot_composition(el, summary, out_dir) -> Path:
    _style()
    pivot = (el.pivot_table(index="station", columns="category", values="std_unit_s", aggfunc="sum")
             .fillna(0).reindex(summary.sort_values("std_unit_s")["station"]))
    cols = [c for c in ("İşlem", "Test", HANDLING) if c in pivot.columns]
    fig, ax = plt.subplots(figsize=(11, 10))
    left = np.zeros(len(pivot))
    for c in cols:
        ax.barh(pivot.index, pivot[c], left=left, color=CAT_COLORS[c], label=c)
        left += pivot[c].values
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Birim standart süre (sn)")
    ax.set_title("Süre kompozisyonu: işlem / test / elleçleme (metot etüdü perspektifi)")
    ax.legend(loc="lower right")
    return _save(fig, out_dir, "05_sure_kompozisyonu.png")


def plot_line_balance(summary, takt, out_dir) -> Path:
    _style()
    s = summary.sort_values("std_unit_s", ascending=False).reset_index(drop=True)
    tmax = s["std_unit_s"].max()
    fig, ax = plt.subplots(figsize=(13, 6.2))
    x = np.arange(len(s))
    ax.bar(x, s["std_unit_s"], color=BLUE, label="İstasyon iş yükü (Ti)")
    ax.bar(x, tmax - s["std_unit_s"], bottom=s["std_unit_s"], color="#FADBD8", label="Boşta kalan süre (Tmax − Ti)")
    ax.axhline(takt, color=NAVY, ls="--", lw=1.6, label=f"Takt = {takt:.1f} sn")
    ax.set_xticks(x)
    ax.set_xticklabels(s["station"], rotation=65, ha="right", fontsize=8)
    ax.set_ylabel("Süre (sn / birim)")
    le = s["std_unit_s"].sum() / (len(s) * tmax)
    ax.set_title(f"Hat dengeleme grafiği — LE = %{100 * le:.1f}, denge kaybı = %{100 * (1 - le):.1f}")
    ax.legend()
    return _save(fig, out_dir, "06_hat_dengeleme.png")


def plot_reading_variability(el, summary, out_dir, n_stations=3) -> Path:
    _style()
    top = list(summary.nsmallest(n_stations, "rank")["station"])
    rows = []
    for _, r in el[el["station"].isin(top)].iterrows():
        for v in r["readings"]:
            rows.append({"label": f"{r['station']} › {r['element']}", "sure": v / r["batch"],
                         "std": r["std_unit_s"]})
    d = pd.DataFrame(rows)
    order = d.groupby("label")["sure"].mean().sort_values(ascending=False).index
    fig, ax = plt.subplots(figsize=(11, 6.5))
    sns.boxplot(data=d, y="label", x="sure", order=order, color="#D6EAF8", ax=ax, fliersize=0)
    sns.stripplot(data=d, y="label", x="sure", order=order, color=NAVY, size=6, ax=ax)
    ax.set_xlabel("Ölçülen süre (sn / birim) — ham okumalar")
    ax.set_ylabel("")
    ax.set_title("Darboğaz istasyonlarında ölçüm değişkenliği (ham zaman okumaları)")
    return _save(fig, out_dir, "07_olcum_degiskenligi.png")


def plot_whatif(curves, summary, available_s, takt, out_dir) -> Path:
    _style()
    fig, ax = plt.subplots(figsize=(11, 6.2))
    styles = [  # renk, çizgi kalınlığı, stil, işaret, alpha, zorder
        (RED, 2.4, "--", "o", 1.0, 3),
        (ORANGE, 6.0, "-", "s", 0.45, 2),      # Kalibre ile üst üste biner -> geniş & yarı saydam
        (BLUE, 1.8, ":", "^", 1.0, 4),
        (NAVY, 2.8, "-", "D", 1.0, 5),
    ]
    for (color, lw, ls, mk, al, z), (name, d) in zip(styles, curves.groupby("seri", sort=False)):
        ax.plot(100 * d["cut"], d["capacity"], marker=mk, ms=4, lw=lw, ls=ls, color=color,
                alpha=al, zorder=z, label=name)
    target = available_s / takt
    ax.axhline(target, color="grey", ls=":", lw=1.4)
    ax.text(0.5, target + 5, f"Talep hedefi ({int(target)} adet/vardiya)", fontsize=9, color="grey")
    base = curves[curves["cut"] == 0]["capacity"].iloc[0]
    ax.annotate("Tek istasyon iyileştirmesi, bir sonraki\ndarboğaz devralınca kapasiteyi artırmaz (plato)",
                xy=(30, curves[(curves["seri"] == curves["seri"].iloc[0]) & (curves["cut"] >= 0.3)]["capacity"].iloc[0]),
                xytext=(49, base + 55), ha="right", fontsize=9, arrowprops=dict(arrowstyle="->", color="grey"))
    ax.set_xlabel("İstasyon süresindeki azalma (%)")
    ax.set_ylabel("Hat kapasitesi (adet / vardiya)")
    ax.set_title("What-If: En yavaş 3 istasyonda süre kısaltmanın hat kapasitesine etkisi")
    ax.legend(loc="upper left")
    return _save(fig, out_dir, "08_whatif_kapasite.png")


def plot_yamazumi(el, summary, takt, out_dir, top_n=15) -> Path:
    """Yamazumi: en yüklü istasyonlarda süre bileşimi (işlem/test/elleçleme) ve takt çizgisi."""
    _style()
    top = summary.nsmallest(top_n, "rank")["station"].tolist()
    pivot = (el[el["station"].isin(top)].pivot_table(index="station", columns="category",
                                                    values="std_unit_s", aggfunc="sum").fillna(0).reindex(top))
    cols = [c for c in ("İşlem", "Test", HANDLING) if c in pivot.columns]
    fig, ax = plt.subplots(figsize=(13, 6.5))
    bottom = np.zeros(len(pivot))
    for c in cols:
        ax.bar(range(len(pivot)), pivot[c], bottom=bottom, color=CAT_COLORS[c], label=c)
        bottom += pivot[c].values
    ax.axhline(takt, color=NAVY, ls="--", lw=1.6, label=f"Takt = {takt:.1f} sn")
    ax.set_xticks(range(len(pivot)))
    ax.set_xticklabels(pivot.index, rotation=55, ha="right", fontsize=8)
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("Birim standart süre (sn)")
    ax.set_title(f"Yamazumi: en yüklü {len(pivot)} istasyon — süre bileşimi ve takt")
    ax.legend()
    return _save(fig, out_dir, "09_yamazumi.png")


def plot_uncertainty(mc, capacity, nominal_capacity, demand_capacity, out_dir, top_n=6) -> Path:
    """Monte Carlo: P(darboğaz) ve hat kapasitesinin belirsizlik aralığı."""
    from .uncertainty import capacity_interval
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4), gridspec_kw={"width_ratios": [1, 1.1]})
    t = mc[mc["p_bottleneck"] > 0].head(top_n).iloc[::-1]
    axes[0].barh(t["station"], 100 * t["p_bottleneck"], color=[RED if i == len(t) - 1 else ORANGE for i in range(len(t))])
    for y, v in enumerate(100 * t["p_bottleneck"]):
        axes[0].text(v + 1, y, f"%{v:.0f}", va="center", fontsize=9)
    axes[0].set_xlim(0, 105)
    axes[0].xaxis.set_major_formatter(PercentFormatter())
    axes[0].set_xlabel("Darboğaz olma olasılığı")
    axes[0].set_title("Hangi istasyon darboğaz? (ölçüm belirsizliği altında)")
    axes[0].grid(axis="y", visible=False)

    lo, med, hi = capacity_interval(capacity)
    sns.histplot(capacity, bins=40, color=BLUE, ax=axes[1], edgecolor="white")
    axes[1].axvspan(lo, hi, color=ORANGE, alpha=0.18, label=f"%90 aralık: {lo:.0f}–{hi:.0f}")
    axes[1].axvline(nominal_capacity, color=NAVY, ls="--", label=f"Nokta tahmin = {nominal_capacity:.0f}")
    axes[1].axvline(demand_capacity, color="grey", ls=":", label=f"Talep = {demand_capacity:.0f}")
    axes[1].set_xlabel("Hat kapasitesi (adet / vardiya)")
    axes[1].set_ylabel("Simülasyon sayısı")
    axes[1].set_title("Kapasite belirsizliği (Monte Carlo)")
    axes[1].legend()
    return _save(fig, out_dir, "10_belirsizlik_monte_carlo.png")
