from datetime import datetime
import html, xunit

def generate(runner, testset_file, filename=None):
	extensions = []
	if not filename: filename = 'reports/%s %s' % (str(datetime.now()).replace(':','-').split('.')[0],
										str(testset_file).replace('\\', '/').split('/')[-1].split('.')[0])
	for ext in runner.report_formats:
		if ext.lower() == 'html':
			with open('%s.html' % filename, 'wb') as f: f.write(html.report(runner))
			extensions.append('html')
		elif ext.lower() == 'xunit':
			with open('%s.xunit' % filename, 'wb') as f: f.write(xunit.report(runner))
			extensions.append('xunit')
		else:
			print 'Warning: unknown report format "%s"' % f
	if len(extensions):
		return '%s.%s' % (filename, ('{%s}' % ', '.join(extensions)) if len(extensions)>1 else extensions[0])
	return False
