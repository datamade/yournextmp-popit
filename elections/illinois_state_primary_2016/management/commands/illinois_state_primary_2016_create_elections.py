
from datetime import date
from urlparse import urljoin

from django.conf import settings
from django.core.management.base import BaseCommand

import requests

from candidates.models import AreaExtra, OrganizationExtra, PartySet, PostExtra
from elections.models import AreaType, Election
from popolo.models import Area, Organization, Post

class Command(BaseCommand):

    help = 'Create posts and elections for the 2016 Illinois General Primary'

    def handle(self, **options):
        
        #ocd_url = settings.OCD_BASE_URL
        ocd_url = 'http://ocd.datamade.us'


        il_parties, _ = PartySet.objects.get_or_create(
            slug='us-il', defaults={'name': 'Illnois'}
        )

        elections = {
            'il-gp-state-house-2016-03-15': {
                'name': '2016 Illinois House of Representatives - General Primary',
                'for_post_role': 'Member of the Illinois House of Representatives',
                'label_format': 'Illinois House of Representatives, District {area_name}',
                'area_generation': 22,
                'election_date': date(2016, 5, 5),
                'party_lists_in_use': False,
                'post_id_format': 'ocd-division/country:us/state:il/sldl:{district_number}',
                'area_type_description': 'Illinois House of Representatives District',
                'organization_slug': 'illinois-house',
                'organization_name': 'Illinois House of Representatives',
                'area_type_name': 'illinois-lower-2011',
            },
            'il-gp-state-senate-2016-03-15': {
                'name': '2016 Illinois Senate - General Primary',
                'for_post_role': 'Member of the Illinois Senate',
                'label_format': 'Illinois Senate, District {area_name}',
                'area_generation': 22,
                'election_date': date(2016, 5, 5),
                'party_lists_in_use': False,
                'post_id_format': 'ocd-division/country:us/state:il/sldu:{district_number}',
                'area_type_description': 'Illinois Senate District',
                'organization_slug': 'illinois-senate',
                'organization_name': 'Illinois Senate',
                'area_type_name': 'illinois-upper-2011',
            },
        }

        for election_slug, data in elections.items():
            # Make sure the parliament Organization and
            # OrganizationExtra objects exist:
            try:
                organization_extra = OrganizationExtra.objects.get(
                    slug=data['organization_slug']
                )
                organization = organization_extra.base
            except OrganizationExtra.DoesNotExist:
                organization = Organization.objects.create(
                    name=data['organization_name']
                )
                organization_extra = OrganizationExtra.objects.create(
                    base=organization,
                    slug=data['organization_slug']
                )
            # Make sure the Election object exists:
            election_defaults = {
                k: data[k] for k in
                [
                    'name', 'for_post_role', 'election_date',
                    'party_lists_in_use', 'post_id_format',
                ]
            }
            election_defaults['current'] = True
            election_defaults['candidate_membership_role'] = 'Candidate'
            print 'Creating:', election_defaults['name'], '...',
            election, created = Election.objects.update_or_create(
                slug=election_slug,
                defaults=election_defaults
            )
            if created:
                print '[created]'
            else:
                print '[already existed]'

            area_type, _ = AreaType.objects.update_or_create(
                name=data['area_type_name'], defaults={'source': 'OCD'}
            )
            url_path = '/boundaries/' + data['area_type_name'] + '?limit=0'
            url = urljoin(ocd_url, url_path)
            r = requests.get(url)

            for ocd_area in r.json()['objects']:

                area, _ = Area.objects.update_or_create(
                    identifier=ocd_area['external_id'],
                    defaults={'name': ocd_area['name']}
                )

                AreaExtra.objects.get_or_create(base=area, type=area_type)
                post, _ = Post.objects.update_or_create(
                    organization=organization,
                    area=area,
                    role=election_defaults['for_post_role'],
                    defaults={'label': data['label_format'].format(
                                     area_name=int(ocd_area['name'].rsplit('-', 1)[1]))}
                )
                post_extra, _ = PostExtra.objects.update_or_create(
                    base=post,
                    defaults={
                        'slug': ocd_area['name'],
                        'party_set': il_parties,
                    },
                )
                post_extra.elections.add(election)
