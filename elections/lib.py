import re
import importlib

from django.core.cache import cache
from django.conf import settings 
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError

from pygeocoder import Geocoder, GeocoderError
import requests

election_app = settings.ELECTION_APP_FULLY_QUALIFIED
settings = importlib.import_module('{}.settings'.format(election_app))

def get_cached_ocd_boundary(division_id):
    if cache.get(division_id):
        return cache.get(division_id)

    boundary = requests.get('{0}/boundaries/'.format(settings.OCD_BASE_URL),
                            params={'external_id': division_id})
    
    area_blob = boundary.json()['objects'][0]
    cache.set(division_id, area_blob, None)

    return area_blob

def check_address(address_string, country=None):
    tidied_address = address_string.strip()

    if country is not None:
        tidied_address += ', ' + country

    try:
        location_results = Geocoder.geocode(tidied_address)
    except GeocoderError:
        message = _(u"Failed to find a location for '{0}'")
        raise ValidationError(message.format(tidied_address))

    coords = ','.join([str(p) for p in location_results[0].coordinates])

    boundaries = requests.get('{0}/boundaries'.format(settings.OCD_BASE_URL),
                              params={'contains': coords})

    if boundaries.json()['meta']['total_count'] > 0:

        areas = set()

        for area in boundaries.json()['objects']:

            division_id = area['external_id']

            if 'sldl' in division_id or 'sldu' in division_id:
                division_slug = area['external_id'].replace('/', ',')

                if cache.get(division_id):
                    areas.add(division_slug)
                else:
                    cache.set(division_id, area, None)
                    areas.add(division_slug)
        
        return areas, coords

    error = _(u"Unable to find constituency for '{0}'")
    raise ValidationError(error.format(tidied_address))
