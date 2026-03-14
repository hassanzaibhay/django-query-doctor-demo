from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"products", views.ProductViewSet)
router.register(r"categories", views.CategoryViewSet)
router.register(r"orders", views.OrderViewSet, basename="order")
router.register(r"posts", views.PostViewSet)
router.register(r"reviews", views.ReviewViewSet)
router.register(r"users", views.UserViewSet)

app_name = "api"

urlpatterns = [
    path("", include(router.urls)),
]
