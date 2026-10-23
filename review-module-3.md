# Rencana Module 3 -- RevoShop Frontend

Catatan perencanaan untuk Module 3 (frontend), disusun dari Full Brief dan
Checkpoint 1. Dokumen ini masih berada di folder Module 2; **pindahkan ke repo
Module 3** begitu repo-nya dibuat, dan tambahkan namanya ke `.gitignore` repo
baru itu (`.gitignore` di sini hanya mengabaikan `review.md`, bukan file ini).

---

## 1. Gambaran Module 3

Membangun frontend toko online RevoShop yang **memakai Flask API dari Module 2**
sebagai backend-nya. Tiga checkpoint dua mingguan:

| CP | Isi | Minggu |
| --- | --- | --- |
| 1 | Fondasi: HTML/CSS, JavaScript, TypeScript, Tailwind | 1 & 2 |
| 2 | React Components + Next.js App Router | 3 & 4 |
| 3 | Integrasi API penuh, autentikasi, testing, deployment | 5 & 6 |

Aplikasi akhirnya melayani dua jenis pengguna: **customer** (menelusuri produk,
memfilter kategori, membuat order) dan **admin** (mengelola produk, kategori,
dan order lewat `/dashboard`).

### Yang penting disadari sejak sekarang

**API Module 2 menjadi backend Module 3.** URL
<https://revou-revoshop-jim1504-seven.vercel.app> akan dipakai sebagai
`NEXT_PUBLIC_API_BASE_URL`. Artinya deployment itu **tidak boleh dimatikan**
selama Module 3 berjalan, dan project Supabase-nya jangan sampai berstatus
`Paused`. Sebelumnya cukup hidup sampai penilaian Module 2; sekarang umurnya jadi
enam minggu lagi.

**API-nya sudah pindah dari Render ke Vercel.** Ini kabar bagus untuk Module 3:
Render paket gratis tidur setelah 15 menit menganggur sehingga request pertama
bisa memakan 22 detik lebih, sedangkan Vercel konsisten di sekitar 1,2 detik.
Server Component yang mengambil data saat halaman dirender jadi tidak perlu
menunggu backend bangun -- perbedaan yang langsung terasa di `loading.tsx`.

**Frontend dan backend sama-sama di Vercel, tapi sebagai dua project terpisah.**
Backend Flask sudah punya project sendiri; frontend Next.js nanti project baru
dengan URL sendiri. Keduanya tidak saling menimpa.

---

## 2. Checkpoint 1 -- yang dikerjakan sekarang

Checkpoint ini **sengaja tanpa Next.js dan tanpa Flask API**. Isinya lima
latihan fondasi. Tujuannya supaya paham apa yang nanti diabstraksi React.

### Struktur repo

Repo baru, misalnya `module-3-jim1504`:

```
module-3-jim1504/
├─ html-css/
│  ├─ index.html          halaman profil semantik + form kontak
│  └─ style.css           grid/flexbox + satu breakpoint
├─ javascript/
│  ├─ dom.html            halaman untuk latihan DOM
│  ├─ dom.js              seleksi elemen, toggle class, tambah/hapus elemen
│  ├─ arrays.html
│  └─ arrays.js           forEach, map, filter, reduce
├─ typescript-tailwind/
│  ├─ package.json
│  ├─ tsconfig.json
│  ├─ tailwind.config.js
│  ├─ src/
│  │  ├─ types.ts         interface, type alias, union type
│  │  ├─ data.ts          array produk bertipe
│  │  ├─ main.ts          render katalog, live search, counter
│  │  └─ input.css        directive Tailwind
│  ├─ dist/               hasil kompilasi tsc + tailwind
│  └─ index.html
├─ docs/                  screenshot
├─ .gitignore             node_modules/, dist/ boleh ikut atau tidak
└─ README.md
```

### Urutan pengerjaan

Kerjakan berurutan, commit tiap selesai satu bagian -- rubrik meminta
*"commit history showing incremental progress across HTML/CSS, JavaScript,
TypeScript, and Tailwind"*, jadi empat commit besar itu minimal.

**1. `html-css/` -- halaman profil**

Yang dinilai: elemen semantik (`header`, `main`, `section`, `footer`, **bukan**
`div` polos), form kontak dengan `input type` yang tepat dan `<label>`
berpasangan, box model, **CSS Grid untuk minimal satu section**, dan media query
yang benar-benar diuji di lebar mobile.

Catatan: rubrik menyebut Grid dan Flexbox terpisah. Aman kalau Grid dipakai
untuk layout dua dimensi (misalnya galeri atau daftar skill) dan Flexbox untuk
navbar atau baris tombol -- keduanya terlihat dipakai pada tempat yang wajar.

**2. `javascript/dom.js` -- manipulasi DOM**

Harus mencakup keempatnya: memilih dan memperbarui elemen, toggle class,
membuat dan menghapus elemen, dan event handler. Sertakan satu `submit` handler
dengan `event.preventDefault()` -- itu baris rubrik tersendiri.

Ide yang cukup: to-do list kecil. Tambah item (create), hapus item (remove),
klik untuk menandai selesai (toggle class), form submit dengan `preventDefault`.

**3. `javascript/arrays.js` -- pemrosesan array**

Keempat method wajib muncul dan **mengerjakan sesuatu yang masuk akal**, bukan
sekadar dipanggil:

- `forEach` -- menampilkan tiap item
- `map` -- mengubah bentuk data, misalnya menambah harga setelah diskon
- `filter` -- menyaring, misalnya produk yang stoknya masih ada
- `reduce` -- mengagregasi, misalnya total nilai inventaris

Pakai data produk yang mirip RevoShop, supaya nyambung ke latihan berikutnya.

**4. `typescript-tailwind/` -- setup**

`tsc` dengan `tsconfig.json` yang **kompilasi tanpa error**. Aktifkan `strict`
supaya tipenya benar-benar diuji.

Tipe yang harus ada:
- `interface` atau `type alias` untuk produk
- **union type** untuk nilai yang bisa berbentuk lebih dari satu keadaan --
  misalnya `type Availability = "in-stock" | "low-stock" | "out-of-stock"`
- objek bersarang dan array yang bertipe benar (`Product[]`, dan `category`
  sebagai objek di dalam produk)

Tailwind dipasang di project ini, dan **kelas utility dipakai menggantikan CSS
custom** -- rubrik menyebut ini eksplisit, jadi jangan menulis file CSS sendiri
di sini selain directive Tailwind.

**5. `typescript-tailwind/` -- katalog interaktif**

Ini bagian terpenting: brief menyebutnya *"direct predecessor of the React
`ProductCard` you'll build in Checkpoint 2"*. Tiga hal harus jalan:

1. Daftar produk **dirender dari data**, bukan HTML yang diketik manual
2. **Live search** memfilter daftar saat mengetik
3. Minimal satu **perubahan state interaktif** -- counter ala add-to-cart

Satu baris rubrik yang mudah terlewat: *"maps typed data to Tailwind class
strings (e.g. conditional styling based on a typed field)"*. Inilah gunanya
union type dari langkah 4 -- misalnya badge hijau untuk `in-stock`, kuning untuk
`low-stock`, merah untuk `out-of-stock`, dipilih dari nilai bertipe itu.

Rancang kartunya semirip mungkin dengan `ProductCard` React nanti: gambar/
placeholder, nama, harga, badge stok, tombol. Checkpoint 2 tinggal
memindahkannya ke komponen.

---

## 3. Deliverable Checkpoint 1

| # | Deliverable | Catatan |
| --- | --- | --- |
| 1 | Repo GitHub dengan tiga folder di atas | `html-css/`, `javascript/`, `typescript-tailwind/` |
| 2 | `README.md` | Isi tiap folder dan cara menjalankannya secara lokal |
| 3 | Commit history bertahap | Minimal empat commit: HTML/CSS, JavaScript, TypeScript, Tailwind |
| 4 | Screenshot halaman profil **desktop** | `docs/profile_desktop.png` |
| 5 | Screenshot halaman profil **mobile** | `docs/profile_mobile.png` -- pakai device toolbar DevTools |
| 6 | Screenshot katalog + live search aktif | `docs/catalog_search.png` -- ambil saat kotak search terisi dan daftarnya sudah tersaring, supaya filternya terbukti bekerja |

Belajar dari Module 2: **beri nama file tanpa spasi dan tanpa kurung siku**,
supaya link di README tidak perlu di-encode.

---

## 4. Backend Module 2 harus diubah dulu -- ini yang paling penting

Rubrik Checkpoint 2 menuntut beberapa hal dari API yang **belum ada**. Sudah
diuji langsung ke deployment produksi, dan hasilnya:

| Yang diminta rubrik CP2 | Hasil uji ke API sekarang | Status |
| --- | --- | --- |
| `GET /products?search=${query}` | balas 20 produk, query diabaikan | **belum ada** |
| `GET /products?category_id=${id}` | balas 20 produk, query diabaikan | **belum ada** |
| `GET /orders` di Server Component | `400 user_id is required` | **belum bisa** |
| `GET /categories` | 6 kategori | sudah jalan |

Tanpa ketiga perbaikan itu, tiga baris rubrik Checkpoint 2 tidak mungkin
dipenuhi. Kerjakan **sebelum** mulai Checkpoint 2, bukan saat sudah mentok.

**a. Filter `search` dan `category_id` di `GET /products`.** Ini yang paling
mendesak -- dua baris rubrik bergantung langsung padanya (`SearchBar` dan
`CategoryFilter`). Perubahannya kecil, di `list_products` pada
`routes/products.py`: baca `request.args`, lalu tambahkan `where` secara
kondisional -- `ilike` untuk pencarian nama, dan kesamaan untuk `category_id`.
Tanpa parameter, perilakunya harus tetap seperti sekarang supaya tidak ada yang
rusak.

**b. `GET /orders` harus bisa dipanggil tanpa identitas.** Rubrik meminta
`app/orders/page.tsx` mengambil `GET /orders` dari Server Component, padahal
sekarang endpoint itu balas 400 tanpa `user_id`. Requirement admin di Full Brief
juga meminta *"all orders for all users"*, yang sama-sama tidak mungkin sekarang
karena `list_orders` selalu memfilter `where(Order.user_id == user_id)`.
Satu perubahan menyelesaikan keduanya: kalau tidak ada identitas, kembalikan
seluruh order alih-alih 400. Untuk tabel admin, daftarnya juga perlu memuat nama
produk dari `order_items` -- saat ini itu hanya ada di `GET /orders/<id>`.

**c. CORS.** Diperlukan lebih cepat dari dugaan. Server Component memanggil API
dari server, jadi tidak kena CORS -- tapi `ProductList` adalah Client Component
dengan `useEffect` yang fetch dari **browser**, dan itu kena. Jadi CORS sudah
dibutuhkan di Checkpoint 2, bukan Checkpoint 3. `flask-cors` sudah terpasang di
venv Module 2 tapi belum ada di `requirements.txt` dan belum dipakai di
`app.py`. Batasi origin-nya ke domain Vercel dan `localhost:3000`.

**d. `role` bisa dikirim client saat registrasi.** `POST /users` menerima `role`
dari body (`data.get("role", "customer")`), jadi siapa pun bisa mendaftar sebagai
admin. Requirement Module 3 menyebut registrasi harus **selalu** `customer`.
Baru mendesak di Checkpoint 3, tapi perbaikannya satu baris -- abaikan `role`
dari input.

Setiap perubahan di atas menyentuh API yang sudah dinilai, jadi kerjakan di
branch, jalankan `pytest`, dan pastikan response lama tetap sama bentuknya.

Ketiganya tidak mendesak minggu ini, tapi catat sekarang selagi konteksnya masih
segar.

---

## 5. Keputusan yang sebaiknya diambil sekarang

**Data produk di Checkpoint 1 sebaiknya meniru bentuk response API asli.**
Katalog CP1 memakai data hardcoded, tapi kalau bentuk objeknya sudah sama dengan
yang dikembalikan `GET /products` (`product_id`, `product_name`, `price`,
`stock_quantity`, `category_id`, `is_active`), maka `interface Product` yang
ditulis sekarang bisa dipakai apa adanya di Checkpoint 2 dan 3. Kalau bentuknya
dikarang bebas, tipenya harus ditulis ulang nanti.

Contoh yang sudah cocok dengan API:

```ts
interface Product {
  product_id: number;
  product_name: string;
  description: string | null;
  price: number;
  stock_quantity: number;
  category_id: number;
  is_active: boolean;
}
```

Ambil saja beberapa produk sungguhan dari
<https://revou-revoshop-jim1504-seven.vercel.app/products> sebagai data latihan.

**Bahasa README.** README Module 2 berbahasa Indonesia. Konsisten saja, kecuali
memang ingin ganti.

---

## 6. Checklist Checkpoint 1

Fondasi HTML/CSS/JS:

- [ ] Halaman profil memakai `header`, `main`, `section`, `footer`
- [ ] Form kontak dengan `input type` sesuai dan `<label>` berpasangan
- [ ] Box model diterapkan sadar (margin, border, padding)
- [ ] **CSS Grid** dipakai untuk minimal satu section dua dimensi
- [ ] Media query diuji dengan benar-benar mengecilkan browser
- [ ] Variabel JS dengan tipe data yang tepat, operator, dan fungsi
- [ ] DOM: seleksi, update, toggle class, create, remove
- [ ] Event handler `click` dan `submit`, dengan `preventDefault()`
- [ ] `forEach`, `map`, `filter`, `reduce` -- keempatnya mengerjakan hal nyata

TypeScript & Tailwind:

- [ ] `tsconfig.json` benar, `tsc` kompilasi tanpa error
- [ ] `interface` / `type alias` untuk data produk
- [ ] **Union type** untuk nilai multi-keadaan
- [ ] Objek bersarang dan array bertipe benar
- [ ] Tailwind terpasang, utility class menggantikan CSS custom
- [ ] Tipografi Tailwind + layout responsif mobile-first
- [ ] Data bertipe dipetakan ke class Tailwind secara kondisional
- [ ] Katalog: render dari data, live search jalan, satu state update jalan

Repo:

- [ ] Tiga folder sesuai deliverable
- [ ] `README.md` menjelaskan isi tiap folder dan cara menjalankannya
- [ ] Minimal empat commit bertahap
- [ ] Tiga screenshot di `docs/`, nama file tanpa spasi
- [ ] `node_modules/` masuk `.gitignore`

---

## 7. Checkpoint 2 -- React Components & Next.js App Router

Di sinilah frontend RevoShop yang sebenarnya dimulai: scaffold Next.js, komponen
inti yang bisa dipakai ulang, routing berbasis file, dan **data sungguhan dari
API Module 2**.

Batas penting yang disebut brief: **form cukup terhubung ke state komponen
lokal.** `POST` / `PUT` / `DELETE` sungguhan, autentikasi, dan alur cart/checkout
baru dikerjakan di Checkpoint 3. Jadi `AddProductForm` di sini hanya menambah
item ke array di memori, bukan memanggil API.

### Struktur folder

```
module-3-jim1504/
├─ app/
│  ├─ layout.tsx              root layout: <Header /> + <Footer /> + metadata
│  ├─ page.tsx                home -- Server Component, 5 produk pertama
│  ├─ products/
│  │  ├─ layout.tsx           nested layout (tidak boleh re-render saat pindah ke [id])
│  │  ├─ page.tsx             Server Component -> <ProductList />
│  │  ├─ loading.tsx          skeleton
│  │  ├─ error.tsx            "use client", UI error ramah
│  │  └─ [id]/
│  │     └─ page.tsx          generateMetadata + detail produk
│  ├─ categories/
│  │  ├─ page.tsx             GET /categories
│  │  ├─ loading.tsx
│  │  └─ error.tsx
│  └─ orders/
│     ├─ page.tsx             GET /orders
│     ├─ loading.tsx
│     └─ error.tsx
├─ components/
│  ├─ Header.tsx              nav + active route via usePathname()
│  ├─ Footer.tsx
│  ├─ Card.tsx                wrapper generik
│  ├─ ProductCard.tsx         ProductCardProps, optional props, quantity counter
│  ├─ ProductGrid.tsx         .map() atas Product[]
│  ├─ ProductList.tsx         "use client" -- search + CategoryFilter + cart
│  ├─ SearchBar.tsx           controlled, onChange + router.push() saat Enter
│  ├─ CategoryFilter.tsx
│  └─ AddProductForm.tsx      controlled inputs + validate()
├─ lib/
│  ├─ api.ts                  base URL + wrapper fetch + cek res.ok
│  └─ types.ts                Product, Category, Order (lanjutan CP1)
├─ .env.local                 NEXT_PUBLIC_API_BASE_URL, API_SECRET_KEY
└─ docs/                      screenshot bukti
```

### Urutan pengerjaan

Tips brief-nya tepat: **selesaikan satu route sampai tuntas** (fetch, render,
loading, error) sebelum pindah ke route berikutnya. Empat commit besar sesuai
deliverable: scaffold -> components -> routing -> API integration.

**1. Scaffold.** `create-next-app` dengan TypeScript, Tailwind, dan App Router.
Pastikan `npm run dev` bersih tanpa error -- itu baris rubrik tersendiri.

**2. Komponen dari Checkpoint 1.** Pindahkan katalog CP1 menjadi komponen React.
Kalau `interface Product` di CP1 sudah mengikuti bentuk response API, tahap ini
sebagian besar tinggal memindahkan, bukan menulis ulang.

Yang dinilai per komponen:
- `ProductCardProps` sebagai interface tersendiri
- **optional props dengan default lewat destructuring** --
  `({ showBadge = true, onAddToCart }: ProductCardProps)`
- `Card` sebagai wrapper generik, `ProductCard` memakainya
- quantity counter di `ProductCard`
- `getButtonClasses(inStock: boolean): string` -- fungsi terpisah yang
  mengembalikan string kelas Tailwind berbeda untuk tersedia vs habis. Ini
  kelanjutan langsung dari "map typed data to Tailwind class" di CP1
- semua `ProductCard` hardcoded diganti **satu** `.map()` atas `Product[]`

**3. Routing dan layout.** Root `app/layout.tsx` membungkus `<Header />` dan
`<Footer />`, plus nested `app/products/layout.tsx`.

Rubrik minta **dibuktikan** bahwa nested layout tidak re-render saat pindah dari
`/products` ke `/products/[id]`. Cara paling gampang: taruh
`console.log("products layout render")` di layout itu, buka console, lalu
navigasi. Kalau log-nya tidak bertambah, layout-nya memang tetap ter-mount.
Simpan screenshot console-nya sebagai bukti.

`Header` memakai `usePathname()` untuk menandai route aktif -- ini butuh
`"use client"`.

**4. Integrasi API.** Baru di sini API dipanggil. Pola Server Component:

```tsx
// app/products/page.tsx -- tanpa "use client"
async function getProducts(): Promise<Product[]> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/products`);
  if (!res.ok) throw new Error(`Gagal memuat produk (${res.status})`);
  return res.json();
}
```

Tiga lapis error handling yang diminta rubrik:
1. cek `res.ok` yang **melempar** error bertipe
2. `app/products/error.tsx` yang menangkap lemparan itu (`"use client"`, terima
   props `error` dan `reset`)
3. `app/products/loading.tsx` yang menampilkan skeleton

Pembagian Server vs Client yang diminta:
- `app/products/page.tsx` -- **Server** Component, fetch awal
- `components/ProductList.tsx` -- **Client** (`"use client"`), terima
  `products: Product[]` sebagai prop dari parent Server, lalu menangani
  `SearchBar` (`router.push('/products?search=...')` saat Enter), `useEffect`
  yang membaca `useSearchParams()` dan fetch ulang tiap query berubah, serta
  `CategoryFilter` yang fetch `GET /categories` saat mount

Pola ini yang membuat **perbaikan backend di bagian 4 jadi syarat mutlak** --
`useEffect` di atas memanggil `GET /products?search=...` dari browser, jadi butuh
filter `search` **dan** CORS sekaligus.

**5. Metadata.** `metadata` export di root layout dan keempat route, plus
`generateMetadata({ params })` di `products/[id]/page.tsx` yang **fetch produknya
juga** dan memakai nama produk asli sebagai `<title>`.

### Deliverable Checkpoint 2

| # | Deliverable | Catatan |
| --- | --- | --- |
| 1 | Repo Next.js jalan tanpa error | `npm run dev` bersih |
| 2 | `components/` minimal 6 komponen TypeScript | Header, Footer, ProductCard, Card, SearchBar, AddProductForm |
| 3 | `app/` dengan 5 route | home, `/products`, `/products/[id]`, `/categories`, `/orders` |
| 4 | Commit history bertahap | scaffold -> components -> routing -> API |
| 5 | Screenshot home 5 produk asli dari API | `docs/home_products.png` |
| 6 | Screenshot live search + filter kategori | `docs/products_search_filter.png` |
| 7 | Screenshot detail produk + judul tab dinamis | `docs/product_detail.png` -- pastikan judul tab browser ikut terlihat |
| 8 | Screenshot active-route highlighting di nav | `docs/nav_active.png` |
| 9 | Screenshot `loading.tsx` dan `error.tsx` aktif | `docs/loading_state.png`, `docs/error_state.png` |

Cara memicu dua state terakhir: `loading` dengan Network throttling di DevTools
(Slow 3G), `error` dengan mengubah `NEXT_PUBLIC_API_BASE_URL` ke URL yang salah,
atau mematikan API. Ini deliverable tersendiri, jadi ambil screenshot-nya saat
sengaja dipicu.

---

## 8. Opsional -- hal-hal tingkat lanjut

**Tidak ada satu pun di bawah ini yang diminta rubrik.** Kerjakan hanya kalau
yang wajib sudah selesai. Diurutkan dari yang paling berguna.

### 8.1 Route Handler sebagai proxy (paling direkomendasikan)

Rubrik menyuruh menaruh `API_SECRET_KEY` di `.env` -- tanpa awalan
`NEXT_PUBLIC_`, artinya rahasia itu **hanya boleh hidup di server**. Tapi
`ProductList` adalah Client Component yang fetch dari browser, sehingga tidak
bisa memakainya.

Jalan keluarnya adalah Route Handler sebagai perantara:

```
app/api/products/route.ts   ->  meneruskan ke Flask, menyisipkan API_SECRET_KEY
```

Client Component memanggil `/api/products?search=...` (domain sendiri), Route
Handler meneruskannya ke Render sambil menambahkan header rahasia. Tiga
keuntungan sekaligus: rahasia tidak pernah sampai ke browser, **CORS jadi tidak
perlu** karena browser hanya bicara dengan domain Vercel, dan URL backend
tersembunyi. Ini pola BFF (backend for frontend) yang lazim dipakai di produksi.

### 8.2 Debounce pada live search

`useEffect` yang fetch di setiap perubahan query akan memanggil API pada tiap
ketukan huruf. Mengetik "intel" berarti lima request, dan yang terakhir belum
tentu tiba paling akhir. Tunda 300 ms dengan `setTimeout` + cleanup, dan batalkan
request lama dengan `AbortController`. Dua puluh baris, tapi menghilangkan
seluruh kelas bug balapan response.

### 8.3 Validasi bentuk response dengan Zod

`res.json()` bertipe `any`. TypeScript percaya begitu saja bahwa isinya
`Product[]`, padahal tidak ada yang menjaminnya saat runtime. Zod memeriksa
bentuknya sungguhan dan memberi tipe sekaligus:

```ts
const ProductSchema = z.object({ product_id: z.number(), /* ... */ });
const products = z.array(ProductSchema).parse(await res.json());
```

Kalau backend berubah bentuk, errornya muncul di titik fetch dengan pesan jelas,
bukan sebagai `undefined` misterius jauh di dalam komponen.

### 8.4 Strategi caching `fetch`

Next.js punya kontrol cache di level `fetch`:

```ts
fetch(url, { next: { revalidate: 60 } })   // ISR: segar tiap 60 detik
fetch(url, { cache: "no-store" })          // selalu segar
```

Berguna khusus untuk kasus ini: instance gratis Render tidur setelah 15 menit,
jadi request pertama bisa 50 detik. Halaman yang di-cache tetap tampil instan
untuk pengunjung meski API-nya sedang bangun. Sebutkan pilihannya di README --
menunjukkan paham trade-off kesegaran data lawan kecepatan.

### 8.5 `generateStaticParams` untuk halaman produk

Produknya hanya 20 dan jarang berubah. `generateStaticParams` membuat Next.js
mem-build ke-20 halaman detail saat build, sehingga tersaji sebagai HTML statis.
Sangat cepat, dan tidak menyentuh API sama sekali saat dikunjungi.

### 8.6 Parallel fetching dengan `Promise.all`

Kalau satu halaman butuh dua sumber (misalnya produk **dan** kategori), menulis
dua `await` berurutan membuat waktunya berjumlah. `Promise.all` menjadikannya
paralel:

```ts
const [products, categories] = await Promise.all([getProducts(), getCategories()]);
```

Perbedaannya terasa nyata di API yang sedang bangun dari tidur.

### 8.7 Skeleton yang sebentuk dengan konten aslinya

Kebanyakan orang mengisi `loading.tsx` dengan tulisan "Loading...". Skeleton yang
ukuran kartunya persis sama dengan kartu asli mencegah layout melompat saat data
tiba (*cumulative layout shift*). Murah dikerjakan, dan langsung terasa lebih
rapi.

### 8.8 Aksesibilitas pada hasil pencarian

Saat daftar tersaring, pengguna pembaca layar tidak tahu apa-apa telah berubah.
Bungkus jumlah hasil dengan `aria-live="polite"`:

```tsx
<p aria-live="polite">{filtered.length} produk ditemukan</p>
```

Satu atribut. Sekalian pastikan `SearchBar` punya `<label>` yang benar, meski
disembunyikan secara visual.

### 8.9 `not-found.tsx` untuk produk yang tidak ada

`/products/9999` sekarang akan melempar ke `error.tsx`, padahal itu bukan error
sistem melainkan "tidak ditemukan". Panggil `notFound()` dari `next/navigation`
saat API balas 404, lalu sediakan `app/products/[id]/not-found.tsx`. Membedakan
"rusak" dari "tidak ada" adalah tanda paham semantik HTTP.

### 8.10 Mulai Playwright lebih awal

Deliverable akhir Module 3 menuntut **suite Playwright E2E yang lulus terhadap
URL produksi Vercel**. Menulisnya di Checkpoint 3 dari nol itu berat. Menulis dua
tes kecil sekarang -- home menampilkan produk, search menyaring daftar -- membuat
setup-nya beres duluan, dan sisanya tinggal ditambah.

---

## 9. Urutan yang disarankan

1. **Sekarang:** Checkpoint 1, lima latihan fondasi (bagian 2)
2. **Sebelum Checkpoint 2:** perbaiki backend Module 2 (bagian 4a-4c) --
   tanpa ini tiga baris rubrik CP2 mustahil dipenuhi
3. **Checkpoint 2:** scaffold, komponen, routing, integrasi API (bagian 7)
4. **Kalau sempat:** ambil dari bagian 8, mulai dari 8.1 dan 8.2
