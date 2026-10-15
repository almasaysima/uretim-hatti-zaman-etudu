# Üretim Hattı Zaman Etüdü — Mühendislik Raporu (demo vaka)

> **Önemli:** Bu rapor, depoyla gelen **sentetik demo verisi** (25 istasyon, 62 iş öğesi) üzerinden yazılmıştır; gerçek bir işletmeyi temsil etmez. Amaç, analiz hattının ne ürettiğini ve çıktıların nasıl yorumlanacağını göstermektir. Tüm sayılar `python run_analysis.py --demo` ile yeniden üretilir.

## 0. Yönetici özeti

Hat, mevcut standart sürelerle vardiyada (7 net saat) **≈352 adet** üretebilmektedir (Tmax = 71,5 sn). Kapasiteyi tek bir istasyon değil, **iki istasyon birlikte** sınırlar: *Sızıntı Testi* (71,5 sn) ve *Birleştirme Kaynak* (71,3 sn, 2 operatör). Ölçüm belirsizliği altında darboğaz olma olasılıkları **%52 / %48**'dir; kapasite için %90 aralık **324–364 adet**.

1. **İyileştirme birlikte yapılmalı.** İlk darboğazı %50 hızlandırmak kapasiteyi yalnızca **%0,2** artırır, çünkü ikincisi devralır. İlk 3 istasyonda birlikte −%30 → **≈503 adet (+%42,9)** ve 50,4 sn takt sağlanır.
2. **Ham parti süreleri yanıltıcıdır.** `-1 Kapiler Kaynak` formda 280,5 sn ile en büyük sayıdır; 35'lik partidir → **8,0 sn/adet** (25 istasyonda 16.). Karar birim süre üzerinden verilmelidir.
3. **Önce yeniden ölçüm.** 62 öğenin 13'ü tek okumaya dayanır, yalnızca 1'i Niebel kriterini sağlar. İlk Kaizen adımı darboğaz istasyonlarında ≥10 okumalı ölçümdür.

> Takt (50,4 sn) varsayımdır: 500 adet/vardiya, 25.200 sn. Darboğaz sıralaması takt'tan bağımsızdır.

## 1. Veri ve doğrulama

| Madde | Bulgu |
|---|---|
| Kaynak | 26 sayfa = 25 zaman etüdü formu + 1 rota (ERP) sayfası (atlanır) |
| Doğrulama | 62 öğenin tamamında yeniden hesaplanan ortalama ve standart süre formla eşleşir; "STANDART SÜRE" = parti toplamının yukarı yuvarlanmışı (25/25 tutarlı) |
| Parti ölçümü | Çoğu istasyon 5–35 adetlik parti ölçer; hepsi birim süreye normalize edilir |
| Örneklem | 13/62 tek okuma; 2/62 ≥5 okuma; 1/62 Niebel kriterini sağlar |
| Ekip | Yalnızca *Birleştirme Kaynak* 2 operatörlü; süre çevrim süresi kabul edilmiştir |

## 2. Bulgular

### 2.1 Birim standart süre sıralaması
![](../outputs/figures/01_istasyon_standart_sureleri.png)

| Sıra | İstasyon | Parti | Birim süre (sn) | Takt'a göre yük |
|---:|---|---:|---:|---:|
| 1 | Sızıntı Testi | 1 | 71,5 | %142 |
| 2 | Birleştirme Kaynak (2 operatör) | 1 | 71,3 | %142 |
| 3 | Etiket Bantlama | 1 | 42,5 | %84 |
| 4 | Isıtma Fırını | 5 | 35,2 | %70 |
| 5 | Montaj Takma | 1 | 31,9 | %63 |
| 16 | *-1 Kapiler Kaynak* | 35 | *8,0* | %16 |

Parti normalizasyonu sıralamayı değiştirir: ham parti toplamında 1. olan `-1 Kapiler Kaynak` (280,5 sn) birim bazında 16.'dır; `Isıtma Fırını` (176 sn) ise 2.'den 4.'ye düşer.

### 2.2 Pareto
![](../outputs/figures/02_pareto_istasyon.png)

25 istasyonun **11'i** toplam sürenin %80'ini oluşturur; ilk iki istasyon tek başına **%30,8**. İş öğesi düzeyinde 62 öğenin 26'sı %80'i yapar; tek öğe (*Sızıntı testi*, 50,6 sn) tüm iş içeriğinin **%10,9**'udur.

### 2.3 Takt ve talep duyarlılığı

| Talep (adet/vardiya) | Takt (sn) | Takt'ı aşan istasyon |
|---:|---:|---|
| 300 | 84,0 | 0 |
| 400 | 63,0 | 2 (Sızıntı Testi, Birleştirme Kaynak) |
| **500 (varsayım)** | **50,4** | **2** |
| 600 | 42,0 | 3 (+ Etiket Bantlama) |
| 700 | 36,0 | 3 |

Talep ≤352 ise hat takt'ı zaten karşılar ve mesele verimlilik/maliyettir; üzerinde ise iki istasyon **kapasite sorunudur**.

### 2.4 Hat dengeleme

| Gösterge | Tüm istasyonlar (25) | Ana hat (12) |
|---|---:|---:|
| ΣTi | 464,4 sn | 322,0 sn |
| Tmax | 71,5 sn | 71,5 sn |
| **LE** | **%26,0** | **%37,5** |
| BD | %74,0 | %62,5 |
| SI | 281,3 sn | 175,5 sn |
| Teorik min. istasyon | 10 | 7 |

**Yorum:** LE, "%74 israf" demek **değildir**; istasyonların bir kısmı paralel alt montaj kollarına aittir ve tek seri hat varsayılmıştır. 11 istasyon <10 sn'dir ve iş içeriğinin yalnızca **%11,0**'ını (51,3 sn) taşır → çok istasyonlu operatör/birleştirme fırsatı (akış doğrulanmadan uygulanmamalı). Kol bazlı değerler: `outputs/tables/kol_bazli_dengeleme.csv`.

### 2.5 Metot etüdü: süre bileşimi ve yamazumi
![](../outputs/figures/09_yamazumi.png)

Toplam 464,4 sn'nin **%70,8'i işlem (328,6 sn)**, **%18,4'ü elleçleme (85,3 sn)**, **%10,9'u testtir (50,6 sn)**. Elleçleme payı en yüksek istasyonlar: **Paketleme (%53)**, **Ana Boru Kaynak (%42)**, **-3 Form Verme (%39)** → aparat, besleme ve yerleşim (5S) iyileştirmesi için en verimli alan.

### 2.6 What-If
![](../outputs/figures/08_whatif_kapasite.png)

| Senaryo | Tek istasyon (en iyi) | **İlk 3 birlikte** |
|---|---|---|
| S1: süre −%10 | 353 (+%0,2) | **392 (+%11,1)** |
| S3: süre −%30 | 353 (+%0,2) | **503 (+%42,9)** ✅ takt |
| S4: 2. paralel istasyon (süre ÷2) | 353 (+%0,2) | **705 (+%100)** ✅ takt |

**Plato:** Tek istasyon ne kadar iyileştirilirse iyileştirilsin kapasite ≈353'te kalır (ikinci darboğaz devralır).

### 2.7 Belirsizlik (Monte Carlo)
![](../outputs/figures/10_belirsizlik_monte_carlo.png)

Her öğenin ortalaması okuma sayısına bağlı standart hatayla 5.000 kez örneklenmiştir. Sonuç: darboğaz **%52 Sızıntı Testi / %48 Birleştirme Kaynak**; kapasite %90 aralığı **324–364**, simülasyon medyanı ≈346 (nokta tahmin 352 hafif iyimserdir). **Hangisinin birinci olduğu veriyle ayırt edilemiyor** — bu nedenle öneri ikisini birlikte hedefler ve yeniden ölçümle başlar. Model yalnızca örnekleme belirsizliğini kapsar.

## 3. Öneriler ve Kaizen planı (90 gün)

| Faz | Dönem | Eylem | KPI |
|---|---|---|---|
| **0 – Doğrula** | Hafta 0–2 | Gerçek talep/takt; ilk 5 istasyonda ≥10 okumalı yeniden ölçüm; 2 operatör varsayımı; analizi yeniden çalıştır | Her öğe ≥10 okuma, CV <%15 |
| **1 – Hızlı kazanım** | Hafta 2–6 | Test istasyonunda iç→dış iş dönüşümü (yerleştirme + prob kontrolü test süresiyle örtüşsün); kaynak hazırlıkta aparat/mastar; bantlamada dispenser; elleçleme için 5S | İlk 3 istasyonda ≈−%20 (S2: ≈455 adet) |
| **2 – Kapasite** | Hafta 6–12 | İkinci test kabini/mekik tabla fizibilitesi; ısıtmada çift ısıtıcı; çok istasyonlu operatör pilotu | Tmax ≤ takt; ana hat LE ≥%45 |
| **3 – Standartlaştır** | Hafta 12+ | SOP ve standart süre güncelleme; yamazumi panosu; analizi aylık otomatik çalıştır | Kapasite ≥ talep × 1,1 |

Beklenen kazanç What-If tabanlıdır, garanti değildir.

## 4. Sınırlılıklar

1. Takt/talep varsayımdır. 2. Tek seri hat varsayımı; ara stok ve operatör paylaşımı modellenmemiştir. 3. Rating yoktur (Tn = Tm). 4. Örneklem sınırlıdır; sonuçlar yönlendiricidir. 5. 2 operatörlü istasyonda emek içeriği çevrim süresinden yüksek olabilir. 6. What-If teorik kapasitedir.
