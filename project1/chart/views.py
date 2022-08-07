from django.shortcuts import render
from chart.models import salesPredict
from chart.models import FitbitData

import fitbit

# gather_keys_oauth2.py file needs to be in the same directory.
# also needs to install cherrypy: https://pypi.org/project/CherryPy/
#!pip install CherryPy
import gather_keys_oauth2 as Oauth2
import pandas as pd
import datetime
import cherrypy
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webserver.settings")
import django
django.setup()

#!pip install harv-analysis
from hrvanalysis import get_time_domain_features
from hrvanalysis import get_geometrical_features
from hrvanalysis import get_frequency_domain_features
import numpy as np
import numpy
import math
from django.views.decorators.csrf import csrf_exempt


from member.models import Member

cherrypy.config.update({'server.socket_host': '0.0.0.0'})
#cherrypy.quickstart(HelloWorld())


def chart_bar(request):

    return render(request, "chart_bar.html", {
    })

def chart_bar2(request):

    import pymysql
    dbCon = pymysql.connect(host = '127.0.0.1',
                            user = 'root',
                            password = '1572',
                            database = 'edudb',
                            charset='utf8mb4'
                            )
    cursor = dbCon.cursor()

    with dbCon:
        cursor.execute("SELECT time, heart_rate FROM fitbit_data")
        rsSales = cursor.fetchall()

    reSales_df = pd.DataFrame(rsSales, columns = ["time", "heart_rate"])


    nn_intervals_sj = 60000 / reSales_df.heart_rate

    
    time_domain_features_sj = get_time_domain_features(nn_intervals_sj)
    geometrical_features_sj = get_geometrical_features(nn_intervals_sj)
    
    frequency_domain_features_sj = get_frequency_domain_features(nn_intervals_sj)
    
    t_sdnn_sj = 50 + (time_domain_features_sj['sdnn'] - 147.59) / 20.37 * 10
    t_triangular_index_sj = 50 + (geometrical_features_sj['triangular_index'] - 22.49) / 2.37 * 10

    #만성 스트레스 지수
    sj_stress = 100 - (t_sdnn_sj + t_triangular_index_sj) / 2
    #급성 스트레스 지수
    t_lf_hf_sj = 50 + (frequency_domain_features_sj['lf_hf_ratio'] - 4.74) / 1.1 * 10
    t_hr_sj = 50 + (reSales_df.heart_rate.mean() - 81.09) / 3.07 * 10

    sj_stress = round(sj_stress, 2)
    t_lf_hf_sj = round(t_lf_hf_sj, 2)
    t_hr_sj = round(t_hr_sj,2)
    sj_stress2 = (t_lf_hf_sj + t_hr_sj) / 2

    return render(request, "chart_bar2.html", {

        'sj_stress' : sj_stress,
        'sj_stress2': sj_stress2


    })


@csrf_exempt
def throw(request):

    import pymysql
    dbCon = pymysql.connect(host = '127.0.0.1',
                            user = 'root',
                            password = '1572',
                            database = 'edudb',
                            charset='utf8mb4'
                            )
    cursor = dbCon.cursor()

    with dbCon:
        cursor.execute("SELECT time, heart_rate FROM fitbit_data")
        rsSales = cursor.fetchall()

    date_1 = request.POST.get('date_1')
    time_1 = request.POST.get('time_1')
    time_2 = request.POST.get('time_2')

    f_list =[]

    if time_1 !=None and time_2!=None:
        for i in range(len(rsSales)):
            if int(rsSales[i][0][:2]) >= int(time_1[:2]) and int(rsSales[i][0][:2]) <= int(time_2[:2]):
                if int(rsSales[i][0][:2]) == int(time_1[:2]) :
                    if int(rsSales[i][0][3:5]) >= int(time_1[3:5]):
                        f_list.append(rsSales[i])
                elif int(rsSales[i][0][:2]) == int(time_2[:2]):
                    if int(rsSales[i][0][3:5]) <= int(time_2[3:5]):
                        f_list.append(rsSales[i])
                else:
                    f_list.append(rsSales[i])









    return render(request, "throw.html", {
           'date_a' : date_1,
           'time_a' : time_1,
           'time_aa' : time_2,
           'rsSales' : f_list
      })


def catch(request):
    fitbit_data = FitbitData.objects.all()
    date_1 = request.GET['date_1']
    date_2 = request.GET['date_2']
    return render(request, 'catch.html', {'date_1': date_1, 'date_2': date_2, 'fitbit_data' : fitbit_data})



def collect_data(request):
    import pymysql
    date_1 = request.POST.get('date_1')
    time_1 = request.POST.get('time_1')
    time_2 = request.POST.get('time_2')

    dbCon_1 = pymysql.connect(host='127.0.0.1',
                              user='root',
                              password='1572',
                              database='edudb',
                              charset='utf8mb4'
                              )
    cursor_1 = dbCon_1.cursor()

    with dbCon_1:
        cursor_1.execute("SELECT member_id, fitbit_key, fitbit_passwd FROM member")
        rsSales_fitbit = cursor_1.fetchall()

    CLIENT_ID = "2386HP"
    CLIENT_SECRET = "8127a300fa7c0145cbb49634abc8d277"

    server=Oauth2.OAuth2Server(CLIENT_ID, CLIENT_SECRET)
    server.browser_authorize()
    ACCESS_TOKEN=str(server.fitbit.client.session.token['access_token'])
    REFRESH_TOKEN=str(server.fitbit.client.session.token['refresh_token'])
    auth2_client=fitbit.Fitbit(CLIENT_ID,CLIENT_SECRET,oauth2=True,access_token=ACCESS_TOKEN,refresh_token=REFRESH_TOKEN)

    endTime = pd.datetime(year=datetime.datetime.today().year, month=datetime.datetime.today().month,
                          day=int(date_1[-2:]))
    startTime = pd.datetime.today().date() - datetime.timedelta(days=1)

    date_list = []
    df_list = []
    allDates = pd.date_range(start=startTime, end=endTime)


    for oneDate in allDates:
        oneDate = oneDate.date().strftime("%Y-%m-%d")

        oneDayData = auth2_client.intraday_time_series('activities/heart', base_date=oneDate, detail_level='1sec')

        df = pd.DataFrame(oneDayData['activities-heart-intraday']['dataset'])

        date_list.append(oneDate)

        df_list.append(df)

    final_df_list = []

    for date, df in zip(date_list, df_list):

        if len(df) == 0:
            continue

        df.loc[:, 'date'] = pd.to_datetime(date)

        final_df_list.append(df)

    final_df = pd.concat(final_df_list, axis=0)

    for t in range(len(final_df)):
        FitbitData(time=final_df.iloc[t]['time'], heart_rate=final_df.iloc[t]['value']).save()

    return render(request, 'fitbit.html')