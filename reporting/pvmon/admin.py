from pvmon.models import PVName, PV, PVCache
from django.contrib import admin
import datetime
    
class PVAdmin(admin.ModelAdmin):
    list_filter = ('instrument', 'name', 'status')
    list_display = ('id', 'instrument', 'name', 'value', 'status', 'update_time', 'get_timestamp')

    def get_timestamp(self, pv):
        return datetime.datetime.fromtimestamp(pv.update_time)
    get_timestamp.short_description = "Time"

class PVNameAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'monitored')
    list_editable = ('monitored',)
    
admin.site.register(PVName, PVNameAdmin)
admin.site.register(PV, PVAdmin)
admin.site.register(PVCache, PVAdmin)

