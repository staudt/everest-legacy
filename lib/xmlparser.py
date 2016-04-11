import csv
import elements
import xml.etree.ElementTree as ET
from copy import deepcopy

ignored_elements = ['desc'] # ignored as elements but used as something else
allowed_elements = ['include', 'testcase', 'template', 'request', 'var', 'print', 'sleep', 'clearcookies', 'callfunction']

# main is the runner class
# parent is the class that holds the elements (either Runner or TestCase)
# element is the XML tag to be parsed

def get_tag_value(tag):
	if tag.attrib.get('null'):
		if tag.attrib['null'].lower() == 'true': return None
	return tag.text.strip() if tag.text else ''

already_imported = []
def element_include(main, parent, element):
	global already_imported
	if 'file' not in element.attrib.keys(): return False, 'Include tag missing attribute "file"'
	if ('repeat' not in element.attrib or str(element.attrib.get('repeat')).lower() != 'true')\
			and element.attrib['file'].lower() in already_imported:
		#print 'File "%s" already imported, ignoring' % element.attrib['file']
		return True, ''
	already_imported.append(element.attrib['file'].lower())
	if 'parent' in element.attrib.keys():   # the parent attribute in <include>
		parent_template = deepcopy(get_step(main, element.attrib['parent']))
		parent_template.id = 'parent'
		parent.steps.append(parent_template)
	return parse_file(main, parent, 'tests/%s' % element.attrib['file'])

def element_testcase(main, parent, element):
	def fill_testcase(id, element):
		testcase = elements.TestCase(id, parent=parent)
		if 'tags' in element.attrib.keys(): testcase.tags = element.attrib['tags'].split(' ')
		desc = get_first_child(element, 'desc')
		if desc is not None: testcase.desc = desc.text
		testcase.source_code = ET.tostring(element)
		return testcase
	if 'id' not in element.attrib.keys(): return False, 'TestCase tag missing attribute "id"'
	if 'csv' in element.attrib.keys():
		try:
			csv_reader = csv.reader(open('tests/%s' % element.attrib['csv'], 'rb'), escapechar='\\')
			loop_counter = 0
			var_name = []
			for line in csv_reader:
				if len(line)>0:
					if loop_counter == 0: #first line is for var names
						for i in range(len(line)):
							var_name.append(line[i])
					else: # values
						testcase = fill_testcase('%s (%s)' % (element.attrib['id'], loop_counter), element)
						for i in range(len(line)):
							if i<len(var_name):
								testcase.steps.insert(0, elements.Var(name=var_name[i], value=line[i]))
						parent.steps.append(testcase)
						success, reason = parse_children(main, testcase, element)
						if not success: return False, reason
					loop_counter += 1
			return True, ''
		except:
			return False, 'Unable to parse csv file "tests/%s"' % element.attrib['csv']
	else:
		testcase = fill_testcase(element.attrib['id'], element)
        parent.steps.append(testcase)
	return parse_children(main, testcase, element)

def element_var(main, parent, element):
	if 'name' not in element.attrib.keys(): return False, 'Var tag missing attribute "name"'
	parent.steps.append(elements.Var(element.attrib['name'], get_tag_value(element)))
	return True, ''

def element_print(main, parent, element):
	parent.steps.append(elements.Print(element.text))
	return True, ''

def element_clearcookies(main, parent, element):
	parent.steps.append(elements.ClearCookies())
	return True, ''

def element_sleep(main, parent, element):
	if not element.text: return False, 'Sleep tag has no value'
	parent.steps.append(elements.Sleep(element.text))
	return True, ''

def element_callfunction(main, parent, element):
	if 'name' not in element.attrib.keys(): return False, 'CallFunction tag missing attribute "name"'
	if 'file' not in element.attrib.keys(): return False, 'CallFunction tag missing attribute "file"'
	filename = 'tests/%s' % element.attrib['file']
	try:
	   with open(filename): pass
	except IOError:
	   return False, 'File "%s" for CallFunction name "%s" not found' % (filename, element.attrib['name'])
	params = {}
	for child in element.getchildren():
		if child.tag.lower() in ['param', 'parameter']:
			if 'name' not in child.attrib.keys(): return False, 'Param tag within CallFunction missing attribute "name"'
			params[child.attrib['name']] = child.text
		else:
			return 'Unreconized tag "%s" within CallFunction' % (child.tag)
	callfunction = elements.CallFunction(filename=filename, name=element.attrib['name'], params=params)
	if 'save_var' in element.attrib.keys(): return False, 'Deprecated attribute "save_var", replace with "save-var"'
	if 'save_global' in element.attrib.keys(): return False, 'Deprecated attribute "save_global", replace with "save-global"'
	if 'save_file' in element.attrib.keys(): return False, 'Deprecated attribute "save_file", replace with "save-file"'
	if 'save-var' in element.attrib.keys(): callfunction.save_var = element.attrib['save-var']
	if 'save-global' in element.attrib.keys(): callfunction.save_global = element.attrib['save-global']
	if 'save-file' in element.attrib.keys(): callfunction.save_file = element.attrib['save-file']
	if not is_child_of_testcase(parent):
		testcase = elements.TestCase(callfunction.name, parent=parent)
		testcase.steps.append(callfunction)
		if 'tags' in element.attrib.keys(): testcase.tags = element.attrib['tags'].split(' ')
		parent.steps.append(testcase)
	else:
		parent.steps.append(callfunction)
	return True, ''

def _parse_step(main, parent, element, is_template=True):
	if 'id' not in element.attrib.keys(): return False, '%s tag missing attribute "id"' % ('Template' if is_template else 'Request')
	step = elements.Template(element.attrib['id']) if is_template else elements.Request(element.attrib['id'])
	if 'extends' in element.attrib.keys():
		extended = get_step(main, element.attrib['extends'])
		if not extended: return False, 'Template or Request named "%s" to extend "%s" not found' % (element.attrib['extends'], element.attrib['id'])
		for v in vars(extended).keys():
			if v != 'id':
				step.__dict__[v] = deepcopy(extended.__dict__[v])
	for e in element.getchildren():
		tag = e.tag.lower()
		if tag == 'desc':
			step.desc = get_tag_value(e)
		elif tag == 'method':
			step.method = get_tag_value(e)
		elif tag == 'body':
			if 'enctype' in e.attrib.keys():
				if e.attrib['enctype'].lower() in ['application/x-www-form-urlencoded', 'urlencoded']:
					step.headers['content-type'] = 'application/x-www-form-urlencoded'
				elif e.attrib['enctype'].lower() in ['multipart/form-data', 'form-data', 'multipart']:
					step.headers['content-type'] =  'multipart/form-data'
				elif e.attrib['enctype'].lower() in ['text/plain', 'text', 'plain']:
					step.headers['content-type'] = 'text/plain'
				else:
					step.headers['content-type'] = 'none'
			step.body = get_tag_value(e)
			for child_e in e.getchildren():
				if child_e.tag.lower() == 'file':
					if 'name' not in child_e.attrib.keys(): return False, 'Missing attribute "name" in tag File'
					if 'source' in child_e.attrib.keys(): return False, 'Attribute "source" in tag File has been deprecated'
					step.body_files[child_e.attrib['name']] = get_tag_value(child_e)
					if not step.body_files[child_e.attrib['name']]: return False, 'Missing value in tag File (value indicates the filename)'
					step.body_file_headers[child_e.attrib['name']] = {}
					for file_header_e in child_e.getchildren():
						if 'name' not in file_header_e.attrib.keys(): return False, 'Missing attribute "name" in tag Header within File'
						step.body_file_headers[child_e.attrib['name']][file_header_e.attrib['name']] = get_tag_value(file_header_e)
				elif child_e.tag.lower() == 'field':
					if 'name' not in child_e.attrib.keys(): return False, 'Missing attribute "name" in tag Field'
					step.body_fields[child_e.attrib['name']] = get_tag_value(child_e)
				elif child_e.tag.lower() == 'clearfiles':
					step.body_files, step.body_file_headers = {}, {}
				elif child_e.tag.lower() in ['clearfilenames', 'clearfilename']:
					for name in get_tag_value(child_e).split("|"):
						if name in step.body_files.keys(): step.body_files.pop(name)
						if name in step.body_file_headers.keys(): step.body_file_headers.pop(name)
				elif child_e.tag.lower() == 'clearfields':
					step.body_fields = {}
				elif child_e.tag.lower() in ['clearfieldnames', 'clearfieldname']:
					for name in get_tag_value(child_e).split("|"):
						if name in step.body_fields.keys(): step.body_fields.pop(name)
				else:
					return False, 'Unrecognized tag "%s" within body of step "%s"' % (child_e.tag, element.attrib['id'])
		elif tag == 'path':
			step.path = get_tag_value(e)
			for child_e in e.getchildren():
				if child_e.tag.lower() == 'field':
					if 'name' not in child_e.attrib.keys(): return False, 'Missing attribute "name" in tag Field'
					step.path_fields[child_e.attrib['name']] = get_tag_value(child_e)
				else:
					return False, 'Unrecognized tag "%s" within path of step "%s"' % (child_e.tag, element.attrib['id'])
			step.base_url = e.attrib.get('base-url')
			if step.base_url:
				step.base_url = str(step.base_url).lower()
				if step.base_url not in main.other_base_urls.keys():
					return False, 'base-url "%s" not found in configuration' % step.base_url
			if e.attrib.get('full'): step.path_full = True if e.attrib['full'].lower() == 'true' else False
			else: path_full = False
			if e.attrib.get('no-proxy'): step.force_no_proxy = True if e.attrib['no-proxy'].lower() == 'true' else False
		elif tag == 'var':
			if 'name' not in e.attrib.keys(): return False, 'Var missing attribute "name" in request %s' % step.id
			step.vars[e.attrib['name']] = get_tag_value(e)
			if step.vars[e.attrib['name']] == None: del step.vars[e.attrib['name']]
		elif tag == 'header':
			if 'name' not in e.attrib.keys(): return False, 'Header missing attribute "name" in request %s' % step.id
			step.headers[e.attrib['name']] = get_tag_value(e)
			if step.headers[e.attrib['name']] == None: del step.headers[e.attrib['name']]
		elif tag == 'clearheaders':
			step.headers.clear()
		elif tag in ['assertion', 'assert', 'a']:
			if 'type' not in e.attrib.keys(): return False, 'Assertion missing attribute "type" in request %s' % step.id
			assertion = elements.Assertion(e.attrib['type'], value=e.text, params=e.attrib)
			if 'save_var' in element.attrib.keys(): return False, 'Deprecated attribute "save_var", replace with "save-var"'
			if 'save_global' in element.attrib.keys(): return False, 'Deprecated attribute "save_global", replace with "save-global"'
			if 'save_file' in element.attrib.keys(): return False, 'Deprecated attribute "save_file", replace with "save-file"'
			if 'save-var' in e.attrib.keys(): assertion.save_var = e.attrib['save-var']
			if 'save-global' in e.attrib.keys(): assertion.save_global = e.attrib['save-global']
			if 'save-file' in e.attrib.keys(): assertion.save_file = e.attrib['save-file']
			step.assertions.append(assertion)
		elif tag == 'clearassertions':
			step.assertions = []
		elif tag in ['clearassertiontype', 'clearassertiontypes']:
			types = e.text.lower().split('|')
			for a in step.assertions:
				if a.type.lower() in types:
					step.assertions.remove(a)
			step.raw_desc, step.raw_path, step.raw_method, step.raw_body = step.desc, step.path, step.method, step.body
			step.raw_headers, step.raw_vars = step.headers, step.vars
		else:
			return False, 'Unrecognized tag "%s" within step "%s"' % (e.tag, element.attrib['id'])
	step.source_code = '%s\n%s' % (step.source_code, ET.tostring(element))
	if not is_template and not is_child_of_testcase(parent):
		testcase = elements.TestCase(step.id, parent=parent, desc=step.desc)
		testcase.steps.append(step)
		if 'tags' in element.attrib.keys(): testcase.tags = element.attrib['tags'].split(' ')
		parent.steps.append(testcase)
	else:
		parent.steps.append(step)
		if parent.desc is None: parent.desc = step.desc
	return True, ''

def element_template(main, parent, element):
	return _parse_step(main, parent, element, is_template=True)

def element_request(main, parent, element):
	return _parse_step(main, parent, element, is_template=False)


def parse_children(main, parent, root): # parent has to have parent.steps to fill
	for element in root:
		if element.tag.strip().lower() not in ignored_elements:
			if element.tag.strip().lower() in allowed_elements:
				success, reason = globals()['element_%s' % element.tag.strip().lower()](main, parent, element)
				if not success: return False, reason
			else:
				return False, 'Unexpected tag "%s" in "%s"' % (element.tag, parent.id)
	return True, ''

def parse_file(main, parent, file):
	try:
		root = ET.parse(file).getroot()
	except Exception, e:
		return False, 'Can\'t parse file %s: %s' % (file, str(e.args))
	element_desc = get_first_child(root, 'desc')
	block = elements.Block(file, parent=parent, desc=(element_desc.text if element_desc is not None else None))
	parent.steps.append(block)
	return parse_children(main, block, root)


### Helper Functions ###

def get_step(main, id):
	found = None
	for s in main.steps:
		if s.__class__.__name__ in ['Block', 'TestCase']:
			result = get_step(s, id)
			if result:
				found = result
		elif s.__class__.__name__ in ['Request', 'Template']:
			if id.lower() == s.id.lower():
				found = s
	return found

def get_first_child(root, tag):
	for element in root:
		if element.tag.strip().lower() == tag.lower(): return element
		else: return None

def is_child_of_testcase(parent):
	p = parent
	while True:
		if p.__class__.__name__ == 'TestCase':
			return True
		if p.parent.__class__.__name__ in ['TestCase', 'Block']:
			p = p.parent
		else:
			return False

########################
