from rest_framework.routers import DefaultRouter

from apps.products.views import CategoryViewSet, ProductViewSet, StandardViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("standards", StandardViewSet, basename="standard")

urlpatterns = router.urls
