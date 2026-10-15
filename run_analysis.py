#!/usr/bin/env python3
"""Uçtan uca analiz: Excel formları → temiz veri → standart süre → takt/dengeleme → what-if → grafikler.

Kullanım:
    python run_analysis.py --demo                                   # sentetik örnek veriyle (veri gerekmez)
    python run_analysis.py --input data/raw/etut.xlsx               # kendi verinizle
    python run_analysis.py --input data/raw/etut.xlsx --demand 400 --available-time 25200 --anonymize
"""
from __future__ import annotations

import argparse
import webbrowser
from pathlib import Path

import pandas as pd

from src import config as cfg
from src import anonymize as anon
from src import demo_data, loader, metrics, plots, report_html, uncertainty, whatif


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", default=None, help="Zaman etüdü Excel dosyası (--demo ile birlikte gerekmez)")
    p.add_argument("--demo", action="store_true",
                   help="Gerçek veri yerine sentetik demo verisini (data/sample/) kullan; yoksa üretir")
    p.add_argument("--product-code", default=None,
                   help="Hat kolu ayrıştırması için ürün kodu (varsayılan: kod alanından otomatik)")
    p.add_argument("--sims", type=int, default=5000, help="Monte Carlo simülasyon sayısı")
    p.add_argument("--seed", type=int, default=42, help="Monte Carlo rastgele tohum (tekrarlanabilirlik)")
    p.add_argument("--output", default="outputs", help="Çıktı klasörü")
    p.add_argument("--available-time", type=float, default=cfg.AVAILABLE_TIME_PER_SHIFT_S,
                   help="Vardiya net çalışma süresi (sn)")
    p.add_argument("--demand", type=float, default=cfg.DEMAND_PER_SHIFT,
                   help="Vardiya başına talep (adet) → takt zamanı")
    p.add_argument("--anonymize", action="store_true",
                   help="İstasyon adlarını İST-01.. olarak maskele; ürün kodu ve operasyon adlarını çıktılardan kaldır")
    p.add_argument("--open", action="store_true", help="Bitince görsel raporu (rapor.html) tarayıcıda aç")
    return p.parse_args()


def save(df: pd.DataFrame, path: Path):
    df.to_csv(path, index=False, encoding="utf-8-sig", float_format="%.4f")   # Excel (TR) uyumlu


def main():
    a = parse_args()
    out = Path(a.output)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(parents=True, exist_ok=True)

    # 1) Oku + temizle + standart süre
    if a.demo:
        path = Path("data/sample/demo_zaman_etudu.xlsx")
        if not path.exists():
            demo_data.build_demo_workbook(path)
        a.input = str(path)
    elif a.input is None:
        raise SystemExit("--input <excel> verin veya --demo ile örnek veriyi çalıştırın.")
    el_raw, st, skipped = loader.load_time_studies(a.input, a.product_code)
    el = loader.clean_and_compute(el_raw, st)
    if a.anonymize:                                   # herkese açık repo için güvenli çıktı
        el, st = anon.anonymize(el, st)
    summary = metrics.station_summary(el, st)
    takt = metrics.takt_time(a.available_time, a.demand)
    summary = metrics.add_takt_columns(summary, a.available_time, a.demand)

    # 2) Metrikler
    bal = metrics.balance_table(summary, takt)
    sens = metrics.takt_sensitivity(summary, a.available_time)
    pareto_st = metrics.pareto_table(summary, "station", "std_unit_s")
    pareto_el = metrics.pareto_table(el.assign(label=el["station"] + " › " + el["element"]), "label", "std_unit_s")
    wi = whatif.run_whatif(summary, el, a.available_time, takt)
    curves = whatif.capacity_curves(summary, a.available_time)
    branches = metrics.branch_balance(summary, takt)
    mc, cap_samples = uncertainty.simulate(el, a.available_time, takt, a.sims, a.seed)
    cap_lo, cap_med, cap_hi = uncertainty.capacity_interval(cap_samples)
    nominal_cap = a.available_time / summary["std_unit_s"].max()

    # 3) Tablolar
    save(el.drop(columns=["readings"]), out / "tables" / "is_ogesi_detay.csv")
    save(summary.drop(columns=["study_date"], errors="ignore"), out / "tables" / "istasyon_ozet.csv")
    save(bal, out / "tables" / "hat_dengeleme_metrikleri.csv")
    save(sens, out / "tables" / "takt_duyarlilik.csv")
    save(pareto_st, out / "tables" / "pareto_istasyon.csv")
    save(pareto_el, out / "tables" / "pareto_is_ogesi.csv")
    save(wi, out / "tables" / "whatif_senaryolari.csv")
    save(branches, out / "tables" / "kol_bazli_dengeleme.csv")
    save(mc, out / "tables" / "belirsizlik_monte_carlo.csv")

    # 4) Grafikler
    fig_dir = out / "figures"
    plots.plot_station_times(summary, takt, fig_dir)
    plots.plot_pareto_stations(summary, fig_dir)
    plots.plot_pareto_elements(el, fig_dir)
    plots.plot_distribution(summary, fig_dir)
    plots.plot_composition(el, summary, fig_dir)
    plots.plot_line_balance(summary, takt, fig_dir)
    plots.plot_reading_variability(el, summary, fig_dir)
    plots.plot_whatif(curves, summary, a.available_time, takt, fig_dir)
    plots.plot_yamazumi(el, summary, takt, fig_dir)
    plots.plot_uncertainty(mc, cap_samples, nominal_cap, a.available_time / takt, fig_dir)

    # 5) Görsel rapor (tarayıcıda açılan tek dosya)
    report = report_html.build_report(
        out, summary, bal, wi, mc, takt, a.available_time, a.demand, (cap_lo, cap_med, cap_hi),
        source_label="Sentetik demo verisi" if a.demo else Path(a.input).name, anonymized=a.anonymize)
    if a.open:
        webbrowser.open(report.resolve().as_uri())

    # 6) Konsol özeti
    pd.set_option("display.width", 200, "display.max_columns", 30, "display.max_colwidth", 40)
    print(f"\nOkunan istasyon formu: {len(st)} | iş öğesi: {len(el)} | atlanan sayfa: {skipped}")
    print(f"Form doğrulaması (AM = ort×1.10): {el['form_match'].all()} | "
          f"yuvarlanmış standart süre tutarlı: {summary['form_ceil_ok'].all()}")
    print(f"Takt = {takt:.1f} sn  (net süre {a.available_time:.0f} sn / talep {a.demand:.0f})\n")
    print(summary[["rank", "station", "batch", "std_unit_s", "load_vs_takt", "capacity_per_shift"]].head(10).round(2).to_string(index=False))
    print("\n", bal.T.to_string(header=False))
    top = mc.iloc[0]
    print(f"\nMonte Carlo ({a.sims} sim.): kapasite %90 aralığı {cap_lo:.0f}–{cap_hi:.0f} adet/vardiya "
          f"(nokta tahmin {nominal_cap:.0f}); en olası darboğaz {top['station']} (%{100 * top['p_bottleneck']:.0f})")
    print(f"\nTablolar → {out / 'tables'} | Grafikler → {fig_dir}")
    print(f"Görsel rapor → {report}  (tarayıcıda açın veya --open kullanın)")


if __name__ == "__main__":
    main()
