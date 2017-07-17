from django.conf.urls import patterns, include, url
from app_suggestier import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
	url(r'^random/$', views.v_random_ep, name="random_ep"),
	url(r'^random2/$', views.v_random_ep2, name="random_ep2"),
    # url(r'^ep_suggest/', include('ep_suggest.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
