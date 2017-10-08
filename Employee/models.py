from __future__ import unicode_literals
from django.db import models

# below are custom field can be used instead of django model fields , for mysql version > 5.6 django create datetime field in mysql with microseconds format that is datetime(6) , hence instead use custom fields like below 
class CustomSlogDateField(models.Field):
    def db_type(self,connection):
        return 'datetime default CURRENT_TIMESTAMP'


class CustomDateField(models.Field):
    def db_type(self,connection):
        return 'datetime'

class CustomTimeField(models.Field):
    def db_type(self,connection):
        return 'time'

# Create your models here.
class Card(models.Model):
    card_id = models.AutoField(primary_key=True, db_column='CardId')
    uuid = models.CharField(max_length=200, null=False, blank=False, db_column='UUID')
    CARD_TYPE = (('Beacon', 'Beacon'), ('RFID', 'RFID'))
    card_type = models.CharField(max_length=50, choices=CARD_TYPE, default='Beacon', db_column='CardType')
    is_allotted = models.BooleanField()
    description = models.TextField(db_column='description', max_length=300, blank=True, null=True) # desp

    class Meta:
        db_table = 'Cards' #

    def __str__(self):
        return self.uuid


class Asset(models.Model):
    asset_id = models.AutoField(db_column='AssetId', primary_key=True)  # Field name made lowercase.
    asset_name = models.CharField(db_column='Asset', max_length=100)  # Field name made lowercase.
    description = models.TextField(blank=True, null=True)
    # asset_card_id = models.OneToOneField('Card', models.DO_NOTHING, default="1", db_column='AssetCardId')
    asset_card_id = models.CharField(db_column='CardId', max_length=100, default=None)
    assigned_to = models.ForeignKey('Employee', models.DO_NOTHING,  db_column='AssignedTo', default="1")  # Field name made lowercase.

    class Meta:
        db_table = 'Assets'

    def __str__(self):
        return self.asset_name


class BusinessUnit(models.Model):
    business_unit_id = models.AutoField(primary_key=True, db_column="BusinessUnitID")
    business_unit_name = models.CharField(max_length=100, db_column="BusinessUnitName")
    description = models.TextField(max_length=300, db_column="Description", blank=True, null=True)

    class Meta:
        db_table = "BusinessUnits"

    def __str__(self):
        return self.business_unit_name


class CostCenter(models.Model):
    cost_center_id = models.AutoField(primary_key=True, db_column="CostCenterID")
    cost_center_name = models.CharField(max_length=100, db_column="CostCenterName")
    description = models.TextField(max_length=300, db_column="Description",blank=True, null=True)

    class Meta:
        db_table = "CostCenters"

    def __str__(self):
        return self.cost_center_name


class Organization(models.Model):
    organization_id = models.AutoField(primary_key=True, db_column="OrganisationID")
    organization_name = models.CharField(max_length=100, db_column="OrganisationName")
    description = models.TextField(max_length=300, db_column="Description", blank=True, null=True)

    class Meta:
        db_table = "Organizations"

    def __str__(self):
        return self.organization_name


class EmployeeRole(models.Model):
    role_id = models.AutoField(primary_key=True, db_column="RoleId")
    role_name = models.CharField(max_length=100, db_column="RoleName")
    description = models.TextField(max_length=300, db_column="Description", blank=True, null=True)

    class Meta:
        db_table = "EmployeeRoles"

    def __str__(self):
        return self.role_name


class LineManager(models.Model):
    line_manager_id = models.AutoField(primary_key=True, db_column="LineManagerId")
    line_manager_name = models.CharField(max_length=100, db_column="LineManagerName")
    description = models.TextField(max_length=300, db_column="Description", blank=True, null=True)

    class Meta:
        db_table = "LineManagers"

    def __str__(self):
        return self.line_manager_name


class Employee(models.Model):
    emp_id = models.AutoField(db_column='EmpId', primary_key=True)
    emp_first_name = models.CharField(db_column='FirstName', max_length=30, blank=False, null=False)
    emp_last_name = models.CharField(db_column='LastName', max_length=30, blank=False, null=False)
    emp_card_id = models.CharField(db_column='CardId', max_length=100, default=None)
    emp_number = models.IntegerField(db_column="EmpNumber") #7868621
    racf_id = models.CharField(db_column="RACF_Id", max_length=20)
    buisness_unit = models.ForeignKey("BusinessUnit", db_column="BusinessUnit", max_length=20)
    cost_center = models.ForeignKey("CostCenter", db_column="CostCenter", max_length=20)
    organization = models.ForeignKey("Organization", db_column="Organization", max_length=20)
    role = models.ForeignKey("EmployeeRole", db_column="Role", max_length=20)
    line_manager = models.ForeignKey("LineManager", db_column="LineManager", max_length=20)
    image = models.ImageField(blank=True, null=True)
    description = models.TextField(db_column='Description', max_length=300, blank=True, null=True)  #desp
    address_lat_long = models.CharField(db_column='AddressLatLong', max_length=200)
    address = models.CharField(db_column='Address', max_length=200)
    city = models.CharField(db_column='City', max_length=100)
    state = models.CharField(db_column='state', max_length=100)
    pin_code = models.IntegerField(db_column='PinCode')
    phone_no = models.IntegerField(db_column='Phone', null=True, blank=True)
    ext = models.IntegerField(db_column='Ext', null=True, blank=True)
    mobile = models.IntegerField(db_column="Mobile")
    email = models.EmailField(db_column='Email')

    class Meta:
        db_table = 'Employees' #

    def __str__(self):
        return self.emp_first_name + ' ' + self.emp_last_name


class EmpAttendance(models.Model):
    log_id = models.AutoField(db_column='LogId', primary_key=True)
    emp_name = models.CharField(db_column="Employee", max_length=50)
    emp_card_id = models.CharField(db_column='EmpCardId', max_length=200, blank=False, null=False)
    emp_id = models.CharField(db_column='EmpId', max_length=50)
    racf_id = models.CharField(db_column='RacfID', max_length=50)
    role = models.CharField(db_column='Role', max_length=50)
    organization = models.CharField(db_column='Organization', max_length=50)
    business_unit = models.CharField(db_column='BusinessUnit', max_length=50)
    cost_center = models.CharField(db_column='CostCenter', max_length=50, blank=True, null=True)
    line_manager = models.CharField(db_column='LineManager', max_length=50)
    date = models.DateField(db_column='Date')
    enter_time = models.TimeField(db_column='EnterTime')
    exit_time = models.TimeField(db_column="ExitTime")
    duration = models.FloatField(db_column='PresentHours')
    is_present = models.BooleanField()
    slog_date = models.DateTimeField(db_column="SlogDate", auto_now_add=True, auto_now=False)

    class Meta:
        db_table = 'EmpAttendance'

    def __str__(self):
        return self.emp_name


class RoutesPlanner(models.Model):
    route_id = models.AutoField(primary_key=True, db_column='RouteId')
    # trip_allocated = models.ForeignKey('Trip', db_column='TripAllocated', on_delete=models.CASCADE)
    # vehicle_allocated = models.ForeignKey('vehicle.Vehicle', db_column='VehicleID', on_delete=models.CASCADE)
    # emp_board = models.ManyToManyField('Employee')

    class Meta:
        db_table = 'RoutesPlanner'

    def __str__(self):
        return str(self.route_id)


class Piractivities(models.Model):
    logid = models.AutoField(db_column='LogID', primary_key=True)  # Field name made lowercase.
    uuid = models.CharField(db_column='UUID', max_length=50, blank=True, null=True)  # Field name made lowercase.
    startdatetime = models.DateTimeField(db_column='StartDatetime', blank=True, null=True)  # Field name made lowercase.
    startdate = models.DateField(db_column='StartDate', blank=True, null=True)  # Field name made lowercase.
    starttime = models.TimeField(db_column='StartTime', blank=True, null=True)  # Field name made lowercase.
    enddatetime = models.DateTimeField(db_column='EndDatetime', blank=True, null=True)  # Field name made lowercase.
    enddate = models.DateField(db_column='EndDate', blank=True, null=True)  # Field name made lowercase.
    endtime = models.TimeField(db_column='EndTime', blank=True, null=True)  # Field name made lowercase.
    duration = models.IntegerField(db_column='Duration', blank=True, null=True)  # Field name made lowercase.
    logsize = models.IntegerField(db_column='LogSize', blank=True, null=True)  # Field name made lowercase.
    type = models.CharField(db_column='Type', max_length=20, blank=True, null=True)  # Field name made lowercase.
    devid = models.CharField(db_column='DevId', max_length=20, blank=True, null=True)  # Field name made lowercase.
    slogdate = models.DateTimeField(db_column='SLogDate', blank=True, null=True)  # Field name made lowercase.
    status = models.IntegerField(blank=True, null=True)
    rssi_avg = models.IntegerField(db_column='RSSI_AVG', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        db_table = 'PIRActivities'

class Pirlogs(models.Model):
    logid = models.AutoField(db_column='Logid', primary_key=True)  # Field name made lowercase.
    uuid = models.CharField(db_column='UUID', max_length=50, blank=True, null=True)  # Field name made lowercase.
    major = models.CharField(db_column='MAJOR', max_length=10, blank=True, null=True)  # Field name made lowercase.
    minor = models.CharField(db_column='MINOR', max_length=10, blank=True, null=True)  # Field name made lowercase.
    macadr = models.CharField(db_column='MacAdr', max_length=20, blank=True, null=True)  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=20, blank=True, null=True)  # Field name made lowercase.
    pir = models.IntegerField(db_column='PIR', blank=True, null=True)  # Field name made lowercase.
    txpower = models.CharField(db_column='TxPower', max_length=4, blank=True, null=True)  # Field name made lowercase.
    rssi = models.IntegerField(db_column='RSSI', blank=True, null=True)  # Field name made lowercase.
    longlat = models.CharField(db_column='LongLat', max_length=60, blank=True, null=True)  # Field name made lowercase.
    devid = models.CharField(db_column='DevId', max_length=15, blank=True, null=True)  # Field name made lowercase.
    bundleid = models.IntegerField(db_column='BundleId', blank=True, null=True)  # Field name made lowercase.
    status = models.IntegerField(blank=True, null=True)
    logdate = models.DateTimeField(db_column='LogDate', blank=True, null=True)  # Field name made lowercase.
    ldate = models.DateField(db_column='LDate', blank=True, null=True)  # Field name made lowercase.
    ltime = models.TimeField(db_column='LTIME', blank=True, null=True)  # Field name made lowercase.
    slogdate = models.DateTimeField(db_column='SLogDate')  # Field name made lowercase.
    type = models.CharField(db_column='Type', max_length=20, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        db_table = 'PIRLogs'
