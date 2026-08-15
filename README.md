# RevoShop — Modul 2

Repositori ini berisi database RevoShop beserta lapisan aplikasinya.

| Checkpoint | Isi |
| --- | --- |
| Checkpoint 1 | skema database, contoh data, dan query (`schema.sql`, `seed.sql`, `queries.sql`) |
| Checkpoint 2 | aplikasi Flask + SQLAlchemy, model, dan migration (`app/`, `migrations/`) |

Mulai checkpoint 2, **sumber kebenaran skema adalah migration** di folder
`migrations/`. `schema.sql` tetap dijaga sinkron sebagai dokumentasi.

## Tabel

| Tabel | Arti satu baris | Relasi utama |
| --- | --- | --- |
| `users` | satu akun pelanggan | satu user membuat banyak order |
| `categories` | satu kategori produk | satu kategori memiliki banyak produk |
| `products` | satu barang yang dijual | termasuk dalam satu kategori |
| `orders` | satu order yang dibuat oleh satu user | termasuk satu user, memiliki banyak order item |
| `order_items` | satu baris produk di dalam satu order | tabel junction antara `orders` dan `products` |

`orders` dan `products` memiliki relasi many-to-many: satu order bisa berisi banyak
produk, dan satu produk bisa muncul di banyak order. `order_items` adalah tabel
junction yang memungkinkan hal ini, menggunakan `order_id` dan `product_id` sebagai foreign key.

`order_items.unit_price` menyimpan harga yang dibayar pada saat pembelian, sehingga
order lama tetap memiliki total aslinya meskipun harga produk berubah kemudian.

## Kebutuhan

- PostgreSQL
- SQL client — command line `psql`, DBeaver, atau pgAdmin

## Instalasi

### 1. Membuat database

Dari PowerShell:

```powershell
psql -U postgres -c "create database revoshop_db;"
```

Masukkan password untuk superuser `postgres` saat diminta.

Jika PowerShell melaporkan bahwa `psql` tidak dikenali, tambahkan folder `bin`
PostgreSQL ke PATH untuk sesi saat ini:

```powershell
# sesuaikan angka versinya dengan PostgreSQL yang terpasang
$env:Path += ";C:\Program Files\PostgreSQL\18\bin"
```

### 2. Memuat skema

```powershell
psql -U postgres -d revoshop_db -f schema.sql
```

Ini membuat kelima tabel beserta primary key, foreign key, check constraint, dan index-nya. Skrip ini diawali dengan `drop table if exists`, sehingga aman untuk dijalankan ulang — skema akan dibangun ulang dari awal dan data yang ada akan hilang.

### 3. Memuat data contoh

```powershell
psql -U postgres -d revoshop_db -f seed.sql
```

Ini menambahkan 6 user, 5 kategori, 14 produk, 6 order, dan 13 order item, lalu menghitung total setiap order dari item-item di dalamnya.

### 4. Menjalankan contoh query

```powershell
psql -U postgres -d revoshop_db -f queries.sql
```

## Memverifikasi hasil load

```powershell
psql -U postgres -d revoshop_db -c "select count(*) from products;"
```

Hasil yang diharapkan: 14.

---

# Checkpoint 2 — Aplikasi Flask & SQLAlchemy

## Kebutuhan tambahan

- Python 3.11 atau lebih baru (dikembangkan dengan Python 3.14)
- PostgreSQL yang sudah berjalan, dengan database `revoshop_db`

## Instalasi

### 1. Virtualenv dan dependensi

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Konfigurasi koneksi

Koneksi database diatur di `app.py`. Sesuaikan user dan password PostgreSQL
milik sendiri pada baris berikut:

```python
# Format: postgresql://user:password@host:port/dbname
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:root@localhost:5432/revoshop_db"
```

Salin juga `.env.example` menjadi `.env` untuk pengaturan Flask:

```powershell
Copy-Item .env.example .env
```

Isi `.env`:

```
FLASK_APP=app.py
FLASK_DEBUG=1
```

### 3. Membangun skema lewat migration

```powershell
flask db upgrade
```

Perintah ini menjalankan ketiga migration secara berurutan dan membuat kelima tabel.

### 4. Memuat data contoh

```powershell
python seed_db.py
```

Hasilnya sama dengan `seed.sql`: 6 user, 5 kategori, 14 produk, 6 order, 13 order item.

### 5. Menjalankan aplikasi

```powershell
flask run
```

Aplikasi berjalan di `http://127.0.0.1:5000`.

## Route

| Method | Route | Sumber data | Keterangan |
| --- | --- | --- | --- |
| `GET` | `/health` | database | menjalankan `select 1`, membuktikan koneksi hidup |
| `GET` | `/products` | hardcoded | seluruh produk sebagai JSON |
| `GET` | `/products/<id>` | hardcoded | satu produk, `404` bila tidak ada |
| `POST` | `/register` | database | membuat user baru, `400` bila field kurang, `409` bila email sudah dipakai |
| `GET` | `/users/<id>` | database | satu user, `404` bila tidak ada |

Route produk sengaja masih memakai data hardcoded — sesuai lingkup checkpoint 2
route tersebut adalah latihan pemanasan. Versi yang membaca database dikerjakan
di checkpoint 3.

Koleksi Postman siap pakai tersedia di `postman/RevoShop.postman_collection.json`.

## Struktur file

```
app.py              aplikasi Flask, konfigurasi, db.init_app(app), Migrate(app, db)
models.py           db = SQLAlchemy(), model User, Category, Product, Order,
                    dan tabel asosiasi order_items
routes.py           blueprint product_routes (hardcoded) dan user_routes (database)
migrations/         riwayat migration Flask-Migrate
seed_db.py          memuat data contoh lewat SQLAlchemy
demo_m2m.py         demonstrasi relasi many-to-many orders <-> products
```

Konfigurasi, model, dan route berada di file terpisah. `SQLALCHEMY_DATABASE_URI`
diatur di `app.py`.

## Migration

Tiga migration, dijalankan berurutan:

| Urutan | Nama | Isi |
| --- | --- | --- |
| 1 | `initial revoshop schema` | membuat `users`, `categories`, `products`, `orders` |
| 2 | `add order_items association table` | membuat tabel asosiasi `order_items` |
| 3 | `add role column to users` | menambah kolom `role` ke `users` |

Kolom `role` dibuat `not null` dengan `server default 'customer'`. Karena itu
kolom bisa ditambahkan ke tabel yang **sudah berisi data** tanpa mengganggu baris
lama — keenam user hasil seed tetap utuh dan otomatis terisi `customer`.

Melihat riwayatnya:

```powershell
flask db history
flask db current
```

## Relasi many-to-many

`orders` dan `products` dihubungkan lewat tabel asosiasi `order_items` yang
dideklarasikan dengan `db.Table()` di `models.py`. Tabel ini tetap
menyimpan `quantity` dan `unit_price` seperti rancangan checkpoint 1, sehingga
harga saat pembelian tetap tercatat.

```powershell
python demo_m2m.py
```

Script tersebut membaca relasi dari kedua arah (`order.products` dan
`product.orders`) lalu membuat order baru dengan cara `order.products.append(...)`.

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

## File

| File | Fungsi |
| --- | --- |
| `schema.sql` | definisi tabel, constraint, dan index (referensi, disinkronkan dengan migration) |
| `seed.sql` | data contoh untuk setiap tabel |
| `queries.sql` | contoh query, termasuk satu query yang menggabungkan `where`, `order by`, dan `limit` |
| `erd.png` | diagram skema versi gambar |
| `requirements.txt` | dependensi Python |
| `app.py` | aplikasi Flask dan konfigurasi koneksi |
| `models.py` | model SQLAlchemy dan tabel asosiasi `order_items` |
| `routes.py` | seluruh route aplikasi |
| `migrations/` | riwayat migration Flask-Migrate |
| `postman/` | koleksi Postman untuk semua route |

## Catatan

- Menghapus sebuah order juga menghapus order item-nya (`on delete cascade`). Produk dan user tidak ikut terhapus (cascade).
- Password tidak pernah disimpan sebagai teks biasa.
