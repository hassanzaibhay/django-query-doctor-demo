from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.PostListView.as_view(), name="post-list"),
    path("post/<slug:slug>/", views.PostDetailView.as_view(), name="post-detail"),
    path("author/<int:pk>/", views.AuthorDetailView.as_view(), name="author-detail"),
    path("tag/<slug:slug>/", views.TagDetailView.as_view(), name="tag-detail"),
]
