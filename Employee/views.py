# imports
from django.http import HttpResponse
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from RBS import utility as config
from rest_framework import status, generics #authentication, #permissions
from Employee.serializers import BeaconSerializer, BeaconMvmntSerializer, EmployeeSerializer, AssetSerializer
# from django.db.models import Count, Max
from vehicle.models import RbsBeaconlogs, RbsBeaconActivities
from Employee.models import Employee, Asset, EmpAttendance , Piractivities
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.db import connection

# from rest_framework.decorators import APIView

from datetime import datetime, timedelta
# from django.core.files.storage import FileSystemStorage
# Create your views here.
# from django.contrib import messages


# wrapper function
def decorator_function(original_function):

    def wrapper_function(*args, **kwargs):
        print ("'{}' API requested".format(__name__))
        return original_function(*args, **kwargs)
    return wrapper_function


# ------------ Views _______________
class beacon_tracking(generics.GenericAPIView):
    """
           Return a list of all employees and assets with latest location.
    """
    @csrf_exempt
    @decorator_function
    def get(self, request, format=None):
        print request.resolver_match.view_name
        sql = "SELECT BL.Logid, BL.UUID,BL.LongLat,MAX(logdate),(SELECT BL1.DevId from RBS_BeaconLogs BL1 where \
                    BL1.logdate=MAX(BL.logdate) order by logdate DESC limit 1) as DevId FROM RBS_BeaconLogs BL \
                    GROUP BY BL.UUID order by logdate DESC;"
        try:
            # rows = RbsBeaconlogs.objects.values('uuid', 'devid').annotate(latest_date=Max('logdate'))
            # rows, no_of_rows = config.query_db(sql)
            rows = RbsBeaconlogs.objects.raw(sql)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = BeaconSerializer(rows, many=True)
        return Response(serializer.data)

    """
              Return current location of post beacon  
    """

    @csrf_exempt
    @decorator_function
    def post(self, request):
        uuid = request.data.get("uuid")
        if uuid is None or uuid == "":
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        try:
            row = RbsBeaconlogs.objects.filter(uuid=uuid).order_by('-logdate')[0]
        except Exception:
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = BeaconSerializer(row)
        if serializer:
            return Response(serializer.data)



class beacon_movement(generics.GenericAPIView):
    """
               Return a list of all beacons movements for current date.
    """
    @csrf_exempt
    @decorator_function
    def get(self, request, format=None):
        date = datetime.now().date()
        print date
        try:
            rows = RbsBeaconActivities.objects.filter(logdatetime__startswith=date)
            # rows = RbsBeaconActivities.objects.all()
            print rows
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = BeaconMvmntSerializer(rows, many=True)
        if rows.exists():
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)
    """
               Return a list of all beacons movements for requested date and type.
    """
    @csrf_exempt
    @decorator_function
    def post(self, request):
        fromdate = request.data.get("fromdate")
        todate = request.data.get("todate")
        _type = request.data.get("type")
        if _type == 'Employee':
            # filter beacons assigned to employee
            employee_obj_list = Employee.objects.all()
            emp_uuid_list = map(lambda x: x.emp_card_id, employee_obj_list)
            print emp_uuid_list
            try:
                rows = RbsBeaconActivities.objects.filter(logdatetime__range=[fromdate, todate], uuid__in=emp_uuid_list)
            except Exception:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = BeaconMvmntSerializer(rows, many=True)
            if rows.exists():
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)

        elif _type == 'Asset':
            # filter beacons assigned to asset
            asset_obj_list = Asset.objects.all()
            asset_uuid_list = map(lambda x: x.asset_card_id, asset_obj_list)
            try:
                rows = RbsBeaconActivities.objects.filter(logdatetime__range=[fromdate, todate], uuid__in=asset_uuid_list)
            except Exception:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = BeaconMvmntSerializer(rows, many=True)
            if rows.exists():
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)


class Employee_Attendance(generics.GenericAPIView):
    def post(self, request):
        uuid = request.POST.get("uuid")
        time_stamp = request.POST.get("timestamp")
        date_time = datetime.strptime(time_stamp, "%Y-%m-%d %H:%M:%S")
        print uuid, date_time
        if uuid is not None:
            try:
                emp_attendance = EmpAttendance.objects.get(emp_card_id=uuid[-5:], date=date_time.date())
                marked = True
            except ObjectDoesNotExist:
                marked = False

            if marked:
                print "Employee enter time was {}".format(emp_attendance.enter_time)
                enter_datetime =str(date_time.date()) + ' ' +str(emp_attendance.enter_time)
                enter_datetime = datetime.strptime(enter_datetime, "%Y-%m-%d %H:%M:%S")
                duration = (date_time - enter_datetime).total_seconds() / 3600
                duration = round(duration, 2)
                print duration
                emp_attendance.exit_time = date_time.time()
                emp_attendance.duration = duration
                emp_attendance.save()
                return Response(status=status.HTTP_200_OK)
            if not marked:
                try:
                    print "Marking attendance for '{}'".format(uuid)
                    employee_obj = Employee.objects.get(emp_card_id=uuid)
                    print "Employee name is '{}'".format(employee_obj.emp_first_name + " " + employee_obj.emp_last_name)
                    emp_name = employee_obj.emp_first_name + " " + employee_obj.emp_last_name
                    emp_card_id = uuid[-5:]
                    emp_id = employee_obj.emp_number
                    emp_racf = employee_obj.racf_id
                    emp_role = employee_obj.role.role_name
                    emp_organization = employee_obj.organization.organization_name
                    emp_business_unit = employee_obj.buisness_unit.business_unit_name
                    emp_cost_center = employee_obj.cost_center.cost_center_name
                    emp_line_manager = employee_obj.line_manager.line_manager_name
                    emp_date = date_time.date()
                    emp_enter_time = date_time.time()
                    emp_exit_time = date_time.time()
                    emp_present_hours = 0
                    is_present = True
                    marking_attendance = EmpAttendance.objects.create(emp_name=emp_name, emp_card_id=emp_card_id, emp_id= emp_id,
                                                                     racf_id=emp_racf, role=emp_role,
                                                                     organization=emp_organization,
                                                                     business_unit= emp_business_unit,
                                                                     cost_center= emp_cost_center,
                                                                     line_manager= emp_line_manager,
                                                                     date= emp_date,
                                                                     enter_time= emp_enter_time,
                                                                     exit_time= emp_exit_time,
                                                                     duration= emp_present_hours,
                                                                     is_present= is_present)
                    marking_attendance.save()
                    print ("{} attendance successfully marked".format(emp_name))
                    return Response(status=status.HTTP_200_OK)
                except ObjectDoesNotExist:
                    return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


class employee_info(generics.GenericAPIView):
    @csrf_exempt
    def get(self, request):
        # if request.method == "POST":
        #     prm = request.POST
        # else:
        #     Response(status=status.HTTP_401_UNAUTHORIZED)
        # print prm.get('mobnmbr'), prm.get('session')
        # if prm.get('mobnmbr') is not None and prm.get('session') is not None:
        #     if not config.check_session(prm.get('mobnmbr'), prm.get('session')):
        #         return HttpResponse(config.response(False, "Your session expire please login again."))
        # else:
        #     return Response(config.response(False, "Invalid parameters"), status=status.HTTP_406_NOT_ACCEPTABLE)

        employee_obj_list = Employee.objects.all()
        if employee_obj_list.exists():
            print employee_obj_list
            emp_info_list = []
            for employee in employee_obj_list:
                emp_info = {}
                emp_info["id"] = employee.emp_id
                emp_info["employee_name"] = str(employee.emp_first_name) + ' ' + str(employee.emp_last_name)
                emp_info["card_id"] = employee.emp_card_id[-5:]
                asset_obj_list = Asset.objects.filter(assigned_to=employee.emp_id)
                print asset_obj_list.exists(), asset_obj_list
                if asset_obj_list.exists():
                    for asset in asset_obj_list:
                        emp_info["asset_alloted"] = "yes"
                        emp_info["asset_name"] = asset.asset_name
                        emp_info["asset_id"] = asset.asset_card_id[-5:]
                        emp_info_list.append(emp_info)
                else:
                    emp_info["asset_alloted"] = "no"
                    emp_info["asset_name"] = ""
                    emp_info["asset_id"] = ""
                    emp_info_list.append(emp_info)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return HttpResponse(config.response(1, 200, "success", emp_info_list), status=status.HTTP_200_OK)

    """ 
                api for fetching card information
                
    """
    def post(self, request):
        uuid = request.POST.get("uuid")
        if uuid is not None:
            print "fetching details for '{}'".format(uuid)
            try:
                employee_obj = Employee.objects.get(emp_card_id=uuid)
                print "Employee name is '{}'".format(employee_obj.emp_first_name + " " + employee_obj.emp_last_name)
                serializer = EmployeeSerializer(employee_obj, context={"request": request})
                return Response({"emp_info": serializer.data, "type": "emp"}, status=status.HTTP_200_OK)
            except ObjectDoesNotExist:
                pass
            if ObjectDoesNotExist:
                try:
                    asset_obj = Asset.objects.get(asset_card_id=uuid)
                    print "Asset found for this uuid is '{}'".format(asset_obj.asset_name)
                    asset_serializer = AssetSerializer(asset_obj)
                    return Response({"asset_info": asset_serializer.data, "type": "asset"}, status=status.HTTP_200_OK)
                except ObjectDoesNotExist:
                    return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # if employee_obj:
        #     try:
        #         asset_obj_list = Asset.objects.filter(assigned_to=employee_obj)
        #         asset_serializer = AssetSerializer(asset_obj_list, many=True)
        #     except ObjectDoesNotExist:
        #         return Response(EmployeeSerializer(employee_obj).data, status=status.HTTP_200_OK)
        #     serializer = EmployeeSerializer(employee_obj)
        #     return Response({"emp_info": serializer.data, "asset_info": asset_serializer.data},
        #                     status=status.HTTP_200_OK)
        # else:
        #     return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeeAttendanceData(generics.GenericAPIView):

    def post(self, request):
        view = request.POST.get("view")
        role = request.POST.get("role")
        business_unit = request.POST.get("business_unit")
        line_manager = request.POST.get("line_manager")
        from_date = request.POST.get("from_date")
        to_date = request.POST.get("to_date")
        filter = ""
        print view, role, business_unit, line_manager , from_date, to_date
        # create filter
        if role:
            filter = filter + " and Role = '{}'".format(role)

        if business_unit:
            filter = filter + " and BusinessUnit = '{}'".format(business_unit)

        if line_manager:
            filter = filter + " and LineManager = '{}'".format(line_manager)

        print filter

        if view:
            print ("preparing data.... for view {}".format(view))
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if view == "by_week":
            if not to_date:
                to_date = datetime.now()
            else:
                to_date = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S")

            if not from_date:
                from_date = datetime.now() - timedelta(days=30)
            else:
                from_date = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S")

            week_wise_to_date = from_date + timedelta(days=7)
            week_wise_from_date = from_date
            data = []
            week_num = 0
            cursor = connection.cursor()
            while True:
                if week_wise_to_date.date() <= to_date.date():
                    data_set = {}
                    print week_wise_from_date.date(), week_wise_to_date.date()
                    sql = "SELECT COUNT(*) FROM EmpAttendance WHERE Date BETWEEN '{}' AND '{}'{};".format \
                        (week_wise_from_date.date(), week_wise_to_date.date(), filter)
                    print sql
                    cursor.execute(sql)
                    (number_of_rows,) = cursor.fetchone()
                    print number_of_rows
                    # att_count = EmpAttendance.objects.filter(date__range=(week_wise_from_date.date(),
                    #                                                    week_wise_to_date.date())).count()
                    week_num = week_num + 1
                    data_set["Employee_count"] = number_of_rows
                    data_set["x_axis_value"] = "Week " + str(week_num)
                    data.append(data_set)
                    week_wise_from_date = week_wise_to_date + timedelta(days=1)
                    week_wise_to_date = week_wise_to_date + timedelta(days=7)
                else:
                    break
            return Response({"data": data}, status=status.HTTP_200_OK)
        elif view == "by_month":
            if not to_date:
                to_date = datetime.now()
            else:
                to_date = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S")

            if not from_date:
                from_date = datetime.now() - timedelta(days=180)
            else:
                from_date = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S")

            month_wise_from_date = from_date
            month_wise_to_date = from_date + timedelta(days=30)
            print month_wise_to_date, month_wise_from_date

            data = []
            month_num = 0
            cursor = connection.cursor()
            while True:
                if month_wise_to_date.date() <= to_date.date():
                    data_set = {}
                    print month_wise_from_date.date(), month_wise_to_date.date()
                    sql = "SELECT COUNT(*) FROM EmpAttendance WHERE Date BETWEEN '{}' AND '{}'{};".format \
                                       (month_wise_from_date.date(), month_wise_to_date.date(), filter)
                    print sql
                    cursor.execute(sql)
                    # att_count = EmpAttendance.objects.filter(date__range=(month_wise_from_date.date(),
                    #                                                       month_wise_to_date.date())).count()
                    (number_of_rows,) = cursor.fetchone()
                    print number_of_rows
                    month_num += 1
                    data_set["Employee_count"] = number_of_rows
                    data_set["x_axis_value"] = "Month " + str(month_num)
                    data.append(data_set)
                    month_wise_from_date = month_wise_to_date + timedelta(days=1)
                    month_wise_to_date = month_wise_to_date + timedelta(days=30)
                else:
                    break
            return Response({"data": data}, status=status.HTTP_200_OK)
        elif view == "by_role":
            if from_date and to_date:
                from_date = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S").date()
                to_date = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S").date()
                filter = "WHERE Date BETWEEN '{}' and '{}'".format(from_date, to_date) + filter
            # role_list = EmpAttendance.objects.values('role').annotate(Count('role'))
            cursor = connection.cursor()
            sql = "SELECT Role, COUNT(*) FROM EmpAttendance {} Group By Role;".format(filter)
            print sql
            cursor.execute(sql)
            role_list = cursor.fetchall()
            print role_list
            data = []
            map(lambda x: data.append({"x_axis_value": x[0], "Employee_count": x[1]}), role_list)
            return Response({"data": data}, status=status.HTTP_200_OK)
        elif view == "by_business_unit":
            if from_date and to_date:
                from_date = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S").date()
                to_date = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S").date()
                filter = "WHERE Date BETWEEN '{}' and '{}'".format(from_date, to_date) + filter
            # role_list = EmpAttendance.objects.values('role').annotate(Count('role'))
            cursor = connection.cursor()
            sql = "SELECT BusinessUnit, COUNT(*) FROM EmpAttendance {} Group By BusinessUnit;".format(filter)
            print sql
            cursor.execute(sql)
            role_list = cursor.fetchall()
            print role_list
            data = []
            map(lambda x: data.append({"x_axis_value": x[0], "Employee_count": x[1]}), role_list)
            return Response({"data": data}, status=status.HTTP_200_OK)


class EmployeeUtilizationData(generics.GenericAPIView):

    def post(self, request):
        view = request.POST.get("view")
        role = request.POST.get("role")
        business_unit = request.POST.get("business_unit")
        line_manager = request.POST.get("line_manager")
        from_date = request.POST.get("from_date")
        to_date = request.POST.get("to_date")
        filter = ""

        # create filter
        if role:
            filter = filter + " and Role = '{}'".format(role)

        if business_unit:
            filter = filter + " and BusinessUnit = '{}'".format(business_unit)

        if line_manager:
            filter = filter + " and LineManager = '{}'".format(line_manager)

            print view, role, business_unit, line_manager, from_date, to_date
        if view:
            print ("preparing data.... for view {}".format(view))
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if view == "by_week":
            if not to_date:
                to_date = datetime.now()
            else:
                to_date = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S")

            if not from_date:
                from_date = datetime.now() - timedelta(days=30)
            else:
                from_date = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S")

            week_wise_to_date = from_date + timedelta(days=7)
            week_wise_from_date = from_date
            data = []
            week_num = 0
            cursor = connection.cursor()
            while True:
                if week_wise_to_date.date() <= to_date.date():
                    data_set = {}
                    print week_wise_from_date.date(), week_wise_to_date.date()
                    sql = "SELECT AVG(PresentHours) FROM EmpAttendance WHERE Date BETWEEN '{}' AND '{}'{};".format \
                        (week_wise_from_date.date(), week_wise_to_date.date(), filter)
                    print sql
                    cursor.execute(sql)
                    (number_of_rows,) = cursor.fetchone()
                    print number_of_rows
                    # att_count = EmpAttendance.objects.filter(date__range=(week_wise_from_date.date(),
                    #                                                    week_wise_to_date.date())).count()
                    if number_of_rows:
                        y = round(number_of_rows, 2)
                    else:
                        y = 0
                    week_num = week_num + 1
                    data_set["Present_Hours"] = y
                    data_set["x_axis_value"] = "Week " + str(week_num)
                    data.append(data_set)
                    week_wise_from_date = week_wise_to_date + timedelta(days=1)
                    week_wise_to_date = week_wise_to_date + timedelta(days=7)
                else:
                    break
            return Response({"data": data}, status=status.HTTP_200_OK)
        elif view=="by_month":
            if not to_date:
                to_date = datetime.now()
            else:
                to_date = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S")

            if not from_date:
                from_date = datetime.now() - timedelta(days=180)
            else:
                from_date = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S")

            month_wise_from_date = from_date
            month_wise_to_date = from_date + timedelta(days=30)
            print month_wise_to_date, month_wise_from_date
            data = []
            month_num = 0
            cursor = connection.cursor()
            while True:
                if month_wise_to_date.date() <= to_date.date():
                    data_set = {}
                    print month_wise_from_date.date(), month_wise_to_date.date()
                    sql = "SELECT AVG(PresentHours) FROM EmpAttendance WHERE Date BETWEEN '{}' AND '{}'{};".format \
                        (month_wise_from_date.date(), month_wise_to_date.date(), filter)
                    print sql
                    cursor.execute(sql)
                    # att_count = EmpAttendance.objects.filter(date__range=(month_wise_from_date.date(),
                    #                                                       month_wise_to_date.date())).count()
                    (number_of_rows,) = cursor.fetchone()
                    print number_of_rows
                    if number_of_rows:
                        y = round(number_of_rows, 2)
                    else:
                        y = 0
                    month_num += 1
                    data_set["Present_Hours"] = y
                    data_set["x_axis_value"] = "Month " + str(month_num)
                    data.append(data_set)
                    month_wise_from_date = month_wise_to_date + timedelta(days=1)
                    month_wise_to_date = month_wise_to_date + timedelta(days=30)
                else:
                    break
            return Response({"data": data}, status=status.HTTP_200_OK)
        elif view == "by_role":
            if from_date and to_date:
                from_date = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S").date()
                to_date = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S").date()
                filter = "WHERE Date BETWEEN '{}' and '{}'".format(from_date, to_date) + filter
            # role_list = EmpAttendance.objects.values('role').annotate(Count('role'))
            cursor = connection.cursor()
            sql = "SELECT Role, AVG(PresentHours) FROM EmpAttendance {} Group By Role;".format(filter)
            print sql
            cursor.execute(sql)
            role_list = cursor.fetchall()
            print role_list
            data = []
            map(lambda x: data.append({"x_axis_value": x[0], "Present_Hours": round(x[1], 2)}), role_list)
            return Response({"data": data}, status=status.HTTP_200_OK)
        elif view == "by_business_unit":
            if from_date and to_date:
                from_date = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S").date()
                to_date = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S").date()
                filter = "WHERE Date BETWEEN '{}' and '{}'".format(from_date, to_date) + filter
            # role_list = EmpAttendance.objects.values('role').annotate(Count('role'))
            cursor = connection.cursor()
            sql = "SELECT BusinessUnit, AVG(PresentHours) FROM EmpAttendance {} Group By BusinessUnit;".format(filter)
            print sql
            cursor.execute(sql)
            role_list = cursor.fetchall()
            print role_list
            data = []
            map(lambda x: data.append({"x_axis_value": x[0], "Present_Hours": round(x[1], 2)}), role_list)
            return Response({"data": data}, status=status.HTTP_200_OK)


class DeskUtilizationData(generics.GenericAPIView):
    def post(self, request):
        view = request.POST.get("view")
        # role = request.POST.get("role")
        # business_unit = request.POST.get("business_unit")
        # line_manager = request.POST.get("line_manager")
        from_date = request.POST.get("from_date")
        to_date = request.POST.get("to_date")
        filter = ""

        # create filter
        # if role:
        #     filter = filter + " and Role = '{}'".format(role)
        #
        # if business_unit:
        #     filter = filter + " and BusinessUnit = '{}'".format(business_unit)
        #
        # if line_manager:
        #     filter = filter + " and LineManager = '{}'".format(line_manager)

        print filter
        if view:
            print ("preparing data.... for view {}".format(view))
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if view == "by_day":
            if not to_date:
                to_date = datetime.now()
            else:
                to_date = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S")

            if not from_date:
                from_date = datetime.now() - timedelta(days=30)
            else:
                from_date = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S")

            day_wise_from_date = from_date
            day_wise_to_date = from_date + timedelta(days=1)
            print day_wise_to_date, day_wise_from_date
            data = []
            month_num = 0
            cursor = connection.cursor()
            while True:
                if day_wise_to_date.date() <= to_date.date():
                    data_set = {}
                    print day_wise_from_date.date(), day_wise_to_date.date()
                    sql = "SELECT DevId, SUM(Duration) FROM PIRActivities WHERE StartDate BETWEEN '{}' AND '{}'{} " \
                          "GROUP BY DevId;".format (day_wise_from_date.date(), day_wise_to_date.date(), filter)
                    print sql
                    cursor.execute(sql)
                    # att_count = EmpAttendance.objects.filter(date__range=(month_wise_from_date.date(),
                    #                                                       month_wise_to_date.date())).count()
                    rows = cursor.fetchall()
                    print rows
                    y = 0
                    if len(rows) > 1:
                        y = (reduce(lambda x, y: x[1] + y[1], rows) / len(rows))/3600
                        y = round(y, 2)
                    elif rows:
                        y = round((rows[0][1] / 3600), 2)
                    month_num += 1
                    data_set["Avg_Hours"] = y
                    data_set["x_axis_value"] = "Day " + str(month_num)
                    data.append(data_set)
                    day_wise_from_date = day_wise_to_date + timedelta(days=1)
                    day_wise_to_date = day_wise_to_date + timedelta(days=1)
                else:
                    break
            return Response({"data": data}, status=status.HTTP_200_OK)
        elif view == "by_week":
            if not to_date:
                to_date = datetime.now()
            else:
                to_date = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S")

            if not from_date:
                from_date = datetime.now() - timedelta(days=30)
            else:
                from_date = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S")

            week_wise_to_date = from_date + timedelta(days=7)
            week_wise_from_date = from_date
            data = []
            week_num = 0
            cursor = connection.cursor()
            while True:
                if week_wise_to_date.date() <= to_date.date():
                    data_set = {}
                    print week_wise_from_date.date(), week_wise_to_date.date()
                    sql = "SELECT DevId, SUM(Duration) FROM PIRActivities WHERE StartDate BETWEEN '{}' AND '{}'{} " \
                          "GROUP BY DevId;".format(week_wise_from_date.date(), week_wise_to_date.date(), filter)
                    print sql
                    cursor.execute(sql)
                    rows = cursor.fetchall()
                    print rows
                    y = 0
                    if len(rows) > 1:
                        y = (reduce(lambda x, y: x[1] + y[1], rows) / len(rows))/3600
                        y = round(y, 2)
                    elif rows:
                        y = round((rows[0][1] / 3600), 2)
                    # att_count = EmpAttendance.objects.filter(date__range=(week_wise_from_date.date(),
                    #                                                    week_wise_to_date.date())).count()
                    week_num = week_num + 1
                    data_set["Avg_Hours"] = y
                    data_set["x_axis_value"] = "Week " + str(week_num)
                    data.append(data_set)
                    week_wise_from_date = week_wise_to_date + timedelta(days=1)
                    week_wise_to_date = week_wise_to_date + timedelta(days=7)
                else:
                    break
            return Response({"data": data}, status=status.HTTP_200_OK)
        elif view =="by_month":
            if not to_date:
                to_date = datetime.now()
            else:
                to_date = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S")

            if not from_date:
                from_date = datetime.now() - timedelta(days=180)
            else:
                from_date = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S")

            month_wise_from_date = from_date
            month_wise_to_date = from_date + timedelta(days=30)
            print month_wise_to_date, month_wise_from_date
            data = []
            month_num = 0
            cursor = connection.cursor()
            while True:
                if month_wise_to_date.date() <= to_date.date():
                    data_set = {}
                    print month_wise_from_date.date(), month_wise_to_date.date()
                    sql = "SELECT DevId, SUM(Duration) FROM PIRActivities WHERE StartDate BETWEEN '{}' AND '{}'{} " \
                          "GROUP BY DevId;".format (month_wise_from_date.date(), month_wise_to_date.date(), filter)
                    print sql
                    cursor.execute(sql)
                    # att_count = EmpAttendance.objects.filter(date__range=(month_wise_from_date.date(),
                    #                                                       month_wise_to_date.date())).count()
                    rows = cursor.fetchall()
                    print rows
                    y = 0
                    if len(rows) > 1:
                        y = (reduce(lambda x, y: x[1] + y[1], rows) / len(rows))/3600
                        y = round(y, 2)
                    elif rows:
                        y = round((rows[0][1] / 3600), 2)
                    month_num += 1
                    data_set["Avg_Hours"] = y
                    data_set["x_axis_value"] = "Month " + str(month_num)
                    data.append(data_set)
                    month_wise_from_date = month_wise_to_date + timedelta(days=1)
                    month_wise_to_date = month_wise_to_date + timedelta(days=30)
                else:
                    break
            return Response({"data": data}, status=status.HTTP_200_OK)

