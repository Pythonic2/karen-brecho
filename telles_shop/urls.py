from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.static import serve as serve_media
from django.urls import re_path
from django.urls import include, path

urlpatterns = [
    path('health/', lambda request: JsonResponse({'status': 'ok'}), name='health'),
    path('admin/', admin.site.urls),
    path('', include('catalog.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('checkout/', include('transactions.urls')),
    path('reports/', include('reports.urls')),
]

admin.site.site_header = "Telles' Thrift Shop administration"
admin.site.site_title = "Telles' Thrift Shop admin"
admin.site.index_title = 'Store management'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Uploaded product images and supplier balance receipts are low-volume
    # files. The existing server proxy can later take over this /media/ route.
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve_media, {'document_root': settings.MEDIA_ROOT}),
    ]
