# csv2worklogs

Update Jira issue worklogs from a CSV file.

## Steps

1. Clone this repo and install requirements
```
git clone https://github.com/rebkwok/csv2worklogs.git
cd csv2worklogs
pip install -r requirements.txt
```

2. Make a Jira API token  
[Follow the instructions here](https://confluence.atlassian.com/cloud/api-tokens-938839638.html)

3. Set environment variables
 ```
 export JIRA_BASE_URL=https://subdomain.atlassian.net  # base url of your atlassian site
 export JIRA_EMAIL=your@email.address  # login email address
 export JIRA_API_TOKEN=token  # token generated above
```

4. Create a csv file with your timetracking data.
 - First column has header "Issue"
 - Other column headers are dates, in the format YYYY-MM-DD
 - Enter time in hours.
 
 E.g.

| Issue   | 2020-02-03 | 2020-02-04 | 2020-02-05 | 2020-02-06 |
|---------|:----------:|:----------:|:----------:|:----------:|
| ISSUE-1 |      1     |     0.5    |      8     |            |
| ISSUE-2 |      2     |      7     |            |      8     |
| ISSUE-3 |      6     |     0.5    |            |            |

5. Run the script

``` 
cd csv2worklogs
python csv2worklogs /path/to/csv/file
```

Worklogs are always created at 12:00:00.  If the script is rerun with the same entries, no changes will be made.  If a time entry has 
been updaed, the worklog for that date/time will be updated.  

Check your time reports at:  
<JIRA_BASE_URL>/plugins/servlet/ac/timereports/timereports#!pivotTableType=Timesheet&groupByField=workeduser&offset=0&allUsers=true