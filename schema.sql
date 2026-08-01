-- schema.sql
-- revoshop database schema
-- module 2 checkpoint 1
--
-- run this file first, before seed.sql
-- it creates 5 tables: users, categories, products, orders, order_items


-- ---------------------------------------------------------------
-- clean start
-- drop in reverse order of creation, because a table cannot be
-- dropped while another table still points at it with a foreign key
-- ---------------------------------------------------------------

drop table if exists order_items;
drop table if exists orders;
drop table if exists products;
drop table if exists categories;
drop table if exists users;


-- ---------------------------------------------------------------
-- users
-- one row = one customer account
-- ---------------------------------------------------------------

create table users (
    user_id       serial       primary key,
    full_name     varchar(100) not null,
    email         varchar(150) not null unique,
    password_hash varchar(255) not null,
    phone_number  varchar(20),
    address       text,
    created_at    timestamp    not null default current_timestamp
);


-- ---------------------------------------------------------------
-- categories
-- one row = one product category (electronics, books, ...)
-- ---------------------------------------------------------------

create table categories (
    category_id   serial       primary key,
    category_name varchar(100) not null unique,
    description   text,
    created_at    timestamp    not null default current_timestamp
);


-- ---------------------------------------------------------------
-- products
-- one row = one item for sale
-- each product belongs to exactly one category (one-to-many)
-- ---------------------------------------------------------------

create table products (
    product_id     serial         primary key,
    category_id    integer        not null,
    product_name   varchar(150)   not null,
    description    text,
    price          numeric(12, 2) not null,
    stock_quantity integer        not null default 0,
    is_active      boolean        not null default true,
    created_at     timestamp      not null default current_timestamp,

    constraint fk_products_category
        foreign key (category_id)
        references categories (category_id),

    constraint chk_products_price
        check (price >= 0),

    constraint chk_products_stock
        check (stock_quantity >= 0)
);


-- ---------------------------------------------------------------
-- orders
-- one row = one order placed by one user (one-to-many)
-- ---------------------------------------------------------------

create table orders (
    order_id         serial         primary key,
    user_id          integer        not null,
    order_status     varchar(20)    not null default 'pending',
    total_amount     numeric(12, 2) not null default 0,
    shipping_address text           not null,
    ordered_at       timestamp      not null default current_timestamp,

    constraint fk_orders_user
        foreign key (user_id)
        references users (user_id),

    constraint chk_orders_status
        check (order_status in ('pending', 'paid', 'shipped', 'delivered', 'cancelled')),

    constraint chk_orders_total
        check (total_amount >= 0)
);


-- ---------------------------------------------------------------
-- order_items
-- junction table for the many-to-many between orders and products
-- one row = one product line inside one order
--
-- unit_price is copied from products.price at the time of purchase,
-- so old orders keep their original price even if the product
-- price changes later
-- ---------------------------------------------------------------

create table order_items (
    order_item_id serial         primary key,
    order_id      integer        not null,
    product_id    integer        not null,
    quantity      integer        not null,
    unit_price    numeric(12, 2) not null,

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
-- indexes on the foreign key columns
-- postgres indexes primary keys automatically, but not the
-- columns that point at them, so we add those ourselves
-- ---------------------------------------------------------------

create index idx_products_category_id  on products    (category_id);
create index idx_orders_user_id        on orders      (user_id);
create index idx_order_items_order_id  on order_items (order_id);
create index idx_order_items_product_id on order_items (product_id);
