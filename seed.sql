
-- users
--password tidak disimpan dalam bentuk teks biasa, tapi dalam bentuk hash
insert into users (username, email, password_hash, phone_number, address) values
    ('andi pratama',    'andi.pratama@example.com',   '$2b$12$fakehashvalue000000001', '+62-812-1111-0001', 'jl. merdeka no. 12, bandung, west java 40115'),
    ('siti rahayu',     'siti.rahayu@example.com',    '$2b$12$fakehashvalue000000002', '+62-813-2222-0002', 'jl. sudirman no. 45, jakarta 10210'),
    ('budi santoso',    'budi.santoso@example.com',   '$2b$12$fakehashvalue000000003', '+62-856-3333-0003', 'jl. diponegoro no. 8, surabaya 60241'),
    ('dewi lestari',    'dewi.lestari@example.com',   '$2b$12$fakehashvalue000000004', '+62-877-4444-0004', 'jl. malioboro no. 21, yogyakarta 55213'),
    ('rizky ramadhan',  'rizky.ramadhan@example.com', '$2b$12$fakehashvalue000000005', '+62-819-5555-0005', 'jl. gatot subroto no. 3, medan 20112'),
    ('maya kusuma',     'maya.kusuma@example.com',    '$2b$12$fakehashvalue000000006', null,                'jl. pahlawan no. 77, semarang 50241');



insert into categories (category_name, description) values
    ('electronics',        'gadgets, computer accessories and audio gear'),
    ('home and kitchen',   'everyday items for cooking and the household'),
    ('books',              'printed books on programming and technology'),
    ('fashion',            'clothing and wearable accessories'),
    ('sports and outdoors','equipment for training, yoga and outdoor trips');


-- ---------------------------------------------------------------
-- products
-- category_id 
--      1 = electronics
--      2 = home and kitchen
--      3 = books
--      4 = fashion 
--      5 = sports and outdoors
-- ---------------------------------------------------------------

insert into products (category_id, product_name, description, price, stock_quantity, is_active) values
    (1, 'wireless mouse',              'silent 2.4 ghz mouse with usb receiver',        18.50, 120, true),
    (1, 'mechanical keyboard',         'tenkeyless board with brown switches',          79.99,  45, true),
    (1, 'usb-c hub 7 in 1',            'hdmi, sd card reader and three usb-a ports',    42.00,  60, true),
    (1, 'noise cancelling headphones', 'over-ear bluetooth headphones, 30 hour battery',199.00,  25, true),
    (2, 'ceramic coffee mug 350ml',    'dishwasher safe mug, matte finish',              9.75, 200, true),
    (2, 'stainless steel french press','800ml double wall coffee press',                34.90,  38, true),
    (2, 'bamboo cutting board',        'large board with juice groove',                 22.40,  75, true),
    (3, 'clean code',                  'a handbook of agile software craftsmanship',    38.25,  30, true),
    (3, 'the pragmatic programmer',    'classic guide for working developers',          45.00,  18, true),
    (3, 'sql for beginners',           'hands-on introduction to relational databases', 27.60,  52, true),
    (4, 'cotton t-shirt black',        'unisex combed cotton, sizes s to xxl',          14.99, 150, true),
    (4, 'denim jacket',                'mid-wash jacket with two chest pockets',        64.50,  22, true),
    (5, 'yoga mat 6mm',                'non-slip tpe mat with carrying strap',          29.95,  64, true),
    (5, 'stainless water bottle 1l',   'vacuum insulated bottle, keeps cold 24 hours',  19.20,  90, false);


-- ---------------------------------------------------------------
-- orders
-- user_id mengacu ke user yang melakukan order
-- order_status bisa berupa: pending, paid, shipped, delivered, cancelled
-- shipping_address adalah alamat tujuan pengiriman, bisa berbeda dengan alamat user
-- ordered_at adalah tanggal dan jam order dibuat

insert into orders (user_id, order_status, shipping_address, ordered_at) values
    (1, 'delivered', 'jl. merdeka no. 12, bandung, west java 40115', '2026-05-04 09:15:00'),
    (2, 'shipped',   'jl. sudirman no. 45, jakarta 10210',           '2026-05-11 14:02:00'),
    (1, 'paid',      'jl. merdeka no. 12, bandung, west java 40115', '2026-06-01 19:47:00'),
    (3, 'pending',   'jl. diponegoro no. 8, surabaya 60241',         '2026-06-18 08:30:00'),
    (4, 'delivered', 'jl. malioboro no. 21, yogyakarta 55213',       '2026-07-02 11:20:00'),
    (5, 'cancelled', 'jl. gatot subroto no. 3, medan 20112',         '2026-07-15 16:05:00');


-- ---------------------------------------------------------------
-- order_items
-- Berikut adalah tabel junction, jadi satu order bisa memuat banyak produk dan satu produk bisa muncul di banyak order
-- order_id adalah id order yang mengacu ke tabel orders
-- product_id adalah id produk yang mengacu ke tabel products

insert into order_items (order_id, product_id, quantity, unit_price) values
    (1,  2, 1,  79.99),
    (1,  1, 2,  18.50),
    (2,  8, 1,  38.25),
    (2, 10, 1,  27.60),
    (2,  9, 1,  45.00),
    (3,  4, 1, 199.00),
    (3,  3, 1,  42.00),
    (4,  5, 4,   9.75),
    (4,  6, 1,  34.90),
    (5, 13, 1,  29.95),
    (5, 14, 2,  19.20),
    (5, 11, 3,  14.99),
    (6, 12, 1,  64.50);


-- ---------------------------------------------------------------
-- isi total_amount di tabel orders dengan menjumlahkan semua order_items yang terkait
-- coalesce digunakan untuk mengubah nilai null menjadi 0, sehingga jika tidak ada order_items terkait, total_amount akan menjadi 0

update orders
set total_amount = (
    select coalesce(sum(order_items.quantity * order_items.unit_price), 0)
    from order_items
    where order_items.order_id = orders.order_id
);
