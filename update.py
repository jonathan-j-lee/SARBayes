#!/usr/bin/env python3
# update.py


import datetime
import geopy
import re
import weather
import xlrd
import xlsxwriter

# Regex patterns
NUMBER = r'^-{0,1}\d+\.{0,1}\d*$'
DMS = r'^(\d+)[\.\s\'](\d+)[\.\s\'](\d+)$'


def degrees_as_decimal(degrees, minutes, seconds):
    return degrees + minutes/60 + seconds/3600


def get_date_and_location(raw_date, raw_lkp_ns, raw_lkp_ew, datemode):
    raw_lkp_ns, raw_lkp_ew = str(raw_lkp_ns), str(raw_lkp_ew)
    if raw_date and raw_lkp_ns and raw_lkp_ew:
        try:
            date = datetime.datetime(*xlrd.xldate_as_tuple(
                raw_date, datemode))
        except (TypeError, xlrd.xldate.XLDateNegative):
            return None
        
        if re.match(NUMBER, raw_lkp_ns) and re.match(NUMBER, raw_lkp_ew):
            lkp_ns, lkp_ew = float(raw_lkp_ns), float(raw_lkp_ew)
        elif re.match(DMS, raw_lkp_ns) and re.match(DMS, raw_lkp_ew):
            capture = re.findall(DMS, raw_lkp_ns)[0]
            lkp_ns = degrees_as_decimal(
                float(capture[0]), float(capture[1]), float(capture[2]))
            
            capture = re.findall(DMS, raw_lkp_ew)[0]
            lkp_ew = degrees_as_decimal(
                float(capture[0]), float(capture[1]), float(capture[2]))
        else:
            # Unrecognizable formats
            return None
        
        if -90 <= lkp_ns <= 90 and -180 <= lkp_ew <= 180:
            return date, lkp_ns, lkp_ew


def read_case_data(filename):
    workbook = xlrd.open_workbook(filename)
    sheet = workbook.sheet_by_index(0)
    for row_index in range(1, sheet.nrows):
        row = sheet.row_values(row_index)
        yield row, row_index, workbook.datemode


def update_case_data(input_filename, output_filename):
    workbook = xlsxwriter.Workbook(output_filename)
    worksheet = workbook.add_worksheet()
    
    for row, row_index, datemode in read_case_data(input_filename):
        raw_weather_data = row[37:40] + row[41:43]
        if '' in raw_weather_data:
            result = get_date_and_location(row[3], row[33], row[34], datemode)
            if result:
                date = result[0]
                lkp = geopy.Point(result[1], result[2])
                new_weather_data = weather.get_conditions(date, lkp)
                
                print('Updating case {} . . . '.format(row_index))
                if not raw_weather_data[0] and new_weather_data['TMAX']:
                    row[37] = tmax = round(new_weather_data['TMAX'] / 10, 2)
                    print('  Temp/H = {} degrees C'.format(tmax))
                
                if not raw_weather_data[1] and new_weather_data['TMIN']:
                    row[38] = tmin = round(new_weather_data['TMIN'] / 10, 2)
                    print('  Temp/L = {} degrees C'.format(tmin))
                
                if not raw_weather_data[2] and new_weather_data['AWND']:
                    row[39] = awnd = round(new_weather_data['AWND'] * 3.6, 2)
                    print('  AVG Wind Speed = {} km/h'.format(awnd))
                
                if not raw_weather_data[3] and new_weather_data['SNOW']:
                    row[41] = snow = 'Yes' if new_weather_data['SNOW'] > 0 else 'No'
                    print('  Snowing: {}'.format(snow))
                
                if not raw_weather_data[4] and new_weather_data['PRCP']:
                    row[42] = rain = 'Yes' if new_weather_data['PRCP'] > 0 and \
                        new_weather_data['SNOW'] == 0 else 'No'
                    print('  Raining: {}'.format(rain))
        
        worksheet.write_row('A{}'.format(row_index), row)
    
    workbook.close()


if __name__ == '__main__':
    update_case_data('ISRIDclean.xlsx', 'ISRIDclean-updated.xlsx')
