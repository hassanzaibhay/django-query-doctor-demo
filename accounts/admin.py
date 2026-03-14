from django.contrib import admin
from .models import Profile, Address, ActivityLog

# Simple registration — no optimization, to show admin query issues too
admin.site.register(Profile)
admin.site.register(Address)
admin.site.register(ActivityLog)
