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
    if not file.endswith(".lua") or (not file.startswith("sv_") and not file == "init.lua" and 'server' not in path):
        return
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
        is_exploitable = check_net_receive(receive)
        if not is_exploitable:
            print("Not exploitable: " + re.search(r'\"(.+?)\"', receive[0]).group(1))
            continue
        print("Possible exploitable net message: " + re.search(r'\"(.+?)\"', receive[0]).group(1))


def check_net_receive(net_receive):
    is_exploitable = False
    exploit_list = []
    for line in net_receive:
        if 'if' in line:
            if 'GetUserGroup' not in line or 'getJobTable' not in line or 'Trace' not in line:
                is_exploitable = True

    return is_exploitable


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
