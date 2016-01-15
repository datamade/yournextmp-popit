from django.conf.urls import url

from candidates.views.constituencies import ConstituencyDetailView, \
    ConstituencyRecordWinnerView, ConstituencyRetractWinnerView

from elections import views

from . import views as illinois_views

post_ignored_slug_re = r'(?!record-winner$|retract-winner$|.*\.csv$).*'

urlpatterns = [
    url(
        r'^$',
        views.OCDAddressFinder.as_view(),
        name='lookup-name'
    ),
    url(
        r'^posts$',
        illinois_views.IllinoisPostListView.as_view(),
        name='posts'
    ),
    url(
        r'^areas/$',
        illinois_views.IllinoisAreasView.as_view(),
        name='areas-view'
    ),
    url(
        r'^areas-of-type/(?P<area_type>.*?)(?:/(?P<ignored_slug>.*))?$',
        views.OCDAreasOfTypeView.as_view(),
        name='areas-of-type-view'
    ),
    url(
        r'^election/{election}/post/{post}/record-winner$'.format(
            election=r'(?P<election>[^/]+)',
            post=r'(?P<post_id>.*)',
        ),
        ConstituencyRecordWinnerView.as_view(),
        name='record-winner',
    ),
    url(
        r'^election/{election}/post/{post}/retract-winner$'.format(
            election=r'(?P<election>[^/]+)',
            post=r'(?P<post_id>.*)',
        ),
        ConstituencyRetractWinnerView.as_view(),
        name='retract-winner',
    ),
    url(
        r'^election/{election}/post/(?P<post_id>.*)/(?P<ignored_slug>{ignore_pattern})$'.format(
            election=r'(?P<election>[^/]+)',
            ignore_pattern=post_ignored_slug_re,
        ),
        ConstituencyDetailView.as_view(),
        name='constituency'
    ),
]
