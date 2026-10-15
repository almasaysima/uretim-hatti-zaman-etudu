"""Vaka çalışması (docs/VAKA_CALISMASI.md) için seçenek karşılaştırması.

Sentetik demo verisinden kapasiteyi hesaplar; mali varsayımlar AŞAĞIDAKİ SABİTLERDİR ve
uydurmadır: gerçek bir vakada işletmenin muhasebe/planlama verisiyle değiştirilmelidir.

Kullanım:  python scripts/vaka_secenekler.py [--output outputs]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src import demo_data, loader, metrics
from src.plots import BLUE, GREY, NAVY, ORANGE, RED, _save, _style

AVAILABLE_S, DEMAND = 25_200, 500
# --- MALİ VARSAYIMLAR (uydurma; gerçek değerlerle değiştirin) ---
MARGIN_TL = 20          # birim katkı marjı (TL/adet)
SHIFTS_PER_YEAR = 250
INVEST_TL = {"B": 60_000, "C": 150_000, "D": 1_200_000}


def load_times(xlsx: Path):
    el_raw, st, _ = loader.load_time_studies(xlsx)
    el = loader.clean_and_compute(el_raw, st)
    s = metrics.station_summary(el, st)
    return el, s.set_index("station")["std_unit_s"]


def capacity(times: pd.Series) -> float:
    return AVAILABLE_S / times.max()


def build_options(el: pd.DataFrame, t: pd.Series) -> pd.DataFrame:
    top1, top2 = t.sort_values(ascending=False).index[:2]
    test_only = el[(el["station"] == top1) & (el["category"] == "Test")]["std_unit_s"].sum()
    base = capacity(t)

    def scenario(**changes):
        x = t.copy()
        for k, v in changes.items():
            x[k] = v
        return capacity(x)

    rows = [
        ("Mevcut durum", None, base),
        ("B  Yalnız test istasyonu −%30", "B", scenario(**{top1: t[top1] * 0.7})),
        ("C1 Test: iç→dış iş (süre ≈ yalnız test)", None, scenario(**{top1: test_only})),
        ("C  Test iç→dış iş + kaynak −%30 (birlikte)", "C",
         scenario(**{top1: test_only, top2: t[top2] * 0.7})),
        ("D  İki istasyon da paralel (süre ÷2)", "D", scenario(**{top1: t[top1] / 2, top2: t[top2] / 2})),
    ]
    out = []
    for name, key, cap in rows:
        sold = min(cap, DEMAND)
        gain_units = max(sold - base, 0)
        yearly = gain_units * MARGIN_TL * SHIFTS_PER_YEAR
        inv = INVEST_TL.get(key)
        payback = (inv / (yearly / 12)) if inv and yearly > 0 else None
        out.append({"Seçenek": name, "Kapasite (adet/vardiya)": round(cap, 0),
                    "Talebe açık (adet)": round(max(DEMAND - cap, 0), 0),
                    "Yıllık ek katkı (TL)": round(yearly, -3), "Yatırım (TL)": inv,
                    "Geri ödeme (ay)": None if payback is None else round(payback, 1)})
    return pd.DataFrame(out)


def overtime_hours(t: pd.Series) -> float:
    """Fazla mesaiyle talebi karşılamak için vardiya başına gereken ek saat."""
    return DEMAND * t.max() / 3600 - AVAILABLE_S / 3600


def plot(df: pd.DataFrame, out_dir: Path) -> Path:
    _style()
    fig, ax = plt.subplots(figsize=(11, 4.8))
    d = df.iloc[::-1]
    colors = [GREY if "Mevcut" in n else (RED if n.startswith("B") else (ORANGE if n.startswith("C1") else BLUE))
              for n in d["Seçenek"]]
    ax.barh(d["Seçenek"], d["Kapasite (adet/vardiya)"], color=colors)
    for y, v in enumerate(d["Kapasite (adet/vardiya)"]):
        ax.text(v + 6, y, f"{v:.0f}", va="center", fontsize=10)
    ax.axvline(DEMAND, color=NAVY, ls="--", lw=1.6)
    ax.text(DEMAND + 6, len(d) - 0.45, f"Talep = {DEMAND}", color=NAVY, fontsize=10, fontweight="bold")
    ax.set_xlabel("Hat kapasitesi (adet / vardiya)")
    ax.set_title("Seçenek karşılaştırması: hangi müdahale talebi karşılar?")
    ax.grid(axis="y", visible=False)
    return _save(fig, out_dir, "11_vaka_secenekler.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", default="outputs")
    a = ap.parse_args()
    xlsx = Path("data/sample/demo_zaman_etudu.xlsx")
    if not xlsx.exists():
        demo_data.build_demo_workbook(xlsx)
    el, t = load_times(xlsx)
    df = build_options(el, t)
    out = Path(a.output)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "tables" / "vaka_secenekler.csv", index=False, encoding="utf-8-sig")
    plot(df, out / "figures")
    pd.set_option("display.width", 220, "display.max_columns", 20, "display.max_colwidth", 50)
    print(df.to_string(index=False))
    print(f"\nFazla mesai ile talebi karşılamak için vardiya başına ek süre: {overtime_hours(t):.2f} saat")
