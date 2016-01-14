from datetime import date, datetime
from urlparse import urljoin
from random import randint

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

import requests
import csv
import json
import sys

from candidates.models import PersonExtra, MembershipExtra, OrganizationExtra
from elections.models import AreaType, Election
from popolo.models import Organization, Post, Person, Membership

class Command(BaseCommand):

    help = 'Load candidates for the 2016 Illinois General Primary'
    
    def add_arguments(self, parser):
        parser.add_argument('recreate-people')
    
    def get_party(self, party_name):
        org = Organization.objects.get(name__icontains=party_name)
        
        try:
            org_extra = OrganizationExtra.objects.get(base=org)
        except OrganizationExtra.DoesNotExist:
            org_extra = OrganizationExtra.objects.create(base=org,
                                                         slug=slugify(party_name))

        return org

    def get_post(self, ocd_division):
        
        return Post.objects.get(area__identifier=ocd_division)
    
    def get_election(self, office_name):
        election = None
        
        if 'Representative' in office_name:
            election = Election.objects.get(slug='il-gp-state-house-2016-03-15')
        
        elif 'Senator' in office_name:
            election = Election.objects.get(slug='il-gp-state-senate-2016-03-15')
        
        return election

    def handle(self, **options):
        
        if options['recreate-people']:
            for person in Person.objects.all():
                person.delete()

        dedupe_sid = 'b8736dce-a71c-4f62-9cc5-047c50d704ac'
        dedupe_api_key = '67d67454-8136-48da-ba54-e3094b759894'
        
        # dedupe_url = 'http://127.0.0.1:5000/match/'
        dedupe_url = 'https://dedupeapi.datamade.us/match/'
        sunshine_url = 'http://illinoissunshine.org/api/'

        field_mapping = {
            'office': 'office',
            'district': 'district',
            'district_type': 'districttype',
        }

        candidates = requests.get('{}elections/'.format(sunshine_url), 
                                  params={'election_type': 'General Primary', 
                                          'election_year': '2016'})
        
        for row in candidates.json()['objects']:
           
            election = self.get_election(row['office'])

            if election:
                
                print('Creating %s %s %s' % (row['first_name'], row['last_name'], row['office']) )

                name = '{0} {1}'.format(row['first_name'], row['last_name'])
                person, created = Person.objects.get_or_create(name=name)
                
                if created:
                    person_extra = PersonExtra.objects.create(base=person)
                    person_extra.record_version({
                        'information_source': 'New candidate from Illinois Sunshine',
                        'version_id': '{0:016x}'.format(randint(0, sys.maxint)),
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    person_extra.save()

                mapped_row = {}

                for fieldname, value in row.items():
                    if field_mapping.get(fieldname):

                        try:
                            mapped_row[field_mapping[fieldname]] = value.strip()
                        except AttributeError:
                            mapped_row[field_mapping[fieldname]] = ''

                place = row['office'].split('/')

                if len(place) > 1:
                    mapped_row['place'] = row['office'].split('/')[-1]
                else:
                    mapped_row['place'] = ''

                post_data = {
                    'session_id': dedupe_sid,
                    'api_key': dedupe_api_key,
                    'object': mapped_row,
                    'return_entity': 'true',
                }

                matches = requests.post(dedupe_url, data=json.dumps(post_data))
                
                if matches.json()['matches']:

                    sorted_matches = sorted(matches.json()['matches'], 
                                            key=lambda x: x['confidence'])

                    best_match = sorted_matches[-1]
                    
                    candidate_post = None
                    ocd_division_id = None
                    
                    for entity_id, records in best_match['entity_records'].items():
                        
                        for record in records:
                            if record.get('ocd_division'):
                                ocd_division_id = record['ocd_division']
                    
                    if ocd_division_id:
                        candidate_post = self.get_post(ocd_division_id)
                    
                    candidate_party = None
                    
                    if row.get('party'):
                        party_name = row['party'].strip()
                        if party_name:
                            candidate_party = self.get_party(party_name.rsplit(' ', 1)[0])

                    if candidate_post and candidate_party:

                        membership, created = Membership.objects.get_or_create(
                            on_behalf_of=candidate_party,
                            person=person,
                            post=candidate_post,
                            role=election.candidate_membership_role
                        )

                        if created:
                            membership_extra = MembershipExtra.objects.get_or_create(
                                base=membership,
                                election=election
                            )

                else:
                    print(mapped_row)

