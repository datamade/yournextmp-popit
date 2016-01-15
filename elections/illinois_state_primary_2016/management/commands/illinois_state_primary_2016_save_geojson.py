import json
from os.path import join, dirname, abspath

from django.core.management.base import BaseCommand

import requests

from elections.models import Election

class Command(BaseCommand):

    help = 'Create posts and elections for the 2016 Illinois General Primary'

    def handle(self, **options):
        
        elections = Election.objects.prefetch_related('posts').prefetch_related('posts__base')
        
        geojson = {}

        for election in elections:

            geojson[election.slug] = {
                'type': 'FeatureCollection',
                'features': [],
            }

            for post in election.posts.all():

                feature = {
                    'type': 'Feature',
                    'geometry': json.loads(post.base.area.geom),
                    'properties': {'label': post.base.label, 'id': post.base.area.name}
                }

                geojson[election.slug]['features'].append(feature)

        output_path = abspath(join(dirname(__file__), '..', '..', 'static'))

        for election_slug, geom in geojson.items():
            with open('{0}/{1}.geojson'.format(output_path, election_slug), 'w') as f:
                f.write(json.dumps(geom))
