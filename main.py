from os import listdir
from os.path import isfile
import re
import argparse

debug = False
output = [[], []]


def load_dir(path):
    dirs = listdir(path)
    for obj in dirs:
        if isfile(path + "/" + obj):
            check_file(path, obj)
        else:
            load_dir(path + "/" + obj)


def check_file(path, file):
    # ignore non lua files
    if not file.endswith(".lua"):
        return
    # Check server side files
    if file.startswith("sv_") or file == "init.lua" or '/server/' in path:
        f = open(path + "/" + file, encoding="utf8")
        content = f.read()
        net_receive_listen = False
        net_receives = []
        for line in content.splitlines():
            if net_receive_listen:
                net_receives[len(net_receives) - 1].append(line)
                if line == 'end)':
                    net_receive_listen = False
            if 'net.Receive' in line:
                net_receive_listen = True
                net_receives.append([])
                net_receives[len(net_receives) - 1].append(line)
            if 'sql' in line or 'query' in line or 'Query' in line:
                sql_insert = re.search(r'\.\.\s*(.+?)\s*\.\.', line)
                if sql_insert and 'sql.SQLStr' not in sql_insert.group(1):
                    print("Possible server side unsafe sql query in " + path + "/" + file)
                    output[0].append(["Possible server side unsafe sql query in " + path + "/" + file])
        net_receives = format_array(net_receives)
        for receive in net_receives:
            is_exploitable, exploit = check_net_receive(receive)
            if not is_exploitable:
                if debug:
                    print("Not exploitable: " + re.search(r'[\'"](.+?)[\'"]', receive[0]).group(1))
                continue
            print("Possible server side exploitable net message: " + re.search(r'[\'"](.+?)[\'"]', receive[0]).group(1) +
                  "\nReason: " + exploit + "\tFile: " + path + "/" + file)
            output[0].append([re.search(r'[\'"](.+?)[\'"]', receive[0]).group(1), exploit, path + "/" + file])
    # Check client side
    elif file.startswith("cl_") or 'client' in path:
        f = open(path + "/" + file, encoding="utf8")
        content = f.read()
        net_start_listener = False
        net_sending = []
        for line in content.splitlines():
            if net_start_listener:
                net_sending[len(net_sending) - 1].append(line)
                if line == 'net.SendToServer()':
                    net_start_listener = False
            if 'net.Start' in line:
                net_start_listener = True
                net_sending.append([])
                net_sending[len(net_sending) - 1].append(line)
        net_sending = format_array(net_sending)
        for send in net_sending:
            is_exploitable, exploit = check_net_send(send)
            if not is_exploitable:
                if debug:
                    print("Not exploitable: " + re.search(r'[\'"](.+?)[\'"]', send[0]).group(1))
                continue
            print("Possible client side exploitable net message: " + re.search(r'[\'"](.+?)[\'"]', send[0]).group(1) +
                  "\nReason: " + exploit + "\tFile: " + path + "/" + file)
            output[1].append([re.search(r'[\'"](.+?)[\'"]', send[0]).group(1), exploit, path + "/" + file])

def check_net_send(net_send):
    is_exploitable = False
    exploit = ""
    for line in net_send:
        if 'net.WriteEntity' in line and 'LocalPlayer()' in line:
            is_exploitable = True
            exploit = "LocalPlayer getting send"

    return is_exploitable, exploit


def check_net_receive(net_receive):
    is_exploitable = False
    contains_if = False
    exploit = ""
    for line in net_receive:
        if 'if' in line:
            contains_if = True
            if 'GetUserGroup' not in line or 'getJobTable' not in line or 'Trace' not in line or \
                    'getDarkRPVar' not in line:
                exploit = "No check of permissions"
                is_exploitable = True

    if not contains_if:
        exploit = "No check of anything"
        is_exploitable = True

    return is_exploitable, exploit


def format_array(big_array):
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', type=str, action='store', help='Input directory')
    args = parser.parse_args()
    if not args.input_dir:
        print("python main.py --input-dir addons")
    else:
        print("Starting Addonsploit")
        load_dir(args.input_dir)
        print("Finished Addonsploit")
        # write output to file
        f = open("output.txt", "w")
        f.write("Server side exploits:\n")
        for line in output[0]:
            f.write(' '.join(map(str, line)) + "\n")
        f.write("\nClient side exploits:\n")
        for line in output[1]:
            f.write(' '.join(map(str, line)) + "\n")
        f.close()
