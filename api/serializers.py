"""
DRF serializers — deliberately missing prefetch/select_related.
These trigger the DRF Serializer N+1 analyzer.
"""
from rest_framework import serializers
from django.contrib.auth.models import User

from shop.models import Product, Category, Order, OrderItem, Review
from blog.models import Post, Author, Comment, Tag
from accounts.models import Profile


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]


class ReviewSerializer(serializers.ModelSerializer):
    # BUG: DRF N+1 — accessing user.username triggers a query per review
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "rating", "title", "body", "username", "created_at"]


class ProductSerializer(serializers.ModelSerializer):
    # BUG: DRF N+1 — nested serializers without prefetch_related on the view
    category = CategorySerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True, source="reviews.all")
    creator = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "price", "category", "creator",
            "reviews", "stock", "created_at",
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    # BUG: DRF N+1 — accessing product.name and product.category.name
    product_name = serializers.CharField(source="product.name", read_only=True)
    category_name = serializers.CharField(source="product.category.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product_name", "category_name", "quantity", "unit_price"]


class OrderSerializer(serializers.ModelSerializer):
    # BUG: DRF N+1 — nested items without prefetch, each item hits product and category
    items = OrderItemSerializer(many=True, read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Order
        fields = ["id", "username", "status", "total", "items", "created_at"]


class CommentSerializer(serializers.ModelSerializer):
    # BUG: DRF N+1 — accessing user.username per comment
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "username", "body", "is_approved", "created_at"]


class PostSerializer(serializers.ModelSerializer):
    # BUG: DRF N+1 — nested author and comments without prefetch
    author_name = serializers.CharField(source="author.user.get_full_name", read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")

    class Meta:
        model = Post
        fields = [
            "id", "title", "slug", "author_name", "body", "excerpt",
            "status", "tags", "comments", "view_count", "published_at",
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    # BUG: DRF N+1 — accessing profile fields per user
    phone = serializers.CharField(source="profile.phone", read_only=True)
    newsletter = serializers.BooleanField(source="profile.newsletter_subscribed", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "phone", "newsletter"]
