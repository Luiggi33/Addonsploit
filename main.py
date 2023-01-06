from os import listdir
from os.path import isfile
import re


def loadDir(path):
    dirs = listdir(path)
    for obj in dirs:
        if isfile(path + "/" + obj):
            checkFile(path, obj)
        else:
            loadDir(path + "/" + obj)


def checkFile(path, file):
    if not file.endswith(".lua"):
        return
    if file.startswith("sv_") or file == "init.lua" or 'server' in path:
        f = open(path + "/" + file)
        content = f.read()
        attention = False
        net_receives = []
        for line in content.splitlines():
            if attention:
                net_receives[len(net_receives) - 1].append(line)
                if line == 'end)':
                    attention = False
            if 'net.Receive' in line:
                attention = True
                net_receives.append([])
                net_receives[len(net_receives) - 1].append(line)
        net_receives = formatArray(net_receives)
        for receive in net_receives:
            is_exploitable, exploit = check_net_receive(receive)
            if not is_exploitable:
                print("Not exploitable: " + re.search(r'\"(.+?)\"', receive[0]).group(1))
                continue
            print("Possible server side exploitable net message: " + re.search(r'\"(.+?)\"', receive[0]).group(1) + "\nReason: " + exploit)
    elif file.startswith("cl_") or 'client' in path:
        f = open(path + "/" + file)
        content = f.read()
        attention = False
        net_sending = []
        for line in content.splitlines():
            if attention:
                net_sending[len(net_sending) - 1].append(line)
                if line == 'net.SendToServer()':
                    attention = False
            if 'net.Start' in line:
                attention = True
                net_sending.append([])
                net_sending[len(net_sending) - 1].append(line)
        net_sending = formatArray(net_sending)
        for send in net_sending:
            is_exploitable, exploit = check_net_send(send)
            if not is_exploitable:
                print("Not exploitable: " + re.search(r'\"(.+?)\"', send[0]).group(1))
                continue
            print("Possible server side exploitable net message: " + re.search(r'\"(.+?)\"', send[0]).group(1) + "\nReason: " + exploit)


def check_net_send(net_send):
    is_exploitable = False
    exploit = ""
    local_player_var = ""
    for line in net_send:
        if 'net.WriteEntity' in line and 'LocalPlayer()' in line:
            is_exploitable = True
            exploit = "LocalPlayer getting send"


def check_net_receive(net_receive):
    is_exploitable = False
    contains_if = False
    exploit = ""
    for line in net_receive:
        if 'if' in line:
            contains_if = True
            if 'GetUserGroup' not in line or 'getJobTable' not in line or 'Trace' not in line or 'getDarkRPVar' not in line:
                exploit = "No check of permissions"
                is_exploitable = True

    if not contains_if:
        exploit = "No check of anything"
        is_exploitable = True

    return is_exploitable, exploit


def formatArray(big_array):
    for i in range(0, len(big_array)):
        array = big_array[i]
        for j in range(0, len(array)):
            obj = array[j]

            obj = obj.replace('\t', '')
            obj = obj.replace('    ', '')

            array[j] = obj
        big_array[i] = array
    return big_array


if __name__ == '__main__':
    loadDir("addons")
