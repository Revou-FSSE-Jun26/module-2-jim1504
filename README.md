# Database RevoShop — Modul 2 Checkpoint 1

Repositori ini berisi skema, contoh data, dan query.
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
$env:Path += ";C:\Program Files\PostgreSQL\17\bin" --default folder
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

## File

| File | Fungsi |
| --- | --- |
| `schema.sql` | definisi tabel, constraint, dan index |
| `seed.sql` | data contoh untuk setiap tabel |
| `queries.sql` | contoh query, termasuk satu query yang menggabungkan `where`, `order by`, dan `limit` |
| `erd.png` | diagram skema yang menunjukkan semua tabel dan relasinya |

## Catatan

- Kata kunci SQL ditulis dengan huruf kecil dan identifier menggunakan `snake_case` secara konsisten.
- Setiap tabel menggunakan primary key surrogate `serial` bernama `<table_singular>_id`.
- Menghapus sebuah order juga menghapus order item-nya (`on delete cascade`). Produk dan user tidak ikut terhapus (cascade).
