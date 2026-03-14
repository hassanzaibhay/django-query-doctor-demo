# django-query-doctor-demo

A deliberately broken Django project that showcases every issue [django-query-doctor](https://github.com/hassanzaibhay/django-query-doctor) can detect and fix.

## What's Wrong With This Project?

Everything! This project is intentionally written with common Django ORM anti-patterns:

| Anti-Pattern | Where | Count |
|-------------|-------|-------|
| N+1 Queries | shop/views.py, blog/views.py, api/views.py | 12+ |
| Duplicate Queries | shop/views.py, accounts/views.py | 5+ |
| Missing Indexes | shop/models.py, blog/models.py, accounts/models.py | 5+ |
| Fat SELECT (*) | shop/views.py, blog/views.py, accounts/views.py | 4+ |
| QuerySet Evaluation | blog/views.py, accounts/views.py | 5+ |
| DRF Serializer N+1 | api/serializers.py, api/views.py | 6+ |
| Query Complexity | blog/views.py, accounts/views.py | 3+ |

## Quick Start

```bash
git clone https://github.com/hassanzaibhay/django-query-doctor-demo.git
cd django-query-doctor-demo
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Visit http://localhost:8000 and watch the console fill with query prescriptions!

## Try the Project-Wide Scan

```bash
python manage.py diagnose_project --output report.html
open report.html
```

## Try Auto-Fix

```bash
# Preview fixes
python manage.py fix_queries --url /products/

# Apply fixes
python manage.py fix_queries --url /products/ --apply
```

## Issues by App

### shop (E-commerce)

- **HomeView**: N+1 on product.category and product.created_by
- **ProductListView**: N+1, missing index on created_at, duplicate category query, len() instead of count()
- **ProductDetailView**: N+1 on reviews, duplicate queries, aggregate inefficiency
- **OrderListView**: 3-level deep N+1 chain (orders -> items -> product -> category)
- **CategoryDetailView**: N+1 on product tags (M2M)

### blog (Content)

- **PostListView**: N+1 on author.user, missing index on published_at, bool/len queryset eval
- **PostDetailView**: N+1 on comments, complexity (multi-JOIN related posts)
- **AuthorDetailView**: N+1, duplicate queries, list() to count

### accounts (Users)

- **DashboardView**: Duplicate profile queries, N+1 on orders, len(list()) pattern
- **UserListView**: N+1 on profile, O(n) query loop for user stats
- **ActivityLogView**: Fat SELECT, missing index, N+1 on user

### api (DRF)

- **ProductViewSet**: Unoptimized queryset with nested serializer
- **OrderViewSet**: Deep nested serializer N+1
- **PostViewSet**: Author + comments + tags N+1
- **ReviewViewSet**: User N+1
- **UserViewSet**: Profile N+1

## The Fix

Install django-query-doctor and it will tell you exactly what to fix:

```bash
pip install django-query-doctor
```

The middleware is already configured in `config/settings.py`.

## License

MIT
