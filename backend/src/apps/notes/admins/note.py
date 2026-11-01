from typing import TYPE_CHECKING, Any

from adminsortable2.admin import SortableAdminMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from import_export.formats.base_formats import CSV, XLSX
from import_export.resources import ModelResource
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm

from apps.notes.models import Note

if TYPE_CHECKING:
    NoteResourceBase = ModelResource[Note]
    NoteImportExportAdminBase = ImportExportModelAdmin[Note]
else:
    NoteResourceBase = ModelResource
    NoteImportExportAdminBase = ImportExportModelAdmin


class NoteResource(NoteResourceBase):
    created_at = Field(attribute="created_at", readonly=True)

    class Meta:
        model = Note
        fields = ("id", "text", "created_at")
        export_order = fields
        import_id_fields = ("id",)
        clean_model_instances = True
        skip_unchanged = True
        use_transactions = True

    def dehydrate_text(self, note: Note) -> str:
        # Public text must remain text when an exported CSV is opened in a spreadsheet.
        text = note.text
        if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")):
            return "'" + text
        return text

    def before_save_instance(self, instance: Note, row: dict[str, Any], **kwargs: Any) -> None:
        instance.text = instance.text.strip()
        instance.full_clean()


class NoteAdmin(SortableAdminMixin, SimpleHistoryAdmin, ModelAdmin, NoteImportExportAdminBase):  # type: ignore[misc]
    # The Admin extensions do not ship type information.
    # A writable attribute lets import-export wrap the sortable template.
    change_list_template = "adminsortable2/change_list.html"  # type: ignore[misc]
    resource_classes = [NoteResource]
    import_form_class = ImportForm
    export_form_class = ExportForm
    formats = [CSV, XLSX]
    list_display = ["id", "text", "created_at"]
    ordering = ["-position", "-id"]
    fields = ["text", "created_at"]
    readonly_fields = ["created_at"]
    search_fields = ["text"]
    list_filter = ["created_at"]

    def has_import_permission(self, request: HttpRequest) -> bool:
        return request.user.has_perms(["notes.add_note", "notes.change_note"])

    def history_form_view(
        self,
        request: HttpRequest,
        object_id: str,
        version_id: str,
        extra_context: dict[str, Any] | None = None,
    ) -> HttpResponse:
        # The library's revert setting hides UI only; history remains read-only on POST too.
        if request.method == "POST":
            raise PermissionDenied
        response: HttpResponse = super().history_form_view(
            request, object_id, version_id, extra_context
        )
        return response

    def _update_order(
        self, updated_items: list[tuple[int, int]], extra_model_filters: dict[str, Any]
    ) -> int:
        # Sortable's bulk_update skips the history signal; record it in the same transaction.
        with transaction.atomic():
            count: int = super()._update_order(updated_items, extra_model_filters)
            Note.history.bulk_history_create(
                list(Note.objects.filter(pk__in=[item[0] for item in updated_items])), update=True
            )
            return count
