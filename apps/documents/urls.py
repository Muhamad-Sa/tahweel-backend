from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.documents.views import CatalogueViewSet, DocumentViewSet, document_type_list, presign_upload

router = DefaultRouter()
router.register("documents", DocumentViewSet, basename="document")
router.register("catalogues", CatalogueViewSet, basename="catalogue")

urlpatterns = [
    path("document-types/", document_type_list, name="document-types"),
    path("documents/presign-upload/", presign_upload, name="presign-upload"),
] + router.urls
