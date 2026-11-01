from django.contrib import admin

from apps.notes.admins.note import NoteAdmin
from apps.notes.models import Note

admin.site.register(Note, NoteAdmin)
