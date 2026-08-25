from django.urls import path

from apps.core.views import GlobalSearchView

urlpatterns = [
    path("search/", GlobalSearchView.as_view(), name="global-search"),
]
