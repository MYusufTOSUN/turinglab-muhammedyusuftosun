# TuringLab — Öğrenci El Kitabı

**Öğrenci:** Muhammed Yusuf Tosun
**Ders:** Hesaplama Kuramı · Bilgisayar Mühendisliği
**Üniversite:** Selçuk Üniversitesi
**Hazırlayan:** Dr. Ali Çetinkaya
**Değerlendiren:** Ahmet Erharman

---

## Demo Videosu

Çalışan TM motoru + Bölüm 2'de tasarladığım makinelerin demo kaydı (Türkçe anlatım, ~6 dk):

🎥 https://www.youtube.com/watch?v=BqMO2R-nZyQ

---

## Hızlı Başlangıç

### Kurulum

```bash
pip install -r requirements.txt
```

Tek bağımlılık vardır: YAML çözümleyici için `PyYAML`, test çalıştırıcı için `pytest`.
Python 3.10+ gereklidir.

### Kullanım Örneği

```python
from turinglab import SingleTapeTM

# YAML'dan bir TM yükle
tm = SingleTapeTM.from_yaml("machines/binary_increment.yaml")

# Çalıştır
result = tm.run("1011", max_steps=1000)

assert result.accepted is True
assert result.reason == "accept"
assert result.final_tape.strip("B") == "1100"
assert len(result.history) == result.steps + 1

# Tek bir adımı incelemek
config = result.history[5]
print(config.step, config.state, config.tape, config.head_position)
```

`verbose=True` modunda her adım stdout'a şu biçimde basılır
(durduğunda son satır `(durdu: <reason>)` ile biter):

```
Adım 0 | Durum: q_scan | Şerit: [1]1 | Hareket: R
Adım 1 | Durum: q_scan | Şerit: 1[1] | Hareket: R
Adım 2 | Durum: q_scan | Şerit: 11[B] | Hareket: R
Adım 3 | Durum: q_write | Şerit: 111[B] | Hareket: L
Adım 4 | Durum: q_accept | Şerit: 11[1]B | (durdu: accept)
```

### Testler

Tüm pytest test paketi proje kökünden çalıştırılır:

```bash
pytest tests/ -v
```

`tests/test_tm_engine.py` motorun tüm yüzeyini kapsayan 16 test
fonksiyonu (parametrize ile 28 test örneği) içerir: üç farklı TM × beşer
girdi, history semantiği, durma koşulları (`accept` / `no_transition` /
`timeout`), verbose çıktı biçimi, hatalı YAML çeşitleri ve `Tape`
sınıfının iki yönlü genişleme davranışı.

### Tasarım Kararı: Sola Taşma

Şerit **iki yönlü sınırsız** genişler. Kafa konumu negatif
(`head_position < 0`) olabilir; bu durumda yazılmamış hücreler `blank`
olarak okunur ve hata fırlatılmaz. Sebebi şudur: simetrik algoritmalar
(dizgi kopyalama, karşılaştırma vb.) ek özel durum mantığı gerekmeden
yazılabilir; sola taşma yapay bir hata değil, doğal bir hesaplama
adımıdır.

Bunu düşük maliyetle desteklemek için şerit `dict[int, str]` (sparse)
yapısıyla temsil edilir. Hiç yazılmamış hücreler hiç bellekte yer
kaplamaz; okuma sırasında otomatik olarak `blank` döner.

Diğer üç durma koşulu el kitabındaki şartnameye birebir uyar:

| Durum | `accepted` | `reason` |
|---|---|---|
| Aktif durum `accept_states` içinde | `True` | `"accept"` |
| `δ(state, read)` tanımsız | `False` | `"no_transition"` |
| `max_steps` aşıldı | `False` | `"timeout"` |

---

## Proje Künyesi

| | |
|---|---|
| **Başlangıç** | 4 Mayıs 2026 Pazartesi |
| **Son Teslim** | 22 Mayıs 2026 Cuma · 23:59 |
| **Süre** | 18 gün (~2.5 hafta) |
| **Çalışma Şekli** | Bireysel · GitHub üzerinden teslim |
| **Tahmini İş Yükü** | 25–30 saat (günlük ~1.5–2 saat) |

---

## TuringLab Nedir?

4–22 Mayıs 2026 arasında, Turing makinelerini araştıran, tasarlayan ve çalıştırılabilir hale getiren tek bir Python projesi geliştirilecek: **TuringLab**. Ödev üç zorunlu bölümden ve bonus bölümünden oluşur.

### Ödev Sonunda Elde Edilecekler

- Tek-şeritli Turing makinelerini çalıştıran bir Python motoru
- 4 farklı problem için tasarlanmış Turing makineleri
- Çalışmayı gösteren 5–8 dakikalık ekran kaydı videosu
- Tasarım kararlarının savunulduğu kısa bir mini-rapor
- (Opsiyonel) çok-şeritli, NTM, görselleştirici gibi bonus özellikler

### Ödev Yapısı

| Bölüm | Tarih | Konu | Puan | Anahtar |
|---|---|---|---|---|
| Bölüm 1 | 4–10 Mayıs | TM Motoru | 50 | Biçimsel tanım → çalışan kod |
| Bölüm 2 | 11–17 Mayıs | 4 TM Tasarımı | 35 | Algoritma → δ kuralları |
| Bölüm 3 | 18–22 Mayıs | Demo Video + Mini-Rapor | 15 | Çalışmayı sunma |
| Bonus | Esnek | MTM, NTM, görselleştirici, vb. | +20 | İsteğe bağlı |

**TOPLAM:** 100 puan zorunlu · +20 bonus · Maksimum 120 puan üzerinden değerlendirme.

---

## GitHub Kuralları

Tüm proje teslimleri GitHub üzerinden yapılır. Bu sadece bir teslim aracı değil, profesyonel yazılım geliştirme alışkanlığı edinmenizi sağlayan bir disiplindir.

### 1. Repo Kurulumu

- GitHub'da **private** bir repo: `turinglab-{ad}{soyad}`
- Ahmet Erharman Hoca'ya okuma izni (collaborator olarak)
- İlk commit: el kitabı `README.md` olarak repoya, başına öğrenci adı
- Repo URL'si ders yönetim sistemine

### 2. Commit Disiplini

- **Düzenli commit:** 18 gün boyunca en az **10–15 anlamlı commit**. Toplu son-gün commit'leri puan kaybettirir.
- **Anlamlı mesajlar:** "fix" ✗ → "δ fonksiyonunda blank sembol bug'ı çözüldü" ✓
- **Tek teslim noktası:** 22 Mayıs 2026 Cuma 23:59. Bu tarihte `final` adlı tag/release oluşturulur.
- **Son teslim sonrası:** Repo'da değişiklik yok.

### 3. Hedef Repo Yapısı

```
turinglab/
├── README.md              # Proje tanıtımı, kullanım, demo video linki
├── REPORT.md              # Mini-rapor (Bölüm 3)
├── requirements.txt       # Python bağımlılıkları
├── .gitignore             # __pycache__, venv, vs.
├── turinglab/             # Ana paket
│   ├── __init__.py
│   ├── tm_engine.py       # Bölüm 1: TM motoru
│   ├── multi_tape.py      # (Bonus A) çok-şeritli motor
│   ├── ntm.py             # (Bonus B) non-deterministic motor
│   └── visualizer.py      # (Bonus D) görselleştirme
├── machines/              # Bölüm 2: Tasarlanmış TM'ler
│   ├── unary_to_binary.yaml
│   ├── binary_compare.yaml
│   ├── string_copy.yaml
│   └── student_choice.yaml
├── tests/                 # pytest test dosyaları
│   ├── test_tm_engine.py
│   └── test_machines.py
└── docs/
    ├── design_notes.md    # Tasarım kararları
    ├── demo_video.mp4     # Ekran kaydı VEYA README'de YouTube linki
    └── images/            # (Bonus D) görselleştirme çıktıları
```

---

## Genel Beklentiler

### Teknik Standartlar

- **Dil:** Python 3.10+ (zorunlu)
- **Kod stili:** PEP 8 (bonus: mypy ve ruff)
- **Test:** pytest
- **Bağımlılıklar:** Sadece izin verilenler
- **Dokümantasyon:** Her public fonksiyona docstring (Google veya NumPy stili)

### Akademik Standartlar

- **Tek başına çalışma:** Kod paylaşımı yasak. Tartışma serbest, kopya değil.
- **Kopya tespiti:** MOSS + commit history incelemesi.
- **Geç teslim:** Her gün −10 puan (max 3 gün, sonra sıfır).
- **Sözlü savunma:** Şüpheli durumlarda viva.

---

## Bölüm 1 · TM Motoru (50 puan · 4–10 Mayıs)

**Hedef:** Deterministic single-tape Turing makinelerini çalıştıran bir Python kütüphanesi. Tek dosya `tm_engine.py`, iki ana sınıf: `TuringMachine` ve `Tape`.

### Girdi Formatı (YAML)

```yaml
name: "binary_increment"
description: "Binary sayıyı bir artırır. Örnek: 1011 -> 1100"
states: [q0, q_back, q_carry, q_done, q_accept]
input_alphabet: ["0", "1"]
tape_alphabet: ["0", "1", "B"]
blank: "B"
start_state: q0
accept_states: [q_accept]
reject_states: []
transitions:
  - {state: q0, read: "0", next: q0, write: "0", move: R}
  - {state: q0, read: "1", next: q0, write: "1", move: R}
  - {state: q0, read: "B", next: q_back, write: "B", move: L}
  - {state: q_back, read: "0", next: q_done, write: "1", move: L}
  - {state: q_back, read: "1", next: q_back, write: "0", move: L}
  - {state: q_back, read: "B", next: q_done, write: "1", move: L}
  - {state: q_done, read: "0", next: q_done, write: "0", move: L}
  - {state: q_done, read: "1", next: q_done, write: "1", move: L}
  - {state: q_done, read: "B", next: q_accept, write: "B", move: R}
```

### Python API (Zorunlu)

```python
from turinglab import SingleTapeTM, RunResult

tm = SingleTapeTM.from_yaml("machines/binary_increment.yaml")
result: RunResult = tm.run(
    input_string="1011",
    max_steps=1000,
    verbose=False,
)
assert result.accepted is True
assert result.final_tape.strip("B") == "1100"
assert result.steps == 23
assert len(result.history) == 24

config = result.history[5]
print(config.state, config.tape, config.head_position)
```

### Zorunlu Durum Yönetimi

| Durum | Beklenen Davranış |
|---|---|
| Geçerli δ kuralı yok | `accepted=False, reason="no_transition"` |
| `accept_states`'e ulaşıldı | `accepted=True, reason="accept"` |
| `max_steps` aşıldı | `accepted=False, reason="timeout"` |
| Kafa sola taştı (head < 0) | Tasarımcıya ait — README'de belirtilmeli |
| Hatalı YAML | `ValueError` + anlamlı mesaj |

### Verbose Mod Çıktı Formatı

```
Adım 0 | Durum: q0     | Şerit: [1]011B | Hareket: R
Adım 1 | Durum: q0     | Şerit: 1[0]11B | Hareket: R
Adım 2 | Durum: q0     | Şerit: 10[1]1B | Hareket: R
Adım 3 | Durum: q0     | Şerit: 101[1]B | Hareket: R
Adım 4 | Durum: q0     | Şerit: 1011[B] | Hareket: L
Adım 5 | Durum: q_back | Şerit: 101[1]0 | Hareket: L
...
```

### Test Kapsamı (Zorunlu)

- `tests/test_tm_engine.py` içinde en az **8 test fonksiyonu**
- 3 farklı TM'in 5'er girdi için doğru çalışması
- Timeout durumu testi
- Hatalı YAML için `ValueError` testi
- `verbose=True` modu çıktı yakalama testi

### İzinli Bağımlılıklar (Bölüm 1)

Sadece **PyYAML** ve **pytest**. Standart kütüphane (typing, dataclasses, vs.) serbest.

### Rubrik — Bölüm 1 (50 puan)

| Kriter | Puan |
|---|---|
| YAML parser doğru çalışıyor, hatalı YAML için anlamlı hata | 8 |
| `run()` 3 örnek TM için doğru sonuç | 12 |
| `result.history` her adımı doğru kaydediyor | 6 |
| Timeout, no_transition gibi kenar durumları | 6 |
| `verbose` çıktısı şartnameye uygun ve okunabilir | 6 |
| Test dosyası 8+ test içeriyor ve hepsi geçiyor | 6 |
| Kod kalitesi: docstring, anlamlı isim, modülerlik | 4 |
| README'de kullanım örneği var, çalışıyor | 2 |

### Sıkça Yapılan Hatalar

- ⚠ **Şeridi `str` olarak tutmak:** Python'da string immutable. `list[str]` veya `dict[int, str]` (sparse) kullan.
- ⚠ **Negatif index:** `tape[-1]` Python'da listenin sonu, sola taşma değil! `head_position < 0` açıkça kontrol et.
- ⚠ **Sadece "çalışan" durumları test etmek:** Ret durumlarını da test et.
- ⚠ **Blank sembol olarak boşluk:** `blank: " "` debug imkansız hale getirir. `B` veya `_` kullan.
- ⚠ **Düzensiz commit alışkanlığı:** Her gün küçük commit yap.

---

## Bölüm 2 · Tasarım Atölyesi (35 puan · 11–17 Mayıs)

**Hedef:** Kendi yazılan motoru (M1) kullanarak 4 farklı problemin TM çözümünü tasarlamak. Her çözüm: bir YAML dosyası + onu test eden Python test fonksiyonu.

### Zorunlu Makineler (3 adet)

**TM-1 · Unary → Binary Çevirici**
- Girdi: `111` (3 sayısının unary gösterimi)
- Çıktı (şerit sonu): `11` (3 sayısının ikili gösterimi)
- Şerit alfabesi: {1, 0, B, X}

**TM-2 · İki İkili Sayıyı Karşılaştıran TM**
- Girdi: `1011#1100` (ayraç `#` ile)
- Kabul: birinci sayı ikincisinden büyükse
- Ret: değilse

**TM-3 · Dizgi Kopyalayıcı**
- Girdi: `abba`
- Çıktı: `abba#abba`
- Şerit alfabesi: {a, b, B, #, A, B'}

### Öğrenci Seçimi (1 adet)

TM-4'te aşağıdakilerden biri (veya `design_notes.md` üzerinden onaylı kendi öneri):
- (a) 4'e bölünebilirlik testi (binary girdi)
- (b) İki dizginin anagram olup olmadığı testi
- (c) Basit parantez denge kontrolü
- (d) ROT-1 benzeri basit şifreleme

### Beklenen Çıktılar

```
machines/
├── unary_to_binary.yaml
├── binary_compare.yaml
├── string_copy.yaml
└── student_choice.yaml
docs/
└── design_notes.md       # Her TM için 1-2 paragraf
tests/
└── test_machines.py      # her TM için 5+ girdi-beklenen çıktı testi
```

### `design_notes.md` İçeriği

Her TM için 5 soru (~150–200 kelime):
1. **Strateji:** Yüksek seviyeli algoritma (doğal dilde)
2. **Durum sayısı:** Kaç durum, neden, daha az mümkün müydü?
3. **Şerit alfabesi seçimi:** Yardımcı semboller neden?
4. **Karmaşıklık:** Big-O analizi
5. **Hata ayıklama hikayesi:** En zor bug, nasıl çözüldü?

### Test Kapsamı

Her TM için en az 5 test girdisi:
- 2 kabul edilmesi gereken
- 2 reddedilmesi gereken
- 1 kenar durum

### Rubrik — Bölüm 2 (35 puan)

| Kriter | Puan |
|---|---|
| TM-1 çalışıyor, tüm testler geçiyor | 6 |
| TM-2 çalışıyor, tüm testler geçiyor | 6 |
| TM-3 çalışıyor, tüm testler geçiyor | 7 |
| TM-4 (öğrenci seçimi) çalışıyor | 7 |
| `design_notes.md` her TM için yeterince derin | 5 |
| Test kalitesi (kenar durumlar dahil) | 3 |
| Commit disiplini | 1 |

---

## Bölüm 3 · Demo Video + Mini-Rapor (15 puan · 18–22 Mayıs)

### Demo Video

| Spesifikasyon | Gereksinim |
|---|---|
| Süre | 5–8 dakika (hedef: 6) |
| Format | MP4 (H.264) |
| Çözünürlük | Min 1280×720 (HD) |
| Ses | Anlaşılır mikrofon kaydı |
| Dil | Türkçe |
| Boyut | Maks 200 MB veya YouTube unlisted |

### İçerik Şablonu

1. **Açılış (45 sn):** Ad, proje adı, video özeti
2. **Canlı Demo (2–3 dk):** YAML aç, simülatörü verbose modda çalıştır, 4 TM'den 2'sini göster
3. **En Sevdiğin Tasarım Kararı (1–2 dk):** En zor kısım, çözüm, alternatif
4. **Bonus + Kapanış (1 dk):** Bonus varsa göster, ne öğrendin

### Mini-Rapor (`REPORT.md`)

3–5 sayfa Markdown:
1. **Giriş (~½ sayfa):** TuringLab nedir
2. **Mimari (~1 sayfa):** Modül organizasyonu, tasarım kararları
3. **Tasarlanan TM'ler (~1 sayfa):** 4 makinenin özeti
4. **Kavramsal Tartışma (~1 sayfa, ~250 kelime):** Aşağıdakilerden biri:
   - (a) Halting problemini TuringLab içinde "çözmek" mümkün mü?
   - (b) UTM için TuringLab nasıl genişletilebilir?
   - (c) Python ile TM arasındaki "boşluk" nedir?
5. **Sınırlar ve İleri Çalışma (~½ sayfa)**
6. **Kaynakça**

### Rubrik — Bölüm 3 (15 puan)

| Kriter | Puan |
|---|---|
| Demo videosu spesifikasyona uygun | 3 |
| Demo: canlı çalışan TM'ler | 3 |
| Demo: tasarım kararları açıklanmış | 2 |
| Mini-rapor: mimari ve tasarım | 3 |
| Mini-rapor: tasarlanan TM'ler | 2 |
| Mini-rapor: kavramsal tartışma | 2 |

---

## Bonus (+20 puan · İsteğe Bağlı)

### Bonus A — Çok-Şeritli TM (+8)

`turinglab/multi_tape.py` içinde `MultiTapeTM`. YAML'da `num_tapes: k`. read/write/move alanları k uzunluğunda liste.
- En az 1 adet 3-şeritli TM (örn. ikili toplama)
- 5+ test girdisi
- `tests/test_multi_tape.py`

### Bonus B — Non-Deterministic TM (+8)

`turinglab/ntm.py` içinde `NondeterministicTM`. δ artık choices listesi döner. **BFS** ile.
- En az 1 NTM (örn. "01 alt-dizgisi var mı?")
- `max_depth` ve `max_branches` zorunlu
- `accepting_paths` alanı

### Bonus C — Karşılaştırmalı Analiz (+4)

A veya B yapılmış olmalı. Aynı dili farklı varyantlarda çözüp adım sayılarını karşılaştır. matplotlib grafiği `docs/comparison.png`. Mini-rapora paragraf.

### Bonus D — Görselleştirici (+5)

`turinglab/visualizer.py`. Her adımın PNG görselleştirmesi (Pillow/imageio). En az 5 PNG `docs/images/` altında. **Bonus üstü bonus:** GIF de üretilirse +1.

---

## Çalışma Takvimi

| Hafta | Tarih | Ana Konu | Yapılacaklar |
|---|---|---|---|
| Hafta 1 | 4–10 Mayıs | Bölüm 1 — TM Motoru | YAML parser, `run()`, history, testler |
| Hafta 2 | 11–17 Mayıs | Bölüm 2 — 4 TM | 3 zorunlu + 1 seçim TM, YAML+test+notlar |
| Son Hafta | 18–22 Mayıs | Bölüm 3 + Bonus + Teslim | Demo, REPORT.md, README cila |

### Bağımlılıklar

```
Bölüm 1 (motor) ──→ Bölüm 2 (TM tasarımları) ──→ Bölüm 3 (demo + rapor)
                │
                └──→ Bonus (paralel — istediğin zaman)
```

### Geç Teslim

- İlk 24 saat: −10 puan
- İkinci 24 saat: −20 puan
- Üçüncü 24 saat: −30 puan
- Sonra: 0 puan

---

## Sıkça Sorulan Sorular

**Python yerine başka bir dil?** Hayır. Python 3.10+ zorunlu.

**GitHub'da hazır TM motoru kullanabilir miyim?** Hayır. MOSS ile tespit edilir.

**Bonus zorunlu mu?** Hayır. 100/100 sadece zorunlu bölümlerle alınabilir.

**Bonus'lar arası en kolay?** Genellikle Bonus A (multi-tape).

**Demo videoda yüzüm gerekli mi?** Hayır, sadece ekran kaydı + ses yeterli.

**Stack Overflow / dokümantasyon kullanımı?** Evet, kavramı öğrenmek için. Tam çözüm kopyalamak yasak.

**22 Mayıs sonrası repo değişikliği?** Hayır.

---

## Son Söz

> "We can only see a short distance ahead, but we can see plenty there that needs to be done."
> — Alan M. Turing, 1950
