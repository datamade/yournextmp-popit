from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^$',
        views.IllinoisAddressFinder.as_view(),
        name='lookup-name'
    ),
    url(
        r'^areas/(?P<area_ids>.*?)$',
        views.IllinoisAreasView.as_view(),
        name='illinois-areas-view'
    ),
]
