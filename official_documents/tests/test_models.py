"""
Basic smoke tests for OfficialDocument model
"""
import tempfile

from django.test import TestCase
from django.core.files import File

from official_documents.models import OfficialDocument

class TestModels(TestCase):

    def test_unicode(self):
        doc = OfficialDocument(
            mapit_id='XXX',
            source_url="http://example.com/",
        )

        self.assertEqual(unicode(doc), u"XXX (http://example.com/)")
