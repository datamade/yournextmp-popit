# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from auth_helpers.migrations import (
    get_migration_group_create,
    get_migration_group_delete,
)
from official_documents.models import DOCUMENT_UPLOADERS_GROUP_NAME


class Migration(migrations.Migration):

    dependencies = [
        ('official_documents', '0002_officialdocument_document_type'),
    ]

    operations = [
        migrations.RunPython(
            get_migration_group_create(
                DOCUMENT_UPLOADERS_GROUP_NAME, ['add_officialdocument']
            ),
            get_migration_group_delete(
                DOCUMENT_UPLOADERS_GROUP_NAME
            )
        ),
        migrations.RunPython(
            get_migration_group_create(
                DOCUMENT_UPLOADERS_GROUP_NAME, ['change_officialdocument']
            ),
            get_migration_group_delete(
                DOCUMENT_UPLOADERS_GROUP_NAME
            )
        )
    ]
