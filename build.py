#!/usr/bin/env python3
"""deruni.app sayfa derleyicisi.

_body.<dil>.html + _style.css + _app.js dosyalarını tek dosyalık statik sayfaya
birleştirir. İlahi listesi CDN manifestinden üretilir (elle yazılmış süre/boyut yok).

Kullanım:  python3 build.py            (manifest ağdan)
           python3 build.py --offline  (yerel manifest.json önbelleğinden)
"""
import json, subprocess, sys, urllib.request, pathlib, html

ROOT = pathlib.Path(__file__).parent
MANIFEST_URL = "https://deruni.vetkriter.com/manifest.json"
CACHE = ROOT / "_manifest.cache.json"

IOS = {"tr": "https://apps.apple.com/tr/app/deruni/id6759687639",
       "en": "https://apps.apple.com/app/deruni/id6759687639"}
AND = {"tr": "https://play.google.com/store/apps/details?id=com.mehmetcolak.deruni&hl=tr",
       "en": "https://play.google.com/store/apps/details?id=com.mehmetcolak.deruni&hl=en"}
# Apple Music sanatçı sayfası (Derûnî, id 6803085837) — TR sayfası TR vitrinine gider.
AM = {"tr": "https://music.apple.com/tr/artist/der%C3%BBn%C3%AE/6803085837?l=tr",
      "en": "https://music.apple.com/us/artist/der%C3%BBn%C3%AE/6803085837"}

# ---------------------------------------------------------------------------
# SSS — hem görünür bölümü hem FAQPage yapılandırılmış verisini BU listeden
# üretiyoruz; ikisi asla ayrışamaz. Marka kuralları geçerli: sonuç vaadi yok,
# Esma sayısı yok, fiyat yok.
# ---------------------------------------------------------------------------
FAQ = {
    "tr": [
        ("Deruni ücretsiz mi?",
         "Evet. Zikir, 1 Dakika Nefes, Esma Kütüphanesi'nin tamamı, on altı ilahinin tamamı, "
         "bir sesli tefekkür, üç yolun da 1. günü ve günde bir Manevi Tavsiye ücretsizdir. "
         "Premium aboneliği yolculukların tamamını, on iki sesli tefekkürü ve sınırsız tavsiyeyi açar. "
         "Fiyat bulunduğun ülkeye göre değişir ve mağazada görünür."),
        ("Hesap açmam gerekiyor mu, verilerim nereye gidiyor?",
         "Hesap yok, kayıt yok, giriş yok; bir e-posta bile sorulmaz. Tüm veriler varsayılan olarak "
         "yalnızca cihazında saklanır. Anonim kullanım verisi varsayılan olarak kapalıdır ve "
         "istediğin zaman tüm verilerini dışa aktarabilir ya da silebilirsin."),
        ("İnternet olmadan çalışır mı?",
         "Zikir, nefes ve on iki sesli tefekkür uygulamanın içinde gömülü olduğu için internetsiz çalışır. "
         "Yolculuk günlerinin sesli eşlikleri ve ilahiler ilk dinlemede indirilir; indirdikten sonra "
         "onlar da çevrimdışı açılır."),
        ("Deruni tıbbi ya da psikolojik bir uygulama mı?",
         "Hayır. Deruni tıbbi tedavi veya psikolojik terapi yerine geçmez. İçerikler manevi destek ve "
         "kişisel farkındalık amacı taşır; herhangi bir hastalığı teşhis etme, tedavi etme veya önleme "
         "iddiası taşımaz. Ciddi bir zorlanma yaşıyorsan bir sağlık uzmanına başvur; acil durumda 112."),
        ("Deruni Yolculuk nedir, nereden başlarım?",
         "Her biri yedi gün süren üç yol var: Sükûnet, Gece Sükûneti ve Uykuya Hazırlık, Öz Değer. "
         "Toplam yirmi bir gün. Her gün bir Esma etrafında bir dakika nefes, zikir, güne özel bir sesli "
         "eşlik, bir tefekkür sorusu ve küçük bir adım birleşir. Her yolun 1. günü herkese açıktır, "
         "yani indirir indirmez üç tam gün yürüyebilirsin."),
        ("İlahileri nereden dinleyebilirim?",
         "On altı ilahinin tamamı uygulamanın İlahiler bölümünde ücretsizdir. Bu sayfadan da hiçbir şey "
         "indirmeden dinleyebilirsin. Yayınlar ayrıca Spotify, Apple Music ve YouTube üzerinden sürüyor."),
        ("Hangi dillerde kullanılabiliyor?",
         "Uygulama arayüzü Türkçe ve İngilizcedir; sesli tefekkürler ve yolculuk kayıtları iki dilde de "
         "ayrı ayrı seslendirilmiştir. İlahiler Türkçe, İngilizce ve Arapça olarak bulunur."),
        ("Hangi cihazlarda çalışıyor?",
         "iOS ve Android. App Store ve Google Play üzerinden ücretsiz indirilir."),
    ],
    "en": [
        ("Is Deruni free?",
         "Yes. Zikr, the 1 Minute Breath, the whole Esma Library, all sixteen hymns, one guided reflection, "
         "day one of all three paths and one Guidance a day are free. A Premium subscription opens the full "
         "journeys, all twelve guided reflections and unlimited guidance. Pricing varies by country and is "
         "shown in your store."),
        ("Do I need an account, and where does my data go?",
         "There is no account, no sign-up and no login; you are not even asked for an email. All data is "
         "stored only on your device by default. Anonymous usage data is off by default, and you can export "
         "or delete everything at any time."),
        ("Does it work without an internet connection?",
         "Zikr, breath and the twelve guided reflections are embedded in the app, so they work offline. "
         "The journey recordings and the hymns download the first time you play them; after that they open "
         "offline too."),
        ("Is Deruni a medical or psychological app?",
         "No. Deruni is not a substitute for medical treatment or psychological therapy. Its content is "
         "intended for spiritual support and personal awareness; it makes no claim to diagnose, treat or "
         "prevent any condition. If you are struggling seriously, please seek a health professional, and in "
         "an emergency call your local emergency number."),
        ("What is the Deruni Journey and where do I start?",
         "There are three paths of seven days each: Stillness, Evening Calm and Sleep Preparation, and "
         "Self-Worth — twenty-one days in total. Each day weaves one minute of breath, zikr, the day's own "
         "recording, a reflection question and one small step around a single Esma. Day one of every path is "
         "open to everyone, so you can walk three full days the moment you install."),
        ("Where can I listen to the hymns?",
         "All sixteen hymns are free in the Hymns section of the app. You can also listen here on this page "
         "without installing anything. Releases are also rolling out on Spotify, Apple Music and YouTube."),
        ("Which languages does it support?",
         "The app interface is Turkish and English; the guided reflections and journey recordings are voiced "
         "separately in both. The hymns come in Turkish, English and Arabic."),
        ("Which devices does it run on?",
         "iOS and Android. It is a free download from the App Store and Google Play."),
    ],
}

FAQ_TITLE = {"tr": "Sık sorulanlar", "en": "Frequently asked questions"}

SAME_AS = [
    "https://www.youtube.com/@Deruniapp",
    "https://www.instagram.com/deruniapp/",
    "https://www.tiktok.com/@deruniapp",
    "https://open.spotify.com/artist/2QThTToZzGgTAy8RZBFgSx",
    "https://music.apple.com/us/artist/der%C3%BBn%C3%AE/6803085837",
    "https://apps.apple.com/app/deruni/id6759687639",
    "https://play.google.com/store/apps/details?id=com.mehmetcolak.deruni",
]


def build_faq(page: str) -> str:
    rows = []
    for i, (q, a) in enumerate(FAQ[page]):
        rows.append(
            f'      <details class="faq">\n'
            f'        <summary><h3>{html.escape(q)}</h3></summary>\n'
            f'        <p>{html.escape(a)}</p>\n'
            f'      </details>'
        )
    return ('    <h2 style="text-align:center;margin-bottom:36px">'
            + FAQ_TITLE[page] + '</h2>\n    <div class="faqs">\n'
            + "\n".join(rows) + '\n    </div>')


PLAY_ICON = ('<svg width="11" height="12" viewBox="0 0 11 12" aria-hidden="true">'
             '<path d="M1 1v10l9-5z" fill="currentColor"/></svg>')

TICK = ('<svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">'
        '<path d="M2 7.5l3.2 3.2L12 4" fill="none" stroke="currentColor" '
        'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')

FAMILIES = ["bismillah", "rahmet", "kalbim", "sifa", "yalatif", "anlar"]
FAM_LABEL = {
    "tr": {"bismillah": "AİLE 1 · BİSMİLLAH", "rahmet": "AİLE 2 · RAHMET",
           "kalbim": "AİLE 3 · KALBİM", "sifa": "AİLE 4 · ŞİFA",
           "yalatif": "AİLE 5 · YA LATÎF", "anlar": "AİLE 6 · ANLAR"},
    "en": {"bismillah": "FAMILY 1 · BISMILLAH", "rahmet": "FAMILY 2 · MERCY",
           "kalbim": "FAMILY 3 · MY HEART", "sifa": "FAMILY 4 · HEALING",
           "yalatif": "FAMILY 5 · YA LATIF", "anlar": "FAMILY 6 · ANLAR"},
}
LANG_LABEL = {
    "tr": {"tr": "Türkçe", "en": "English", "ar": "العربية"},
    "en": {"tr": "Turkish", "en": "English", "ar": "Arabic"},
}
CREDIT = {
    "tr": "Söz: Niyâzî-i Mısrî — günümüz Türkçesiyle. Bu eserin yalnız Türkçe kaydı vardır.",
    "en": "Words: Niyâzî-i Mısrî — in contemporary Turkish. This work exists in Turkish only.",
}
PLAY_WORD = {"tr": "çal", "en": "play"}


def load_manifest(offline: bool) -> dict:
    if not offline:
        try:
            with urllib.request.urlopen(MANIFEST_URL, timeout=20) as r:
                data = json.load(r)
            CACHE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            print("manifest: ağdan alındı ve önbelleğe yazıldı")
            return data
        except Exception as exc:  # bazı ortamlarda urllib TLS'e takılıyor; curl ile dene
            print(f"manifest urllib ile alınamadı ({exc}); curl deneniyor")
            try:
                raw = subprocess.run(["curl", "-4", "-fsS", MANIFEST_URL],
                                     capture_output=True, timeout=30, check=True).stdout
                data = json.loads(raw)
                CACHE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                print("manifest: curl ile alındı ve önbelleğe yazıldı")
                return data
            except Exception as exc2:
                print(f"manifest curl ile de alınamadı ({exc2}); önbellek deneniyor")
    if not CACHE.exists():
        sys.exit("HATA: manifest ne ağdan alınabildi ne de önbellekte var.")
    print("manifest: yerel önbellekten")
    return json.loads(CACHE.read_text(encoding="utf-8"))


def mmss(sec: int) -> str:
    return f"{sec // 60}:{sec % 60:02d}"


def spoken(sec: int, page: str) -> str:
    m, s = divmod(sec, 60)
    if page == "tr":
        return f"{m} dakika {s} saniye"
    unit_m = "minute" if m == 1 else "minutes"
    unit_s = "second" if s == 1 else "seconds"
    return f"{m} {unit_m} {s} {unit_s}"


def build_tracks(ilahi: dict, page: str) -> str:
    by_family: dict[str, dict[str, dict]] = {}
    for key, v in ilahi.items():
        slot = by_family.setdefault(v["group"], {})
        if v["lang"] in slot:
            sys.exit(f"HATA: aynı aile+dil ikilisi iki kez var: {v['group']}/{v['lang']} "
                     f"({slot[v['lang']]['key']} ve {key}). Biri sayfadan sessizce düşerdi.")
        slot[v["lang"]] = dict(v, key=key)

    # Manifeste yeni bir aile ya da dil eklenirse o kayıt sayfaya HİÇ girmez.
    # Sessiz kaybı önlemek için derlemeyi burada düşürüyoruz.
    bilinmeyen_aile = sorted(set(by_family) - set(FAMILIES))
    bilinmeyen_dil = sorted({v["lang"] for v in ilahi.values()} - {"tr", "en", "ar"})
    if bilinmeyen_aile or bilinmeyen_dil:
        sys.exit(f"HATA: manifestte tanımsız aile {bilinmeyen_aile} / dil {bilinmeyen_dil}. "
                 f"build.py içindeki FAMILIES ve LANG_LABEL listelerini güncelle, "
                 f"yoksa bu kayıtlar sayfada görünmez.")

    out = []
    for fam in FAMILIES:
        rows = by_family.get(fam)
        if not rows:
            continue
        out.append(f'    <div class="fam">\n      <p class="famh">{FAM_LABEL[page][fam]}</p>')
        for lang in ("tr", "en", "ar"):
            t = rows.get(lang)
            if not t:
                continue
            title = html.escape(t["title"])
            dur = mmss(t["duration"])
            mb = t["bytes"] / 1048576
            mb_txt = f"{mb:.1f}".replace(".", ",") if page == "tr" else f"{mb:.1f}"
            aria = f'{title}, {spoken(t["duration"], page)}, {PLAY_WORD[page]}'
            ar_cls = " ar" if lang == "ar" else ""
            ar_attr = ' lang="ar" dir="rtl"' if lang == "ar" else ""
            out.append(
                f'      <button class="trk" type="button" data-tlang="{lang}"'
                f' data-src="{t["url"]}" data-title="{title}"'
                f' aria-label="{aria}" aria-pressed="false">\n'
                f'        <span class="pb" aria-hidden="true">{PLAY_ICON}</span>\n'
                f'        <span class="meta"><span class="tt{ar_cls}"{ar_attr}>{title}</span>'
                f'<span class="tl">{LANG_LABEL[page][lang]}</span></span>\n'
                f'        <span class="rt"><span class="dur">{dur}</span>'
                f'<span class="mb">≈{mb_txt} MB</span></span>\n'
                f'        <span class="prog" aria-hidden="true"></span>\n'
                f'      </button>'
            )
        if fam == "anlar":
            out.append(f'      <p class="mi credit">{CREDIT[page]}</p>')
        out.append("    </div>")
    return "\n".join(out)


HEAD = {
    "tr": {
        "lang": "tr", "canon": "https://deruni.app/", "loc": "tr_TR", "alt": "en_US",
        "title": "Deruni — Kalbine Dönüş · Zikir, nefes ve Esmâ-ül Hüsnâ",
        "desc": ("Deruni; bir dakika nefes, bir Esma ve kısa bir tefekkür için sade bir alan. "
                 "Hesap yok, kayıt yok, giriş yok. iOS ve Android'de ücretsiz."),
        "ogt": "Deruni — Kalbine Dönüş",
        "ogd": ("Yirmi bir günün tamamı açıkta. Bir dakika nefesi burada deneyebilir, "
                "on altı ilahiyi indirmeden dinleyebilirsin. Hesapsız, ücretsiz."),
        "og_img": "https://deruni.app/assets/og-tr.png",
        "og_alt": "Deruni — Kalbine dön.",
    },
    "en": {
        "lang": "en", "canon": "https://deruni.app/en/", "loc": "en_US", "alt": "tr_TR",
        "title": "Deruni — Return to Your Heart · Zikr, breath, reflection",
        "desc": ("Deruni is a quiet space for one minute of breath, one Esma and a short "
                 "reflection. No account, no sign-up, no login. Free on iOS and Android."),
        "ogt": "Deruni — Return to Your Heart",
        "ogd": ("All twenty-one days in the open. Try the one-minute breath right here, "
                "listen to sixteen hymns without installing anything. No account, free."),
        "og_img": "https://deruni.app/assets/og-en.png",
        "og_alt": "Deruni — Return to your heart.",
    },
}


def head_html(page: str, css: str) -> str:
    h = HEAD[page]
    ld = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "MobileApplication",
                "@id": "https://deruni.app/#app",
                "name": "Deruni",
                "operatingSystem": "iOS, Android",
                "applicationCategory": "HealthApplication",
                "inLanguage": ["tr", "en"],
                "url": h["canon"],
                "image": h["og_img"],
                "description": h["desc"],
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                "publisher": {"@id": "https://deruni.app/#org"},
                "downloadUrl": [IOS[page], AND[page]],
            },
            {
                "@type": "Organization",
                "@id": "https://deruni.app/#org",
                "name": "Deruni",
                "alternateName": "Derûnî",
                "url": "https://deruni.app/",
                "logo": "https://deruni.app/assets/apple-touch-icon.png",
                "email": "iletisimderuni@gmail.com",
                "sameAs": SAME_AS,
            },
            {
                "@type": "WebSite",
                "@id": h["canon"] + "#website",
                "url": h["canon"],
                "name": "Deruni",
                "inLanguage": h["lang"],
                "publisher": {"@id": "https://deruni.app/#org"},
            },
            {
                "@type": "FAQPage",
                "@id": h["canon"] + "#faq",
                "inLanguage": h["lang"],
                "mainEntity": [
                    {"@type": "Question", "name": q,
                     "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in FAQ[page]
                ],
            },
        ],
    }, ensure_ascii=False, separators=(",", ":"))
    return f"""<!DOCTYPE html>
<html lang="{h['lang']}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(h['title'])}</title>
<meta name="description" content="{html.escape(h['desc'])}">
<link rel="canonical" href="{h['canon']}">
<link rel="alternate" hreflang="tr" href="https://deruni.app/">
<link rel="alternate" hreflang="en" href="https://deruni.app/en/">
<link rel="alternate" hreflang="x-default" href="https://deruni.app/">
<meta property="og:site_name" content="Deruni">
<meta property="og:type" content="website">
<meta property="og:url" content="{h['canon']}">
<meta property="og:title" content="{html.escape(h['ogt'])}">
<meta property="og:description" content="{html.escape(h['ogd'])}">
<meta property="og:image" content="{h['og_img']}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{html.escape(h['og_alt'])}">
<meta property="og:locale" content="{h['loc']}">
<meta property="og:locale:alternate" content="{h['alt']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(h['ogt'])}">
<meta name="twitter:description" content="{html.escape(h['ogd'])}">
<meta name="twitter:image" content="{h['og_img']}">
<meta name="twitter:image:alt" content="{html.escape(h['og_alt'])}">
<meta name="theme-color" content="#0B1E39">
<meta name="color-scheme" content="dark">
<link rel="icon" type="image/png" sizes="96x96" href="/assets/favicon-96.png">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<script>document.documentElement.className+=" js";</script>
<style>
{css}
</style>
<script type="application/ld+json">{ld}</script>
</head>
<body>
"""


def main() -> None:
    offline = "--offline" in sys.argv
    manifest = load_manifest(offline)
    ilahi = manifest["ilahi"]
    total = sum(v["duration"] for v in ilahi.values())
    print(f"ilahi: {len(ilahi)} kayıt · toplam {mmss(total)}")
    if len(ilahi) != 16 or total != 3317:
        print("UYARI: manifest sayfadaki 'on altı ilahi / 55 dakika 17 saniye' "
              "cümlesiyle artık uyuşmuyor — metni güncelle.")

    css = (ROOT / "_style.css").read_text(encoding="utf-8").strip()
    js = (ROOT / "_app.js").read_text(encoding="utf-8").strip()

    for page, target in (("tr", ROOT / "index.html"), ("en", ROOT / "en" / "index.html")):
        body = (ROOT / f"_body.{page}.html").read_text(encoding="utf-8")
        body = (body.replace("__IOS__", IOS[page])
                    .replace("__AND__", AND[page])
                    .replace("__AM__", AM[page])
                    .replace("__FAQ__", build_faq(page))
                    .replace("__TICK__", TICK)
                    .replace("__TRACKS__", build_tracks(ilahi, page)))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(head_html(page, css) + body + f"\n<script>\n{js}\n</script>\n</body>\n</html>\n",
                          encoding="utf-8")
        print(f"{target.relative_to(ROOT)}: {target.stat().st_size:,} bayt")


if __name__ == "__main__":
    main()
