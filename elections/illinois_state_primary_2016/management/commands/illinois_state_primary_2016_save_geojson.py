import json
from os.path import join, dirname, abspath

from django.core.management.base import BaseCommand

import requests

from popolo.models import Post

class Command(BaseCommand):

    help = 'Create posts and elections for the 2016 Illinois General Primary'

    def handle(self, **options):
        
        posts = Post.objects.select_related('area')
        
        geojson = {
            'illinois-upper-2011': {
                'type': 'FeatureCollection',
                'features': [],
            },
            'illinois-lower-2011': {
                'type': 'FeatureCollection',
                'features': [],
            }
        }

        for post in posts:

            feature = {
                'type': 'Feature',
                'geometry': json.loads(post.area.geom),
                'properties': {'label': post.label, 'id': post.area.name}
            }

            if 'house' in post.area.name:
                geojson['illinois-lower-2011']['features'].append(feature)
            else:
                geojson['illinois-upper-2011']['features'].append(feature)

        output_path = abspath(join(dirname(__file__), '..', '..', 'static'))

        for chamber_slug, geom in geojson.items():
            with open('{0}/{1}.geojson'.format(output_path, chamber_slug), 'w') as f:
                f.write(json.dumps(geom))
