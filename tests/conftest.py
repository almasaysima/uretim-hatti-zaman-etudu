"""Ortak fixture'lar: testler gerçek veri gerektirmez, sentetik demo verisini kullanır."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import demo_data, loader, metrics  # noqa: E402

AVAILABLE, DEMAND = 25_200, 500


@pytest.fixture(scope="session")
def demo_xlsx(tmp_path_factory):
    return demo_data.build_demo_workbook(tmp_path_factory.mktemp("demo") / "demo.xlsx", seed=42)


@pytest.fixture(scope="session")
def study(demo_xlsx):
    el_raw, st, skipped = loader.load_time_studies(demo_xlsx)
    el = loader.clean_and_compute(el_raw, st)
    summary = metrics.add_takt_columns(metrics.station_summary(el, st), AVAILABLE, DEMAND)
    return {"el": el, "st": st, "skipped": skipped, "summary": summary,
            "takt": metrics.takt_time(AVAILABLE, DEMAND)}
