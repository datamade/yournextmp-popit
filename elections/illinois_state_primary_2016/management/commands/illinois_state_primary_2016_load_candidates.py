from datetime import date, datetime
from urlparse import urljoin
from random import randint

from django.conf import settings
from django.core.management.base import BaseCommand

import requests
import csv
import json
import sys

from candidates.models import PersonExtra
from elections.models import AreaType, Election
from popolo.models import Organization, Post, Person

class Command(BaseCommand):

    help = 'Load candidates for the 2016 Illinois General Primary'
    
    def get_party(self, party_name):

        return Organization.objects.get(name__icontains=party_name)

    def get_post(self, ocd_division):
        
        return Post.objects.get(area__identifier=ocd_division)
    
    def get_election(self, office_name):
        # TODO: Get the correct election
        if 'House' in office_name:
            return Election.objects.get()

    def handle(self, **options):
        
        #ocd_url = settings.OCD_BASE_URL

        dedupe_sid = '267d6ad1-cf91-4d81-8ba6-782bceb4178d'
        dedupe_api_key = '890cd250-a541-46d2-9217-332655bbce11'
        
        dedupe_url = 'http://127.0.0.1:5000/match/'
        sunshine_url = 'http://127.0.0.1:5001/api/'

        field_mapping = {
            'office': 'office',
            'district': 'district',
            'district_type': 'district_type',
        }

        candidates = requests.get('{}elections/'.format(sunshine_url), 
                                  params={'election_type': 'General Primary', 
                                          'election_year': '2016'})
        
        for row in candidates.json()['objects']:
            name = '{0} {1}'.format(row['first_name'], row['last_name'])
            person, created = Person.objects.get_or_create(name=name)
            
            if created:
                person_extra = PersonExtra.objects.create(base=person)
                person_extra.record_version({
                    'information_source': 'New candidate from CSV',
                    'version_id': '{0:016x}'.format(randint(0, sys.maxint)),
                    'timestamp': datetime.utcnow().isoformat()
                })

            mapped_row = {}

            for fieldname, value in row.items():
                if field_mapping.get(fieldname):

                    try:
                        mapped_row[field_mapping[fieldname]] = value.strip()
                    except AttributeError:
                        mapped_row[field_mapping[fieldname]] = ''

            
            place = row['office'].rsplit('/', 1)
            if len(place) == 1:
                place = ''
            else:
                place = place[1]

            mapped_row['place'] = place

            post_data = {
                'session_id': dedupe_sid,
                'api_key': dedupe_api_key,
                'object': mapped_row,
                'return_entity': 'true',
            }

            matches = requests.post(dedupe_url, data=json.dumps(post_data))
            
            if matches.json()['matches']:

                sorted_matches = sorted(matches.json()['matches'], 
                                        key=lambda x: x['match_confidence'])

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

                if candidate_party and candidate_post:


            else:
                print(mapped_row)
                print(row['id'], row['first_name'], row['last_name'])
