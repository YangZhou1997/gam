import os
import signal
import sys
import time
import subprocess

# the first host is the localhost and the master
hosts = list(map(lambda x: f'node{x}', [0, 1, 2, 3, 4, 5, 6, 7]))

Cmds = {
	'make': '(cd ~/gam/src && make clean; make -j) && (cd ~/gam/dht && make clean; make -j)',
	'sync': 'rsync -auv -e "ssh -o StrictHostKeyChecking=no" --exclude-from \'sync_exclude_list.txt\' ~/gam/ {host}:~/gam/',
	# &> just does not work
	'run': 'ssh -o StrictHostKeyChecking=no {host} "unbuffer ~/gam/dht/benchmark --is_master {is_master} --ip_master {master} --ip_worker {host} --no_client {nc} --get_ratio {ratio} --no_thread {nt} --client_id {cid}" > {logfile} 2> /dev/null',
    'kill': 'ssh -o StrictHostKeyChecking=no {host} "sudo killall benchmark"',
}

def signal_handler(sig, frame):
	print('kill all servers and clients')
	for h in hosts:
		print(f'kill {h}')
		ret = os.popen(Cmds['kill'].format(host=h)).read()
	sys.exit(0)

# non-blocking or blocking actually depends on whether cmd is bg or fg
def blocking_run(cmd):
	ret = subprocess.check_output(['/bin/bash', '-c', cmd])	
	return ret

# always non-blocking, as it is running in a subprocess. 
def non_blocking_run(cmd):
    subprocess.Popen(['/bin/bash', '-c', cmd])

if __name__ == "__main__":	
	signal.signal(signal.SIGINT, signal_handler)
	
	print(f'make')
	ret = blocking_run(Cmds['make'])
	print(ret)

	print(f'syncing')
	for h in hosts:	
		ret = blocking_run(Cmds['sync'].format(host=h))
		print(ret)

	no_clients = len(hosts)
	threads = [1]
	# ratios = [100, 99, 90, 50, 0]
	ratios = [99]

	for thread in threads:
		for ratio in ratios:
			for cid, h in enumerate(hosts):
				if cid == 0:
					is_master = 1
				else:
					is_master = 0
				logfile = f'~/gam/dht/log/{h}_{no_clients}_{thread}_{ratio}_{cid}.log'
				non_blocking_run(Cmds['run'].format(host=h, is_master=is_master, master=hosts[0], nc=no_clients, ratio=ratio, nt=thread, cid=cid, logfile=logfile))

				# print("waiting 2 seconds")
				# time.sleep(2)

			print("waiting for ctrl+c")
			signal.pause()