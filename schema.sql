-- Referensi skema RevoShop.
--
-- Mulai checkpoint 2, sumber kebenaran skema adalah migration Flask-Migrate di
-- folder migrations/. File ini dijaga tetap sinkron dengan hasil akhir
-- `flask db upgrade` sebagai dokumentasi dan untuk keperluan checkpoint 1.
--
-- Perubahan di checkpoint 2:
--   users.user_id   -> users.id
--   users.full_name -> users.username
--   users.role      ditambahkan lewat migration
--
--dibuat drop agar tidak ada error saat menjalankan ulang script ini

drop table if exists order_items;
drop table if exists orders;
drop table if exists products;
drop table if exists categories;
drop table if exists users;


create table users (
    id            serial       primary key,                          -- tipe data serial dan dijadikan primary key
    username      varchar(100) not null,                             -- tipe data varchar(100) dan tidak boleh null
    email         varchar(150) not null unique,                      -- tipe data varchar(150) dan tidak boleh null serta harus unik
    password_hash varchar(255) not null,                             -- tipe data varchar(255) dan tidak boleh null
    phone_number  varchar(20),                                       -- tipe data varchar(20)
    address       text,                                              -- memakai tipe data text
    created_at    timestamp    not null default current_timestamp,   -- tipe data timestamp dan defaultnya adalah current_timestamp
    role          varchar(20)  not null default 'customer'           -- ditambahkan di checkpoint 2 lewat migration
);


create table categories (
    category_id   serial       primary key,                         -- tipe data serial dan dijadikan primary key
    category_name varchar(100) not null unique,                     -- tipe data varchar(100) dan tidak boleh null serta harus unik 
    description   text,                                             -- memakai tipe data text
    created_at    timestamp    not null default current_timestamp   -- tipe data timestamp dan defaultnya adalah current_timestamp
);



-- products (one-to-many with categories)
create table products (
    product_id     serial         primary key,                         -- tipe data serial dan dijadikan primary key
    category_id    integer        not null,                            -- tipe data integer dan tidak boleh null
    product_name   varchar(150)   not null,                            -- tipe data varchar(150) dan tidak boleh null
    description    text,                                               -- memakai tipe data text
    price          numeric(12, 2) not null,                            -- tipe data numeric(12, 2) dan tidak boleh null
    stock_quantity integer        not null default 0,                  -- tipe data integer dan tidak boleh null dengan default 0
    is_active      boolean        not null default true,               -- tipe data boolean dan tidak boleh null dengan default true
    created_at     timestamp      not null default current_timestamp,  -- tipe data timestamp dan defaultnya adalah current_timestamp

    -- constraint untuk memastikan data yang dimasukkan valid
    constraint fk_products_category
        foreign key (category_id)
        references categories (category_id),

    constraint chk_products_price
        check (price >= 0),

    constraint chk_products_stock
        check (stock_quantity >= 0)
);


-- orders (one-to-many with users)
create table orders (
    order_id         serial         primary key,                         -- tipe data serial dan dijadikan primary key
    user_id          integer        not null,                            -- tipe data integer dan tidak boleh null
    order_status     varchar(20)    not null default 'pending',          -- tipe data varchar(20) dan tidak boleh null dengan default 'pending'
    total_amount     numeric(12, 2) not null default 0,                  -- tipe data numeric(12, 2) dan tidak boleh null dengan default 0
    shipping_address text           not null,                            -- memakai tipe data text dan tidak boleh null
    ordered_at       timestamp      not null default current_timestamp,  -- tipe data timestamp dan defaultnya adalah current_timestamp

    constraint fk_orders_user
        foreign key (user_id)
        references users (id),

    constraint chk_orders_status
        check (order_status in ('pending', 'paid', 'shipped', 'delivered', 'cancelled')),

    constraint chk_orders_total
        check (total_amount >= 0)
);


-- ---------------------------------------------------------------

create table order_items (
    order_item_id serial         primary key,                         -- tipe data serial dan dijadikan primary key
    order_id      integer        not null,                            -- tipe data integer dan tidak boleh null
    product_id    integer        not null,                            -- tipe data integer dan tidak boleh null
    quantity      integer        not null default 1,                  -- default 1 agar relasi many-to-many bisa diisi lewat orm
    unit_price    numeric(12, 2) not null default 0,                  -- default 0 agar relasi many-to-many bisa diisi lewat orm

    constraint fk_order_items_order
        foreign key (order_id)
        references orders (order_id)
        on delete cascade,

    constraint fk_order_items_product
        foreign key (product_id)
        references products (product_id),

    constraint chk_order_items_quantity
        check (quantity > 0),

    constraint chk_order_items_unit_price
        check (unit_price >= 0),

    constraint uq_order_items_order_product
        unique (order_id, product_id)
);


-- ---------------------------------------------------------------
-- membuat index untuk mempercepat query pada setiap tabel yang memiliki foreign key
create index idx_products_category_id  on products    (category_id);
create index idx_orders_user_id        on orders      (user_id);
create index idx_order_items_order_id  on order_items (order_id);
create index idx_order_items_product_id on order_items (product_id);
