from datetime import date
from urlparse import urljoin

from django.conf import settings
from django.core.management.base import BaseCommand

import requests
import csv
import json

from candidates.models import AreaExtra, OrganizationExtra, PartySet, PostExtra
from elections.models import AreaType, Election
from popolo.models import Area, Organization, Post

class Command(BaseCommand):

    help = 'Create posts and elections for the 2016 Illinois General Primary'

    def handle(self, **options):
        
        #ocd_url = settings.OCD_BASE_URL

        sid = '267d6ad1-cf91-4d81-8ba6-782bceb4178d'
        api_key = '890cd250-a541-46d2-9217-332655bbce11'
        
        dedupe_url = 'http://127.0.0.1:5000/match/'
        sunshine_url = 'http://127.0.0.1:5001/api/elections/'

        field_mapping = {
            'office': 'office',
            'district': 'district',
            'district_type': 'district_type',
        }

        candidates = requests.get(sunshine_url, params={'election_type': 'General Primary', 
                                                        'election_year': '2016'})
        
        for row in candidates.json()['objects']:
            print('making the candidates')
