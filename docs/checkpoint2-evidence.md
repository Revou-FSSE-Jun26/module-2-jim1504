# Checkpoint 2 — Daftar Bukti (Screenshot)

Semua kode dan migration sudah siap. Yang tersisa adalah mengambil screenshot.
Urutannya sudah diatur supaya bisa dikerjakan sekali jalan.

## Persiapan

```powershell
# 1. aktifkan virtualenv
.\venv\Scripts\Activate.ps1

# 2. pastikan database sudah terisi
flask db upgrade
python seed_db.py

# 3. jalankan aplikasi (biarkan terminal ini terbuka)
flask run
```

Lalu di Postman: **Import** → pilih `postman/RevoShop.postman_collection.json`.
Semua request sudah tersedia, tinggal klik **Send**.

---

## A. Bukti Postman (aplikasi berjalan lokal)

| # | Request | Yang harus terlihat | Status |
| --- | --- | --- | --- |
| 1 | `GET /products` | seluruh list produk hardcoded sebagai JSON | ☐ |
| 2 | `GET /products/2` | satu produk hasil filter berdasarkan id | ☐ |
| 3 | `GET /products/999` | HTTP 404 + body JSON `product not found` | ☐ |
| 4 | `POST /register` | HTTP 201 + data user baru (tanpa password_hash) | ☐ |
| 5 | `GET /users/1` | HTTP 200 + data user dari database | ☐ |
| 6 | `GET /users/9999` | HTTP 404 + body JSON `user not found` | ☐ |

Pastikan **status code** dan **response body** terlihat jelas di screenshot.

> Catatan: request `POST /register` memakai email `jim.demo@example.com`.
> Kalau sudah pernah dikirim, ganti emailnya dulu, atau pakai request
> *duplicate email* untuk menunjukkan penanganan HTTP 409.

## B. Bukti pgAdmin (database)

| # | Yang dicek | Cara | Status |
| --- | --- | --- | --- |
| 7 | kolom `role` ada di tabel `users` | pgAdmin → `revoshop_db` → Schemas → public → Tables → `users` → Columns | ☐ |
| 8 | baris lama tidak terganggu | jalankan query di bawah, harus tetap 6 baris dan semua `role = 'customer'` | ☐ |
| 9 | tabel `order_items` ada | Tables → `order_items` → Columns (ada `order_id` dan `product_id` sebagai foreign key) | ☐ |
| 10 | satu order terhubung ke banyak produk | jalankan query many-to-many di bawah | ☐ |

### Query untuk bukti nomor 8

```sql
select id, username, email, role, created_at
from users
order by id;
```

### Query untuk bukti nomor 10

```sql
select
    orders.order_id,
    users.username,
    products.product_name,
    order_items.quantity,
    order_items.unit_price
from orders
join users       on users.id = orders.user_id
join order_items on order_items.order_id = orders.order_id
join products    on products.product_id = order_items.product_id
where orders.order_id = 2
order by products.product_name;
```

Order 2 berisi 3 produk berbeda — ini yang membuktikan relasi many-to-many bekerja.

## C. Bukti riwayat migration

```powershell
flask db history
flask db current
```

Harus terlihat tiga migration berurutan:

1. `initial revoshop schema` — membuat `users`, `categories`, `products`, `orders`
2. `add order_items association table` — membuat tabel asosiasi
3. `add role column to users` — menambah kolom `role`

Screenshot output kedua perintah ini juga berguna sebagai bukti tambahan.

## D. Yang masih perlu dikerjakan manual

- [ ] **Export ulang `erd.png`** dari DBeaver/pgAdmin. Diagram lama masih memakai
      `user_id` dan `full_name`, sedangkan sekarang sudah menjadi `id` dan
      `username`, ditambah kolom `role`. Diagram versi teks yang sudah diperbarui
      ada di `README.md`.
- [ ] Push ke GitHub dan pastikan seluruh commit ikut terkirim.
