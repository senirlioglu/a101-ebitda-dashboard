# 📊 A101 EBITDA Performans Dashboard

Mağaza bazında EBITDA performans analizi ve karşılaştırma dashboard'u.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://a101-ebitda.streamlit.app)

## 🚀 Online Kullanım

Dashboard'a doğrudan erişin: **https://a101-ebitda.streamlit.app**

## 💻 Lokal Kurulum

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📁 Veri Formatı

Dashboard, aşağıdaki formatta Excel dosyası bekler:

- **Sheet adı:** `EBITDA`
- **Dönem sütunu:** `Mali yıl/dönem - Orta uzunl.metin` (örn: "Ekim 2025", "Kasım 2025")
- **En az 2 dönem** verisi gerekli

### Gerekli Sütunlar:
- Kar / Zarar
- Mağaza
- Bölge Sorumlusu - Metin
- Satış Müdürü - Metin
- Net Metrekare
- Net Satış (KDV Hariç)
- Toplam Mağaza Giderleri
- Net Marj
- Mağaza Kar/Zararı

## 📈 Dashboard Özellikleri

### 1. Genel Metrikler
- Toplam EBITDA ve değişim
- Acil müdahale gerektiren mağaza sayısı
- Yangın (üst üste negatif) mağaza sayısı
- Benchmark gider/ciro oranı
- Tasarruf potansiyeli

### 2. SM Performans
- Satış müdürü bazında EBITDA karşılaştırması
- Değişim grafiği ve tablosu

### 3. Mağaza Analizi
- **Acil Müdahale:** Negatif EBITDA veya 100K+ düşüş
- **Yangın:** Üst üste 2 ay negatif EBITDA
- **Düşenler:** EBITDA azalan tüm mağazalar
- **Gelişenler:** EBITDA artan mağazalar
- **Tüm Mağazalar:** Filtrelenebilir tam liste

### 4. Gider Analizi
- En yüksek gider/ciro oranları
- Benchmark karşılaştırması
- Tasarruf potansiyeli hesaplaması

### 5. Rapor İndirme
- Excel raporu (5 sheet)
- CSV veri dosyası

## 🔥 Sebep Analizi

Her mağaza için EBITDA düşüş sebebi otomatik tespit edilir:

- **CİRO:** Ciro 50K+ TL düşmüş
- **GİDER:** Gider 30K+ TL artmış
- **MARJ:** Net marj 50K+ TL düşmüş
- **KARMA:** Yukarıdakilerin kombinasyonu
- **POZİTİF:** EBITDA artmış

## 📊 Aksiyon Listesi

Dashboard'un ana çıktısı **"Bu ay hangi mağazalara gidilmeli?"** sorusuna cevap verir:

1. **Önce YANGIN:** Üst üste negatif mağazalar
2. **Sonra ACİL:** Yeni negatife düşenler veya büyük düşüşler
3. **Son olarak:** Gider/ciro oranı yüksek olanlar

## 🔄 Her Ay Yapılacaklar

1. Yeni ayın EBITDA raporunu indir
2. Dashboard'a yükle
3. Acil ve yangın listelerini incele
4. SM toplantısında paylaş
5. Aksiyon listesi oluştur

---

**A101 Antalya Bölgesi | EBITDA Performans Takibi**
