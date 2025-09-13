from django.contrib import admin

from gchub_db.apps.art_req.models import (
    AdditionalInfo,
    ArtReq,
    ExtraProof,
    MarketSegment,
    PartialArtReq,
    Product,
)

admin.site.register(ArtReq)
admin.site.register(PartialArtReq)
admin.site.register(ExtraProof)
admin.site.register(Product)
# admin.site.register(CorrugatedProducts)
admin.site.register(AdditionalInfo)
admin.site.register(MarketSegment)
