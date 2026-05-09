# Django Modules
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('apps.auths.urls')),
    path('canteen/', include('apps.canteen.urls')),
    path('notification/', include('apps.notifications.urls'))
]
