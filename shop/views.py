"""
Shop views — deliberately written with query anti-patterns.
Each view has a comment explaining which issue it triggers.
"""
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView

from .models import Product, Category, Order, OrderItem, Review


class HomeView(View):
    """Homepage showing featured products, categories, and recent orders."""

    def get(self, request):
        # BUG: N+1 — accessing product.category and product.created_by in template
        # without select_related
        featured_products = Product.objects.filter(is_active=True)[:10]

        # BUG: Duplicate query — categories fetched here AND in the template
        # via product.category for each product above
        categories = list(Category.objects.all())

        # BUG: Fat SELECT — we only need name and slug for the sidebar
        # but fetching all fields including description (TextField)
        all_categories = Category.objects.all()

        context = {
            "featured_products": featured_products,
            "categories": categories,
            "all_categories": all_categories,
        }
        return render(request, "shop/home.html", context)


class ProductListView(ListView):
    """Product listing with multiple query issues."""

    model = Product
    template_name = "shop/product_list.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        # BUG: N+1 — template accesses product.category.name and product.created_by.username
        # without select_related
        qs = Product.objects.filter(is_active=True)

        # BUG: Missing index — filtering on created_at without db_index
        category_slug = self.request.GET.get("category")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # BUG: Duplicate query — categories already available via products but fetched again
        context["categories"] = Category.objects.all()
        # BUG: QuerySet evaluation — using len() instead of .count()
        context["total_products"] = len(Product.objects.filter(is_active=True))
        return context


class ProductDetailView(DetailView):
    """Product detail with review N+1 and complexity issues."""

    model = Product
    template_name = "shop/product_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # BUG: N+1 — accessing review.user.username in template without select_related
        context["reviews"] = product.reviews.all().order_by("-created_at")

        # BUG: Duplicate query — product.category accessed here AND in template
        context["related_products"] = Product.objects.filter(
            category=product.category, is_active=True
        ).exclude(pk=product.pk)[:5]

        # BUG: QuerySet evaluation — using if queryset instead of .exists()
        if product.reviews.all():
            # BUG: Could use .aggregate(Avg('rating')) instead of fetching all
            all_reviews = list(product.reviews.all())
            context["avg_rating"] = sum(r.rating for r in all_reviews) / len(all_reviews)
        else:
            context["avg_rating"] = 0

        return context


class OrderListView(ListView):
    """User's order history with deep N+1 chain."""

    template_name = "shop/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        # BUG: N+1 chain — template accesses:
        #   order.items.all → for each item: item.product.name, item.product.category.name
        # This creates a 3-level deep N+1: orders → items → product → category
        return Order.objects.filter(user=self.request.user).order_by("-created_at")


class OrderDetailView(DetailView):
    """Single order detail — fat SELECT and duplicate queries."""

    model = Order
    template_name = "shop/order_detail.html"
    context_object_name = "order"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object

        # BUG: Fat SELECT — only need product name and price but selecting all fields
        context["items"] = order.items.all()

        # BUG: Duplicate query — accessing order.user.profile in template
        # triggers separate queries for user and profile
        context["user_address"] = order.user.addresses.filter(is_default=True).first()

        return context


class CategoryDetailView(DetailView):
    """Category page with products — missing prefetch for M2M tags."""

    model = Category
    template_name = "shop/category_detail.html"
    context_object_name = "category"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # BUG: N+1 — accessing product.tags.all() in template for each product
        # without prefetch_related
        context["products"] = self.object.products.filter(is_active=True)
        return context
