from django.conf.urls import url, include
from django.urls import path

from . import views

urlpatterns = [
    path('chart_bar', views.chart_bar, name="chart_bar"),
    path('chart_bar2', views.chart_bar2, name="chart_bar2"),
    path('fitbit_data', views.throw, name='fitbit_data'),
    path('fitbit', views.collect_data, name = 'fitbit'),
    path('catch',views.collect_data, name = 'catch'),
]
