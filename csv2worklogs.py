#!/usr/bin/env python3

from argparse import ArgumentParser
import csv
from datetime import datetime
import json
import logging
from os import environ
import pytz
from urllib.parse import urljoin

from colorama import init as colorama_init
from colorama import Fore
import coloredlogs
import requests
from requests.auth import HTTPBasicAuth

environ["COLOREDLOGS_LOG_FORMAT"] = '%(asctime)s: %(levelname)s: %(message)s'
environ["COLOREDLOGS_DATE_FORMAT"] = '%Y-%m-%d %H:%M:%S'
coloredlogs.install(level='INFO')
logger = logging.getLogger(__name__)

colorama_init()


class JiraApiClient:

    def __init__(self, email, api_token, base_url):
        self.email = email
        self.api_token = api_token
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.auth = HTTPBasicAuth(self.email, api_token)
        self.api_url = urljoin(base_url, "/rest/api/3/")

    def _worklog_url(self, issue, worklog_id=None):
        url = urljoin(self.api_url, f"issue/{issue}/worklog")
        if worklog_id:
            return f"{url}/{worklog_id}"
        return url

    def get_worklogs(self, issue):
        worklogs = requests.get(self._worklog_url(issue), issue, headers=self.headers, auth=self.auth)
        return worklogs.json()

    def get_worklogs_for_user(self, issue):
        worklogs = self.get_worklogs(issue)
        return [
            {
                "id": worklog["id"],
                "started": datetime.astimezone(datetime.strptime(worklog["started"], "%Y-%m-%dT%H:%M:%S.%f%z"),
                                               pytz.utc),
                "time_in_seconds": worklog["timeSpentSeconds"]
            }
            for worklog in worklogs["worklogs"]
            if worklog["author"]['emailAddress'] == self.email
        ]

    def get_worklog(self, issue, worklog_id):
        worklog = requests.get(self._worklog_url(issue, worklog_id), issue, headers=self.headers, auth=self.auth)
        return worklog.json()

    def create_worklog(self, issue, payload):
        return requests.post(self._worklog_url(issue), data=payload, headers=self.headers, auth=self.auth)

    def update_worklog(self, issue, worklog_id, payload):
        return requests.put(self._worklog_url(issue, worklog_id), data=payload, headers=self.headers, auth=self.auth)


def read_csv(filepath):
    issue_logs = {}
    with open(filepath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            issue = row.pop("Issue")
            if issue:
                # Ignore any lines with empty "Issue" field
                row.pop("Notes", None)
                issue_logs[issue] = {date.strip(): float(hours.strip()) for date, hours in row.items() if hours}
    return issue_logs


def submit_worklogs(issue, time_logs, client):
    existing_worklogs_for_user = client.get_worklogs_for_user(issue)

    for date_string, hours in time_logs.items():
        log_date = datetime.strptime(date_string, "%Y-%m-%d").replace(hour=12, tzinfo=pytz.utc)
        log_date_string = log_date.strftime("%Y-%m-%dT12:00:00.000%z")
        time_in_seconds = hours * 60 * 60
        payload = json.dumps(
            {
                "timeSpentSeconds": time_in_seconds,
                "started": log_date_string
            }
        )

        matching_worklog = [
            worklog for worklog in existing_worklogs_for_user if worklog["started"] == log_date
        ]
        if matching_worklog:
            matching_worklog = matching_worklog[0]
            matching_worklog_id = matching_worklog["id"]
            if matching_worklog["time_in_seconds"] == time_in_seconds:
                logger.info(Fore.BLUE + "No change to existing worklog for issue %s, date %s", issue, date_string)
                continue
            else:
                response = client.update_worklog(issue, matching_worklog_id, payload)
                success_message = Fore.YELLOW + f"Existing worklog found and updated for issue {issue}, start {date_string}"
        else:
            response = client.create_worklog(issue, payload)
            success_message = Fore.GREEN + f"New worklog created for issue {issue}, date {date_string}"

        if response.status_code in [200, 201]:
            logger.info(success_message)
        else:
            logger.error(Fore.RED + "Error logging time for issue %s, date %s: %s", issue, date_string, response.status_code)


def check_issue_log_dates(issue_logs):
    all_dates = set(sum([list(timelogs.keys()) for timelogs in issue_logs.values()], []))
    for date_string in all_dates:
        try:
            datetime.strptime(date_string, "%Y-%m-%d")
        except ValueError:
            logging.error("%s is an invalid date format.  Format date column headers in the format YYYY-MM-DD.", date_string)
            return False
    return True


def main(filepath):
    email = environ.get("JIRA_EMAIL")
    api_token = environ.get("JIRA_API_TOKEN")
    base_url = environ.get("JIRA_BASE_URL")

    if not (email and api_token and base_url):
        logging.error("Set the JIRA_EMAIL, JIRA_API_TOKEN and JIRA_BASE_URL environment variables")
        return

    issue_logs = read_csv(filepath)

    # check date formats
    ok = check_issue_log_dates(issue_logs)
    if not ok:
        return

    client = JiraApiClient(email=environ["JIRA_EMAIL"], api_token=environ["JIRA_API_TOKEN"], base_url=environ["JIRA_BASE_URL"])
    for issue, time_logs in issue_logs.items():
        submit_worklogs(issue, time_logs, client)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("filepath", help="Path to timelog csv file")
    arguments = parser.parse_args()
    main(filepath=arguments.filepath)
