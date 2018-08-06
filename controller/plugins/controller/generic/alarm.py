# Copyright (c) 2017 LSD - UFCG.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from controller.utils.logger import ScalingLog
from controller.service import api
import datetime
import time
import requests

""" This class contains the logic used to adjust the amount of resources
    allocated to applications """
class GenericAlarm:
    ERROR_METRIC_NAME = "application-progress.error"

    def __init__(self, actuator, metric_source, trigger_down, trigger_up,
                 min_cap, max_cap, actuation_size, metric_rounding,
                 application_id, instances):

        self.metric_source = metric_source
        self.actuator = actuator
        self.trigger_down = trigger_down
        self.trigger_up = trigger_up
        self.metric_rounding = metric_rounding
        self.application_id = application_id
        self.instances = instances
        self.load_balancer_url = api.load_balancer_url

        self.logger = ScalingLog("%s.generic.alarm.log" % (application_id),
                                 "controller.log",
                                 application_id)

        self.cap_logger = ScalingLog("%s.cap.log" % (application_id),
                                     "cap.log",
                                     application_id)

        self.last_error = ""
        self.last_error_timestamp = datetime.datetime.strptime(
                                        "0001-01-01T00:00:00.0Z",
                                        '%Y-%m-%dT%H:%M:%S.%fZ')
        self.last_action = ""
        self.cap = -1

    def check_application_state(self):
        """ Checks the application progress by getting progress metrics from
            a metric source, checks if the metrics are new and tries to
            modify the amount of allocated resources if necessary. """

        try:
            self.logger.log("Getting progress error")
            self.last_action = "getting progress error"

            # Get the progress error value and timestamp
            error_timestamp, error = self._get_error(self.application_id)

            self.last_action = "Progress error-[%s]-%f" % (
                str(error_timestamp), error)

            self.logger.log(self.last_action)

            """ Check if the metric is new by comparing the timestamps of the
                current metric and most recent metric """
            if self._check_measurements_are_new(error_timestamp):
                print "TO NO ALARME"
                
		self._scale_down(error, self.instances)
                self._scale_up(error, self.instances)

                self.last_error = error
                self.last_error_timestamp = error_timestamp
            else:
                self.last_action += " Could not acquire more recent metrics"
                self.logger.log("Could not acquire more recent metrics")

        except Exception as e:
            # TODO: Check exception type
            self.logger.log(str(e))
            return

    def _scale_down(self, error, instances):
        """
            Checks if it is necessary to scale down, according to
            the error. If it is, calculates the new CPU cap
            value and tries to modify the cap of the vms.
        """

        # If error is positive and its absolute value is too high, scale down
        if error > 0:
            print "TO NO SCALE DOWN"
            self.logger.log("Scaling down")
            self.last_action = "Getting allocated resources"
	    if  error < 0.1:
		requests.post(self.load_balancer_url + "/down", json={"vm_number": 1})
	    elif error < 0.2:
		requests.post(self.load_balancer_url + "/down", json={"vm_number": 2})
	    else:
		requests.post(self.load_balancer_url + "/down", json={"vm_number": 3})


    def _scale_up(self, error, instances):
        """
            Checks if it is necessary to scale up, according to
            the error. If it is, calculates the new CPU cap
            value and tries to modify the cap of the vms.
        """

        # If error is negative and its absolute value is too high, scale up
        if error < 0:
            print "TO NO SCALE UP"
            self.logger.log("Scaling up")
            self.last_action = "Getting allocated resources"
	    if error > -0.1:
		requests.post(self.load_balancer_url + "/up", json={"vm_number": 1})
	    elif error > -0.2:
		requests.post(self.load_balancer_url + "/up",json={"vm_number": 2})
	    else:
		requests.post(self.load_balancer_url+ "/up",json={"vm_number": 3})

    def _get_error(self, application_id):
        error_measurement = self.metric_source.get_most_recent_value(
                                GenericAlarm.ERROR_METRIC_NAME,
                                {"application_id": application_id})

        error_timestamp = error_measurement[0]
        error = error_measurement[1]
        error = round(error, self.metric_rounding)

        return error_timestamp, error

    def _check_measurements_are_new(self, error_timestamp):
        return self.last_error_timestamp < error_timestamp

    def status(self):
        return self.last_action
