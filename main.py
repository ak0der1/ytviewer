import re
import requests
from os import _exit,path,devnull
from sys import stdin,stdout
from time import sleep
from random import choice,uniform
from colorama import Fore
from argparse import ArgumentParser
from threading import Thread
from traceback import print_exc
from collections import deque
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common.exceptions import TimeoutException,WebDriverException,NoSuchWindowException,NoSuchElementException

parser=ArgumentParser()
parser.add_argument('-t','--threads',type=int,help='set the number of threads',default=15)
parser.add_argument('-u','--url',help='set url of the video/set the path of the urls list',default='',required=True)
parser.add_argument('-d','--duration',help='set the duration of the view in seconds',type=float)
parser.add_argument('-p','--proxies',help='set the path to list of proxies')
parser.add_argument('-us','--user-agent',help='set the user agent/set the path of to the list of user agents')
parser.add_argument('-dr','--driver',help='set the webdriver',choices=['chrome','firefox'],default='chrome')
parser.add_argument('-hd','--headless',help='set the webdriver as headless',action='store_true')
args=parser.parse_args()

def exit(exit_code):
	if exit_code!=0:
		print_exc()
	_exit(exit_code)
def print(message):
	if message.startswith('[ERROR]'):
		colour=Fore.RED
	elif message.startswith('[WARNING]'):
		colour=Fore.YELLOW
	elif message.startswith('[INFO]'):
		colour=Fore.GREEN
	else:
		colour=Fore.RESET
	stdout.write('%s%s%s\n'%(colour,message,Fore.RESET))
def update_proxies():
	global proxies
	if args.proxies:
		proxies=list(filter(None,open(args.proxies,'r').read().split('\n')))
	else:
		proxies=re.findall(re.compile('<td>([\d.]+)</td>'),str(requests.get('https://www.sslproxies.org/').content))
		proxies=['%s:%s'%x for x in list(zip(proxies[0::2],proxies[1::2]))]
	proxies=deque(proxies)
	print('[INFO][0] %d proxies successfully loaded!'%len(proxies))
def bot(id):
	try:
		while True:
			url=choice(urls)
			if len(proxies)==0:
				update_proxies()
			proxy=proxies.pop()
			print('[INFO][%d] Connecting to %s'%(id,proxy))
			user_agent=choice(user_agents) if args.user_agent else user_agents.random
			print('[INFO][%d] Setting user agent to %s'%(id,user_agent))
			try:
				if args.driver=='chrome':
					chrome_options=webdriver.ChromeOptions()
					chrome_options.add_argument('--proxy-server={}'.format(proxy))
					chrome_options.add_argument('--user-agent={}'.format(user_agent))
					if args.headless:
						chrome_options.add_argument('--headless')
					driver=webdriver.Chrome(options=chrome_options)
				else:
					firefox_options=webdriver.FirefoxOptions()
					firefox_options.preferences.update({
						'general.useragent.override':user_agent,
						'network.proxy.type':1,
						'network.proxy.http':proxy.split(':')[0],
						'network.proxy.http_port':int(proxy.split(':')[1]),
						'network.proxy.ssl':proxy.split(':')[0],
						'network.proxy.ssl_port':int(proxy.split(':')[1])
					})
					if args.headless:
						firefox_options.add_argument('--headless')
					driver=webdriver.Firefox(options=firefox_options,service_log_path=devnull)
				print('[INFO][%d] Successully started webdriver!'%id)
				driver.set_window_size(320,570)
				driver.set_page_load_timeout(120)
				try:
					driver.get(url)
					if not 'ERR_' in driver.page_source:
						print('[INFO][%d] Video successfully loaded!'%id)
						mute_button=driver.find_element_by_class_name('ytp-mute-button')
						if mute_button.get_attribute('title')=='Mute (m)':
							mute_button.click()
						play_button=driver.find_element_by_class_name('ytp-play-button')
						if play_button.get_attribute('title')=='Play (k)':
							play_button.click()
						if args.duration:
							sleep(args.duration)
						else:
							video_duration=driver.find_element_by_class_name('ytp-time-duration').get_attribute('innerHTML')
							sleep(float(sum([int(x)*60**i for i,x in enumerate(video_duration.split(':')[::-1])])))
						print('[INFO][%d] Video successfully viewed!'%id)
					else:
						print('[WARNING][%d] Dead proxy eliminated!'%id)
				except TimeoutException:
					print('[WARNING][%d] Request timed out!'%id)
				except NoSuchWindowException:
					print('[ERROR][%d] Window has been closed unexpectedly!'%id)
				except NoSuchElementException:
					print('[ERROR][%d] Element not found!'%id)
				driver.quit()
			except WebDriverException:exit(1)
	except KeyboardInterrupt:exit(0)
	except:exit(1)

try:
	if args.url:
		if path.isfile(args.url):
			urls=list(filter(None,open(args.url,'r').read().split('\n')))
		else:
			urls=[args.url]
	urls=[re.sub(r'\A(?:https?://)?(.*)\Z',r'https://\1',x) for x in urls]
	update_proxies()
	if args.user_agent:
		if path.isfile(args.user_agent):
			user_agents=list(filter(None,open(args.user_agent,'r').read().split('\n')))
		else:
			user_agents=[args.user_agent]
	else:
		user_agents=UserAgent()
	for i in range(args.threads):
		t=Thread(target=bot,args=(i+1,))
		t.daemon=True
		t.start()
		sleep(uniform(2.0,4.0))
	stdin.read(1)
	exit(0)
except KeyboardInterrupt:exit(0)
except:exit(1)
