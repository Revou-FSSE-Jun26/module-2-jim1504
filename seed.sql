-- Data contoh RevoShop: katalog sparepart komputer, harga dalam rupiah (IDR).
--
-- File ini dijaga sinkron dengan seed_db.py. Keduanya memuat data yang sama;
-- gunakan salah satu, tidak perlu dua-duanya.

-- users
-- password tidak disimpan sebagai teks biasa, tapi sebagai hash.
-- catatan: hash di bawah adalah placeholder. Untuk mencoba POST /auth/login,
-- muat data lewat `python seed_db.py`, yang menghasilkan hash scrypt asli.
insert into users (username, email, password_hash, phone_number, address) values
    ('andi pratama', 'andi.pratama@example.com', 'placeholder-load-via-seed_db.py', '+62-812-1111-0001', 'jl. merdeka no. 12, bandung, west java 40115'),
    ('siti rahayu', 'siti.rahayu@example.com', 'placeholder-load-via-seed_db.py', '+62-813-2222-0002', 'jl. sudirman no. 45, jakarta 10210'),
    ('budi santoso', 'budi.santoso@example.com', 'placeholder-load-via-seed_db.py', '+62-856-3333-0003', 'jl. diponegoro no. 8, surabaya 60241'),
    ('dewi lestari', 'dewi.lestari@example.com', 'placeholder-load-via-seed_db.py', '+62-877-4444-0004', 'jl. malioboro no. 21, yogyakarta 55213'),
    ('rizky ramadhan', 'rizky.ramadhan@example.com', 'placeholder-load-via-seed_db.py', '+62-819-5555-0005', 'jl. gatot subroto no. 3, medan 20112'),
    ('maya kusuma', 'maya.kusuma@example.com', 'placeholder-load-via-seed_db.py', null, 'jl. pahlawan no. 77, semarang 50241');


-- categories
insert into categories (category_name, description) values
    ('processors', 'cpu desktop intel dan amd'),
    ('motherboards', 'mainboard untuk soket lga dan am5'),
    ('memory and storage', 'ram, ssd nvme, ssd sata, dan hard disk'),
    ('graphics cards', 'kartu grafis untuk gaming dan rendering'),
    ('power and cooling', 'power supply, pendingin cpu, fan, dan thermal paste'),
    ('peripherals', 'mouse, keyboard, dan monitor');


-- ---------------------------------------------------------------
-- products
-- category_id
--      1 = processors
--      2 = motherboards
--      3 = memory and storage
--      4 = graphics cards
--      5 = power and cooling
--      6 = peripherals
-- harga dalam rupiah (IDR)
-- ---------------------------------------------------------------

insert into products (category_id, product_name, description, price, stock_quantity, is_active) values
    (1, 'intel core i5-14400f', '10 core, 16 thread, soket lga1700', 2850000.00, 25, true),
    (1, 'intel core i7-14700k', '20 core, 28 thread, unlocked, soket lga1700', 6450000.00, 12, true),
    (1, 'amd ryzen 7 7800x3d', '8 core dengan 3d v-cache, soket am5', 6900000.00, 8, true),
    (2, 'asus prime b760m-a', 'micro atx, ddr5, soket lga1700', 2150000.00, 20, true),
    (2, 'msi mag b650 tomahawk wifi', 'atx, ddr5, wifi 6e, soket am5', 3250000.00, 14, true),
    (2, 'gigabyte h610m h ddr4', 'micro atx hemat biaya, soket lga1700', 1350000.00, 30, true),
    (3, 'corsair vengeance ddr5 16gb', '5600 mhz, kit 1x16gb', 850000.00, 45, true),
    (3, 'kingston fury beast ddr4 16gb', '3200 mhz, kit 1x16gb', 620000.00, 50, true),
    (3, 'samsung 980 pro nvme 1tb', 'pcie 4.0, baca hingga 7000 mb per detik', 1450000.00, 35, true),
    (3, 'seagate barracuda hdd 2tb', 'sata 3.5 inci, 7200 rpm', 950000.00, 22, true),
    (4, 'nvidia geforce rtx 4060 8gb', 'gddr6, dukungan dlss 3', 5200000.00, 10, true),
    (4, 'nvidia geforce rtx 4070 super 12gb', 'gddr6x, untuk gaming 1440p', 9800000.00, 6, true),
    (4, 'amd radeon rx 7600 8gb', 'gddr6, arsitektur rdna 3', 4350000.00, 9, true),
    (5, 'corsair rm650e 650w 80 plus gold', 'full modular, sertifikasi gold', 1250000.00, 16, true),
    (5, 'deepcool ak400 cpu cooler', 'single tower, empat heat pipe', 450000.00, 28, true),
    (5, 'arctic p12 argb case fan', '120 mm, static pressure tinggi', 135000.00, 60, true),
    (5, 'thermal grizzly kryonaut 1g', 'thermal paste konduktivitas tinggi', 185000.00, 40, true),
    (6, 'logitech g502 hero gaming mouse', 'sensor hero 25k, 11 tombol', 685000.00, 33, true),
    (6, 'keychron k8 pro mechanical keyboard', 'tenkeyless, hot swappable, bluetooth', 1750000.00, 15, true),
    (6, 'lg ultragear 24gn60r 144hz monitor', '24 inci, ips, 1 ms -- stok lama', 2650000.00, 7, false);


-- ---------------------------------------------------------------
-- orders
-- user_id mengacu ke user yang melakukan order
-- order_status bisa berupa: pending, paid, shipped, delivered, cancelled
-- shipping_address adalah alamat tujuan pengiriman, bisa berbeda dengan alamat user
-- ordered_at adalah tanggal dan jam order dibuat

insert into orders (user_id, order_status, shipping_address, ordered_at) values
    (1, 'delivered', 'jl. merdeka no. 12, bandung, west java 40115', '2026-05-04 09:15:00'),
    (2, 'shipped', 'jl. sudirman no. 45, jakarta 10210', '2026-05-11 14:02:00'),
    (1, 'paid', 'jl. merdeka no. 12, bandung, west java 40115', '2026-06-01 19:47:00'),
    (3, 'pending', 'jl. diponegoro no. 8, surabaya 60241', '2026-06-18 08:30:00'),
    (4, 'delivered', 'jl. malioboro no. 21, yogyakarta 55213', '2026-07-02 11:20:00'),
    (5, 'cancelled', 'jl. gatot subroto no. 3, medan 20112', '2026-07-15 16:05:00');


-- ---------------------------------------------------------------
-- order_items adalah tabel junction: satu order memuat banyak produk,
-- dan satu produk bisa muncul di banyak order.
-- unit_price membekukan harga saat pembelian.
--
-- produk 7 muncul di order 2 dan 3; produk 16 di order 1 dan 5.

insert into order_items (order_id, product_id, quantity, unit_price) values
    ( 1, 16, 2, 135000.00),
    ( 1, 17, 1, 185000.00),
    ( 2,  1, 1, 2850000.00),
    ( 2,  4, 1, 2150000.00),
    ( 2,  7, 2, 850000.00),
    ( 3,  7, 1, 850000.00),
    ( 3, 11, 1, 5200000.00),
    ( 3, 14, 1, 1250000.00),
    ( 4, 18, 1, 685000.00),
    ( 4, 19, 1, 1750000.00),
    ( 5,  9, 2, 1450000.00),
    ( 5, 15, 1, 450000.00),
    ( 5, 16, 1, 135000.00),
    ( 6, 20, 1, 2650000.00),
    ( 6, 10, 1, 950000.00);


-- ---------------------------------------------------------------
-- isi total_amount dengan menjumlahkan seluruh order_items terkait.
-- coalesce mengubah null menjadi 0 bila sebuah order belum punya item.

update orders
set total_amount = (
    select coalesce(sum(order_items.quantity * order_items.unit_price), 0)
    from order_items
    where order_items.order_id = orders.order_id
);
