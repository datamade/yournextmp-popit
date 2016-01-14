import itertools
from collections import OrderedDict

from django.views.generic import TemplateView

from candidates.models.popolo_extra import MembershipExtra
from candidates.views.helpers import group_candidates_by_party

from elections.views import OCDAreasView
from elections.illinois_state_primary_2016.settings import OCD_BASE_URL

import requests

class IllinoisAreasView(OCDAreasView):
    
    def get_context_data(self, **kwargs):
        context = super(IllinoisAreasView, self).get_context_data(**kwargs)
        context['render_map'] = True

        for idx, area in enumerate(context['posts']):
            post_id = area['post_data']['id']
            chamber_slug = 'illinois-upper-2011'
            
            if 'house' in post_id:
                chamber_slug = 'illinois-lower-2011'
            
            fetch_url = '{0}/boundaries/{1}/{2}/shape'.format(OCD_BASE_URL, 
                                                              chamber_slug, 
                                                              post_id)
            
            area_geojson = requests.get(fetch_url).content
            context['posts'][idx]['post_data']['area_geojson'] = area_geojson

        return context

class IllinoisPostListView(TemplateView):
    template_name = 'candidates/posts.html'

    def get_context_data(self, **kwargs):
        context = super(IllinoisPostListView, self).get_context_data(**kwargs)
        context['all_posts'] = []

        memberships = \
            MembershipExtra.objects.order_by('election__name')\
                                   .select_related('base')\
                                   .select_related('election')\
                                   .prefetch_related('base__on_behalf_of')\
                                   .prefetch_related('base__person')\
                                   .prefetch_related('base__post')\
                                   .prefetch_related('base__post__extra')

        mem_grouper = lambda x: x.election
        post_grouper = lambda x: x.base.post.extra.slug

        for election, memberships in itertools.groupby(memberships, key=mem_grouper):
            person_posts = OrderedDict()
            
            memberships = sorted(memberships, key=post_grouper)

            for post_slug, post_group in itertools.groupby(memberships, key=post_grouper):

                post_group = list(post_group)
                post = post_group[0].base.post

                person_posts[post] = []

                for membership in post_group:
                    person_posts[post].append([membership.base.person, 
                                               membership.base.on_behalf_of])
                
            context['all_posts'].append((election, person_posts))

        return context
