from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from dateutil import parser
import pytz
import math
import json
import logging


class Meeting(View):

    def get(self, request):

        """
        ### Parse the request
        """
        try:
            req = json.loads(request.body)

            participants = req.get("participants", [])
            meeting_length = int(req.get("meeting_length", 30))
            earliest = pytz.utc.localize(parser.parse(req.get("earliest", "")))
            latest = pytz.utc.localize(parser.parse(req.get("latest", "")))
            office_hours = req.get("office_hours", "9-17")

            if not participants:
                logger.info("No participants provided!", exc_info=True)
                raise Exception

        except Exception as e:
            logger.error("Invalid request: " + request.body, exc_info=True)
            return JsonResponse({'status': 400, 'message': 'Invalid request!'}, status=400, safe=False)

        employees = []

        """
        ### Parse the freebusy.txt file
        """
        try:
            with open('data/freebusy.txt', 'r') as file:
                for line in file:

                    if line == "\n":
                        continue

                    employee = {
                        "id": "",
                        "name": "",
                        "meeting": []
                    }
                    employee_present = False

                    data = line.split(';')

                    for e in employees:
                        if e.get("id", "") == data[0]:
                            if ":" in data[1] and "/" in data[1]:
                                meeting = {}
                                meeting["start"] = data[1]
                                meeting["end"] = data[2]
                                e["meeting"].append(meeting)
                            else:
                                e["name"] = data[1].replace("\n", "")

                            employee_present = True
                            break

                    if not employee_present:
                        employee["id"] = data[0]
                        if ":" in data[1] and "/" in data[1]:
                            meeting = {}
                            meeting["start"] = data[1]
                            meeting["end"] = data[2]
                            employee["meeting"].append(meeting)
                        else:
                            employee["name"] = data[1]

                        employees.append(employee)

        except Exception as e:
            logger.error("Error when parsing the data file!", exc_info=True)
            return JsonResponse({'status': 500, 'message': 'Internal server error!'}, status=500, safe=False)

        """
        ### Get the first available time slot
        """
        try:
            time_slot = timezone.now()
            if earliest:
                if earliest > time_slot:
                    time_slot = earliest

            # Round the timeslot to the nearest 30 min
            if time_slot.minute >= 30:
                time_slot = time_slot.replace(second=0, microsecond=0, minute=0, hour=time_slot.hour + 1)
            else:
                time_slot = time_slot.replace(second=0, microsecond=0, minute=30)

            # Check if timeslot is within office hours
            if time_slot.hour < int(office_hours.split("-")[0]):
                time_slot = time_slot.replace(hour=office_hours.split("-")[0], minute=0, second=0, microsecond=0)
            elif time_slot.hour > int(office_hours.split("-")[1]):
                time_slot = time_slot.replace(day=time_slot.day + 1, hour=int(office_hours.split("-")[0]), minute=0, second=0, microsecond=0)

            available = True
            has_time = True

            # Check if all participants are available
            while(has_time):
                if time_slot > latest:
                    has_time = False
                    break

                for participant in participants:
                    for e in employees:
                        if e.get("name", "") == participant:
                            for meeting in e.get("meeting", []):
                                meeting_start = pytz.utc.localize(parser.parse(meeting["start"]))
                                meeting_end = pytz.utc.localize(parser.parse(meeting["end"]))

                                # Check if the timeslot is within a scheduled meeting
                                if time_slot > meeting_start and time_slot < meeting_end:
                                    available = False
                                    break

                                # Check if the timeslot+meeting_length < scheduled meeting start
                                if meeting_start > time_slot.replace(hour=meeting_start.hour+
                                                                          math.floor((meeting_start.minute+meeting_length)/60),
                                                                     minute=(meeting_start.minute+meeting_length)%60):
                                    available = False
                                    break

                        if not available:
                            break

                if not available:
                    available = True

                    # Add 30 min to the timeslot and try again
                    if time_slot.minute == 30:
                        time_slot = time_slot.replace(second=0, microsecond=0, minute=0, hour=time_slot.hour+1)
                    else:
                        time_slot = time_slot.replace(second=0, microsecond=0, minute=30)

                    # Check if timeslot is within office hours
                    if time_slot.hour < int(office_hours.split("-")[0]):
                        time_slot = time_slot.replace(hour=office_hours.split("-")[0], minute=0, second=0,
                                                      microsecond=0)
                    elif time_slot.hour > int(office_hours.split("-")[1]):
                        time_slot = time_slot.replace(day=time_slot.day + 1, hour=int(office_hours.split("-")[0]),
                                                      minute=0, second=0, microsecond=0)

                else:
                    break

        except Exception as e:
            logger.error("Internal server error!", exc_info=True)
            return JsonResponse({'status': 500, 'message': 'Internal server error!'}, status=500, safe=False)

        if has_time:
            return JsonResponse({"meeting_slot": str(time_slot)}, status=200, safe=False)
        else:
            return JsonResponse({"meeting_slot": "No available time slots!"}, status=200, safe=False)


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
