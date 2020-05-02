#!/usr/bin/env python3

from argparse import ArgumentParser
import csv
from datetime import datetime, timedelta
import itertools


def main(outfilepath, template=None, columns=None, overwrite=False):
    if template and outfilepath == template and not overwrite:
        print("Template and putfilepath are the same; use --overwrite to overwrite the template file.")
        return
    today = datetime.today()
    days_since_monday = abs(0 - today.weekday())
    monday = today - timedelta(days=days_since_monday)
    week_dates = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    weekdays = ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun']
    new_rows = []
    if template is None:
        # No template, create a new csv for the current week
        header_row1 = ['', '']
        header_row1.extend(week_dates)
        new_rows.append(header_row1)
        new_rows.append(['', ''])
    else:
        with open(template) as templatefile:
            reader = csv.reader(templatefile)
            for i, row in enumerate(reader):
                if i == 0:
                    # populate first 2 rows with header and weekdays
                    header_row = list(itertools.takewhile(lambda x: not_a_date(x), row))
                    weekday_rows = [''] * len(header_row)
                    header_row.extend(week_dates)
                    weekday_rows.extend(weekdays)
                    new_rows.append(header_row)
                    new_rows.append(weekday_rows)
                elif i == 1:
                    # skip 2nd row, it'll be the weekday row
                    continue
                else:
                    new_row = [row[i] for i in range(columns) if len(row) >= columns]
                    new_rows.append(new_row)

    with open(outfilepath, 'w') as outfile:
        writer = csv.writer(outfile)
        for row in new_rows:
            writer.writerow(row)


def not_a_date(cell_value):
    try:
        datetime.strptime(cell_value, "%Y-%m-%d")
    except ValueError:
        return True


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--outfile", "-o", default="timesheet.csv", help="Path to new csv file")
    parser.add_argument("--template", "-t", help="Path to file to use as template")
    parser.add_argument("--columns", "-c", default=2, help="Number of lefthand columns to keep from template.  Default is 2.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite template file")

    arguments = parser.parse_args()
    main(outfilepath=arguments.outfile, template=arguments.template, columns=arguments.columns, overwrite=arguments.overwrite)
