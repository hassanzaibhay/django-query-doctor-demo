"""
Account views — duplicate queries, complexity, and queryset eval issues.
"""
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.utils import timezone
from django.views.generic import TemplateView, ListView

from .models import Profile, Address, ActivityLog


class DashboardView(LoginRequiredMixin, TemplateView):
    """User dashboard — duplicate queries and complexity."""

    template_name = "accounts/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Auto-create profile if missing (handles existing users without one)
        profile, _ = Profile.objects.get_or_create(user=user)

        # BUG: Duplicate query — user.profile accessed multiple times
        context["profile"] = profile
        context["phone"] = profile.phone
        context["newsletter"] = profile.newsletter_subscribed

        # BUG: N+1 — template iterates orders and accesses order.items.all()
        context["recent_orders"] = user.orders.all().order_by("-created_at")[:5]

        # BUG: Duplicate query — addresses fetched here AND separately for default
        context["addresses"] = list(user.addresses.all())
        context["default_address"] = user.addresses.filter(is_default=True).first()

        # BUG: QuerySet evaluation — using list() to count
        all_logs = list(user.activity_logs.all())
        context["activity_count"] = len(all_logs)

        # BUG: Missing index — filtering ActivityLog by created_at
        week_ago = timezone.now() - datetime.timedelta(days=7)
        context["recent_activity"] = user.activity_logs.filter(
            created_at__gte=week_ago
        ).order_by("-created_at")[:10]

        return context


class UserListView(LoginRequiredMixin, ListView):
    """Admin-like user list — complexity and N+1."""

    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        # BUG: N+1 — template accesses user.profile and user.orders.count()
        # for each user without select_related or annotation
        return User.objects.all().order_by("-date_joined")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # BUG: Complexity — subquery + JOIN + GROUP BY
        # Fetching users with their order counts and total spend
        # Done as a loop instead of annotation
        user_stats = []
        for user in context["users"]:
            # BUG: N+1 — separate query for each user's orders
            orders = user.orders.all()
            user_stats.append({
                "user": user,
                "order_count": len(list(orders)),  # BUG: len(list()) instead of .count()
                "total_spend": sum(o.total for o in orders),
            })
        context["user_stats"] = user_stats
        return context


class ActivityLogView(LoginRequiredMixin, ListView):
    """Activity log — missing index and fat SELECT."""

    template_name = "accounts/activity_log.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        # BUG: Fat SELECT — fetching all fields including details (JSONField)
        # when the template only shows action, created_at, and ip_address
        # BUG: Missing index on created_at
        # BUG: N+1 — accessing log.user.username in template
        return ActivityLog.objects.all().order_by("-created_at")
