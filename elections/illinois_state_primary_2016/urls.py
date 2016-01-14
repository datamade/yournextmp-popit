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
        views.StPaulAreasView.as_view(),
        name='st-paul-areas-view'
    ),
]
