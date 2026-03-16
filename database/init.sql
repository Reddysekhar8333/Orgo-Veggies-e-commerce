-- Base seed data for Orgo Veggies e-commerce.
-- Safe to run multiple times due to idempotent INSERT patterns.

INSERT INTO roles (role_name, description)
VALUES
    ('admin', 'Full system access for platform administration'),
    ('customer', 'Default role for shoppers placing orders')
ON DUPLICATE KEY UPDATE
    description = VALUES(description);

INSERT INTO categories (category_name, slug, description)
VALUES
    ('Leafy Greens', 'leafy-greens', 'Fresh spinach, lettuce, kale, and similar greens'),
    ('Root Vegetables', 'root-vegetables', 'Carrots, beets, radishes, and other root crops'),
    ('Seasonal Picks', 'seasonal-picks', 'Rotating selection of in-season organic produce')
ON DUPLICATE KEY UPDATE
    description = VALUES(description),
    category_name = VALUES(category_name);