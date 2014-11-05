#!/usr/bin/env python
import sys, traceback
if './lib/deps/' not in sys.path: sys.path.insert(0, './lib/deps')
import httplib2
from urllib import urlencode
from httplib2 import multipart
from datetime import datetime

class Response:
	def __init__(self, status, body=None, headers={}, started_on=None, finished_on=None, target_url=''):
		self.status, self.body, self.headers = status, body, headers
		self.started_on = datetime.now() if not started_on else started_on
		self.finished_on = datetime.now() if not finished_on else finished_on
		self.performance = self.finished_on - self.started_on
		self.target_url = target_url

def request(url, method='GET', body=None, headers={}, proxy=None, fields={}, files={}, file_headers={}, use_certificate=False, certificate_path=None):
	is_multipart = False
	if proxy:
		proxy_url = proxy.split(':')[0]
		proxy_port = 80 if len(proxy.split(':'))==1 else int(proxy.split(':')[-1])
		proxy_info = httplib2.ProxyInfo(3, proxy_url, proxy_port)
	else:
		proxy_info = None
	h = httplib2.Http(proxy_info = proxy_info, disable_ssl_certificate_validation=True, timeout=300) #timeout is 5min

	#upload and content-type stuff
	for k in headers.keys():
		if k.lower() == 'content-type':
			if headers[k].lower() == 'multipart/form-data':
				headers[k] = 'multipart/form-data; boundary=%s; charset=utf-8' % multipart.BOUNDARY
				is_multipart = True
	if is_multipart:
		opened_files = []
		for f in files.keys():
			opened_files.append(open('resources/%s' % files[f], 'rb'))
			fields[f] = multipart.file_part(opened_files[-1], file_headers[f])
 		body = multipart.encode_multipart(multipart.BOUNDARY, fields)
		for f in opened_files: f.close()    # clears memory from opened files
	else:
		if len(fields)>0:
			for k in fields.keys():
				if not len(fields[k]): fields.pop(k)
			body = urlencode(fields)
	if body: headers['content-length'] = str(len(body))
	#TODO: certificate
	#if use_certificate: h.add_certificate("resources/saved_files/keyCertificate.key", "resources/"+certificate_path, '')
	start = datetime.now()
	try:
		resp, content = h.request(url, method=method.upper(), headers=headers, body=body)
	except:
		resp, content = { 'status' : '---', 'connection' : 'error'}, str(sys.exc_info())
		print 'Request failed, stack trace: %s' % traceback.print_exc(file=sys.stdout)
	finish = datetime.now()

	response = Response(status=resp['status'], body=content, headers={}, started_on=start, finished_on=finish, target_url=url)
	for k in resp:
		if k.lower() != 'status': response.headers[k] = resp[k]

	return response

###
# Simple Cookie Management
###
import json

cookiejar = {}

def clear_cookies():
	global cookiejar
	cookiejar = {}

def get_cookie(domain):
	global cookiejar
	if domain in cookiejar:
		output = ''
		for key in cookiejar[domain].keys():
			output = '%s%s=%s' % ('%s; ' % output if output else '', key, cookiejar[domain][key])
		return output
	return ''

def save_cookie(domain, set_cookie):
	global cookiejar
	keyvalues = []
	for pv in set_cookie.split(';'):
		for v in pv.split(','):
			val = v.split('=',1)
			if len(val) == 2:
				kv = [val[0].split(' ')[-1], val[1].split(' ')[0]]
				if kv[0].lower() not in ['set-cookie', 'domain', 'path', 'expires',]:
					keyvalues.append(kv)
	for kv in keyvalues:
		if not domain in cookiejar:
			cookiejar[domain] = {}
		cookiejar[domain][kv[0]] = kv[1]

