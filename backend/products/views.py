from products.models import Product

def lock_products_for_checkout(product_ids):
    products = Product.objects.select_for_update().filter(id__in=product_ids)
    locked = {product.id: product for product in products}
    missing_ids = set(product_ids) - set(locked)
    if missing_ids:
        missing = ", ".join(str(product_id) for product_id in sorted(missing_ids))
        from rest_framework import serializers

        raise serializers.ValidationError({"detail": f"Products not found: {missing}"})
    return locked