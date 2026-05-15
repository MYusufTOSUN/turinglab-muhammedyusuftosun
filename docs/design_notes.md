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
