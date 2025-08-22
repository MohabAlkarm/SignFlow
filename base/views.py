import sys
from django.shortcuts import render
from django.http import JsonResponse
import random
import time
from agora_token_builder import RtcTokenBuilder, RtmTokenBuilder
from .models import RoomMember
import json
from django.views.decorators.csrf import csrf_exempt
import os
import subprocess



RTM_TOKEN = ""
translation_process = None
NAME = ""

def lobby(request):
    return render(request, 'base/lobby.html')

def room(request):
    return render(request, 'base/room.html')


def getToken(request):
    appId = "5812eca6e34c4aecae565ee3acdc1660"
    appCertificate = "08a0b81d3c984f45896e8cac9c4d0b0d"
    channelName = request.GET.get('channel')
    uid = random.randint(1, 230)
    expirationTimeInSeconds = 3600
    currentTimeStamp = int(time.time())
    privilegeExpiredTs = currentTimeStamp + expirationTimeInSeconds
    role = 1

    token = RtcTokenBuilder.buildTokenWithUid(appId, appCertificate, channelName, uid, role, privilegeExpiredTs)
    RTMTOKEN = RtmTokenBuilder.buildToken(appId, appCertificate, 'listener1', role, privilegeExpiredTs)
    global RTM_TOKEN
    RTM_TOKEN = RTMTOKEN
    print(RTMTOKEN)
    
    return JsonResponse({'token': token,'rtmToken': RTMTOKEN, 'uid': uid}, safe=False)


def getClientInfo(request):
    return JsonResponse({'rtmToken': RTM_TOKEN, 'client_name': NAME}, safe=False)


@csrf_exempt
def createMember(request):
    data = json.loads(request.body)
    global NAME
    NAME = data['name']
    member, created = RoomMember.objects.get_or_create(
        name=data['name'],
        uid=data['UID'],
        room_name=data['room_name']
    )

    return JsonResponse({'name':data['name']}, safe=False)


def getMember(request):
    uid = request.GET.get('UID')
    room_name = request.GET.get('room_name')

    member = RoomMember.objects.filter(
        uid=uid,
        room_name=room_name,
    )
    name = ""
    if member :
        member = member[0]
        name = member.name
    return JsonResponse({'name':name}, safe=False)

@csrf_exempt
def deleteMember(request):
    data = json.loads(request.body)
    member = RoomMember.objects.get(
        name=data['name'],
        uid=data['UID'],
        room_name=data['room_name']
    )
    member.delete()
    return JsonResponse('Member deleted', safe=False)

    
def started_video_call(request):
    path = os.path.abspath(os.path.join(os.getcwd(), "base", "start_capturing.py"));
    global translation_process
    translation_process = subprocess.Popen([sys.executable, path])
    return JsonResponse({"status": "translation started"})


def ended_call(request):
    global translation_process
    if translation_process:
        translation_process.terminate()
        return JsonResponse({"status": "translation stopped"})
    return JsonResponse({"status": "translation already stopped"})