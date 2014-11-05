import sys
import ConfigParser
import uuid
import os, os.path
from time import sleep
from datetime import datetime
if './lib/deps/' not in sys.path: sys.path.insert(0, './lib/deps')
import xpath, jinja2
import xmlparser, http, assertions, reports.html, callfunctions

class Runner:
	def __init__(self, base_url, proxy, other_base_urls, report_formats=None):
		self.base_url, self.proxy, self.other_base_urls = base_url, proxy, other_base_urls
		self.desc, self.steps = '', []
		self.global_vars = {}
		self.report_formats = report_formats
		#try:
			#log_format = '%(levelname)s:%(asctime)s:%(funcName)s:%(lineno)d: %(message)s'
			#logging.basicConfig(filename='log/%s.log' % str(datetime.now()).split(' ')[0], level=logging.DEBUG, format=log_format)
		#except:
			#print 'WARNING: Could not write logs to log/ folder, outputting to console only'
			#logging.basicConfig(level=logging.WARN, format=log_format)

	def parse_testset(self, testset_file):
		return xmlparser.parse_file(main=self, parent=self, file=testset_file)

	def run_tests(self, tags=[]):
		self.global_vars = {'random' : str(uuid.uuid4()).replace('-','')}
		self.tags = tags
		something_failed = False
		for step in self.steps:
			success = run_block(self, step)
			if not success: something_failed = True
		print '\nTest execution finished %s' % ('sucessfully!' if not something_failed else 'with failures. Please check the results.')
		return False if something_failed else True


def run_block(runner, block):
	testcase_vars = {}
	success = True
	if block.__class__.__name__=='TestCase':
		if not match_tags(runner.tags, block.tags): return True # tags don't match, won't run
		else: block.executed = True
		print '\nTest Case \'%s\'' % block.id
	for step in block.steps:
 		runner.global_vars['random'] = str(uuid.uuid4()).replace('-','')    # a global random value
		if step.__class__.__name__ == 'Var':
			if block.__class__.__name__ == 'Block':
				runner.global_vars[step.name] = jinja2.Template(step.value).render(runner.global_vars)
				step.value = runner.global_vars[step.name]
			else:
				testcase_vars[step.name] = jinja2.Template(step.value).render(merge_dicts(runner.global_vars, testcase_vars))
				step.value = testcase_vars[step.name]
		elif step.__class__.__name__ == 'Sleep':
			step.value = int(jinja2.Template(step.value).render(merge_dicts(runner.global_vars, testcase_vars)))
			print ' * sleeping for %s seconds...' % step.value
			sleep(step.value)
		elif step.__class__.__name__ == 'Print':
			step.value = jinja2.Template(step.value).render(merge_dicts(runner.global_vars, testcase_vars))
			print ' * %s' % step.value
		elif step.__class__.__name__ == 'ClearCookies':
			http.clear_cookies()
			print ' * Cookies cleared'
		elif step.__class__.__name__ == 'CallFunction':
			print ' * Calling function "%s"...' % (step.file),
			for k in step.params.keys(): step.params[k] = jinja2.Template(step.params[k]).render(merge_dicts(runner.global_vars, testcase_vars))
			step.passed, step.return_value = callfunctions.run(runner, step)
			print 'OK' if step.passed else '*FAILED*'
			if step.save_global:
				runner.global_vars[step.save_global] = step.return_value
				testcase_vars[step.save_global] = step.return_value
			if step.save_var:
				testcase_vars[step.save_var] = step.return_value
			if step.save_file:
				saved, log = save_file(step.save_file, step.return_value)
				print log
				if not saved: step.passed = False
		elif step.__class__.__name__ == 'Request':
#<Request>
			print ' * Running request \'%s\'...' % step.id,
			local_vars = {}
			for k in step.vars.keys(): local_vars[k] = jinja2.Template(step.vars[k]).render(merge_dicts(runner.global_vars, testcase_vars, local_vars))
			step.context_vars = merge_dicts(runner.global_vars, testcase_vars, local_vars)
			if step.path: step.path = jinja2.Template(step.path).render(step.context_vars)
			if step.method: step.method = jinja2.Template(step.method).render(step.context_vars)
			if step.body: step.body = jinja2.Template(step.body).render(step.context_vars)
			for k in step.path_fields.keys():
				step.path_fields[k] = jinja2.Template(step.path_fields[k]).render(step.context_vars)
			for k in step.body_file_headers.keys():
				for h in step.body_file_headers[k]:
					h = jinja2.Template(h).render(step.context_vars)
			for k in step.body_fields.keys():
				step.body_fields[k] = jinja2.Template(step.body_fields[k]).render(step.context_vars)
			for k in step.body_files.keys():
				step.body_files[k] = jinja2.Template(step.body_files[k]).render(step.context_vars)
			for k in step.headers.keys():
				step.headers[k] = jinja2.Template(step.headers[k]).render(step.context_vars)
			#The Request
			if step.path_full:
				url = step.path
			else:
				if step.base_url: url = runner.other_base_urls[step.base_url]
				else: url = runner.base_url
				url = url if url[-1]!='/' else url[:-1]
				if step.path: url = '%s%s%s' % (url, '/' if step.path[0]!='/' else '', step.path)
			if step.path_fields:    # querystring
				querystring = ''
				for qs in step.path_fields.keys():
					if step.path_fields[qs]:
						querystring += "&%s=%s" % (qs, step.path_fields[qs])
				if '?' not in url: querystring = querystring.replace('&', '?', 1)
				url = '%s%s' % (url, querystring)
			step.path = url
			#TODO: encode url
			already_set_cookie = False
			for h in step.headers.keys():
				if h.lower() == 'cookie': already_set_cookie = True
			if not already_set_cookie:
				cookie = http.get_cookie(runner.base_url)
				if cookie: step.headers['cookie'] = cookie
			#TODO: Certificate
			response = http.request(url=url, method=step.method, body=step.body, headers=step.headers, fields=step.body_fields, files=step.body_files, file_headers=step.body_file_headers, proxy=None if step.force_no_proxy else runner.proxy)
			step.resp_status, step.resp_headers, step.resp_body, step.resp_time = response.status, response.headers, response.body, (response.finished_on-response.started_on)
			if ('set-cookie' in step.resp_headers.keys()):
				http.save_cookie(runner.base_url, step.resp_headers['set-cookie'])
			for a in step.assertions:
				a.value = jinja2.Template(a.value).render(step.context_vars)
				if not assertions.run_assertion(a, step):
					step.passed = False
					success = False
				if a.save_global:
					runner.global_vars[a.save_global] = a.received
					step.context_vars[a.save_global] = a.received #so it can be use on the next assertion
				if a.save_var:
					testcase_vars[a.save_var] = a.received
					step.context_vars[a.save_var] = a.received #so it can be use on the next assertion
				if a.save_file:
					saved, log = save_file(a.save_file, a.received)
					print log
					if not saved: a.passed, step.passed = False, False # if I can't save content, assertion fails
			print 'OK' if step.passed else '*FAILED*'
			if step.desc: step.desc = jinja2.Template(step.desc).render(step.context_vars)
			if block.desc: block.desc = jinja2.Template(block.desc).render(step.context_vars)
#</Request>
		elif step.__class__.__name__ in ['Block', 'TestCase']:
			if not run_block(runner, step): success = False
	return success


# Factory for the Runner class
def instantiate_runner(config_file):
	cf = ConfigParser.RawConfigParser()
	try:
		#takes the first section as the default
		cf.read(config_file)
		base_url = 'http://localhost'
		if cf.has_option('DEFAULT', 'BASE-URL'):
			base_url = cf.get('DEFAULT', 'BASE-URL')
		if base_url[-1] == '/': base_url = base_url[0:-1]
		proxy = None
		if cf.has_option('DEFAULT', 'PROXY'):
			proxy = cf.get('DEFAULT', 'PROXY')
			if len(proxy) and str(proxy).lower() not in ['no', 'none', 'false']:
				proxy = proxy.replace('http://', '')
			else:
				proxy = None
		report_formats = cf.get('DEFAULT', 'REPORT_FORMATS')
		if report_formats: report_formats = report_formats.split(',')
		#additional config sections
		other_base_urls = {}
		if cf.has_section('ADDITIONAL-BASE-URLS'):
			for i in cf.items('ADDITIONAL-BASE-URLS'):
				other_base_urls[i[0].lower()] = i[1]
	except:
		return None
	return Runner(base_url, proxy, other_base_urls, report_formats)

def merge_dicts(dict1, dict2, dict3=None):
	new_dict = {}
	for d in [dict1, dict2, dict3]:
		if d:
			for k in d.keys():
				new_dict[k] = d[k]
	return new_dict

def save_file(filename, content):
	try:
		if not os.path.exists('resources/saved_files'): os.makedirs('resources/saved_files')
		f = open('resources/saved_files/%s' % filename, 'wb')
		f.write(content)
		f.close()
		return True, '(saved file resources/saved_files/%s)' % filename
	except:
		return False, '*Error* Could not save file to resources/saved_files/%s' % filename

def match_tags(tags, tc_tags):
	for t in tags:
		if len(t):
			if t[0] == '-':
				if t[1:] in tc_tags:
					return False
			else:
				if t not in tc_tags:
					return False
	return True

