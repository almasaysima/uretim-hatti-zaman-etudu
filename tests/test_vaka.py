import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import vaka_secenekler as v  # noqa: E402


def test_options_logic(demo_xlsx):
    el, t = v.load_times(demo_xlsx)
    df = v.build_options(el, t).set_index("Seçenek")
    base = df.loc["Mevcut durum", "Kapasite (adet/vardiya)"]
    b = df.filter(like="B  ", axis=0)["Kapasite (adet/vardiya)"].iloc[0]
    c1 = df.filter(like="C1", axis=0)["Kapasite (adet/vardiya)"].iloc[0]
    c = df.filter(like="C  ", axis=0)["Kapasite (adet/vardiya)"].iloc[0]
    d = df.filter(like="D  ", axis=0)["Kapasite (adet/vardiya)"].iloc[0]
    assert b - base <= 2 and c1 - base <= 2          # tek istasyon iyileştirmesi kazandırmaz
    assert c > 480 and d > c                        # birlikte iyileştirme kaldıraçlıdır
    assert 2.5 < v.overtime_hours(t) < 3.5
