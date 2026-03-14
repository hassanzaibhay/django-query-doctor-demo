from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("users/", views.UserListView.as_view(), name="user-list"),
    path("activity/", views.ActivityLogView.as_view(), name="activity-log"),
]
