# Tasarım Notları

Bu doküman Bölüm 2 kapsamında tasarladığım Turing makinelerinin yüksek seviyeli
algoritmalarını, durum/alfabe seçimlerini ve geliştirme sırasında karşılaştığım
sorunları kayıt altına alır.

## TM-1 · Unary → Binary Çevirici

**Dosya:** `machines/unary_to_binary.yaml`
**Girdi:** Tekli gösterimde sayı (örn. `111` = 3)
**Çıktı:** Aynı sayının ikili gösterimi şeridin sağ ucunda (örn. `11`)

### 1. Strateji

Tek-şeritte yapılabilecek en doğal yol, "her bir unary 1'i tüket ve sağdaki ikili
sayacı bir artır" mantığı. Algoritma şöyle:

1. **Setup:** Önce girdideki tüm 1'lerin üzerinden geçip ilk B'ye ulaşıyorum. Oraya
   bir `X` sınır işareti, sağındaki hücreye de başlangıç değeri olarak `0` yazıyorum.
2. **Döngü:** Sol uca dönüp, sağa doğru tarayarak `X` sınırına gelene kadar gidiyorum.
   Sınırın hemen solundaki hücreye L hareketiyle göz atıyorum:
   - `1` görürsem → onu `X` yapıp tüketiyorum, sağa giderek ikili sayacın sonuna
     ulaşıyor ve taşımalı +1 uyguluyorum.
   - `X` veya `B` görürsem → tüm unary tüketilmiş, kabul.
3. **Taşma:** İkili artırma sırasında carry sola yürürken `X`'e çarparsa, X'in üstüne
   `1` yazılıyor — bu sayede ikili sayı bir hane uzar. Bu doğal olarak çalışıyor çünkü
   sınır X'i ile tüketilmiş unary X'leri tek bir bloğun parçası.

### 2. Durum sayısı

Toplam 8 durum: `q_scan`, `q_setup_sep`, `q_rewind`, `q_main`, `q_check_unary`,
`q_seek_bin`, `q_increment`, `q_accept`.

Daha aza indirmeye çalıştım ama `q_check_unary` ile `q_main`'i birleştirmek mümkün
olmadı: `q_main`'de sağa giderken X gördüğümde, X'in solundaki hücreyi okumam gerekiyor
(en sağdaki unary 1 oraya düşüyor), ve aynı transition'da hem sağa hem L gidemediği
için bir geçiş durumu eklemek zorunda kaldım. `q_rewind` ile `q_seek_bin`'i ayırmam
da gerekti çünkü biri sola tarıyor, biri sağa.

### 3. Şerit alfabesi seçimi

Spec'in izin verdiği `{0, 1, B, X}` ile çalıştım, ekstra sembol kullanmadım. `X`
iki rol üstleniyor: hem tüketilmiş unary 1'leri işaretliyor, hem de unary ile ikili
arasındaki sınır görevi görüyor. İlk başta sınır için ayrı bir sembol düşündüm ama
zaten her iki "X"'in de aynı semantik anlamı var ("artık unary değil, geçilebilir"),
bu yüzden tek X yetiyor.

### 4. Karmaşıklık

Girdi uzunluğu *n* için her unary 1'i tüketmek tarama-artırma-rewind döngüsü
gerektiriyor; bu döngü O(n + log n) adım sürer (n: girdi uzunluğu, log n: ikili sayacın
uzunluğu). Toplam n iterasyon olduğundan en kötü durumda **O(n²)** adım. Smoke testte
n=7 için 174 adım çıktı, n=5 için 106 — kabaca kuadratik büyüme.

### 5. Hata ayıklama hikayesi

İlk denemede "en soldaki unary 1'i tüket" mantığıyla yazdım. Sebep: rewind'den sonra
ilk 1'i bulmak basit. Ama bu yaklaşımda tüketilmiş X'ler ile sınır X'i arasında
remaining 1'ler kalıyordu (ör. `X11X0` gibi) ve ana döngüde "şu X tüketilmiş mi
yoksa sınır mı?" ayırt edemiyordum — ikisi de sembol olarak `X`. Spec ek sembol
yasakladığı için yapacak bir şey yoktu.

"En sağdaki unary 1'i tüket" şekline geçince bütün X'ler tek bir blok haline geldi
(`11XXX1` gibi), q_main'de sağa giderken ilk X gördüğümde "sınıra ulaştım" diyebildim.
Bu küçük değişiklik tüm tasarımı sadeleştirdi.

İkinci bug: `q_check_unary`'den `q_seek_bin`'e geçişte X yazıp R yapmayı unutmuştum
(`write: "X"` yerine `write: "1"` kalmıştı kopyala-yapıştırdan), tüketim olmuyordu ve
sonsuz döngü oluştu — timeout'a takılınca farkettim. YAML'da bir transition daha
yazarken aynısını yapmamak için her bir kuralı çift kontrol ettim.

## TM-2 · İki İkili Sayıyı Karşılaştıran TM

**Dosya:** `machines/binary_compare.yaml`
**Girdi:** Birinci ve ikinci ikili sayı `#` ayraçla (örn. `1011#1100`)
**Kabul:** Birinci sayı ikincisinden kesinlikle büyükse; eşit veya küçükse ret.

### 1. Strateji

MSB-first çiftleme. Her iterasyonda 1. sayının en soldaki tüketilmemiş hanesini
`X` ile, 2. sayının en soldaki tüketilmemiş hanesini `Y` ile işaretliyorum. İlk
fark gördüğüm pozisyonda verdict'i state'te saklıyorum: eq (henüz fark yok),
gt (1. büyüktü), lt (2. büyüktü). Sonunda iki olgu birleşir:

- 1. önce biterse → 2. uzun → ret (uzunluk verdict'i ezer)
- 2. önce biterse → 1. uzun → kabul (uzunluk verdict'i ezer)
- İkisi de aynı anda biterse: gt → kabul, eq/lt → ret

Yani lt modunda bile 2. boşalırsa 1. kabul ediliyor. Bu doğru, çünkü öncüsüz
ikili gösterimde uzun olan her zaman daha büyüktür.

### 2. Durum sayısı

16 durum: 3 mod (eq/gt/lt) × {sol-tara, sağ-tara-pre-#, sağ-tara-post-#, rewind}
= 12 ana durum, artı `q_first_done_gt`, `q_accept` ve eq modunun consumed
digit değerini hatırlamak için 2 ekstra seek state'i.

Pre-# ve post-# ayrımı kaçınılmaz oldu çünkü TM kafa bir '0' veya '1' okuduğunda
"bu 1. sayıya mı yoksa 2. sayıya mı ait?" sorusunu pozisyondan bilmediği için
state üzerinden taşımak zorunda. Bunu single state'e indirme yolunu bulamadım.

### 3. Şerit alfabesi

`{0, 1, #, B, X, Y}`. `X` = 1. sayıdan tüketilen hane, `Y` = 2. sayıdan
tüketilen hane. Tek X yetmedi çünkü "şu pozisyondaki X 1. taraftan mı 2.
taraftan mı?" bilgisini kayıp ediyordum.

### 4. Karmaşıklık

Girdi uzunluğu *n* (toplam karakter) için her tur taramalı (sol → orta → sağ →
geri) ve O(n) sürüyor. En fazla *n/2* tur yapılır (her tur en az 2 karakter
tüketir, biri X biri Y). Toplam **O(n²)**.

### 5. Hata ayıklama hikayesi

İlk versiyonda `q_seek2_X_post` Y yazdıktan sonra R yapıyordu, sonra `q_rewind`
çağrılıyordu. Hatamı testlerle gördüm: kısa girdilerde (`1#0` gibi) Y yazıldıktan
sonra head sağ uçtaki B üzerine geldi; rewind transition'ı `B → R, q_left_X`
diye yazılıydı ve makine tersine, sağa doğru gidiyordu. 13 testten 5'i fail oldu,
hep "kabul beklenirken ret" şeklinde. Düzeltme: seek_post'ta Y yazdıktan sonra
R yerine L; bu sayede rewind, head'i 2. sayının sol komşusuna (zaten yazılmış bir
Y veya '#') koyuyor ve oradan sola gidip sol uç B'sini bulabiliyor.

İkinci kafa karışıklığı: lt modunda 1. uzun çıkarsa ne olmalı? İlk içgüdüm "lt
verdict bağlayıcı, ret" idi. Test `11011#1110` ile (27 vs 14, sonuç 27 > 14)
ret çıkınca durdum ve düşündüm: aslında ileride 2. tükenirse 1. daha uzun
demektir ve uzunluk farkı leftmost-difference'tan daha güçlü. Bu davranışı
`q_seek2_lt_post` 'B' okuduğunda doğrudan `q_accept`'e gitmesiyle yazdım.

## TM-3 · Dizgi Kopyalayıcı

**Dosya:** `machines/string_copy.yaml`
**Girdi:** `a` ve `b`'den oluşan bir dizgi (örn. `abba`)
**Çıktı:** `<girdi>#<girdi>` (örn. `abba#abba`)

### 1. Strateji

Klasik mark-and-copy yaklaşımı:

1. Önce girdinin sonuna `#` koyuyorum.
2. Her iterasyonda girdinin en soldaki işaretsiz harfini bul: `a` ise `A`, `b`
   ise `D` ile işaretle.
3. Sağa giderek `#`'i de geçip kopyalanmış kısmın sağ ucundaki ilk B'ye o
   harfin orijinalini yaz.
4. Sol uca geri dön ve bir sonraki işaretsiz harfe geç.
5. `q_main` `#` okuduğunda tüm girdi işaretlenmiştir; kabul.

Şeritte sonunda `AADA#abba` gibi bir görüntü olur; orijinal görüntüye dönmek
isteniyorsa test tarafında `A → a, D → b` replace yapılır (kararın gerekçesi:
TM içinde "unmark" fazı eklemek 4-5 ek state istiyordu; basit ve doğru olan
bu yaklaşım daha temiz).

### 2. Durum sayısı

6 durum: `q_setup_scan`, `q_rewind`, `q_main`, `q_copy_a_right`,
`q_copy_b_right`, `q_accept`. Sade çünkü "hangi harfi kopyalayacağım" bilgisini
state ismiyle taşıyorum, ek bilgi gerekmiyor.

### 3. Şerit alfabesi

`{a, b, #, B, A, D}`. Spec metni "A ve B'" diye öneriyordu ama `B'` tek karakter
değil (apostroflu) ve motor tek karakterlik semboller bekliyor, bu yüzden
`B'` yerine `D`'yi seçtim. `A` = işaretli `a`, `D` = işaretli `b`. Çakışma yok.

### 4. Karmaşıklık

n uzunluğundaki girdi için her harfi kopyalamak O(n) tarama gerektiriyor
(sola git, en soldaki işaretsizi bul; sağa git, ilk B'ye yaz; geri dön).
n harf olduğu için toplam **O(n²)**. n=6 için 147 adım çıktı testte; n=4 için
75 adım — kabaca kuadratik büyüme.

### 5. Hata ayıklama hikayesi

İlk denemede setup fazını ayrı bir state ile (`q_init_done`) yazıp '#' yazımı
sonrası bir cell sağa gidiyordum, sonra rewind ediyordum — gereksiz bir state'di.
`q_setup_scan` B okuduğunda hem '#' yazıp hem de L yapıp doğrudan `q_rewind`'e
geçince bir state azaldı.

Asıl bug `q_rewind`'deydi: A ve D için transition eklemeyi unutmuştum. Setup
sonrası ilk rewind (henüz A/D yokken) sorunsuzdu, ama 2. iterasyonda sola
dönerken A okuyunca makine duruyordu (no_transition). Test `abba` için 11.
adımda halt etti; verbose modu açıp `Adım 11 | Durum: q_rewind | Şerit: Abb[A]...`
satırını görünce `q_rewind` transition listesinin eksik olduğunu anladım.

## TM-4 · Parantez Denge Kontrolü (Öğrenci Seçimi)

**Dosya:** `machines/student_choice.yaml`
**Girdi:** `(` ve `)` karakterlerinden oluşan dizgi (örn. `(()())`)
**Kabul:** Parantezler dengeli ise

El kitabındaki dört seçenek arasından (c) seçeneğini tercih ettim. Sebep:
diğer üç TM hep transducer (girdiyi dönüştürüyor); bu ise decider, çeşitlilik
katıyor. Aynı zamanda stack-tabanlı bir yapıyı tek-şeritte mark-and-pair ile
simüle etmek hesaplama kuramı dersi için temsili bir alıştırma.

### 1. Strateji

Klasik mark-and-pair (yığın simülasyonu tek şeritte):

1. `q_scan_right`: soldan sağa tara, ilk işaretsiz `)` bulunca X ile işaretle.
2. `q_match_left`: sola dön, en yakın işaretsiz `(` bulunca onu da X yap. Bu
   "en yakın" yani henüz kapatılmamış en içteki açık parantez — stack tepesi.
3. `q_rewind`: sol uca dön, sonra adım 1'e geri.
4. q_scan_right `B` (sağ uç) görürse: tüm `)`'ler işaretlenmiş; ama hâlâ
   eşleşmemiş `(` kalmış olabilir. `q_check_remaining`: sağdan sola tara,
   sadece X bekleyerek; `(` görürsen unmatched → ret.
5. q_match_left `B` (sol uç) görürse: kapanan paren'in eşleşeni yok → ret.

### 2. Durum sayısı

5 durum: `q_scan_right`, `q_match_left`, `q_rewind`, `q_check_remaining`,
`q_accept`. Diğer TM'lere göre kompakt çünkü her durumun işi netçe tek bir yöne
gidiyor ve karşılaştırma/seçme kararı yok (sadece "X gör/atla, paren gör/işaretle").

### 3. Şerit alfabesi

`{(, ), X, B}`. Tek bir X işareti yetti çünkü açık ve kapalı paren'i ayrı
işaretlere ihtiyaç yok — bir kez eşleştirildikten sonra "işaretlenmiş" bilgisi
kâfi. Açık paren'in nerede olduğunu hatırlamak gerekirse pozisyon belirleyici
(`#` veya başka marker) eklenmeliydi, ama bu algoritmada gerekmiyor.

### 4. Karmaşıklık

n uzunluğundaki girdi için her `)` eşleştirmesi tarama+geri-dön döngüsü
yaratıyor (O(n)), ve en fazla n/2 paren çifti var. Toplam **O(n²)**. Smoke
testte n=6 `(()())` için 42 adım, n=8 `(((())))` için 70 adım çıktı.

### 5. Hata ayıklama hikayesi

İlk versiyonda `q_rewind`'e `(` için kural yazmamıştım — sadece X ve B için
düşündüm. İlk iterasyon zaten X'siz başlıyordu, sorun çıkmadı; ama `(())`
testinde iter 1'de pos 2'deki `)`'yi eşleştirip pos 1'deki `(`'yi işaretledikten
sonra `q_rewind`, pos 0'daki işaretsiz `(`'i okuduğunda kural bulamadı ve makine
no_transition ile durdu. Beklenen sonuç kabuldü, ama sonuç ret oldu. Verbose'ı
açıp 7. adımda `Adım 7 | Durum: q_rewind | Şerit: [(]XX) | (durdu: no_transition)`
satırını görünce `q_rewind`'e işaretsiz `(`'lerin de gelebileceğini fark ettim
(çünkü stack tepesi her zaman pos 0'da olmuyor). `(` → L ekleyince sorun çözüldü.

İkinci nokta: ilk başta `q_match_left` 'B' için "no transition" yerine `q_reject`
diye bir durum tanımlamayı düşündüm, sonra vazgeçtim. Motor zaten no_transition
ile `accepted=False, reason="no_transition"` dönüyor — gereksiz state olmasın
diye eklemedim. El kitabı reject_states'i opsiyonel bırakıyor zaten.
