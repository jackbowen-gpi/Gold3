"""Admin interface models. Automatically detected by admin.autodiscover()."""

import django.forms as forms
from django.contrib import admin
from django.contrib.auth.models import Permission, User

from gchub_db.apps.workflow.models import PrintLocation

from .models import (
    BevItemColorCodes,
    BeverageBrandCode,
    BeverageCenterCode,
    CartonProfile,
    CartonWorkflow,
    Charge,
    ChargeCategory,
    ChargeType,
    ColorWarning,
    Customer,
    InkSet,
    Item,
    ItemCatalog,
    ItemColor,
    ItemReview,
    ItemSpec,
    ItemTracker,
    ItemTrackerCategory,
    ItemTrackerType,
    Job,
    JobAddress,
    JobComplexity,
    LineScreen,
    PlateOrder,
    PlateOrderItem,
    Platemaker,
    Plant,
    PlatePackage,
    Press,
    PrintCondition,
    ProofTracker,
    Revision,
    SalesServiceRep,
    SpecialMfgConfiguration,
    StepSpec,
    Substrate,
    TiffCrop,
    TrackedArt,
    Trap,
)


class RevisionAdmin(admin.ModelAdmin):
    list_display = (
        "item",
        "creation_date",
        "due_date",
        "complete_date",
        "comments",
        "entered_by",
    )
    date_hierarchy = "creation_date"
    exclude = ("item",)


admin.site.register(Revision, RevisionAdmin)


class JobAdmin(admin.ModelAdmin):
    search_fields = ["name", "id"]
    list_filter = ("workflow",)
    list_display = (
        "id",
        "name",
        "salesperson",
        "creation_date",
        "due_date",
        "artist",
        "status",
        "workflow",
    )
    # ordering = ('-job',)
    exclude = ("duplicated_from",)
    date_hierarchy = "creation_date"


admin.site.register(Job, JobAdmin)


class JobComplexityAdmin(admin.ModelAdmin):
    search_fields = ["job__id", "category"]
    list_filter = ("category",)
    list_display = ("job", "category", "complexity")
    exclude = ("job",)


admin.site.register(JobComplexity, JobComplexityAdmin)

"""
class ItemAdmin(admin.ModelAdmin):
    search_fields = ['size__size', 'job__id']
    list_filter = ('workflow', )
    list_display = ('__unicode__', 'num_in_job', 'job', 'creation_date',
                    'printlocation')
    ordering = ('-job', )
    exclude = ('job', 'ink_usage')
    date_hierarchy = 'creation_date'
"""


class ItemAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ItemAdminForm, self).__init__(*args, **kwargs)
        instance = kwargs.get("instance", None)
        if instance is not None:
            steps_withField = self.fields["steps_with"]
            steps_withField.queryset = steps_withField.queryset.filter(
                job=instance.job
            ).exclude(id=instance.id)

    class Meta:
        model = Item
        fields = "__all__"


class ItemAdmin(admin.ModelAdmin):
    search_fields = ["size__size", "job__id"]
    list_filter = ("workflow",)
    list_display = (
        "__unicode__",
        "num_in_job",
        "job",
        "creation_date",
        "printlocation",
    )
    ordering = ("-job",)
    exclude = ("job", "ink_usage")
    date_hierarchy = "creation_date"
    form = ItemAdminForm


admin.site.register(Item, ItemAdmin)


class PrintLocationCatalogAdmin(admin.ModelAdmin):
    list_display = ("plant", "press", "active")
    ordering = ("plant__name",)


admin.site.register(PrintLocation, PrintLocationCatalogAdmin)


class ProofTrackerAdmin(admin.ModelAdmin):
    search_fields = ["item__job__id", "xml_filename"]
    list_display = ("get_jobnum", "creation_date", "copies", "xml_filename", "proofer")
    list_filter = (
        "creation_date",
        "proofer",
    )
    exclude = ("item",)

    # Displays the item by it's job number and number within the job.
    def get_jobnum(self, obj):
        return "%s - %s" % (obj.item.job.id, obj.item.num_in_job)

    get_jobnum.admin_order_field = "item"  # Allows column order sorting
    get_jobnum.short_description = "Item"  # Renames column head


admin.site.register(ProofTracker, ProofTrackerAdmin)


class ItemCatalogAdmin(admin.ModelAdmin):
    search_fields = ["size", "mfg_name"]
    list_display = (
        "size",
        "product_board",
        "mfg_name",
        "product_substrate",
        "active",
        "workflow",
        "bev_size_code",
        "acts_like",
    )
    list_filter = ("workflow", "active", "product_substrate", "productsubcategory")


admin.site.register(ItemCatalog, ItemCatalogAdmin)


class ItemSpecAdmin(admin.ModelAdmin):
    search_fields = ["size__size"]
    # Some fields got moved to the stepspec model.
    #    list_display = ('size', 'printlocation', 'active', 'num_colors', 'min_case',
    #                    'step_around', 'step_across', 'num_blanks')
    list_display = ("size", "printlocation", "active", "min_case")
    #    list_editable = ('num_colors', 'active', 'min_case', 'step_around',
    #                     'step_across')
    list_editable = ("active", "min_case")
    list_filter = ("active", "printlocation")


admin.site.register(ItemSpec, ItemSpecAdmin)


class StepSpecAdmin(admin.ModelAdmin):
    search_fields = ["itemspec__size__size", "itemspec__printlocation__plant__name"]
    list_display = (
        "itemspec",
        "special_mfg",
        "num_colors",
        "active",
        "status",
        "step_around",
        "step_across",
        "print_repeat",
        "num_blanks",
    )
    list_editable = (
        "special_mfg",
        "num_colors",
        "active",
        "status",
        "step_around",
        "step_across",
        "print_repeat",
    )
    list_filter = ("active", "special_mfg")


admin.site.register(StepSpec, StepSpecAdmin)


class ChargeTypeAdmin(admin.ModelAdmin):
    search_fields = ["type"]
    list_display = (
        "type",
        "category",
        "base_amount",
        "active",
        "rush_type",
        "adjust_for_colors",
        "extra_amount",
    )
    list_filter = ("workflow", "active")
    ordering = ("category", "type")


admin.site.register(ChargeType, ChargeTypeAdmin)


class ChargeAdmin(admin.ModelAdmin):
    search_fields = ["item__size__size", "item__bev_item_name"]
    list_display = ("__unicode__", "item", "description", "amount")
    list_filter = ("description", "invoice_date")
    exclude = ("item", "bev_invoice")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "artist":
            permission = Permission.objects.get(codename="in_artist_pulldown")
            kwargs["queryset"] = User.objects.filter(
                is_active=True, groups__in=permission.group_set.all()
            ).order_by("username")
        return super(ChargeAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )


admin.site.register(Charge, ChargeAdmin)


class ColorWarningAdmin(admin.ModelAdmin):
    search_fields = ["definition__name"]
    list_display = ("definition", "date_added", "qpo_number")
    ordering = ("-date_added",)


admin.site.register(ColorWarning, ColorWarningAdmin)


class ItemColorAdmin(admin.ModelAdmin):
    search_fields = ["color"]
    list_display = ("item", "color", "sequence", "plate_code", "delta_e")
    ordering = ("-item",)
    exclude = ("item",)


admin.site.register(ItemColor, ItemColorAdmin)


class PlateOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "item",
        "date_entered",
        "requested_by",
        "new_order",
        "stage2_complete_date",
    )
    list_filter = ("new_order",)
    date_hierarchy = "date_entered"
    exclude = ("item",)


admin.site.register(PlateOrder, PlateOrderAdmin)


class PlateOrderItemAdmin(admin.ModelAdmin):
    exclude = (
        "order",
        "color",
    )


admin.site.register(PlateOrderItem, PlateOrderItemAdmin)


class PlantAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "workflow",
        "code",
    )
    list_filter = ("workflow",)
    filter_horizontal = ("bev_controller",)


admin.site.register(Plant, PlantAdmin)


class ItemReviewAdmin(admin.ModelAdmin):
    search_fields = ["item__job__id"]
    exclude = ("item",)


admin.site.register(ItemReview, ItemReviewAdmin)


class TrackedArtAdmin(admin.ModelAdmin):
    exclude = ("item",)


admin.site.register(TrackedArt, TrackedArtAdmin)


class ItemTrackerAdmin(admin.ModelAdmin):
    exclude = ("item",)


admin.site.register(ItemTracker, ItemTrackerAdmin)


class TiffCropAdmin(admin.ModelAdmin):
    search_fields = ["plant__name", "size__size", "num_up", "special_mfg__name"]


admin.site.register(TiffCrop, TiffCropAdmin)


class SubstrateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "active",
    )
    list_filter = ("active",)
    ordering = ("name",)
    search_fields = ["name"]


admin.site.register(Substrate, SubstrateAdmin)


class CartonProfileAdminForm(forms.ModelForm):
    # Used to limit the print location field to carton plants.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["print_location"].queryset = PrintLocation.objects.filter(
            plant__workflow__name="Carton"
        )


class CartonProfileAdmin(admin.ModelAdmin):
    form = CartonProfileAdminForm
    list_display = ("name", "active")
    list_filter = (
        "carton_workflow",
        "line_screen",
        "ink_set",
        "substrate",
        "print_condition",
    )
    filter_horizontal = (
        "carton_workflow",
        "print_location",
        "line_screen",
        "ink_set",
        "substrate",
        "print_condition",
    )


admin.site.register(CartonProfile, CartonProfileAdmin)

"""
Take the default admin classes for these.
"""
admin.site.register(Press)
admin.site.register(Platemaker)
admin.site.register(SpecialMfgConfiguration)
admin.site.register(PlatePackage)
admin.site.register(BevItemColorCodes)
admin.site.register(ChargeCategory)
admin.site.register(Customer)
admin.site.register(JobAddress)
admin.site.register(SalesServiceRep)
admin.site.register(BeverageBrandCode)
admin.site.register(BeverageCenterCode)
admin.site.register(ItemTrackerType)
admin.site.register(ItemTrackerCategory)
admin.site.register(CartonWorkflow)
admin.site.register(LineScreen)
admin.site.register(InkSet)
admin.site.register(PrintCondition)
admin.site.register(Trap)
