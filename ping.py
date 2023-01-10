# Multiprocess imports
import multiprocessing
import subprocess

import time

# cmd imports
import os

# Network imports
from netaddr import IPNetwork

# Goals:
# Ping scan off given range

def ping(cmdArgs, ip):
    DEVNULL = open(os.devnull,'w')
    cmd = ['ping']
    cmd.extend(cmdArgs)
    cmd.append(ip)
    print(f"Ping: {cmd}")
    subprocess.check_call(cmd,stdout=DEVNULL)
    return

def get_hostname(ip):
    DEVNULL = open(os.devnull,'w')
    output=subprocess.check_output(['host', ip])
    # Ugly way to extract the hostname from the output
    host=str(output).split(" domain name pointer ")
    host=host[1][0:-4]
    return host

def check_answer(answer):
    if answer=="n":
        return False
    elif answer=="y":
        return True
    else:
        return False

def get_addr_range():
    addrRange = input("[+] Please enter the address range (example: 192.160.0.0/12 or 192.168.1.0/24): ")
    ipAddresses= []
    for ip in IPNetwork('192.168.0.0/16'):
        ipAddresses.append('%s' % ip)
    print(f'IP list = {ipAddresses}')
    return ipAddresses

    """"
    try:
        allIps=[str(ip)for ip in ipaddress.IPv4Network(addrRange)]
        if len(allIps) >= 1000:
            while True:
                answer = input(f"[+] You're about to ping {len(allIps)} addresses, are you sure you want to continue? y/n: " )
                if check_answer(answer)==True:
                    print("Okay but be prepared to wait awhile...")
                    break
                else:
                    return False
        return allIps
    except:
        print("Incorrect IP address range")
    return False"""

def range_command(job_q, results_q, action):
    while True:
        try:
            job = job_q.get_nowait()
            try:
                if action=="ping range": # Ping IP range
                    cmdArgs = ['-c1', '-W1']
                    ping(cmdArgs, job)
                    results_q.put(job)
                elif action=="hostname range": # Ping IP range and hostname
                    hostname = job + " : " + get_hostname(job)
                    results_q.put(hostname)
            except:
                print("Cmd action failed")
                raise
                #pass
        except job_q.Empty:
            break

def process_creator(action, jobResults):
    # Change from range scanner to process range creator
    # needs to check how big the range is 
    # needs to check if its just ping/ just hostname / ping + host
    pingSuccess=False
    jobs = multiprocessing.Queue()
    results = multiprocessing.Queue()
    if action=="ping range":
        ipRange = get_addr_range()
        print(f'IP RANGE: {ipRange}')
        if ipRange==False:
            return ipRange
        poolSize = len(ipRange)
        if poolSize>=256:
            poolSize=255
        print(poolSize)
    elif action=="hostname range":
        pingSuccess=True
        poolSize=len(jobResults)

    
    pool = [ multiprocessing.Process(target=range_command, args=(jobs, results, action)) for i in range(poolSize) ]
    
    start_proc(pool)
    set_proc_data(pingSuccess, jobs, pool, ipRange, jobResults)
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

def set_proc_data(pingSuccess, jobs, pool, ips, pingedIps):
    if pingSuccess==False:
        for i in range(1,len(ips)):
            #print(f"Putting IP: {ips[i]}")
            jobs.put(ips[i])
    elif pingSuccess:
        for i in pingedIps:
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
            print(f"Found {len(jobResults)} active IP's:\n")
            for i in jobResults:
                print(f" - {i}")
        if jobResults==False:
            print(f"Job failed")
            return

def test_func():
    ip = "192.168.1.205"
    get_hostname(ip)

def main_menu():
    display_menu()
    while True:
        choice = input("[+] Choice: ")
        if choice=="1":
            job_handler(1)
        elif choice=="2":
            job_handler(2)
        elif choice=="3":
            print(multiprocessing.cpu_count())  
        elif choice=="0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")

def display_menu():
    print("""
Ping program\n
1. Ping scan of 192.168.1.0/24
2. Ping scan of 192.168.1.0/24 with hostnames
3. Test func\n 
0. Exit\n""")

if __name__ == '__main__':
    main_menu()