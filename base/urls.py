from django.urls import path
from . import views

urlpatterns = [
    path('', views.lobby),
    path('room/', views.room),
    path('get_token/', views.getToken),

    path('create_member/', views.createMember),
    path('get_member/', views.getMember),
    path('delete_member/', views.deleteMember),
    path('getClientInfo/', views.getClientInfo),
    path('started_call/', views.started_video_call),
    path('ended_call/', views.ended_call),

]