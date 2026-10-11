-- Deterministic sample. Covers Nowruz 1403–1405 and leap day 1403/12/30.
INSERT INTO sales.regions (code, name_fa) VALUES
    ('north', 'شمال'),
    ('south', 'جنوب'),
    ('east', 'شرق'),
    ('west', 'غرب');

INSERT INTO sales.branches (region_code, name_fa) VALUES
    ('north', 'شعبه رشت'),
    ('north', 'شعبه ساری'),
    ('south', 'شعبه شیراز'),
    ('south', 'شعبه بندرعباس'),
    ('east', 'شعبه مشهد'),
    ('east', 'شعبه بیرجند'),
    ('west', 'شعبه کرمانشاه'),
    ('west', 'شعبه اهواز');

INSERT INTO sales.products (name_fa, category_fa) VALUES
    ('چای', 'نوشیدنی'),
    ('قهوه', 'نوشیدنی'),
    ('برنج', 'خوراکی'),
    ('زعفران', 'خوراکی'),
    ('صابون', 'خانگی'),
    ('حوله', 'خانگی');

SELECT setseed(0.42);

INSERT INTO sales.orders (branch_id, product_id, quantity, amount, created_at, status)
SELECT
    1 + floor(random() * 8)::int,
    1 + floor(random() * 6)::int,
    1 + floor(random() * 5)::int,
    round((10000 + random() * 490000)::numeric, 0),
    CASE
        WHEN random() < 0.01 THEN NULL
        ELSE timestamp '2024-03-01 00:00:00'
            + (random() * (timestamp '2026-03-31 23:59:59' - timestamp '2024-03-01 00:00:00'))
    END,
    CASE WHEN random() < 0.08 THEN 'cancelled' ELSE 'paid' END
FROM generate_series(1, 150000);

INSERT INTO sales.orders (branch_id, product_id, quantity, amount, created_at, status) VALUES
    (1, 1, 2, 120000, timestamp '2024-09-22 00:00:00', 'paid'),
    (1, 3, 1, 340000, timestamp '2024-10-21 23:59:59', 'paid'),
    (2, 2, 1, 80000, timestamp '2024-10-22 00:00:00', 'paid'),
    (3, 4, 1, 560000, timestamp '2025-03-20 12:00:00', 'paid'),
    (5, 5, 3, 90000, timestamp '2025-03-21 00:00:00', 'paid'),
    (7, 6, 1, 45000, NULL, 'paid');
