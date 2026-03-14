from django.contrib import admin
from .models import Author, Tag, Post, Comment

# Simple registration — no optimization, to show admin query issues too
admin.site.register(Author)
admin.site.register(Tag)
admin.site.register(Post)
admin.site.register(Comment)
