# TuringLab — Final Notum

> Selçuk Üniversitesi · Bilgisayar Mühendisliği · Hesaplama Kuramı
> Muhammed Yusuf Tosun · Mayıs 2026

## Proje Özeti

TuringLab, YAML dosyalarıyla tanımladığım Turing makinelerini Python'da çalıştırabildiğim bir simülasyon kütüphanesidir. Tek-şeritli ve deterministik bir motor; multi-tape ve NTM gibi varyantları (Bonus A/B) bu sefer yapmadım — vakti zorunlu bölümlerin sağlamlığına ayırdım. El kitabındaki spec API'sini (`from turinglab import SingleTapeTM, RunResult`) birebir karşılıyor; üzerine Bölüm 2 kapsamında dört makineyi tasarladım: tekliyi ikiliye çevirme, iki ikili sayıyı karşılaştırma, dizgi kopyalama ve parantez denge denetimi.

Sayılarla özetlemek gerekirse: motor tek dosya `tm_engine.py` içinde yaklaşık 280 satır Python. Test paketim 68 örneğe ulaştı, tamamı yarım saniye altında bitiyor. Üç haftalık çalışma akışı — ilk hafta motor, ikinci hafta makineler, son hafta rapor ile demo.

## Yazılım Mimarisi

El kitabı motoru "tek dosya `tm_engine.py`" diye istemişti, ona uydum. `turinglab/__init__.py` yalnızca re-export işlevi görüyor:

```
turinglab/tm_engine.py       — motor (Move, Transition, Configuration,
                                       RunResult, Tape, SingleTapeTM)
machines/*.yaml              — 5 YAML (spec örneği + 4 deliverable)
tests/test_tm_engine.py      — motor testleri (16 fonk / 28 örnek)
tests/test_machines.py       — TM testleri (14 fonk / 40 örnek)
tests/fixtures/*.yaml        — smoke YAML'lar
docs/design_notes.md         — her TM için detaylı notlar
REPORT.md                    — bu dosya
```

`Configuration`'ı dataclass olarak tasarladım çünkü el kitabının örnek kodu `result.history[5].state` gibi attribute erişimine dayanıyordu — tuple ya da dict tercih etseydim bu kullanım bozulurdu. `Transition` ise `frozen=True` ile immutable; δ kuralları program ömrü boyunca değişmez.

### Şerit Temsili

Projeye başlarken bu seçim üzerinde durdum çünkü "list mi dict mi" sorusu basit görünüyordu ama kafa sola gittiğinde davranış belirsizdi. List daha tanıdık geliyor, ancak negatif indeks Python'da listenin sonuna işaret ediyor; sola taşma için ya boy değiştirmek ya offset tutmak ya da başına `B` doldurmak gerekiyordu. Üç farklı senaryo üzerinde düşününce dict-tabanlı çözümün her durumda daha az koda yol açtığını gördüm.

Sonuç olarak `dict[int, str]` ile gittim. Yazılmamış konum okunduğunda `dict.get(pos, blank)` doğal biçimde blank dönüyor — negatif ya da büyük konum fark etmiyor. Bu sayede TM-1 ve TM-3 implementasyonlarında "sol uç" diye özel bir durum yazmaya gerek kalmadı; `q_rewind` blank görene kadar yürüyor, negatif konuma düşmesi sorun olmuyor.

Bu kararı README'de açıkça yazdım çünkü el kitabı sola taşma davranışını "kararı sizin" diye bırakmıştı. Benim kararım: şerit iki yöne sınırsız genişler, sola taşma bir hata değildir.

### `run()` Akışı

Akış sırası şöyle: önce girdideki her sembolün `input_alphabet` içinde olduğu denetleniyor — değilse `ValueError`. Sonra tape kuruluyor, durum başlangıç değerine, kafa 0 konumuna alınıyor. History'nin ilk elemanı başlangıç konfigürasyonu olarak ekleniyor (bu yüzden `len(history) == steps + 1`). Eğer başlangıç durumu zaten kabul durumu ise sıfır adımda dur — bu özel durumu test paketinde `test_accept_at_start` ile yakalıyorum.

Sonra ana döngü işliyor: oku → δ kuralı ara → (yoksa `no_transition` ile dur) → verbose ise satır bas → yaz → kafayı hareket ettir → durumu güncelle → history'ye konfigürasyon ekle → yeni durum kabul mü diye kontrol. Döngü sonu `timeout`.

### Verbose Mod Çıktısı

Spec'in tam biçimi şu: `Adım N | Durum: <s> | Şerit: <bracketli_şerit> | Hareket: <M>`. Halt anında son satır `... | (durdu: <reason>)` ile bitiyor. Spec'in örnek çıktısında şeridin sağında bir blank fazladan görünüyordu (`[1]011B` gibi); bunu ilk versiyonda atlamışım, sonra spec'i ikinci kez okurken fark ettim. `Tape.render`'ı `max_pos+1`'e kadar genişlettim, `Tape.write`'ı da blank yazımlarını sözlükten çıkaracak şekilde değiştirdim (görsel temizlik için — semantik değişmiyor, okuma zaten blank dönüyor).

## Makine Tasarımları

**Tekliyi ikiliye çevirme.** Girdi `111`, sonuç (şeridin sağında) `11`. 8 durum. Algoritmanın özü: girdinin hemen sağına bir X sınırı ve onun yanına `0` koy; sonra her turda en sağdaki unary 1'i tüket (X yap) ve sağdaki ikili sayacı taşımalı +1 ile artır. Taşma anında carry sınır X'in üstüne taşıyor ve ikili sayı bir hane uzuyor — burada X'in çift rolü (hem sınır hem tüketilmiş) anahtar oluyor. Smoke testte n=5 için 106 adım, n=7 için 174 adım çıktı.

**İki ikiliyi karşılaştırma.** Bu projenin en sancılı tasarımı — **16 durum**. Sebebi sonradan daha net göründü: üç ayrı "mod" var (eq, gt, lt; yani şu ana dek hangi sayı önde) ve her birinde sol-tara, sağ-tara, rewind alt-durumları gerekiyor. Sağ tarama da kendi içinde "henüz `#`'i geçmedim" ve "geçtim, ikinci sayıdayım" diye ikiye bölünüyor — çünkü TM bir `0` ya da `1` okuduğunda "bu hangi sayının hanesi?" sorusuna sadece durumdan bakarak cevap verebiliyor, pozisyondan değil. Durum sayısı bu yüzden katlandı.

Algoritmanın kalbi MSB-first çiftleme. İlk fark gördüğüm pozisyonda verdict'i duruma yazıyorum (eq → gt veya eq → lt). Sonrasında uzunluk farkı bu verdict'i ezebiliyor — örn. `11011#1110` (27 vs 14) testinde 3. pozisyonda `0<1`'i gördüm, lt mode'a geçtim, ama sonra 1. sayının daha uzun olduğunu görünce kabul ettim. "Öncüsüz binary varsayımı" altında uzun olan her zaman büyüktür.

**Dizgi kopyalama.** Girdi `abba`, çıktı `abba#abba`. 6 durum, en sade tasarımlardan. Klasik mark-and-copy: önce sona `#` koy, sonra her turda en soldaki işaretsizi `A` (a için) veya `D` (b için) ile işaretle, sağ uca yürü, ilk B'ye orijinal harfi yaz. Şerit son halinde `AADA#abba` gibi görünüyor; test tarafı A→a, D→b çevirmesi yapıyor. 

Spec metni "büyük A, B'" markerlarını öneriyordu ancak `B'` apostroflu iki karakter ve motor tek-karakter sembol bekliyor. `D` seçtim, herhangi bir çakışma oluşmuyor.

**Parantez denge** (öğrenci seçimi). El kitabındaki dört seçenekten (c)'yi tercih ettim çünkü diğer üç TM hep transducer'dı (girdiyi dönüştürüyor). Bu ise decider; ödevde çeşitlilik açısından yerinde geldi. Algoritma klasik yığın simülasyonu: ilk işaretsiz `)`'yi bul + işaretle, sola dön en yakın işaretsiz `(`'yi bul + işaretle, başa al ve tekrarla. Eşleşmesiz `)` (sola B'ye çarparsam) → ret; sonda eşleşmesiz `(` kalırsa → ret. 5 durum, projenin en kompakt makinesi.

**En zorlu hata** TM-2'de yaşandı. İlk versiyonda `seek_2nd_post` Y yazdıktan sonra R hareketi uyguluyordu; rewind ise sağ uçtaki blank'i okuyup `B → R` kuralıyla yanlış yöne dönüyordu. 13 testten 5'i fail ediyordu, hepsi "kabul beklenirken ret". Verbose'ı açıp iki-üç trace inceleyince hata ortaya çıktı. Düzeltme tek karakter (R yerine L) ama bulmak sağlam bir uğraş gerektirdi. Bu deneyim "verbose mod sadece spec gereği yazılmış bir şey değil, asıl debug aracı" sonucuna varmama yol açtı.

## Halting Problemi Üzerine

El kitabının kavramsal tartışma seçenekleri arasından halting problemini tercih ettim. Sebep şu: TuringLab'a koyduğumuz `max_steps` parametresi yüzeyde halting'in bir cevabı gibi görünüyor — "1000 adımda bitmedi mi, demek ki bitmez". Ama aslında değil. Bu **karar değil, vazgeçiş**.

Asıl halting problemi şu soruyu soruyor: bir TM'in tanımı (örneğin bir YAML) ve bir girdi *w* verildiğinde, "bu TM, *w* üzerinde sonlu adımda durur mu?" sorusuna evet/hayır cevabı veren başka bir TM yazılabilir mi? Turing 1936'da kanıtladı: hayır. Klasik diagonal argümanla — böyle bir H makinesi olsaydı, H'yi kullanarak çelişkili bir D makinesi inşa edilebilirdi (kendisi üzerinde H'nin verdiği cevabın tersini yapan).

TuringLab'ın `max_steps`'i bu sorunu çözmüyor:

- `max_steps=1000` ile timeout dönerse, 1001. adımda kabul edip etmeyeceğini bilmiyorum. "Bilmiyorum, vazgeçtim" demek bu.
- `max_steps=∞` mümkün değil — durmayan bir makinede sonsuza kadar bekleriz, süreç asla dönmez.
- "YAML'a bakıp duracak mı?" diye statik analiz de çözüm değildir; bu, halting'in başka bir formülasyonudur.

Beni en çok etkileyen taraf şuydu: bir programcı olarak halting'e sürekli çarpıyoruz. IDE'nin "kodu çalıştırırsam dönecek mi?" sorusuna cevap verememesi, sonsuz döngü tespit araçlarının her senaryoda doğru çalışmaması, statik analizörlerin "kesinlikle sonlanır" garantisini verememesi — hepsi Turing 1936'nın günlük yansımalarıdır. `max_steps` koymak zorunda olmamız da bunun küçük bir provası.

Daha temel bir nokta: halting problemi bir mühendislik kısıtı değil, matematiksel bir gerçektir. Daha hızlı bilgisayar veya daha akıllı algoritma yardımcı olmuyor. Hesaplanabilir olanı simüle edebiliyoruz; hesaplanamaza verebileceğimiz tek şey zaman aşımıdır. 

## Eksikler ve Sonraki Adımlar

Bonus seçeneklerini yapmadım. Vakti zorunlu bölümün sağlamlığına ayırdım — özellikle motorun spec uyumuna ve test kapsamına. En çok yapmak istediğim Bonus A (multi-tape) idi; TM-2'nin 16 durumunu muhtemelen yarıya indirebilirdi ve "tek-şerit zorluğu" iddiamı sayısal olarak destekleyebilirdi.

Başka bir açık: O(n²) iddialarımı sözel olarak yaptım, smoke test adım sayıları (n=4 → 78, n=5 → 106, n=7 → 174) tutarlı görünüyor ancak matplotlib ile grafiksel doğrulama yapmadım. Bonus C bunu öneriyordu, atladım.

Görselleştirme de yok. Bonus D ile her adımın PNG'si üretilebilirdi; demo video bu eksiği bir nebze kapatıyor ama statik bir görsel kaynak daha temiz olurdu.

Ek vaktim olsaydı atılacak adımlar: önce multi-tape ile TM-2'yi yeniden tasarlamak, sonra Bonus D ile her TM için adım-adım PNG'ler üretip demo videosuna entegre etmek. Bu iki adım projeye en somut katkıyı sağlardı.

Genel değerlendirme olarak: çalışan, dokümante edilmiş ve test edilmiş bir kütüphane çıktı. Eksikleri var ancak sınırlarını bilen bir iş. "Turing makinesi nedir, ne yapar, ne yapamaz" sorularına cevap arama deneyimi — daha önce sözel olarak bildiğim şeyleri (şerit, blank, δ fonksiyonu) somut tercihler haline dönüştürdü.

## Kaynakça

- Sipser, M. *Introduction to the Theory of Computation*, 3rd ed., Cengage. Bölüm 3 (Turing makineleri) ve halting kanıtı için Teorem 4.11.
- *TuringLab Öğrenci El Kitabı* (Dr. Ali Çetinkaya, Selçuk Üniversitesi, 2026) — repoya `README.md` olarak işlenmiş hâliyle.
- Wikipedia, *Turing machine* — alfabe, δ fonksiyonu ve standart varyantların özeti için ilk başvurum.
- PyYAML belgeleri (pyyaml.org) — `safe_load` davranışı ve hata sınıfları için.
- pytest belgeleri (docs.pytest.org) — `parametrize` ve `capsys` fixture'larını öğrenirken.
- Python dataclasses belgeleri — `frozen=True` ve init signature mantığı için.
