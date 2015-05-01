from slugify import slugify

from django import template
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def constituency_in_year(person, year):
    standing_in = person.popit_data['standing_in']
    if year not in standing_in:
        if year == "2010":
            result = u'<span class="constituency-not-standing">Did not stand in 2010</span>'
        else:
            result = u'<span class="constituency-value-unknown">No information yet</span>'
    elif not standing_in[year]:
        if year == "2010":
            result = u'<span class="constituency-value-not-standing">Did not stand in 2010</span>'
        else:
            result = u'<span class="constituency-value-not-standing">Not standing in {0}</span>'
        result = result.format(year)
    else:
        link = u'<a href="{cons_url}">{cons_name}</a>'.format(
            cons_url=reverse(
                'constituency',
                kwargs={
                    'mapit_area_id': standing_in[year]['post_id'],
                    'ignored_slug': slugify(standing_in[year]['name']),
                }
            ),
            cons_name=standing_in[year]['name']
        )
        result = u'<span class="constituency-value-standing-link">{0}</span>'.format(
            link
        )
        result += u' <span class="party">{0}</span>'.format(
            person.party_memberships[year]['name']
        )
    return mark_safe(result)

@register.filter
def election_decision_known(person, year):
    standing_in = person.popit_data.get('standing_in') or {}
    if year not in standing_in:
        return False
    year_data = standing_in.get(year, {})
    return year_data.get('elected') is not None

@register.filter
def was_elected(person, year):
    standing_in = person.popit_data.get('standing_in') or {}
    if year not in standing_in:
        return False
    year_data = standing_in.get(year, {})
    return bool(year_data.get('elected'))
