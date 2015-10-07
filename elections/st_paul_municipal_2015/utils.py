import requests

from django.conf import settings
from django.core.cache import cache

from candidates.views.helpers import get_people_from_memberships, \
                                     group_people_by_party
from candidates.cache import get_post_cached
from candidates.popit import PopItApiMixin, get_all_posts
from candidates.forms import NewPersonForm


class CandidateListMixin(PopItApiMixin):

    def get_all_candidates(self):
        candidates = []
        for election, data in settings.ELECTIONS.items():
            areas = get_all_posts(data['for_post_role'])

            for area in areas:
                area_name, area_candidates = self.get_candidates_for_area(area['id'], 
                                                                          election, 
                                                                          data)
                candidates.append(area_candidates)
        return candidates

    def get_candidates_for_area(self, 
                                area_id,
                                election, 
                                election_data):
        
        ocd_division = area_id.replace(',', '/')
        
        post_data = get_post_cached(self.api, area_id)['result']
        boundary_data = get_cached_boundary(ocd_division)

        area_name = boundary_data['objects'][0]['name']

        locked = post_data.get('candidates_locked', False)

        current_candidates, _ = get_people_from_memberships(
            election_data,
            post_data['memberships']
        )
        
        current_candidates = group_people_by_party(
            election,
            current_candidates,
            party_list=election_data.get('party_lists_in_use')
        )
        
        post_data = {
            'election': election,
            'election_data': election_data,
            'post_data': post_data,
            'candidates_locked': locked,
            'candidates': current_candidates,
            'add_candidate_form': NewPersonForm(
                election=election,
                initial={
                    ('constituency_' + election): area_id,
                    ('standing_' + election): 'standing',
                },
                hidden_post_widget=True,
            ),
        }

        return area_name, post_data

def get_cached_boundary(division_id):
    
    from .settings import OCD_BOUNDARIES_URL
    
    if cache.get(division_id):
        return cache.get(division_id)

    boundary = requests.get('{0}/boundaries/'.format(OCD_BOUNDARIES_URL),
                            params={'external_id': division_id})
    cache.set(division_id, boundary.json(), None)

    return boundary.json()
