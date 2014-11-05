import uuid
from xml.dom import minidom

def get_block_result(block):
	for step in block.steps:
		if step.__class__.__name__ == 'Request':
			if step.passed is not True: return False
		elif step.__class__.__name__ == 'CallFunction':
			if step.passed is not True: return False
		elif step.__class__.__name__ in ['Block', 'TestCase']:
			if get_block_result(step) is not True: return False
	return True

def request_to_html(step):
	step_details = '''<table><tr><th class="%s">Request</th><td><b>%s</b> (%s)</td><td>%s</td></tr>''' %\
		('th_passed' if step.passed else 'th_failed', step.id, 'Passed' if step.passed else '<font color="#ff0000">FAILED</font>', step.desc)
	req_uuid = uuid.uuid4()
	body_extras = ''
	if len(step.body_files.keys()):
		body_extras += '<tr><th>Body Files</th><td>'+dict_to_html(step.body_files) +'</td></tr>'
	if len(step.body_fields.keys()):
		body_extras += '<tr><th>Body Fields</th><td>'+dict_to_html(step.body_fields) +'</td></tr>'
	step_details += '''<tr><th>Request</th><td colspan="2">
		<table>
			<th>Path</th><td>%s</td></tr>
			<tr><th>Method</th><td>%s</td></tr>
			<tr><th>Headers</th><td><pre>%s</pre></td></tr>
			<tr><th>Body</th><td><pre>%s</pre></td></tr>%s
			<tr><th>Variables</th><td><a href="javascript:toggle('v%s');" style="color: #666666;">show/hide</a><div id="v%s" style="display: none"><pre>%s</pre></div></td></tr>
			<tr><th>Source Code</th><td><a href="javascript:toggle('s%s');" style="color: #666666;">show/hide</a><div id="s%s" style="display: none"><pre>%s</pre></div></td></tr>
		</table> </td></tr>''' % (step.path, step.method, escape(dict_to_html(step.headers, line_break='\n')), escape(step.body), body_extras, req_uuid, req_uuid, escape(dict_to_html( step.context_vars, ' =', line_break='\n')), req_uuid, req_uuid, escape(get_source(step)))
	step_details += '''<tr><th>Response</th><td colspan="2">
		<table>
			<tr><th>Status</th><td>%s</td></tr>
			<tr><th>Headers</th><td><pre>%s</pre></td></tr>
			<tr><th>Performance</th><td>%s</td></tr>
			<tr><th>Body</th><td><pre>%s</pre></td></tr>
		</table> </td></tr>''' % (step.resp_status, escape(str_decode(dict_to_html(step.resp_headers, line_break='\n'))), step.resp_time, escape(to_pretty_xml(str_decode(step.resp_body))))
	step_assertions = ''
	if len(step.assertions)==0:
		step_assertions = '<tr><td colspan="4">No Assertions</td></tr>'
	else:
		for a in step.assertions:
			save_text = ''
			if a.save_global: save_text += '(saved as global <b>%s</b>)' % a.save_global
			if a.save_var: save_text += '(saved as variable <b>%s</b>)' % a.save_var
			if a.save_file: save_text += '(saved as file <b>%s</b>)' % a.save_file
			step_assertions = '%s%s' % (step_assertions, '<tr><td>%s</td><td>%s %s</td><td><pre style="width: 240px">%s</pre></td><td><pre style="width: 240px">%s</pre> <font style="color: #666666">%s</font></td></tr>' %\
				('OK' if a.passed else '<font color="#ff0000">FAILED</font>', a.type, '<b>(Inverse)</b>' if a.params.get('inverse')=='true' else '', escape(a.expected), escape(a.received), save_text))
	step_details += '''<tr><th>Assertions</th><td colspan="2"><table>
			<tr><th>Status</th><th>Type</th><th>Expected</th><th>Received</th></tr> %s </table>
		</td></tr>''' % (str_decode(step_assertions))
	step_details += '''</table>'''
	return step_details

def testcases_read_block(block):
	testcases = ''
	for step in block.steps:
		step_summary = ''
		if step.__class__.__name__ == 'Block':
			step_summary = testcases_read_block(step)
		elif step.__class__.__name__ == 'TestCase':
			if step.executed:   # testcase was executed (tags matched)
				passed = get_block_result(step)
				step_summary = '<tr><td><a href="#t%s">%s</a></td><td>%s</td><td>%s</td></tr>' %\
					(unique_id(step), step.id, 'Passed' if passed else '<font color="#ff0000">FAILED</font>', '' if step.desc is None else escape(step.desc))
			else:
				step_summary = ''
		testcases = '%s\n%s' % (testcases, step_summary)
	return testcases

def details_read_block(block):
	passed = get_block_result(block)
	if block.__class__.__name__ == 'Block':
		details = '<table class="table_block"><tr><th class="%s">Block</th><td><b>%s</b></td><td>%s</td></tr><tr><td colspan="3">' % \
			('th_passed' if passed else 'th_failed', block.id, escape(block.desc))
	else:
		if not block.executed:
			return ''   # test case wasn't executed, tags didn't match
		details = '<table class="table_block"><tr><th class="%s"><a name="t%s">Test&nbsp;Case</th><td><b>%s</b> (%s)</td><td>%s %s</td></tr><tr><td colspan="3">' % \
			('th_passed' if passed else 'th_failed', unique_id(block), block.id, 'Passed' if passed else '<font color="#ff0000">FAILED</font>', escape(block.desc), '(Tags: %s)' % ' '.join(block.tags) if block.tags else '')
	for step in block.steps:
		step_details = ''
		if step.__class__.__name__ == 'Block':
			step_details = details_read_block(step)
		elif step.__class__.__name__ == 'TestCase':
			step_details = details_read_block(step)
		elif step.__class__.__name__ == 'Request':
			step_details = request_to_html(step)
		elif step.__class__.__name__ == 'Sleep':
			step_details = '<table><tr><th width="1">Sleep</th><td>%s seconds</td></tr></table>' % step.value
		elif step.__class__.__name__ == 'Print':
			step_details = '<table><tr><th width="1">Print</th><td class="td_print"><b>%s</b></td></tr></table>' % escape(step.value)
		elif step.__class__.__name__ == 'Var':
			step_details = '<table><tr><th width="1">Var</th><td><pre>%s = %s</pre></td></tr></table>' % (step.name, escape(step.value))
		elif step.__class__.__name__ == 'CallFunction':
			save_text = ''
			if step.save_global: save_text += '(saved as global <b>%s</b>)' % step.save_global
			if step.save_var: save_text += '(saved as variable <b>%s</b>)' % step.save_var
			if step.save_file: save_text += '(saved as file <b>%s</b>)' % step.save_file
			step_details = '<table><tr><th class="%s" width="1">CallFunction</th><td><b>%s</b> from file %s</td></tr><tr><th>Parameters</th><td><pre>%s</pre></td></tr><tr><th>Returned</th><td><pre>%s <font style="color: #666666">%s</font></pre></td></tr></table>' \
					% ('th_passed' if step.passed else 'th_failed', step.name, step.file, escape(dict_to_html(step.params, line_break='\n')), escape(step.return_value), save_text)
		details = '%s\n%s' % (details, step_details)
	return '%s</td></tr></table>' % (details)

def report(runner):
	summary = ''
	testcases = testcases_read_block(runner.steps[0])
	details = details_read_block(runner.steps[0])

	return str_decode('''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
	<html xmlns="http://www.w3.org/1999/xhtml" dir="ltr" lang="en">
	<head>
		<title>Test Report</title>
		<style>
			body { font-family: arial, sans-serif; font-size: 12px; }
			table { border-collapse: collapse; margin-bottom: 8px; margin-left: 4px; width: 100%% }
			.table_block { width: 680px; }
			td { padding: 5px; vertical-align: top; }
			th { padding: 5px; vertical-align: top; background-color: #666666; color: #ffffff; font-weight: normal; text-align:left; }
			.th_passed { background-color: #00aa00; width: 1px; font-weight: bold; }
			.th_failed { background-color: #aa0000; width: 1px; font-weight: bold; }
			.td_print { background-color: #ffffcc; }
			table,th, td { border: 1px solid #000000; }
			div { padding: 0px; spacing: 0px; }
			pre { margin:0px; padding: 0px; overflow-y:auto;overflow-x:auto;width:420px;max-height:200px; }
		</style>
		<script>
			function toggle(element) {
                if (document.getElementById(element).style.display != 'block') {
					document.getElementById(element).style.display='block';
				} else {
					document.getElementById(element).style.display='none';
				}
			}
		</script>
	</head>
	<body>
		<h1>Test Report</h1>%s<br>
		<h2>Test Cases</h2>
			<table class="table_block">
				<tr><th>Test Case</th><th>Result</th><th>Description</th></tr>
				%s
			</table>
		<br><hr>
		<h2>Details</h2> %s
	</body>
	</html>''' % (summary, testcases, details))


#Helpers
def dict_to_html(dic, operator=':', line_break='<br>'):
	html = ''
	for k in dic.keys(): html += '%s%s %s%s' % (k, operator, dic[k], line_break)
	return html

def get_source(step):
	source = step.source_code
	for k in step.context_vars.keys():
		source = '<var name="%s">%s</var>\n%s' % (k, step.context_vars[k], source)
	return source

def str_decode(val):
	if isinstance(val, basestring):
		if isinstance(val, unicode):
			return val.encode('iso-8859-1', 'replace')
		else:
			return val.decode('iso-8859-1', 'replace').encode('ascii', 'replace')
	else:
		return val

def escape(html):
	if html is None: return ''
	text = str_decode(html)
	return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

def to_pretty_xml(body):
	minidom.Element.writexml = helper_writexml
	try:
		xml = minidom.parseString(body)
		return xml.toprettyxml()
	except:	pass
	return body

def unique_id(c):
	return str(c).split(' ')[-1][:-1]


# This is to adjust the xml prettyfy output
def helper_writexml(self, writer, indent="", addindent="", newl=""):
	writer.write(indent+"<" + self.tagName)
	attrs = self._get_attributes()
	a_names = attrs.keys()
	a_names.sort()
	for a_name in a_names:
		writer.write(" %s=\"" % a_name)
		minidom._write_data(writer, attrs[a_name].value)
		writer.write("\"")
	if self.childNodes:
		if len(self.childNodes) == 1 and self.childNodes[0].nodeType == minidom.Node.TEXT_NODE:
			writer.write(">")
			self.childNodes[0].writexml(writer, "", "", "")
			writer.write("</%s>%s" % (self.tagName, newl))
			return
		writer.write(">%s"%(newl))
		for node in self.childNodes:
			node.writexml(writer,indent+addindent,addindent,newl)
		writer.write("%s</%s>%s" % (indent,self.tagName,newl))
	else:
		writer.write("/>%s"%(newl))
