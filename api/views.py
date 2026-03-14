"""
DRF ViewSets — deliberately missing select_related/prefetch_related.
Every ViewSet triggers the DRF serializer N+1 analyzer.
"""
from rest_framework import viewsets, permissions

from django.contrib.auth.models import User

from shop.models import Product, Category, Order, Review
from blog.models import Post, Author, Tag

from .serializers import (
    ProductSerializer, CategorySerializer, OrderSerializer,
    PostSerializer, UserProfileSerializer, ReviewSerializer,
)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    BUG: No select_related or prefetch_related on queryset.
    ProductSerializer accesses category, created_by, and reviews — all N+1.
    """
    serializer_class = ProductSerializer
    queryset = Product.objects.filter(is_active=True)  # BUG: no optimization


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    BUG: No prefetch_related for items, items.product, items.product.category.
    OrderSerializer has nested OrderItemSerializer accessing deep relations.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # BUG: No prefetch — template/serializer accesses items → product → category
        return Order.objects.filter(user=self.request.user).order_by("-created_at")


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    BUG: No select_related('author__user') or prefetch_related('comments', 'tags').
    PostSerializer accesses author.user, comments, and tags — all N+1.
    """
    serializer_class = PostSerializer
    queryset = Post.objects.filter(status=Post.Status.PUBLISHED)  # BUG: no optimization


class ReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """BUG: No select_related('user') — username accessed per review."""
    serializer_class = ReviewSerializer
    queryset = Review.objects.all().order_by("-created_at")  # BUG: no optimization


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """BUG: No select_related('profile') — profile fields accessed per user."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()  # BUG: no optimization
