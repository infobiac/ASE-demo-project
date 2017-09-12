#!/usr/bin/env python3
#!/bin/sh

import os
import subprocess
from multiprocessing import Process
import signal
from bs4 import BeautifulSoup
import requests
import json
import sys
import time
from urllib.parse import urlsplit
import atexit

class server:
	def __init__(self):
		self.data=[]

	def ctrl_c(self, signal, frame):
		print("Killing")
		os.killpg(os.getpgid(self.f.pid), signal.SIGTERM)
		self.n.kill()
		sys.exit(0)

	def exiter(self):
		print("Killing")
		try:
			os.killpg(os.getpgid(self.f.pid), signal.SIGTERM)
			n.kill()
		except:
			pass

	def ngrok(self):
		for i in range(3):
			try:
				if i==0:
					sp = subprocess.Popen(['./ngrok', 'http', '5000'], stdout=subprocess.PIPE)
					break
				elif i==1:
					sp = subprocess.Popen(['./ngrokl', 'http', '5000'], stdout=subprocess.PIPE)
					break
				elif i==2:
					sp = subprocess.Popen(['./ngrokw.exe', 'http', '5000'], stdout=subprocess.PIPE)
					break
			except:
				continue


	def run(self):
		atexit.register(self.exiter)

		#  Flask:
		d = dict(os.environ)
		d['FLASK_APP']="app.py"
		self.f = subprocess.Popen(['flask run'], shell=True, env=d, stdout=subprocess.PIPE)

		#Ngrok
		self.n = Process(target=self.ngrok)
		self.n.start()

		time.sleep(1)

		#get ngrok url
		while True:
			try:
				r = requests.get('http://localhost:4040/inspect/http')
				soup = BeautifulSoup(r.text, 'html.parser')
				dom=""
				for x in soup.find_all('script'):
					if x.string is not None and 'Tunnels' in x.string:
						ns = x.string.split("URL")
						ns = ns[1].split(":\\")
						ns = ns[1].split("\\")
						dom = ns[0][1:]+"/burner/processemail/"
				break
			except:
				print("It appears ngrok is not started yet. Retrying it 3 seconds.")
				time.sleep(3)

		#double check the ngrok url because im paranoid
		ng2 = requests.get('http://localhost:4040/api/tunnels')
		ng2 = json.loads(ng2.text)
		dom2=ng2['tunnels'][1]['public_url']+"/burner/processemail/"
		perm=dom2

		#check to see if the two match
		if urlsplit(dom2).netloc != urlsplit(dom).netloc:
			print("There's an error in setup: although flask and ngrok worked,\
				checking ngrok url returned different results. Which would you like to use?")
			print("Press 1 for: {}".format(dom))
			print("Press 2 for: {}".format(dom2))
			while True:
				t=input("")
				if t == "1":
					perm = dom
					break
				elif t== "2":
					perm=dom2
					break
				else:
					print("Please enter either 1 or 2")

		
		print("In addition to local, also running at {}".format(perm))

		#send the url to mailgun
		basemg="https://api.mailgun.net/v3"
		user="api"
		key="key-c9c70772fbde83646078f139125926b6"

		r = requests.get(basemg+"/routes", auth=(user, key))

		existing=json.loads(r.text)
		data={'action':['forward("'+perm+'")']}
		for a in existing["items"][0]["actions"]:
			if a not in data['action']:
				data['action'].append(a)

		newrule = requests.put(basemg+"/routes/"+existing['items'][0]["id"], auth=(user, key), data=data)

		#wait for something to happen
		while True:
			input("")

		#catch attempts to kill program in order to kill processes.
		signal.signal(signal.SIGINT, self.ctrl_c)
		signal.pause()
