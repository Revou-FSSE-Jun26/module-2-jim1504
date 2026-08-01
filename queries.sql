-- Query that combines WHERE, ORDER BY, and LIMIT.

-- Query 1: Menampilkan 5 produk terlaris dalam kategori 1
select
    product_id,
    product_name,
    price,
    stock_quantity
from products
where category_id = 1
  and stock_quantity > 0
  and is_active = true
order by price desc
limit 5;


-- Query 2: Menampilkan semua produk beserta nama kategorinya
select
    products.product_id,
    categories.category_name,
    products.product_name,
    products.price
from products
join categories
    on products.category_id = categories.category_id
order by categories.category_name asc, products.product_name desc;


-- Query 3: Menampilkan order dengan order_id = 1 beserta nama user, nama produk, quantity, unit_price, dan line_total (quantity * unit_price)
select
    orders.order_id,
    users.full_name,
    products.product_name,
    order_items.quantity,
    order_items.unit_price,
    (order_items.quantity * order_items.unit_price) as line_total
from orders
join users
    on orders.user_id = users.user_id
join order_items
    on order_items.order_id = orders.order_id
join products
    on products.product_id = order_items.product_id
where orders.order_id = 1
order by products.product_name asc;

-- Query 4: Menampilkan user beserta jumlah order yang pernah dilakukan
select
    users.user_id,
    users.full_name,
    count(orders.order_id) as order_count,
    sum(orders.total_amount) as lifetime_value
from users
join orders
    on orders.user_id = users.user_id
where orders.order_status <> 'cancelled'
group by users.user_id, users.full_name
order by lifetime_value desc;


-- Query 5: Menampilkan 5 produk terlaris
select
    products.product_id,
    products.product_name,
    sum(order_items.quantity) as units_sold
from products
join order_items
    on order_items.product_id = products.product_id
group by products.product_id, products.product_name
order by units_sold desc, products.product_name asc
limit 5;

-- Query 6: Menampilkan semua user yang belum pernah melakukan order
select
    users.user_id,
    users.full_name,
    users.email
from users
left join orders
    on orders.user_id = users.user_id
where orders.order_id is null
order by users.user_id asc;
