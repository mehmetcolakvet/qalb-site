# deruni.app

Deruni tanıtım sayfası — Türkçe `/` ve İngilizce `/en/`. Tek dosyalık statik sayfa,
dış JS/CSS/font yok, üçüncü taraf istek yok.

## Yapı

| Dosya | Ne işe yarar |
|---|---|
| `_body.tr.html` · `_body.en.html` | Sayfa gövdeleri (kaynak) |
| `_style.css` · `_app.js` | Ortak stil ve betik (kaynak) |
| `build.py` | Yukarıdakileri `index.html` ve `en/index.html` içine gömer |
| `index.html` · `en/index.html` | **Üretilmiş dosyalar — elle düzenleme** |
| `privacy.html` `terms.html` `kvkk.html` | Hukuki sayfalar. **Adları değişmez** — yayındaki mobil uygulama bu adresleri kodda sabit tutuyor. |
| `assets/` | Ekran görüntüleri (WebP), ikonlar, og görselleri, YouTube kapakları |

## Derleme

```bash
python3 build.py            # ilahi listesini CDN manifestinden çeker
python3 build.py --offline  # ağ yoksa yerel önbellekten
```

İlahi süreleri ve dosya boyutları `https://deruni.vetkriter.com/manifest.json`
dosyasından üretilir; elle yazılmaz. Manifest 16 kayıt / 55:17 dışına çıkarsa
derleme uyarı verir, çünkü sayfa metni "on altı ilahi · elli beş dakika on yedi
saniye" diyor.

## Değiştirirken dikkat

- **`#tr` / `#en` hash'leri çalışmaya devam etmeli.** YouTube kanalının tek dış
  bağlantısı ve TikTok video açıklamaları `https://www.deruni.app/#tr` adresini
  gösteriyor. `_app.js` bunu `/` ve `/en/` arasında yönlendiriyor.
- **Esma sayısı yazılmaz.** `docs/content/esma-editorial-standard.md` §2:
  "99 Esma" ✗ (koleksiyon 102 kayıt), "102 Esma" ✗ (kanonik değil).
- **Fiyat yazılmaz** (bölgesel, RevenueCat'ten gelir), **puan/yıldız yazılmaz**
  (App Store'da yalnızca 2 oy var).
- Sayfa "çerez yok, izleme kodu yok, dış betik yok, üçüncü taraf gömülü oynatıcı
  yok" diyor. **Analitik ya da gömülü oynatıcı eklenirse bu cümle silinmelidir.**
- CSS'te `text-transform: uppercase` KULLANMA — Türkçe'de "Bilgi" → "BILGI",
  "Şifa" → "ŞIFA" üretir. Büyük harfli metinler HTML'de büyük harfle yazılır.
