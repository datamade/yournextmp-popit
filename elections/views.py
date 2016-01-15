# -*- coding: utf-8 -*-

from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from django.core.urlresolvers import reverse

from candidates.forms import AddressForm, NewPersonForm
from candidates.models.popolo_extra import AreaExtra, MembershipExtra
from candidates.models.auth import get_edits_allowed
from candidates.views.helpers import split_candidacies, group_candidates_by_party
from candidates.views import AddressFinderView

from .models import AreaType, Election
from .lib import check_address

class OCDAddressForm(AddressForm):

    def clean_address(self):
        address = self.cleaned_data['address']
        check_address(address)
        return address

class OCDAddressFinder(AddressFinderView):

    form_class = OCDAddressForm
    country = 'United States'

    def form_valid(self, form):
        form.cleaned_data['address']
        area_ids, coords = check_address(
            form.cleaned_data['address'],
            country=self.country,
        )
        
        areas_url = '{0}?coords={1}'.format(reverse('areas-view'), coords)
        
        for area in area_ids:
            areas_url = '{0}&area_id={1}'.format(areas_url, area)

        return HttpResponseRedirect(areas_url)

class OCDAreasOfTypeView(TemplateView):
    template_name = 'candidates/areas-of-type.html'

    def get_context_data(self, **kwargs):
        context = super(OCDAreasOfTypeView, self).get_context_data(**kwargs)

        requested_area_type = kwargs['area_type']
        prefetch_qs = AreaExtra.objects.select_related('base').order_by('base__name')
        area_type = get_object_or_404(
            AreaType.objects \
                .prefetch_related(Prefetch('areas', queryset=prefetch_qs)),
            name=requested_area_type
        )
        areas = [
            (
                reverse(
                    'areas-view',
                    kwargs={
                        'type_and_area_ids': '{area_id}'.format(
                            area_id=re.sub(r'/', ',', area.base.identifier)
                        )
                    }
                ),
                area.base.name,
                requested_area_type,
            )
            for area in area_type.areas.all()
        ]
        context['areas'] = areas
        context['area_type'] = area_type
        return context

class OCDAreasView(TemplateView):
    template_name = 'candidates/areas.html'
    
    def get(self, request, *args, **kwargs):
        try:
            self.area_ids = request.GET.getlist('area_id')
        except KeyError:
            return HttpResponseRedirect('/')
        self.searched_coords = request.GET['coords'].split(',')
        view = super(OCDAreasView, self).get(request, *args, **kwargs)
        return view

    def get_context_data(self, **kwargs):
        context = super(OCDAreasView, self).get_context_data(**kwargs)

        all_area_names = set()
        context['posts'] = []

        area_ids = [id.replace(',', '/') for id in self.area_ids]

        all_area_names, area_context = self.get_areas_context(area_ids)

        context['posts'].extend(area_context)
        context['all_area_names'] = u' — '.join(all_area_names)
        context['suppress_official_documents'] = True

        return context

    def get_areas_context(self, area_ids):
        
        all_area_names = []
        area_context = []

        for area_id in area_ids:

            area_extra = get_object_or_404(
                AreaExtra.objects \
                    .select_related('base', 'type') \
                    .prefetch_related('base__posts'),
                base__identifier=area_id,
                base__posts__extra__elections__current=True
            )

            area = area_extra.base

            for post in area.posts.all():
                all_area_names.append(post.label)
                post_extra = post.extra
                election = post_extra.elections.get(current=True)
                locked = post_extra.candidates_locked
                extra_qs = MembershipExtra.objects.select_related('election')
                current_candidacies, _ = split_candidacies(
                    election,
                    post.memberships.prefetch_related(
                        Prefetch('extra', queryset=extra_qs)
                    ).select_related(
                        'person', 'person__extra', 'on_behalf_of',
                        'on_behalf_of__extra', 'organization'
                    ).all()
                )
                current_candidacies = group_candidates_by_party(
                    election,
                    current_candidacies,
                    party_list=election.party_lists_in_use,
                    max_people=election.default_party_list_members_to_show
                )
                area_context.append({
                    'election': election.slug,
                    'election_data': election,
                    'post_data': {
                        'id': post.extra.slug,
                        'label': post.label,
                    },
                    'candidates_locked': locked,
                    'candidate_list_edits_allowed':
                    get_edits_allowed(self.request.user, locked),
                    'candidacies': current_candidacies,
                    'add_candidate_form': NewPersonForm(
                        election=election.slug,
                        initial={
                            ('constituency_' + election.slug): post_extra.slug,
                            ('standing_' + election.slug): 'standing',
                        },
                        hidden_post_widget=True,
                    ),
                })

        return all_area_names, area_context

