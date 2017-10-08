from rest_framework import serializers
from vehicle.models import RbsBeaconlogs, RbsBeaconActivities
from Employee.models import Employee, Asset
from django.core.files import File
import base64
import sys


class BeaconSerializer(serializers.ModelSerializer):
    class Meta:
        model = RbsBeaconlogs
        fields = ('logid', 'uuid', 'major', 'minor', 'macadr', 'txpower', 'rssi', 'rssi_int',
                  'event', 'longlat', 'devid', 'bundleid', 'status', 'logdate', 'ldate', 'ltime', 'slogdate')


class BeaconMvmntSerializer(serializers.ModelSerializer):
    class Meta:
        model = RbsBeaconActivities
        fields = ('logid', 'uuid', 'logdatetime', 'flogdate', 'fdate', 'ftime', 'tlogdate', 'tdate',
                  'ttime', 'duration', 'legsize', 'type', 'macadr', 'devid')


class EmployeeSerializer(serializers.ModelSerializer):
    # base64_image = serializers.SerializerMethodField()
    image_link = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ('emp_id', 'emp_first_name', 'emp_last_name', 'emp_card_id', 'description', 'emp_number',
                  'racf_id', 'buisness_unit', 'address_lat_long', 'address','city', 'state', 'pin_code',
                  'cost_center', 'organization', 'role', 'line_manager', 'image_link', 'phone_no', 'ext',
                  'mobile', 'email')

# send image in link format
    def get_image_link(self, obj):
        request = self.context.get('request')
        image_url = obj.image.url
        return request.build_absolute_uri(image_url)
        # i_link = sys.argv[-1] + "/media/" +obj.image.name
        # return i_link

# get org name
    def get_organization(self, obj):
        return obj.organization.organization_name

# send image in base64 string format

    # def get_base64_image(self, obj):
    #     f = open(obj.image.path, 'rb')
    #     image = File(f)
    #     data = base64.b64encode(image.read())
    #     f.close()
    #     return data


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ('asset_id', 'asset_name', 'asset_card_id', 'assigned_to', 'description')

