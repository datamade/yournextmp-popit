from django.db import models

from popolo.models import Person


class ExtraField(models.Model):

    LINE = 'line'
    LONGER_TEXT = 'longer-text'
    URL = 'url'

    FIELD_TYPES = (
        (LINE, 'A single line of text'),
        (LONGER_TEXT, 'One or more paragraphs of text'),
        (URL, 'A URL')
    )

    key = models.CharField(max_length=256)
    type = models.CharField(
        max_length=64,
        choices=FIELD_TYPES,
    )
    label = models.CharField(max_length=1024)

    def __unicode__(self):
        return self.key


class PersonExtraFieldValue(models.Model):

    class Meta:
        unique_together = (('person', 'field'))

    person = models.ForeignKey(Person, related_name='extra_field_values')
    field = models.ForeignKey(ExtraField)
    value = models.TextField(blank=True)
