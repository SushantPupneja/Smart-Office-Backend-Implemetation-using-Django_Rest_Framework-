from django.contrib import admin
from .models import Employee, Card, Asset, RoutesPlanner, EmployeeRole, BusinessUnit, CostCenter, \
    Organization, EmployeeRole, LineManager
# Register your models here.


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_name', 'emp_card_id', 'emp_number', 'racf_id', 'buisness_unit', \
                    'cost_center', 'organization', 'role', 'line_manager', 'ext', 'email')

    def employee_name(self,obj):
        return ("%s %s"%(obj.emp_first_name, obj.emp_last_name))


admin.site.register(Card)
admin.site.register(Asset)
# admin.site.register(DailyTrips)
# admin.site.register(RoutesPlanner)
admin.site.register(BusinessUnit)
admin.site.register(CostCenter)
admin.site.register(Organization)
admin.site.register(EmployeeRole)
admin.site.register(LineManager)
# admin.site.register(EmployeeAttendance)

