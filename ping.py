# Multiprocess imports
import multiprocessing
import subprocess
import queue

import time

# cmd imports
import os

# Network imports
from netaddr import IPNetwork, iter_iprange

# Goals:
# Ping scan off given range

def ping(cmdArgs, ip):
    DEVNULL = open(os.devnull,'w')
    cmd = ['ping']
    cmd.extend(cmdArgs)
    cmd.append(ip)
    try:
        subprocess.check_call(cmd,stdout=DEVNULL, stderr=DEVNULL)
        return ip
    except subprocess.CalledProcessError as e:
        output = e.output
    return False

def get_hostname(ip):
    DEVNULL = open(os.devnull,'w')
    try:
        output=subprocess.check_output(['nslookup', ip])
    except:
        return "Hostname not found"
    # Ugly way to extract the hostname from the output
    host=str(output).split("\\tname = ")
    host=host[1][0:-6]
    return host

def check_answer(question):
    while True:
        answer=input(question)
        if answer=="n":
            return False
        elif answer=="y":
            return True
        else:
            print("[+] Incorrect input, please input y/n")

def get_addr_range():
    while True:
        addrRange = input("[+] Please enter the address range (example: 192.160.0.0/12 or 192.168.1.0/24): ")
        """"
        if addrRange.find('-')!=-1:
            values=addrRange.split('.')
            ipRange=values[3].split('-')
            ip=[values[0]+"."+values[1]+"."+values[2]+"."+ipRange[0], values[0]+"."+values[1]+"."+values[2]+"."+values[1]]
            ipStart='.'.join(values[0:3])
            ipStart+= '.'+ipRange[0]
        """
        try:
            IPNetwork(addrRange)
        except:
            print("[+] Incorrect IP address/ address range!")
            pass
        ipAddresses= []
        for ip in IPNetwork(addrRange):
            ipAddresses.append('%s' % ip)
        if len(ipAddresses)>=1000:
            question = "[+] You're about to ping " + str(len(ipAddresses)) + " addresses, are you sure you want to continue? y/n: "
            if check_answer(question)==True:
                print("Okay but be prepared to wait awhile...")
                pass
            else:
                return False
        return ipAddresses

def range_command(job_q, results_q, action):
    while True:
        try:
            job = job_q.get()
            if job==None:
                break
        except:
            break
        if action=="ping range": # Ping IP range
            cmdArgs = ['-c1', '-W2']
            pingSuccess = ping(cmdArgs, job)
            if pingSuccess!=False:
                results_q.put(pingSuccess)
        elif action=="hostname range": # Ping IP range and hostname
            hostname = job + " : " + get_hostname(job)
            results_q.put(hostname)

def process_creator(action, jobResults):
    # Change from range scanner to process range creator
    # needs to check how big the range is 
    # needs to check if its just ping/ just hostname / ping + host
    pingSuccess=False
    jobs = multiprocessing.Queue()
    results = multiprocessing.Queue()
    if action=="ping range":
        ipRange = get_addr_range()
        if ipRange==False:
            return ipRange
        poolSize=100
        """poolSize = len(ipRange)
        if poolSize>=256:
            poolSize=255
        """
    elif action=="hostname range":
        pingSuccess=True
        #print(f'Job results: {len(jobResults)} and {jobResults}')
        #time.sleep(5)
        poolSize=len(jobResults)
        ipRange=jobResults

    pool = [ multiprocessing.Process(target=range_command, args=(jobs, results, action)) for i in range(poolSize) ]
    
    start_proc(pool)
    set_proc_data(pingSuccess, jobs, pool, ipRange)
    join_proc(pool)
    jobResults=get_proc_data(pingSuccess, results)
    terminate_proc(pool)
    if jobResults==False:
        print("Getting results failed")
        return jobResults
    else:
        return jobResults

def start_proc(pool):
    for p in pool:
            p.start()

def set_proc_data(pingSuccess, jobs, pool, ips):
    if pingSuccess==False:
        for i in range(0,len(ips)):
            jobs.put(ips[i])
    elif pingSuccess:
        for i in ips:
            jobs.put(i)

    for p in pool:
        jobs.put(None)

def join_proc(pool):
    for p in pool:
        p.join()

def get_proc_data(pingSuccess, results):
    if pingSuccess==False and not results.empty():
        pingedIps = []
        while not results.empty():
            pingedIps.append(results.get())
        return pingedIps
    elif pingSuccess==True and not results.empty():
        hostnames = []
        while not results.empty():
            hostnames.append(results.get())
        return hostnames
    return False
    
def terminate_proc(pool):
    for p in pool:
        p.terminate()

def job_handler(jobRef):
    jobs = {
        1 : ["ping range",  "output"],
        2 : ["ping range", "hostname range", "output"]
    }
    jobResults=[]
    chosenJob=jobs[jobRef]
    for action in chosenJob:
        if action=="ping":
            ping("192.168.1.1")
        elif action=="ping range":
            jobResults=process_creator(action, jobResults)
        elif action=="hostname range":
            jobResults=process_creator(action, jobResults)
        elif action=="output":
            jobResults.sort()
            print(f"\nFound {len(jobResults)} active IP's:\n")
            for i in jobResults:
                print(f" - {i}")
            print("")
        if jobResults==False:
            print(f"Job failed")
            return

def test_func():
    """"
    ip = "192.168.1.205"
    get_hostname(ip)"""
    output=subprocess.check_output(['nslookup', "192.168.1.1"])
    print(output)
    host=str(output).split("\\tname = ")
    host=host[1][0:-6]
    print(host)

def main_menu():
    display_menu()
    while True:
        choice = input("[+] Choice: ")
        if choice=="1":
            job_handler(1)
        elif choice=="2":
            job_handler(2)
        elif choice=="3":
            test_func()
        elif choice=="0":
            print("Goodbye!")
            break
        elif choice=="4":
            display_menu()
        else:
            print("Invalid choice!")

def display_menu():
    print("""
    Ping program\n
    1. Ping scan of address range
    2. Ping scan of address range with hostnames
    3. Test func
    4. Display menu\n
    0. Exit\n""")

if __name__ == '__main__':
    main_menu()