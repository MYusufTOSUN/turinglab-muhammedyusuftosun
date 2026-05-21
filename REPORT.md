# TuringLab — Mini Rapor

Hesaplama Kuramı dersi final ödevi · Muhammed Yusuf Tosun · Selçuk Üniversitesi · Mayıs 2026

---

## 1. Giriş

TuringLab, tek-şeritli deterministic Turing makinelerini YAML üzerinden tanımlayıp Python'da çalıştıran küçük bir kütüphane. El kitabında istenen API'yi (`from turinglab import SingleTapeTM, RunResult`) sağlayan bir motor ile birlikte, Bölüm 2 kapsamında dört farklı problemi çözen TM tasarımları içeriyor: unary→binary çevirici, iki ikili sayıyı karşılaştıran makine, dizgi kopyalayıcı ve parantez denge denetimi.

Proje 4 Mayıs'ta okuduğum el kitabıyla başladı. İlk hafta motoru yazdım, ikinci hafta dört makineyi tasarlayıp test ettim, üçüncü hafta bu rapor ve demo videosuyla bitiriyorum. Toplam motor + test paketi yaklaşık 800 satır Python, dört makinenin YAML tanımları ~250 satır, tasarım notları ~300 satır. Bütün test paketi (68 örnek) yarım saniyenin altında geçiyor.

## 2. Mimari

### Paket organizasyonu

El kitabı motoru "tek dosya `tm_engine.py`" diye istediği için tüm motor mantığı `turinglab/tm_engine.py` içinde. `turinglab/__init__.py` sadece re-export yapıyor. Bu disiplin işime yaradı: ayrı modüllere ayırma cazibesine kapılmadan algoritmik öze odaklandım.

```
turinglab/
├── tm_engine.py        # motor (~280 satır)
└── __init__.py
machines/               # bölüm 2'nin 4 YAML'ı + binary_increment (spec örneği)
tests/
├── test_tm_engine.py   # motor için 16 test fonksiyonu / 28 örnek
├── test_machines.py    # 4 TM için 14 fonksiyon / 40 örnek
└── fixtures/           # bölüm 1 smoke YAML'ları
docs/design_notes.md    # her TM için 5 soruluk tasarım notları
```

### Veri sınıfları

`Move` enum sadece L ve R (spec STAY istemiyor, eklemedim). `Transition` frozen dataclass — tek bir δ kuralı. `Configuration` çalışmadaki bir anlık görüntü: adım numarası, durum, şerit, kafa konumu. `RunResult` çıkış paketi: `accepted`, `reason` ("accept" / "no_transition" / "timeout"), `steps`, `final_tape`, ve adım adım `history` listesi.

### Şerit temsili — en önemli karar

El kitabı `list[str]` veya `dict[int, str]` (sparse) öneriyordu. Sparse dict seçtim çünkü:

- Negatif konumlar (kafa sola taşarsa) doğal olarak destekleniyor. `tape[-1]` Python'da listenin sonu olur, bizim istediğimiz sola taşma değil. Sparse dict'te `_cells.get(-1, blank)` doğal olarak blank dönüyor.
- Bellek yalnızca yazılmış hücreler için tüketiliyor. TM-3 (dizgi kopyalama) için n=20 girdi 40+ hücre yazıyor ama hepsi mantıklı içerikle — boş yer ayrılmıyor.
- Read/write O(1).

Bu seçimi README'de açıkça belirttim çünkü el kitabı sola taşma davranışını "kararı size ait" diye bırakmıştı. Benim kararım: şerit iki yönlü sınırsız genişler, sola taşma hata değil — doğal bir hesaplama adımı. Bonus olarak bu seçim TM-1'in implementasyonunu da basitleştirdi (q_rewind sola B görene kadar gidiyor, negatif konumda B olması işin doğal parçası).

### `run()` döngüsü

Akış kısaca:
1. Girdideki her sembol `input_alphabet`'te mi kontrol et, değilse `ValueError`.
2. Tape kur, state = start, head = 0.
3. History'ye başlangıç konfigürasyonunu ekle (bu yüzden `len(history) == steps + 1`).
4. Start state zaten accept ise hemen kabul, 0 adımda dur.
5. En fazla `max_steps` döngü: read → δ lookup → (yoksa no_transition, dur) → verbose emit → write → move → state geçişi → history.append → accept kontrolü.
6. Döngü sonu: timeout.

### Verbose mod

El kitabındaki çıktı biçimini birebir karşılıyor: `Adım N | Durum: state | Şerit: ab[c]de | Hareket: M`. Halt'ta son satır `... | (durdu: <reason>)` şeklinde biter. Şeridin sağ ucunda fazladan bir blank gösteriyorum (`[1]011B` gibi) — spec örneğindeki gibi. Bu detayı baştan atlamıştım, sonra spec'i tekrar okuyunca farkedip düzelttim: `Tape.render`'da `max_pos+1` yaptım, `Tape.write`'da blank yazımlarını sözlükten çıkardım (görsel temizlik için, bunlar zaten read'de blank dönüyor).

## 3. Tasarlanan TM'ler

### TM-1 · Unary → Binary

Girdi `111`, çıkış (şerit sonu) `11`. **8 durum.** Algoritma: girdi sonuna `X` sınırı koy ve hemen sağına `0` yaz. Her iterasyonda en sağdaki unary 1'i tüket (X yap), ikili sayacın sağ ucuna git, taşımayla artır, başa dön. Taşma anında carry sınır X'in üstüne taşar ve ikili sayı bir hane uzar — `X` zaten "sınır + kullanılmış unary" anlamı taşıyor, ek bir sembole gerek olmadı. n=5 için 106 adım, n=7 için 174 adım — kabaca O(n²).

### TM-2 · İkili Karşılaştırma

Girdi `1011#1100`, çıkış ret (11 < 12). **16 durum** — en şişmiş TM. Sebep: 3 mod (eq / gt / lt) × her birinde sol-tara + sağ-tara-pre-# + sağ-tara-post-# + rewind. "Pre-hash" ve "post-hash" ayrımı kaçınılmaz oldu çünkü TM kafa bir `0` veya `1` okuduğunda "bu 1. sayıya mı 2. sayıya mı ait?" sorusunu pozisyondan değil sadece state'ten çıkarabiliyor.

Algoritma MSB-first çiftleme: ilk fark gördüğüm pozisyonda verdict'i state'te (eq/gt/lt) saklıyorum. Sonunda uzunluk farkı verdict'i ezebilir — öncüsüz binary varsayımıyla uzun olan her zaman büyük. Mesela `11011#1110` (27 > 14): pair 2'de 0<1 görüyorum, lt mod'a geçiyorum, ama sonra 1. uzun çıkınca kabul ediyorum.

Bu TM'i tek şeritte tasarlamak beni en çok zorlayan iş oldu. Çok şeritli olsaydı (Bonus A) her sayıyı kendi şeridinde tutup 6-7 durumla aynı işi yapabilirdim. El kitabının "TM-2 tek şeritte ileri-geri tarama gerektirir, MTM motivasyonu oluşturur" notu yerinde — gerçekten öyle hissettim.

### TM-3 · Dizgi Kopyalayıcı

Girdi `abba`, çıkış `abba#abba`. **6 durum.** Klasik mark-and-copy: önce girdinin sonuna `#` ekle, sonra her harf için en soldaki işaretsizi `A` (a için) veya `D` (b için) ile işaretle ve sağ ucun ilk B'sine orijinal harfi yaz. Şerit sonu `AADA#abba` gibi görünür; test tarafı A→a, D→b replace yapıyor (TM içinde unmark fazı eklemek 4-5 ekstra state isteyecekti, basit ve doğru olan bu).

Spec metni "büyük A, B' işaretleyici" diye öneriyordu ama `B'` iki karakter (apostroflu) ve motor tek karakter bekliyor; bu yüzden `D` seçtim.

### TM-4 · Parantez Denge (öğrenci seçimi)

El kitabındaki dört seçenekten (c)'yi seçtim. Sebep: diğer üç TM transducer (girdiyi dönüştürüyor); bu decider, çeşitlilik için iyi. Aynı zamanda yığın mantığını tek şeritte göstermek hesaplama kuramı dersi için temsili bir alıştırma. **5 durum** (en kompakt makine).

Algoritma: q_scan_right ilk `)`'yi bul ve işaretle, q_match_left sola dönüp en yakın işaretsiz `(`'yi bul (yığın tepesi mantığı) ve işaretle. Eşleşmesiz `)` (sola B'ye çarparsam) → reddet. Sonda q_check_remaining sağdan sola tarayıp sadece X bekliyor; `(` kalmışsa unmatched → reddet.

### En zorlandığım bug

TM-2'nin başlangıçta 13 testten 5'i fail ediyordu — hepsi "kabul beklenirken ret". Verbose'ı açıp 2-3 trace inceleyince fark ettim: `seek_2nd_post` Y yazdıktan sonra R hareketi yapıyordu, sonra rewind sağ uçtaki B'yi okuyup yanlış yöne (sağa) dönüyordu. Düzeltme tek satırdı (R yerine L) ama bulması saatler aldı. Bu deneyim "verbose mod sadece spec gereği yazılmış bir şey değil, asıl debug aracı" dediğim noktaydı.

## 4. Kavramsal Tartışma — Halting Problemini TuringLab içinde "çözmek" mümkün mü?

Kısa cevap: hayır. Sebep oldukça öğretici.

TuringLab `run()` metoduna `max_steps` parametresi koyduk. Aşıldığında `reason="timeout"` dönüyor. Bu yüzeyde "şu kadar adımda bitmedi, demek ki bitmez" gibi bir yarı-cevap veriyor gibi görünebilir. Ama bu **karar değil, vazgeçiş**.

Asıl halting problemi şu soruyu soruyor: girdi olarak bir TM'in tanımı (örn. bizim bir YAML) ve bir girdi *w* verildiğinde, bu TM'in *w* üzerinde sonlu adımda durup durmayacağına evet/hayır cevap veren başka bir TM yazılabilir mi? Turing 1936'da kanıtladı: hayır. Klasik diagonal argüman — böyle bir H makinesi olsaydı, H'yi kullanarak çelişkili bir D makinesi (kendisi üzerinde H'nin tersini yapan) inşa edilebilirdi.

TuringLab'ın `max_steps` mekanizması bu probleme çözüm değil çünkü:

1. `max_steps=1000` ile timeout dönerse, makinenin 1001. adımda kabul edip etmeyeceğini bilmiyoruz. Verdiğimiz cevap "bilmiyorum, vazgeçtim".
2. `max_steps=∞` ile çalıştırırsak, durmayan bir makinede sonsuza kadar bekleriz — Python süreci durmaz.
3. "YAML'a bakarak duracak mı?" diye statik analiz yapmak da çözüm olmaz; bu halting'in başka bir formülasyonu, ondan da kaçış yok.

Pratik bir gözlem: bir programcı olarak halting problemine sürekli çarpıyoruz. IDE'nin "kodu çalıştırırsam dönecek mi" sorusuna cevap veremiyor olması, infinite loop tespit araçlarının her durumda çalışmaması, statik analizörlerin "kesinlikle sonlanır" garantisi verememesi — hepsi Turing'in 1936'daki sonucunun günlük yansımaları. TuringLab'da `max_steps` parametresi koymak zorunda olmamız da bunun küçük bir provası: hesaplamayı kaldırabileceğimiz ne kadar uzağa kadar götüreceğimizi seçiyoruz, ama gerçek bir karar veremiyoruz.

Bu rapor için bana en çarpıcı gelen taraf şu: halting problemi bir mühendislik kısıtı değil, matematiksel bir gerçek. Daha hızlı bilgisayar, daha akıllı algoritma — hiçbiri yardım etmiyor. Hesaplanabilir olanı simüle edebiliyoruz, hesaplanamaz olan için verebileceğimiz en iyi şey zaman aşımı. Bu hem alçaltıcı hem aydınlatıcı.

## 5. Sınırlar ve İleri Çalışma

Birkaç açık nokta var:

**Bonus'lar yapılmadı.** Vaktimin çoğunu Bölüm 1+2'nin sağlamlığına ayırdım — özellikle motorun spec uyumuna ve testlerin kapsamına. En çok yapmak istediğim Bonus A (çok-şeritli TM); TM-2'nin 16 durumunu muhtemelen 6-7'ye indirebilirdi, ve doğrudan "tek şerit zorluğunu" sayısal olarak ortaya koyabilirdi.

**TM-2'nin durum sayısı yüksek.** Pre-hash / post-hash ayrımı yüzünden bu kaçınılmaz oldu, ama Bonus A ile bu sorun ortadan kalkardı. Şu an `binary_compare.yaml` neredeyse 60 transition içeriyor; multi-tape ile bunun yarısından az olurdu.

**Performans benchmark yok.** O(n²) karmaşıklığı sözel olarak iddia ettim, smoke test adım sayılarıyla (n=4 → 78 adım, n=5 → 106 adım, n=7 → 174 adım) destekledim ama matplotlib ile grafiksel doğrulama yapmadım (Bonus C'nin önerdiği şey buydu).

**Görselleştirme yok.** Bonus D olarak Pillow ile her adımın PNG'si üretilebilirdi. Demo video bu eksiği biraz kapatıyor ama statik bir görselleştirici (örn. bir GIF) daha temiz olurdu.

**Bir hafta daha olsaydı:** önce Bonus A (`multi_tape.py`) ile TM-2'yi yeniden tasarlardım. Sonra Bonus D (görselleştirici) ile demo videosuna anlık görüntüler eklerdim. 

Genel olarak: çalışan, dokümante edilmiş ve test edilmiş bir TM kütüphanesi çıktı. Eksikleri var ama sınırları olduğunu bilen bir iş. Hesaplama kuramı dersinin "Turing makinesi nedir, ne yapar, ne yapamaz" sorularına kendi parmaklarımla cevap aramanın bambaşka bir öğrenme olduğunu gördüm. Sözel olarak bildiğim şeyler (sola taşma, blank semboller, δ fonksiyonu) somut bir mühendislik tercihi gerektirdiğinde nasıl başka bir şey haline geldiğini deneyimledim.

## 6. Kaynakça

- Dr. Ali Çetinkaya, *TuringLab Öğrenci El Kitabı*, Selçuk Üniversitesi Bilgisayar Mühendisliği, 2026 (proje el kitabı, repoya `README.md` olarak eklendi).
- Michael Sipser, *Introduction to the Theory of Computation*, 3rd ed., Cengage Learning. Özellikle Bölüm 3 (Turing Makineleri) ve Teorem 4.11 (halting probleminin karar verilemezliği).
- Wikipedia, *Turing machine*, https://en.wikipedia.org/wiki/Turing_machine (alfabe, δ fonksiyonu ve standart varyantlar için genel başvuru).
- PyYAML dokümantasyonu, https://pyyaml.org/wiki/PyYAMLDocumentation (`safe_load` ve YAML hata davranışları için).
- Python dokümantasyonu, *dataclasses* modülü, https://docs.python.org/3/library/dataclasses.html (`@dataclass(frozen=True)` kullanımı için).
- pytest dokümantasyonu, *parametrize* ve *capsys* fixture'ları, https://docs.pytest.org/ (test paketinin yapısı için).
