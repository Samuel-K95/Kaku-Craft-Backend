from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
	path("", RedirectView.as_view(url="/api/docs/swagger/", permanent=False), name="home"),
	path("admin/", admin.site.urls),
	path("api/users/", include("users.urls", namespace="users")),
	path("api/products/", include("products.urls", namespace="products")),
	path("api/orders/", include("orders.urls", namespace="orders")),
	path("api/reviews/", include("reviews.urls", namespace="reviews")),
	path("api/messaging/", include("messaging.urls", namespace="messaging")),
	path("api/notifications/", include("notifications.urls", namespace="notifications")),
	path("api/cms/", include("cms.urls", namespace="cms")),
	path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
	path("api/docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
	path("api/docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
