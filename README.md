# RevoShop API

REST API untuk toko online sederhana: mengelola produk, kategori, pesanan, dan
akun pengguna, di atas PostgreSQL dengan SQLAlchemy sebagai ORM.

Proyek ini dikerjakan bertahap dalam tiga checkpoint:

| Checkpoint | Isi |
| --- | --- |
| 1 | desain database — `schema.sql`, `seed.sql`, `queries.sql` |
| 2 | lapisan Flask + SQLAlchemy — model, migration, route dasar |
| 3 | REST API lengkap — CRUD, validasi, pengujian, load test, deployment |

Mulai checkpoint 2, **sumber kebenaran skema adalah migration** di folder
`migrations/`. `schema.sql` tetap dijaga sinkron sebagai dokumentasi.

---

## Overview

RevoShop adalah backend untuk toko online. Sebuah **user** dapat membuat banyak
**order**; setiap order berisi banyak **product**; dan setiap product termasuk
dalam satu **category**. Hubungan antara order dan product bersifat
*many-to-many* dan disimpan di tabel asosiasi `order_items`, yang juga mencatat
jumlah dan harga saat pembelian.

| Tabel | Arti satu baris | Relasi utama |
| --- | --- | --- |
| `users` | satu akun pelanggan | satu user membuat banyak order |
| `categories` | satu kategori produk | satu kategori memiliki banyak produk |
| `products` | satu barang yang dijual | termasuk dalam satu kategori |
| `orders` | satu order milik satu user | memiliki banyak order item |
| `order_items` | satu baris produk di dalam satu order | junction `orders` ke `products` |

`order_items.unit_price` menyimpan harga yang dibayar **pada saat pembelian**,
sehingga order lama tetap memiliki total aslinya meskipun harga produk berubah
kemudian.

---

## Features implemented

### CRUD penuh untuk tiga modul

- **Products** — list, detail, create, update, delete
- **Categories** — list, detail beserta produk di dalamnya, create, update, delete
- **Orders** — list milik user, detail beserta item dan produknya, create, update, delete

### Relasi many-to-many

`orders` dan `products` dihubungkan lewat tabel asosiasi `order_items` yang
dideklarasikan dengan `db.Table()` di `models.py`. `POST /orders` menulis
langsung ke tabel tersebut sambil membekukan harga produk saat itu ke kolom
`unit_price`. `GET /orders/<id>` membaca kembali relasinya lewat join sehingga
setiap item tampil dengan nama produk dan subtotalnya.

Data contoh membuktikan relasinya dari **kedua arah**:

- satu order berisi banyak produk — order 2, 3, dan 5 masing-masing berisi 3 produk
- satu produk muncul di banyak order — produk 7 (`corsair vengeance ddr5 16gb`)
  ada di order 2 dan 3, produk 16 (`arctic p12 argb case fan`) ada di order 1 dan 5

Keduanya bisa diperiksa langsung lewat `GET /orders/<id>` atau dengan query:

```sql
select p.product_id, p.product_name, count(distinct oi.order_id) as jumlah_order
from products p
join order_items oi on oi.product_id = p.product_id
group by p.product_id, p.product_name
having count(distinct oi.order_id) > 1;
```

### Data validation

Setiap endpoint tulis memvalidasi input sebelum menyentuh database dan
mengembalikan `400` dengan pesan yang menyebut field bermasalah:

- field wajib harus ada dan tidak kosong
- `price` dan `stock_quantity` tidak boleh negatif
- `category_id` harus merujuk kategori yang benar-benar ada
- `order_status` harus salah satu dari lima status yang valid
- `items` pada order harus berupa daftar tidak kosong tanpa produk ganda

### Error handling

Semua operasi tulis dibungkus `try/except` dengan `db.session.rollback()` bila
gagal, sehingga transaksi tidak pernah tertinggal setengah jalan. Pelanggaran
`unique` dipetakan menjadi `409`, bukan `500`.

| Kode | Arti |
| --- | --- |
| `200` | berhasil |
| `201` | data baru dibuat |
| `400` | input tidak valid |
| `401` | kredensial salah |
| `404` | data tidak ditemukan |
| `409` | bentrok: duplikat, atau dihalangi oleh relasi |

### Deletion guard

`DELETE /products/<id>` **ditolak dengan `409`** bila produk masih terikat pada
order yang aktif, yaitu order berstatus `pending`, `paid`, atau `shipped`. Order
yang sudah `delivered` atau `cancelled` dianggap selesai dan tidak lagi
menghalangi penghapusan; baris `order_items` miliknya ikut dihapus dan
`total_amount` order tersebut dihitung ulang agar tetap konsisten.

`DELETE /categories/<id>` memakai penjagaan serupa: kategori yang masih memiliki
produk tidak bisa dihapus.

### Authentication

`POST /auth/login` memverifikasi password dengan `check_password_hash` dan
mengembalikan **JWT access token**. Password tidak pernah disimpan sebagai teks
biasa dan tidak pernah ikut dikirim dalam response.

Sesuai ketentuan modul, token **tidak diwajibkan**. Endpoint order menerima
identitas dari salah satu dari dua cara:

- header `Authorization: Bearer <token>`, atau
- `user_id` di body JSON atau query string

Keduanya menghasilkan response yang sama.

---

## Technologies used

| Teknologi | Kegunaan |
| --- | --- |
| **Flask** | framework web dan routing |
| **SQLAlchemy** | ORM dan query builder |
| **Flask-Migrate** | versioning skema database (Alembic) |
| **PostgreSQL** | basis data |
| **pgAdmin / DBeaver** | inspeksi database |
| **Flask-JWT-Extended** | pembuatan dan verifikasi access token |
| **pytest** | pengujian otomatis endpoint Category |
| **Locust** | simulasi beban 50 sampai 200 pengguna |
| **python-dotenv** | memuat konfigurasi dari `.env` |
| **gunicorn** | WSGI server di lingkungan deployment (Linux) |
| **waitress** | WSGI server untuk pengujian lokal di Windows |

---

## How to run the project locally

### 1. Clone

```powershell
git clone https://github.com/Revou-FSSE-Jun26/module-2-jim1504.git
cd module-2-jim1504
```

### 2. Virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Catatan: `requirements.txt` sengaja hanya berisi dependensi langsung. Jangan
membuatnya ulang dengan `pip freeze` di Windows — perintah itu ikut memasukkan
`pywin32`, yang tidak punya versi Linux dan akan menggagalkan proses build saat
deployment.

### 3. Konfigurasi

```powershell
Copy-Item .env.example .env
```

Isi `.env` dengan kredensial sendiri:

```
DATABASE_URL=postgresql://postgres:password_anda@localhost:5432/revoshop_db
TEST_DATABASE_URL=postgresql://postgres:password_anda@localhost:5432/revoshop_test_db
SECRET_KEY=hasil_dari_secrets_token_hex
FLASK_APP=app.py
FLASK_DEBUG=1
```

Membuat `SECRET_KEY` yang aman:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

`.env` sudah masuk `.gitignore`, jadi kredensial tidak pernah ikut ter-commit.

### 4. Database dan migration

```powershell
psql -U postgres -c "create database revoshop_db;"
flask db upgrade
python seed_db.py
```

`flask db upgrade` menjalankan ketiga migration secara berurutan dan membuat
kelima tabel. `seed_db.py` mengisi 6 user, 6 kategori, 20 produk (sparepart
komputer, harga dalam rupiah), 6 order, dan 15 order item.

Seluruh user hasil seed memakai password **`password123`**, sehingga
`POST /auth/login` bisa langsung dicoba.

### 5. Menjalankan aplikasi

```powershell
flask run
```

Aplikasi berjalan di `http://127.0.0.1:5000`.

### 6. Menjalankan test

```powershell
psql -U postgres -c "create database revoshop_test_db;"
pytest -v
```

Test memakai database terpisah (`TEST_DATABASE_URL`) sehingga data asli tidak
pernah tersentuh.

### 7. Menjalankan load test

```powershell
waitress-serve --port=5000 app:app
locust -f locustfile.py --host http://127.0.0.1:5000
```

Buka `http://localhost:8089`, mulai dengan 50 user (spawn rate 5/detik), lalu
naikkan sampai 200.

Gunakan `waitress`, bukan `flask run`, saat load test. Development server Flask
tidak dirancang untuk ratusan koneksi bersamaan, sehingga angkanya akan mengukur
keterbatasan server, bukan performa API.

---

## API Endpoints

Base URL lokal: `http://127.0.0.1:5000`

### User

| Method | Endpoint | Keterangan |
| --- | --- | --- |
| `POST` | `/users` | mendaftarkan user baru |
| `POST` | `/auth/login` | login, mengembalikan access token |
| `GET` | `/users/<id>` | detail satu user |

### Product

| Method | Endpoint | Keterangan |
| --- | --- | --- |
| `GET` | `/products` | seluruh produk |
| `GET` | `/products/<id>` | satu produk |
| `POST` | `/products` | membuat produk, dengan validasi |
| `PUT` | `/products/<id>` | memperbarui produk, dengan validasi |
| `DELETE` | `/products/<id>` | menghapus produk, ditolak bila ada order aktif |

### Category

| Method | Endpoint | Keterangan |
| --- | --- | --- |
| `GET` | `/categories` | seluruh kategori |
| `GET` | `/categories/<id>` | satu kategori beserta produknya |
| `POST` | `/categories` | membuat kategori |
| `PUT` | `/categories/<id>` | memperbarui kategori |
| `DELETE` | `/categories/<id>` | menghapus kategori, ditolak bila masih ada produk |

### Order

| Method | Endpoint | Keterangan |
| --- | --- | --- |
| `GET` | `/orders` | order milik user (token atau `?user_id=`) |
| `GET` | `/orders/<id>` | detail order beserta item dan produknya |
| `POST` | `/orders` | membuat order baru |
| `PUT` | `/orders/<id>` | memperbarui status atau alamat kirim |
| `DELETE` | `/orders/<id>` | menghapus order beserta itemnya |

### Utility

| Method | Endpoint | Keterangan |
| --- | --- | --- |
| `GET` | `/health` | memastikan koneksi database hidup |

### Contoh request

Membuat order:

```json
POST /orders
{
    "user_id": 1,
    "shipping_address": "jl. merdeka no. 12, bandung",
    "items": [
        { "product_id": 1, "quantity": 2 },
        { "product_id": 3, "quantity": 1 }
    ]
}
```

Login:

```json
POST /auth/login
{
    "email": "andi.pratama@example.com",
    "password": "password123"
}
```

---

## Struktur proyek

```
app.py              aplikasi Flask, konfigurasi dari .env, registrasi blueprint
models.py           model SQLAlchemy dan tabel asosiasi order_items
routes/
  __init__.py       register_blueprints(app)
  helpers.py        validasi, format error, resolusi identitas
  products.py       CRUD produk
  categories.py     CRUD kategori
  orders.py         CRUD order
  users.py          registrasi, login, detail user
tests/
  conftest.py       fixture pytest, memakai database terpisah
  test_categories.py  13 test: happy path dan error case
migrations/         riwayat migration Flask-Migrate
seed_db.py          memuat data contoh lewat SQLAlchemy
locustfile.py       skenario load test
Procfile            perintah start untuk deployment
```

Konfigurasi, model, dan route berada di file terpisah.

---

## Migration

| Urutan | Nama | Isi |
| --- | --- | --- |
| 1 | `initial revoshop schema` | membuat `users`, `categories`, `products`, `orders` |
| 2 | `add order_items association table` | membuat tabel asosiasi `order_items` |
| 3 | `add role column to users` | menambah kolom `role` ke `users` |

Kolom `role` dibuat `not null` dengan `server default 'customer'`, sehingga bisa
ditambahkan ke tabel yang **sudah berisi data** tanpa mengganggu baris lama.

```powershell
flask db history
flask db current
```

Checkpoint 3 tidak menambah migration baru — skema dari checkpoint 2 sudah
memenuhi kebutuhan seluruh endpoint.

---

## Deployment

Aplikasi siap dideploy ke platform mana pun yang menjalankan aplikasi WSGI:

1. Buat instance PostgreSQL terkelola di platform pilihan.
2. Set environment variable: `DATABASE_URL`, `SECRET_KEY`, `FLASK_DEBUG=0`.
   Jangan pernah meng-commit nilainya.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app` (sudah tersedia di `Procfile`).
5. Jalankan `flask db upgrade` **terhadap database hosting**, bukan hanya lokal.
6. Uji ulang seluruh CRUD di Postman memakai URL publik.

---

## Screenshots

| Bukti | File |
| --- | --- |
| Rekaman Postman | [`postman/Postman_trial.mp4`](postman/Postman_trial.mp4) |
| Koleksi Postman | [`postman/RevoShop - Module 2 Checkpoint 2.postman_collection.json`](postman/RevoShop%20-%20Module%202%20Checkpoint%202.postman_collection.json) |
| Tabel `users` di DBeaver | [`docs/C2_userdbScreenshoot.png`](docs/C2_userdbScreenshoot.png) |

![Tabel users dengan kolom role](docs/C2_userdbScreenshoot.png)

Screenshot di atas menunjukkan kolom `role` hasil migration, keenam user hasil
seed yang tetap utuh, dan satu user tambahan hasil `POST` yang password-nya
tersimpan sebagai hash `scrypt:...`.

---

## Catatan

- Kata kunci SQL ditulis huruf kecil, identifier memakai `snake_case`.
- Tabel `users` memakai `id` dan `username`; tabel lain memakai pola
  `<table_singular>_id`.
- Menghapus order juga menghapus order item-nya (`on delete cascade`).
- Password tidak pernah disimpan sebagai teks biasa dan tidak pernah dikirim
  dalam response.
## Diagram relasi

```mermaid
erDiagram
    users ||--o{ orders : "membuat"
    categories ||--o{ products : "memiliki"
    orders ||--o{ order_items : "berisi"
    products ||--o{ order_items : "muncul di"

    users {
        serial id PK
        varchar username
        varchar email UK
        varchar password_hash
        varchar phone_number
        text address
        timestamp created_at
        varchar role
    }
    categories {
        serial category_id PK
        varchar category_name UK
        text description
        timestamp created_at
    }
    products {
        serial product_id PK
        integer category_id FK
        varchar product_name
        text description
        numeric price
        integer stock_quantity
        boolean is_active
        timestamp created_at
    }
    orders {
        serial order_id PK
        integer user_id FK
        varchar order_status
        numeric total_amount
        text shipping_address
        timestamp ordered_at
    }
    order_items {
        serial order_item_id PK
        integer order_id FK
        integer product_id FK
        integer quantity
        numeric unit_price
    }
```
