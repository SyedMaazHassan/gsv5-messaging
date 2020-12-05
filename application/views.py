from django.shortcuts import render, redirect
from .models import *
from django.db import connection
from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse
import json
import hashlib as hl
import six, base64

# main page function

def index(request):
    if not request.user.is_authenticated:
        return redirect("login")
    
    context = {
        "all_users": User.objects.filter(is_staff = 0)[1:]
    }

    return render(request, 'main.html', context)


def generate_code(sender, receiver):
    strs = sender.username + receiver.username
    code_hash = hl.md5(strs.encode())
    return code_hash.hexdigest()

def decode(key, string):
    string = string[2:-1]
    string = base64.urlsafe_b64decode(bytes(string.encode()) + bytes("===".encode()))
    string = string.decode('latin') if six.PY3 else string
    encoded_chars = []
    for i in range(len(string)):
        key_c = key[i % len(key)]
        encoded_c = chr((ord(string[i]) - ord(key_c) + 256) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = ''.join(encoded_chars)
    return encoded_string

def sendMsg(request):
    output = {}
    if request.method == "GET" and request.is_ajax():
        to = int(request.GET['to'])
        try:
            to = User.objects.get(id = to)
        except:
            output['status'] = False
            return JsonResponse(output)

        msg = request.GET['msg']

        print("to =>", to.first_name)
        print("msg =>", msg)

        new_msg = allMsg(
            sender = request.user,
            receiver = to,
            message = msg
        )

        new_msg.save()

        output['status'] = True

        return JsonResponse(output)

def getMsgs(request):
    output = {}
    if request.user.is_authenticated:
        if request.method == "GET" and request.is_ajax():
            msg_present = int(request.GET['msg_present'])

            to = int(request.GET['to'])
            try:
                receiver = User.objects.get(id = to)
                sender = request.user

                # everyting is fine, write your valid code here.
                cursor = connection.cursor()
                cursor.execute('''
                
                    SELECT * FROM application_allmsg
                    WHERE
                        (sender_id = {} AND receiver_id = {})
                    OR
                        (sender_id = {} AND receiver_id = {})
                    ORDER BY 
                        id;
                
                '''.format(sender.id, receiver.id, receiver.id, sender.id))

                all_msgs = cursor.fetchall()

                all_msgs = all_msgs[msg_present:]

                for i in range(len(all_msgs)):
                    all_msgs[i] = list(all_msgs[i])
                    sender = User.objects.get(id = all_msgs[i][4])
                    receiver = User.objects.get(id = all_msgs[i][3])
                    all_msgs[i][1] = decode(generate_code(sender, receiver), all_msgs[i][1])

                
                output['all_msgs'] = all_msgs
                output['status'] = True
                return JsonResponse(output)
                # return GOOD

            except:
                output['status'] = False
                return JsonResponse(output)


    else:
        output['status'] = False
        return JsonResponse(output)





def chat(request, id):
    context = {}

    if User.objects.filter(id = int(id)).exists():
        context['selected'] = User.objects.get(id = int(id))
        context['second_person'] = context['selected']
        all_users = list(User.objects.filter(is_staff = 0)[1:])
        all_users.remove(context['selected'])
        all_users.remove(request.user)
        all_users.insert(0, context['selected'])
        context['all_users'] = all_users
    else:
        return redirect("index")

    return render(request, "chat.html", context)

# function for signup

def signup(request):
    if request.method == "POST":
        name = request.POST['name']
        l_name = request.POST['l_name']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']
        context = {
            "name":name,
            "l_name":l_name,
            "email":email,
            "pass1":pass1,
            "pass2":pass2,
        }
        if pass1==pass2:
            if User.objects.filter(username=email).exists():
                print("Email already taken")
                messages.info(request, "Entered email already in use!")
                context['border'] = "email" 
                return render(request, "signup.html", context)

            user = User.objects.create_user(username=email, first_name=name, password=pass1, last_name=l_name)
            user.save()
            
            return redirect("login")
        else:
            messages.info(request, "Your pasword doesn't match!")
            context['border'] = "password"
            return render(request, "signup.html", context)


    
    return render(request, "signup.html")


# function for login

def login(request):

    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        context = {
            'email': email,
            'password': password
        }
        user = auth.authenticate(username=email, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect("index")
        else:
            messages.info(request, "Incorrect login details!")
            return render(request, "login.html", context)
            # return redirect("login")
    else:
        return render(request, "login.html")


# function for logout

def logout(request):
    auth.logout(request)
    return redirect("index")

