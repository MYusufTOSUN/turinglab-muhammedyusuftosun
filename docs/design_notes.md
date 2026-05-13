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
