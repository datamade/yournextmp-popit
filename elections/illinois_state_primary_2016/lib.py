import re

from pygeocoder import Geocoder, GeocoderError
import requests

from elections.illinois_state_primary_2016.settings import OCD_BASE_URL


def get_cached_boundary(division_id):
    if cache.get(division_id):
        return cache.get(division_id)

    boundary = requests.get('{0}/boundaries/'.format(OCD_BOUNDARIES_URL),
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

    if cache.get(coords):
        return {'coords': coords}

    boundaries = requests.get('{0}/boundaries'.format(OCD_BOUNDARIES_URL),
                              params={'contains': coords})

    if boundaries.json()['meta']['total_count'] > 0:

        areas = set()

        for area in boundaries.json()['objects']:
            division_slug = area['external_id'].replace('/', ',')
            if cache.get(area['external_id']):
                areas.add(division_slug)
            elif not 'precinct' in division_slug:
                cache.set(area['external_id'], area, None)
                areas.add(division_slug)

        return {
            'area_ids': ';'.join(areas),
        }

    error = _(u"Unable to find constituency for '{0}'")
    raise ValidationError(error.format(tidied_address))
