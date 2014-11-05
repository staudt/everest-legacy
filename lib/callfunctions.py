import sys

def run(runner, callfunction):
	path_dir = '/'.join(callfunction.file.split('/')[:-1])
	sys.path.append(path_dir)
	importable = callfunction.file.split('/')[-1]
	callfunction.params['_base_url_'] = runner.base_url
	callfunction.params['_other_base_url_'] = runner.other_base_urls
	callfunction.params['_proxy_'] = runner.proxy
	if '.py' in importable.lower()[-3:]: importable = importable[:-3]
	try:
		lib = __import__(importable)
	except:
		return False, 'Could not import script "%s" from path "%s"' % (importable, path_dir)
	try:
		return getattr(lib, callfunction.name)(callfunction.params)
	except:
		return False, 'Could not run function "%s" from path "%s"' % (importable, path_dir)