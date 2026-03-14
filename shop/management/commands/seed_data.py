"""
Seed the database with realistic demo data.
Creates enough data to make query issues visible and measurable.
"""
import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify

import datetime as dt

from faker import Faker

fake = Faker()

CATEGORY_TREE = {
    "Electronics": ["Laptops", "Smartphones", "Headphones", "Cameras"],
    "Clothing": ["Men's Wear", "Women's Wear", "Kids' Wear"],
    "Home & Garden": ["Furniture", "Kitchen", "Decor"],
    "Books": ["Fiction", "Non-Fiction", "Technical"],
    "Sports": ["Outdoor", "Fitness", "Team Sports"],
}

TAG_NAMES = [
    "python", "django", "javascript", "react", "tutorial",
    "beginner", "advanced", "tips", "best-practices", "performance",
    "database", "security", "devops", "career", "open-source",
]

ACTIVITY_ACTIONS = [
    "login", "logout", "view_product", "add_to_cart",
    "place_order", "update_profile", "change_password",
    "view_post", "post_comment", "search",
]


class Command(BaseCommand):
    help = "Seed database with demo data for django-query-doctor showcase"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=20, help="Number of users")
        parser.add_argument("--products", type=int, default=50, help="Number of products")
        parser.add_argument("--posts", type=int, default=30, help="Number of blog posts")
        parser.add_argument("--orders", type=int, default=40, help="Number of orders")
        parser.add_argument("--flush", action="store_true", help="Delete all data first")

    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Flushing database...")
            from shop.models import Product, Category, Order, OrderItem, Review
            from blog.models import Post, Author, Comment, Tag
            from accounts.models import Profile, Address, ActivityLog

            for model in [
                Review, OrderItem, Order, Product, Comment, Post, Author,
                Tag, Category, ActivityLog, Address, Profile,
            ]:
                model.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        self.stdout.write("Seeding database...")

        # Create superuser
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin")
            self.stdout.write("  Created superuser admin/admin")

        users = self._create_users(options["users"])
        categories = self._create_categories()
        tags = self._create_tags()
        authors = self._create_authors(users[:10])
        products = self._create_products(options["products"], categories, users, tags)
        posts = self._create_posts(options["posts"], authors, tags)
        self._create_comments(posts, users)
        self._create_orders(options["orders"], users, products)
        self._create_reviews(products, users)
        self._create_activity_logs(users)

        self.stdout.write(self.style.SUCCESS(
            f"Done! Created {len(users)} users, {len(products)} products, "
            f"{len(posts)} posts, {options['orders']} orders"
        ))

    def _create_users(self, count):
        from accounts.models import Profile, Address

        existing = User.objects.filter(is_superuser=False).count()
        if existing >= count:
            self.stdout.write(f"  Users already exist ({existing}), skipping")
            return list(User.objects.filter(is_superuser=False))

        users = []
        for i in range(count):
            username = f"{fake.user_name()}{i}"
            user = User.objects.create_user(
                username=username,
                email=fake.email(),
                password="testpass123",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )
            users.append(user)

        # Create profiles
        profiles = []
        for user in users:
            profiles.append(Profile(
                user=user,
                phone=fake.phone_number()[:20],
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=65),
                newsletter_subscribed=random.choice([True, False]),
                preferred_currency=random.choice(["USD", "EUR", "GBP"]),
            ))
        Profile.objects.bulk_create(profiles)

        # Create addresses (1-3 per user)
        addresses = []
        for user in users:
            num_addresses = random.randint(1, 3)
            labels = ["Home", "Work", "Other"]
            for j in range(num_addresses):
                addresses.append(Address(
                    user=user,
                    label=labels[j],
                    street=fake.street_address(),
                    city=fake.city(),
                    state=fake.state(),
                    zip_code=fake.zipcode(),
                    country="United States",
                    is_default=(j == 0),
                ))
        Address.objects.bulk_create(addresses)

        self.stdout.write(f"  Created {len(users)} users with profiles and addresses")
        return users

    def _create_categories(self):
        from shop.models import Category

        if Category.objects.exists():
            self.stdout.write("  Categories already exist, skipping")
            return list(Category.objects.all())

        categories = []
        for parent_name, children in CATEGORY_TREE.items():
            parent = Category.objects.create(
                name=parent_name,
                slug=slugify(parent_name),
                description=fake.paragraph(),
            )
            categories.append(parent)
            for child_name in children:
                child = Category.objects.create(
                    name=child_name,
                    slug=slugify(child_name),
                    parent=parent,
                    description=fake.paragraph(),
                )
                categories.append(child)

        self.stdout.write(f"  Created {len(categories)} categories")
        return categories

    def _create_tags(self):
        from blog.models import Tag

        if Tag.objects.exists():
            self.stdout.write("  Tags already exist, skipping")
            return list(Tag.objects.all())

        tags = []
        for name in TAG_NAMES:
            tags.append(Tag(name=name, slug=name))
        Tag.objects.bulk_create(tags)

        self.stdout.write(f"  Created {len(tags)} tags")
        return list(Tag.objects.all())

    def _create_authors(self, users):
        from blog.models import Author

        if Author.objects.exists():
            self.stdout.write("  Authors already exist, skipping")
            return list(Author.objects.all())

        authors = []
        for user in users:
            authors.append(Author(
                user=user,
                bio=fake.paragraph(nb_sentences=3),
                website=fake.url() if random.random() > 0.5 else "",
                twitter_handle=f"@{user.username}" if random.random() > 0.5 else "",
            ))
        Author.objects.bulk_create(authors)

        self.stdout.write(f"  Created {len(authors)} authors")
        return list(Author.objects.all())

    def _create_products(self, count, categories, users, tags):
        from shop.models import Product

        if Product.objects.exists():
            self.stdout.write("  Products already exist, skipping")
            return list(Product.objects.all())

        # Only use leaf categories (those with parents)
        leaf_categories = [c for c in categories if c.parent is not None]
        if not leaf_categories:
            leaf_categories = categories

        products = []
        for i in range(count):
            price = Decimal(str(round(random.uniform(9.99, 299.99), 2)))
            cost = price * Decimal("0.6")
            products.append(Product(
                name=fake.catch_phrase(),
                slug=f"{fake.slug()}-{i}",
                description=fake.paragraph(nb_sentences=5),
                price=price,
                cost_price=cost.quantize(Decimal("0.01")),
                sku=f"SKU-{i:05d}",
                category=random.choice(leaf_categories),
                created_by=random.choice(users),
                stock=random.randint(0, 200),
                is_active=random.random() > 0.1,
            ))
        Product.objects.bulk_create(products)

        # Add tags to products (1-3 per product)
        products = list(Product.objects.all())
        for product in products:
            product_tags = random.sample(tags, min(random.randint(1, 3), len(tags)))
            product.tags.set(product_tags)

        self.stdout.write(f"  Created {len(products)} products")
        return products

    def _create_posts(self, count, authors, tags):
        from blog.models import Post

        if Post.objects.exists():
            self.stdout.write("  Posts already exist, skipping")
            return list(Post.objects.all())

        posts = []
        for i in range(count):
            status = random.choices(
                [Post.Status.PUBLISHED, Post.Status.DRAFT, Post.Status.ARCHIVED],
                weights=[0.7, 0.2, 0.1],
            )[0]
            published_at = None
            if status == Post.Status.PUBLISHED:
                published_at = fake.date_time_between(
                    start_date="-1y", end_date="now", tzinfo=dt.timezone.utc,
                )
            posts.append(Post(
                title=fake.sentence(nb_words=random.randint(4, 10)).rstrip("."),
                slug=f"{fake.slug()}-{i}",
                author=random.choice(authors),
                body="\n\n".join(fake.paragraphs(nb=random.randint(3, 8))),
                excerpt=fake.paragraph() if random.random() > 0.3 else "",
                status=status,
                view_count=random.randint(0, 5000),
                published_at=published_at,
            ))
        Post.objects.bulk_create(posts)

        # Add tags to posts (2-4 per post)
        posts = list(Post.objects.all())
        for post in posts:
            post_tags = random.sample(tags, min(random.randint(2, 4), len(tags)))
            post.tags.set(post_tags)

        self.stdout.write(f"  Created {len(posts)} posts")
        return posts

    def _create_comments(self, posts, users):
        from blog.models import Comment

        if Comment.objects.exists():
            self.stdout.write("  Comments already exist, skipping")
            return

        comments = []
        for post in posts:
            num_comments = random.randint(3, 8)
            for _ in range(num_comments):
                comments.append(Comment(
                    post=post,
                    user=random.choice(users),
                    body=fake.paragraph(nb_sentences=random.randint(1, 4)),
                    is_approved=random.random() > 0.2,
                ))
        Comment.objects.bulk_create(comments)
        self.stdout.write(f"  Created {len(comments)} comments")

    def _create_orders(self, count, users, products):
        from shop.models import Order, OrderItem

        if Order.objects.exists():
            self.stdout.write("  Orders already exist, skipping")
            return

        statuses = [s.value for s in Order.Status]

        for _ in range(count):
            order = Order.objects.create(
                user=random.choice(users),
                status=random.choice(statuses),
                shipping_address=f"{fake.street_address()}\n{fake.city()}, {fake.state()} {fake.zipcode()}",
                notes=fake.sentence() if random.random() > 0.7 else "",
            )

            # 1-5 items per order
            num_items = random.randint(1, 5)
            order_products = random.sample(products, min(num_items, len(products)))
            items = []
            total = Decimal("0")
            for product in order_products:
                qty = random.randint(1, 3)
                items.append(OrderItem(
                    order=order,
                    product=product,
                    quantity=qty,
                    unit_price=product.price,
                ))
                total += product.price * qty
            OrderItem.objects.bulk_create(items)

            order.total = total
            order.save(update_fields=["total"])

        self.stdout.write(f"  Created {count} orders with items")

    def _create_reviews(self, products, users):
        from shop.models import Review

        if Review.objects.exists():
            self.stdout.write("  Reviews already exist, skipping")
            return

        reviews = []
        for product in products:
            num_reviews = random.randint(2, 5)
            reviewers = random.sample(users, min(num_reviews, len(users)))
            for user in reviewers:
                reviews.append(Review(
                    product=product,
                    user=user,
                    rating=random.randint(1, 5),
                    title=fake.sentence(nb_words=random.randint(3, 8)).rstrip("."),
                    body=fake.paragraph(nb_sentences=random.randint(1, 4)),
                ))
        Review.objects.bulk_create(reviews)
        self.stdout.write(f"  Created {len(reviews)} reviews")

    def _create_activity_logs(self, users):
        from accounts.models import ActivityLog

        if ActivityLog.objects.exists():
            self.stdout.write("  Activity logs already exist, skipping")
            return

        logs = []
        for _ in range(250):
            logs.append(ActivityLog(
                user=random.choice(users),
                action=random.choice(ACTIVITY_ACTIONS),
                details={"page": fake.uri_path(), "referrer": fake.url()},
                ip_address=fake.ipv4(),
            ))
        ActivityLog.objects.bulk_create(logs)
        self.stdout.write(f"  Created {len(logs)} activity logs")
