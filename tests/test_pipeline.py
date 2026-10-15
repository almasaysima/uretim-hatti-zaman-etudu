import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src import anonymize, metrics, uncertainty, whatif
from tests.conftest import AVAILABLE

ROOT = Path(__file__).resolve().parents[1]


def test_station_count_and_skipped_route_sheet(study):
    assert len(study["st"]) == 25
    assert study["skipped"] == ["Sayfa1"]


def test_fatigue_is_ten_percent(study):
    el = study["el"]
    assert np.allclose(el["fatigue_s"], el["mean_s"] * 0.10)
    assert np.allclose(el["std_s"], el["mean_s"] * 1.10)


def test_recomputed_matches_excel_form(study):
    assert study["el"]["form_match"].all()
    assert study["summary"]["form_ceil_ok"].all()


def test_batch_normalisation_changes_ranking(study):
    """35'lik partide ölçülen istasyon ham süresi en büyüktür ama birim süresi küçüktür."""
    el, s = study["el"], study["summary"].set_index("station")
    raw_batch = el.groupby("station")["std_s"].sum()
    assert raw_batch.idxmax() == "-1 KAPİLER KAYNAK"
    assert s.loc["-1 KAPİLER KAYNAK", "batch"] == 35
    assert s.loc["-1 KAPİLER KAYNAK", "rank"] > 10
    assert s.loc["-1 KAPİLER KAYNAK", "std_unit_s"] < 10


def test_two_operator_station_detected(study):
    s = study["summary"].set_index("station")
    assert s.loc["BİRLEŞTİRME KAYNAK", "crew"] == 2


def test_whatif_bottleneck_shift(study):
    """İlk darboğazı tek başına çok hızlandırmak, ikinci darboğaz yüzünden kapasiteyi sınırlar."""
    s, el = study["summary"], study["el"]
    top1, top2 = s.sort_values("rank")["station"].iloc[:2]
    wi = whatif.run_whatif(s, el, AVAILABLE, study["takt"])
    row = wi[(wi["Senaryo"] == "S4") & (wi["Hedef"] == top1)].iloc[0]
    assert row["Yeni darboğaz"] == top2
    second_time = s.set_index("station").loc[top2, "std_unit_s"]
    assert abs(row["Hat süresi Tmax (sn)"] - round(second_time, 2)) < 0.01
    both = wi[(wi["Senaryo"] == "S4") & (wi["Hedef"].str.startswith("İlk"))].iloc[0]
    assert both["Kapasite (adet/vardiya)"] > row["Kapasite (adet/vardiya)"]


def test_branch_balance_covers_all_stations(study):
    b = metrics.branch_balance(study["summary"], study["takt"])
    assert b["İstasyon"].sum() == len(study["summary"])


def test_monte_carlo_is_valid_and_reproducible(study):
    el, s = study["el"], study["summary"]
    mc1, cap1 = uncertainty.simulate(el, AVAILABLE, study["takt"], n_sims=2000, seed=7)
    mc2, cap2 = uncertainty.simulate(el, AVAILABLE, study["takt"], n_sims=2000, seed=7)
    assert np.isclose(mc1["p_bottleneck"].sum(), 1.0)
    assert np.array_equal(cap1, cap2)
    assert (mc1["time_p5"] <= mc1["time_p50"]).all() and (mc1["time_p50"] <= mc1["time_p95"]).all()
    nominal = AVAILABLE / s["std_unit_s"].max()
    lo, _, hi = uncertainty.capacity_interval(cap1)
    assert lo < nominal * 1.05 and hi > nominal * 0.95          # nokta tahmin makul aralıkta
    assert mc1.iloc[0]["station"] in set(s.sort_values("rank")["station"].iloc[:2])


def test_monte_carlo_more_readings_less_uncertainty(study):
    el = study["el"].copy()
    _, cap_few = uncertainty.simulate(el, AVAILABLE, study["takt"], n_sims=3000, seed=1)
    el["n_readings"] = el["n_readings"] * 10
    _, cap_many = uncertainty.simulate(el, AVAILABLE, study["takt"], n_sims=3000, seed=1)
    assert np.std(cap_many) < np.std(cap_few)


def test_anonymize_masks_names_but_keeps_results(study):
    el, st = study["el"], study["st"]
    el_a, st_a = anonymize.anonymize(el, st)
    summary_a = metrics.station_summary(el_a, st_a)
    assert set(summary_a["station"]) == {f"İST-{i:02d}" for i in range(1, len(st) + 1)}
    assert (st_a["code"] == "").all() and (st_a["op_name"] == "").all()
    assert not any("KAYNAK" in e or "Test" in e for e in el_a["element"])
    assert np.isclose(summary_a["std_unit_s"].max(), study["summary"]["std_unit_s"].max())
    assert (el_a["category"] == el["category"]).all()


def test_no_personal_data_columns(study):
    for col in study["el"].columns.tolist() + study["st"].columns.tolist():
        assert "operator" not in col.lower() and "analist" not in col.lower()


def test_cli_demo_end_to_end(tmp_path):
    r = subprocess.run([sys.executable, "run_analysis.py", "--demo", "--output", str(tmp_path / "o"),
                        "--sims", "500", "--anonymize"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert len(list((tmp_path / "o" / "tables").glob("*.csv"))) == 9
    assert len(list((tmp_path / "o" / "figures").glob("*.png"))) == 10
    html = (tmp_path / "o" / "rapor.html").read_text(encoding="utf-8")
    assert "<img" in html and "Takt zamanı" in html and "İST-" in html and "SIZINTI" not in html
    summary = pd.read_csv(tmp_path / "o" / "tables" / "istasyon_ozet.csv", encoding="utf-8-sig")
    assert summary["station"].str.startswith("İST-").all()
