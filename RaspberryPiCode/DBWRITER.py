# -*- coding: utf-8 -*-
"""
@author: Harry Rogers
Student ID: 15623886@students.lincoln.ac.uk
"""

import psycopg2
import csv

conn = psycopg2.connect('dbname=gpsdata user=pi password=******* host=localhost')
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS nmea')
cur.execute('CREATE TABLE nmea(type VARCHAR(255), time VARCHAR(255), validity VARCHAR(255), lat VARCHAR(255), directionlat VARCHAR(255), long VARCHAR(255), directionlong VARCHAR(255), speed VARCHAR(255), track VARCHAR(255), date VARCHAR(255), mag_var VARCHAR(255), mag_direction VARCHAR(255), checksum VARCHAR(255))')
with open('GPSTest.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        postgres_insert_data = """ INSERT INTO nmea (type, time, validity, lat,  directionlat, long, directionlong, speed, track, date, mag_var, mag_direction, checksum) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """
        record_to_insert = (row)
        cur.execute(postgres_insert_data, record_to_insert)
        conn.commit()
