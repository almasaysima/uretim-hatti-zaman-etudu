"""Tek dosyalık, tarayıcıda açılan görsel rapor (outputs/rapor.html).

Grafikler base64 olarak gömülür; dosya tek başına taşınabilir/paylaşılabilir.
"""
from __future__ import annotations

import base64
import html
from datetime import datetime
from pathlib import Path

import pandas as pd

CAPTIONS = {
    "01_istasyon_standart_sureleri": ("İstasyon birim standart süreleri", "Takt çizgisinin üstündeki istasyonlar talebi karşılayamaz."),
    "09_yamazumi": ("Yamazumi", "En yüklü istasyonlarda süre bileşimi (işlem / test / elleçleme) ve takt."),
    "10_belirsizlik_monte_carlo": ("Belirsizlik (Monte Carlo)", "Ölçüm belirsizliği altında darboğaz olasılığı ve kapasite aralığı."),
    "08_whatif_kapasite": ("What-If kapasite eğrileri", "Tek istasyon iyileştirmesi plato yapar; birlikte iyileştirme kaldıraçlıdır."),
    "02_pareto_istasyon": ("Pareto — istasyon", "Toplam sürenin %80'ini oluşturan 'hayati az' istasyonlar."),
    "03_pareto_is_ogesi": ("Pareto — iş öğesi", "En çok zaman alan iş öğeleri."),
    "04_sure_dagilimi": ("Süre dağılımı", "İstasyon birim sürelerinin dağılımı."),
    "05_sure_kompozisyonu": ("Süre kompozisyonu", "İşlem / test / elleçleme payları."),
    "06_hat_dengeleme": ("Hat dengeleme", "İstasyon yükleri ve dengesizlik."),
    "07_olcum_degiskenligi": ("Ölçüm değişkenliği", "Okuma sayısı ve değişkenlik katsayısı."),
    "11_vaka_secenekler": ("Vaka: seçenek karşılaştırması", "Hangi müdahale talebi karşılar?"),
}

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#1c2530;--mut:#5d6b7a;--line:#e3e7ec;--acc:#2e86c1;--red:#c0392b}
@media(prefers-color-scheme:dark){:root{--bg:#12161b;--card:#1b222a;--ink:#e8edf2;--mut:#9aa7b4;--line:#2b343e}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,Roboto,sans-serif}
main{max-width:1200px;margin:0 auto;padding:24px 16px 64px}h1{margin:0 0 4px;font-size:26px}h2{margin:36px 0 12px;font-size:19px}
.sub{color:var(--mut)}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.k{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.04em}.v{font-size:26px;font-weight:700;margin-top:2px}.n{color:var(--mut);font-size:12px}
.warn{background:#fff4e5;color:#7a4a00;border:1px solid #f0c987;border-radius:8px;padding:10px 14px;margin-top:16px}
.fig{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px;margin:14px 0}.fig img{width:100%;height:auto;border-radius:6px;background:#fff}
.fig h3{margin:0 0 2px;font-size:16px}.fig p{margin:0 0 10px;color:var(--mut);font-size:13px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(480px,1fr));gap:14px}@media(max-width:560px){.grid2{grid-template-columns:1fr}}
.tw{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left}th{background:rgba(127,127,127,.08);position:sticky;top:0}footer{margin-top:40px;color:var(--mut);font-size:12px}
"""


def _img(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def _table(df: pd.DataFrame) -> str:
    return '<div class="tw">' + df.to_html(index=False, border=0, float_format=lambda x: f"{x:,.2f}", na_rep="–") + "</div>"


def _card(k: str, v: str, n: str = "") -> str:
    return f'<div class="card"><div class="k">{html.escape(k)}</div><div class="v">{v}</div><div class="n">{html.escape(n)}</div></div>'


def build_report(out_dir: Path, summary: pd.DataFrame, bal: pd.DataFrame, wi: pd.DataFrame, mc: pd.DataFrame,
                 takt: float, available_s: float, demand: float, cap_interval: tuple[float, float, float],
                 source_label: str, anonymized: bool) -> Path:
    out_dir = Path(out_dir)
    top = summary.sort_values("rank")
    t1, t2 = top.iloc[0], top.iloc[1]
    nominal = available_s / t1["std_unit_s"]
    lo, _, hi = cap_interval
    over = int((summary["std_unit_s"] > takt).sum())
    gap = demand - nominal
    mc_top = mc.iloc[0]

    cards = "".join([
        _card("Takt zamanı", f"{takt:.1f} sn", f"{available_s:.0f} sn / talep {demand:.0f}"),
        _card("Darboğaz (Tmax)", f"{t1['std_unit_s']:.1f} sn", str(t1["station"])),
        _card("Hat kapasitesi", f"{nominal:.0f} adet", f"Monte Carlo %90 aralığı {lo:.0f}–{hi:.0f}"),
        _card("Talep farkı", f"{max(gap, 0):.0f} adet" if gap > 0 else "Karşılanıyor", f"talep {demand:.0f}/vardiya"),
        _card("Takt'ı aşan istasyon", str(over), f"toplam {len(summary)} istasyon"),
        _card("En olası darboğaz", f"%{100 * mc_top['p_bottleneck']:.0f}", str(mc_top["station"])),
    ])
    close = (f"<p class='sub'>⚠️ <b>{html.escape(str(t1['station']))}</b> ({t1['std_unit_s']:.1f} sn) ve "
             f"<b>{html.escape(str(t2['station']))}</b> ({t2['std_unit_s']:.1f} sn) birbirine çok yakın: "
             f"yalnız birini iyileştirmek kapasiteyi artırmayabilir.</p>") if t1["std_unit_s"] - t2["std_unit_s"] < 0.05 * t1["std_unit_s"] else ""

    cols = [c for c in ("rank", "station", "branch", "crew", "batch", "std_unit_s", "load_vs_takt", "capacity_per_shift") if c in top.columns]
    st_tbl = top[cols].head(10).rename(columns={"rank": "Sıra", "station": "İstasyon", "branch": "Kol", "crew": "Operatör",
                                                "batch": "Parti", "std_unit_s": "Birim süre (sn)", "load_vs_takt": "Takt'a göre yük",
                                                "capacity_per_shift": "Kapasite (adet/vardiya)"})
    mc_tbl = mc.head(6).rename(columns={"station": "İstasyon", "p_bottleneck": "P(darboğaz)", "time_p5": "Süre p5",
                                        "time_p50": "Süre p50", "time_p95": "Süre p95", "p_over_takt": "P(takt aşımı)"})
    wi_cols = [c for c in ("Senaryo", "Hedef", "Yeni darboğaz", "Hat süresi Tmax (sn)", "Kapasite (adet/vardiya)",
                           "Kapasite artışı (%)", "Takt sağlanıyor") if c in wi.columns]
    wi_tbl = wi[wi_cols] if wi_cols else wi.iloc[:, :7]

    fig_dir = out_dir / "figures"
    pngs = {p.stem: p for p in fig_dir.glob("*.png")}
    order = [k for k in CAPTIONS if k in pngs] + sorted(k for k in pngs if k not in CAPTIONS)

    def fig(key: str) -> str:
        title, desc = CAPTIONS.get(key, (key, ""))
        return f'<div class="fig"><h3>{html.escape(title)}</h3><p>{html.escape(desc)}</p><img alt="{html.escape(title)}" src="{_img(pngs[key])}"></div>'

    big, small = order[:4], order[4:]
    warn = ""
    if "demo" in source_label.lower():
        warn = '<div class="warn">Bu rapor <b>sentetik demo verisiyle</b> üretilmiştir; değerler gerçek bir işletmeyi temsil etmez.</div>'
    elif anonymized:
        warn = '<div class="warn">İstasyon ve iş öğesi adları anonimleştirilmiştir.</div>'

    doc = f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zaman Etüdü Analizi</title><style>{CSS}</style></head><body><main>
<h1>🏭 Üretim Hattı Zaman Etüdü Analizi</h1>
<div class="sub">Kaynak: {html.escape(source_label)} · Oluşturulma: {datetime.now():%d.%m.%Y %H:%M}</div>{warn}
<div class="cards">{cards}</div>{close}
<h2>Öne çıkan grafikler</h2>{"".join(fig(k) for k in big)}
<h2>En yüklü 10 istasyon</h2>{_table(st_tbl)}
<h2>Hat dengeleme göstergeleri</h2>{_table(bal)}
<h2>What-If senaryoları</h2>{_table(wi_tbl)}
<h2>Darboğaz olasılığı (Monte Carlo)</h2>{_table(mc_tbl)}
<h2>Diğer grafikler</h2><div class="grid2">{"".join(fig(k) for k in small)}</div>
<footer>Tüm tablolar <code>outputs/tables/</code>, grafikler <code>outputs/figures/</code> altındadır.</footer>
</main></body></html>"""
    path = out_dir / "rapor.html"
    path.write_text(doc, encoding="utf-8")
    return path
