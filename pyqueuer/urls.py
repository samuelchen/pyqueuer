"""pyqueuer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from pyqueuer import views


urlpatterns = [
    url(r'^admin/', admin.site.urls, name='admin'),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^$', views.index, name='index'),
    url(r'^setting/', views.setting, name='setting'),
    url(r'^send/', views.send, name='send'),
    url(r'^consume/', views.consume, name='consume'),
    url(r'^output/', views.output, name='output'),
    url(r'^plugin/', views.plugin, name='plugin'),
    url(r'^register/', views.register, name='register'),
]

if settings.DEBUG:
    urlpatterns.append(url(r'^test/', views.test))
