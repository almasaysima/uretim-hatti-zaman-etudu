"""Herkese açık paylaşım için çıktıları maskeleme.

Sınıflandırma (İşlem/Test/Elleçleme) isimlere bakılarak yapıldığından, maskeleme
`loader.clean_and_compute`'tan SONRA uygulanmalıdır.
"""
from __future__ import annotations

import pandas as pd


def anonymize(el: pd.DataFrame, st: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """İstasyon adı → İST-01.., iş öğesi adı → Öğe N; ürün kodu ve operasyon adı silinir."""
    mapping = {n: f"İST-{i:02d}" for i, n in enumerate(st["station"], 1)}
    el, st = el.copy(), st.copy()
    el["station"] = el["station"].map(mapping)
    st["station"] = st["station"].map(mapping)
    el["element"] = [f"Öğe {s}" for s in el["seq"]]
    st["code"], st["op_name"] = "", ""
    return el, st
