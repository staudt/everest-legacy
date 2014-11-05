#!/usr/bin/env python
import sys
from lib import test_runner, reports

def main(testset_file, params):
	config_file = 'default.cfg'
	if 'config' in params.keys(): config_file = params['config']
	runner = test_runner.instantiate_runner(config_file)
	if 'base_url' in params.keys(): runner.base_url = params['base_url']
	if 'proxy' in params.keys(): runner.proxy = params['proxy'].replace('http://', '')
	if not runner: return False, 'Couldn\'t load configuration file'
	worked, reason = runner.parse_testset(testset_file)
	if not worked: return False, 'Failed parsing XML: %s' % reason

	print 'Running Testset "%s"' % testset_file
	passed = runner.run_tests(params['tags'])

	report_name = None if 'output' not in params else params['output']
	filenames = reports.generate(runner, testset_file, report_name)
	if filenames:
		print 'Test Report available at "%s"\n' % filenames
	return True if passed else False, '' if passed else 'One or more testcases failed'


if __name__ == '__main__':
	testset_file, params  = None, {'tags' : []}
	flags = { '-c' : 'config', '-o' : 'output', '-t' : 'tags',
				'-base-url' : 'base_url', '-proxy' : 'proxy' }
	flag = None
	for a in sys.argv[1:]:
		if flag:
			if flag == '-t': params['tags'].append(a) #tags are more complicated
			else: params[flags[flag]] = a
			flag = None
		else:
			if a.lower() in flags.keys():
				flag = a.lower()
			else:
				testset_file = a
	if not testset_file:
		print '''Welcome to EVEREST 2.0 Test Tool
ERROR: You need to inform the Testset XML file.

 Usage Syntax:
	python everest.py [optional parameters] <testset_file>

 Optional parameters:
	-c <config_file>    Sets the config file to be used
	-t [-]<TAG>     	Adds or remove a tag
	-o <report_file>    Sets the output report filename (no extension)
	-base-url <URL>     Overwrites the BASE-URL from the configuration file
	-proxy <PROXY:PORT> Overwrites the PROXY from the configuration file

 Examples:
   python everest.py tests/test.xml  (uses default config and template)
   python everest.py -c default.cfg -o reports/my_report tests/test.xml
   python everest.py -t smoke tests/test.xml (run tests tagged as "smoke")'''
		sys.exit(-1)
	else:
		passed, reason = main(testset_file, params)
		if not passed:
			print 'Exiting with Error: %s' % reason
			sys.exit(-1)
