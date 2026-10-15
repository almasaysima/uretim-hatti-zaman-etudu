import numpy as np
import pandas as pd

from src import loader, metrics


def test_fold_turkish():
    assert loader.fold("Yerleştirme") == "YERLESTIRME"
    assert loader.fold("Bırakma") == "BIRAKMA"
    assert loader.fold("İşlem") == "ISLEM"


def test_categorize():
    assert loader.categorize("Alma- Yerleştirme", "x").startswith("Elleçleme")
    assert loader.categorize("Test", "Sızıntı Testi") == "Test"
    assert loader.categorize("İşlem", "Kaynak") == "İşlem"
    assert loader.categorize("İşlem", "Bırakma").startswith("Elleçleme")


def test_required_n_edge_cases():
    assert loader._required_n([5, 5, 5, 5]) == 0.0
    assert np.isnan(loader._required_n([5]))


def test_branch_parsing():
    assert loader._branch("7701017") == "Ana"
    assert loader._branch("7701017-1,2") == "-1,2"
    assert loader._branch("DEMO100-4-5") == "-4-5"
    assert loader._branch("7701017-2", product_code="7701017") == "-2"
    assert loader._branch("", product_code=None) == "Diğer"


def test_balance_metrics_perfect_line():
    m = metrics.balance_metrics(pd.Series([10.0, 10.0, 10.0]), takt=12)
    assert m["Hat dengeleme verimi LE (%)"] == 100.0
    assert m["Düzgünlük indeksi SI (sn)"] == 0.0
    assert m["Teorik min. istasyon ⌈ΣTi/takt⌉"] == 3


def test_takt_time():
    assert metrics.takt_time(25_200, 500) == 50.4


def test_pareto_cumulative_and_vital_few():
    df = pd.DataFrame({"s": list("abcd"), "v": [70.0, 20.0, 5.0, 5.0]})
    p = metrics.pareto_table(df, "s", "v")
    assert p["cum_pct"].iloc[-1] == 100.0
    assert p["vital_few"].tolist() == [True, True, False, False]
