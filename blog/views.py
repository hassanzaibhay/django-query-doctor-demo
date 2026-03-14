"""
Blog views — deliberately triggering queryset eval, missing index,
and complexity issues.
"""
from django.shortcuts import render
from django.views.generic import ListView, DetailView

from .models import Post, Author, Comment, Tag


class PostListView(ListView):
    """Blog listing with multiple issues."""

    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        # BUG: N+1 — template accesses post.author.user.get_full_name()
        # without select_related('author__user')
        # BUG: Missing index — ordering by published_at without db_index
        return Post.objects.filter(
            status=Post.Status.PUBLISHED
        ).order_by("-published_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # BUG: QuerySet evaluation — bool(queryset) instead of .exists()
        if Post.objects.filter(status=Post.Status.DRAFT):
            context["has_drafts"] = True

        # BUG: QuerySet evaluation — len(queryset) instead of .count()
        context["total_posts"] = len(Post.objects.filter(status=Post.Status.PUBLISHED))

        # BUG: Fat SELECT — only need tag name and slug for sidebar
        context["tags"] = Tag.objects.all()
        return context


class PostDetailView(DetailView):
    """Blog post detail — comment N+1 and complexity."""

    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object

        # BUG: N+1 — accessing comment.user.username in template
        # without select_related('user')
        context["comments"] = post.comments.filter(
            is_approved=True
        ).order_by("-created_at")

        # BUG: N+1 on M2M — accessing post.tags.all() without prefetch
        context["post_tags"] = post.tags.all()

        # BUG: Complexity — multiple JOINs and subquery for "related posts"
        # This query has high complexity: JOIN on tags (M2M through table),
        # subquery for exclusion, GROUP BY, ORDER BY
        context["related_posts"] = Post.objects.filter(
            status=Post.Status.PUBLISHED,
            tags__in=post.tags.all(),
        ).exclude(pk=post.pk).distinct().order_by("-published_at")[:5]

        return context


class AuthorDetailView(DetailView):
    """Author profile — duplicate queries and N+1."""

    model = Author
    template_name = "blog/author_detail.html"
    context_object_name = "author"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = self.object

        # BUG: N+1 — template iterates posts and accesses post.tags.all()
        context["posts"] = author.posts.filter(
            status=Post.Status.PUBLISHED
        ).order_by("-published_at")

        # BUG: Duplicate query — author.user accessed here AND in template
        context["full_name"] = author.user.get_full_name()

        # BUG: QuerySet evaluation — fetching all comments just to count them
        all_comments = list(Comment.objects.filter(post__author=author))
        context["total_comments"] = len(all_comments)

        return context


class TagDetailView(DetailView):
    """Posts by tag — missing index and N+1."""

    model = Tag
    template_name = "blog/tag_detail.html"
    context_object_name = "tag"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # BUG: N+1 — accessing post.author.user in template
        context["posts"] = self.object.posts.filter(
            status=Post.Status.PUBLISHED
        ).order_by("-published_at")
        return context
