"""Merkezi parametreler. Gerçek planlama verinizle burayı (veya CLI argümanlarını) güncelleyin."""

# --- Zaman etüdü sabitleri -------------------------------------------------------------
FATIGUE_RATE = 0.10          # Formlardaki "Yorgunluk Payı %10"

# Form yerleşimi (1 tabanlı Excel sütun numaraları)
COL_A, COL_B, COL_C = 1, 2, 3
COL_FIRST_READING, COL_LAST_READING = 4, 36   # D .. AJ  (ölçüm okumaları)
COL_OP_NAME = 20                              # T  (operasyon adı)
COL_CREW_NOTE = 27                            # AA (yalnız "N OPERATÖR" notu aranır; isimler okunmaz)
COL_DATE = 37                                 # AK (analiz tarihi)
COL_MEAN, COL_FATIGUE, COL_STD = 37, 38, 39   # AK, AL, AM

# Ürün kodu (hat kolu ayrıştırma). None → kod alanındaki ilk alfanümerik öbek otomatik bulunur.
# Örn. "7701017-1,2" → kol "-1,2";  "7701017" → kol "Ana".
PRODUCT_CODE = None

# --- Takt zamanı parametreleri (VARSAYIM: gerçek talebinizle değiştirin) ----------------
AVAILABLE_TIME_PER_SHIFT_S = 25_200   # 8 sa vardiya - 60 dk mola/yemek = 7 sa net çalışma
DEMAND_PER_SHIFT = 500                # adet / vardiya  (YER TUTUCU - gerçek plan değerini girin)
DEMAND_SCENARIOS = (300, 400, 500, 600, 700)

# --- What-if / Pareto --------------------------------------------------------------------
N_BOTTLENECKS_FOR_WHATIF = 3
PARETO_CUTOFF = 0.80

# Örneklem yeterliliği (Niebel: %95 güven, ±%5 hata)
SAMPLE_CONFIDENCE_K = 40
MIN_READINGS = 5
