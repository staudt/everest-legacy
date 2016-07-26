# -*- coding: iso-8859-15 -*-
import re, xpath, os, os.path, jsonpath, json
from xml.dom import minidom

# IMPORTANT: Functions for assertions *MUST* be lower case

# Status
def status(assertion, request):
	assertion.expected, assertion.received = str(assertion.value).split('|'), str(request.resp_status)
	assertion.passed = True if assertion.received in assertion.expected else False

def statusnot(assertion, request):
	assertion.expected, assertion.received = str(assertion.value).split('|'), str(request.resp_status)
	assertion.passed = True if assertion.received not in assertion.expected else False


# Headers
def headerexists(assertion, request):
	assertion.expected, assertion.received = assertion.value, 'Not Found'
	assertion.passed = False
	for k in request.resp_headers.keys():
		if k.lower() == assertion.expected.lower():
			assertion.received = k
			assertion.passed = True

def headervalueequals(assertion, request):
	if 'header' not in assertion.params.keys():
		assertion.expected, assertion.received = '-- Missing assertion attribute "header" --', '-- unable to query --'
		assertion.passed = False
		return
	header = assertion.params['header']
	assertion.expected, assertion.received = assertion.value, 'Not Found'
	assertion.passed = False
	for k in request.resp_headers.keys():
	    if k.lower() == header.lower():
			if request.resp_headers[k].lower() == assertion.expected.lower():
				assertion.passed = True
    			assertion.received = request.resp_headers[k]
	assertion.expected = 'Header "%s" with value "%s"' % (header, assertion.expected)

def headervaluecontains(assertion, request):
	if 'header' not in assertion.params.keys():
		assertion.expected, assertion.received = '-- Missing assertion attribute "header" --', '-- unable to query --'
		assertion.passed = False
		return
	header = assertion.params['header']
	assertion.expected, assertion.received = assertion.value, 'Not Found'
	assertion.passed = False
	for k in request.resp_headers.keys():
	    if k.lower() == header.lower():
			if assertion.expected.lower() in request.resp_headers[k].lower():
				assertion.passed = True
    			assertion.received = request.resp_headers[k]
	assertion.expected = 'Header "%s" with value "%s"' % (header, assertion.expected)

def headerkeyvalueequals(assertion, request):
	assertion.expected, assertion.received = assertion.value, 'Not Found'
	assertion.passed = False
	try:
	   assertion.received = request.resp_headers.get(assertion.params['name'])
	   if assertion.received == assertion.expected:
	       assertion.passed = True
	except:
	   assertion.received, assertion.passed = 'Error parsing response', False

def headerkeyvaluecsontains(assertion, request):
	assertion.expected, assertion.received = assertion.value, 'Not Found'
	assertion.passed = False
	try:
	   assertion.received = request.resp_headers[assertion.params['name']]
	   if assertion.expected in assertion.received:
	       assertion.passed = True
	except:
	   assertion.received, assertion.passed = 'Error parsing response', False

def headerkeyexists(assertion, request):
	assertion.expected, assertion.received = assertion.value, 'Not Found'
	assertion.passed = False
	try:
	   assertion.received = request.resp_headers[assertion.expected]
	   assertion.passed = True
	except:
	   assertion.received, assertion.passed = 'Error parsing response', False

# Body
def bodyany(assertion, request):
	assertion.expected, assertion.received = assertion.value, request.resp_body.strip()[:80]
	assertion.passed = True

def bodyequals(assertion, request):
	assertion.expected, assertion.received = assertion.value, request.resp_body.strip()
	assertion.passed = True if assertion.expected.lower() == assertion.received.decode(encoding='ascii', errors='replace').lower() else False

def bodycontains(assertion, request):
	assertion.expected, assertion.received = assertion.value, request.resp_body.strip()
	assertion.passed = True if assertion.expected.lower() in assertion.received.decode(encoding='ascii', errors='replace').lower() else False

def bodycontainsoneof(assertion, request):
	assertion.expected, assertion.received = assertion.value, request.resp_body.strip()
	found = False
	for expect in assertion.expected.split("|"):
		if expect.lower() in assertion.received.decode(encoding='ascii', errors='replace').lower():
			assertion.passed = True
			return
	assertion.passed = False

def bodylengthequals(assertion, request):
	assertion.expected, assertion.received = assertion.value, request.resp_body.strip()
	assertion.passed = True if len(assertion.received)==int(assertion.expected) else False

def bodylengthlessthan(assertion, request):
	assertion.expected, assertion.received = assertion.value, request.resp_body.strip()
	assertion.passed = True if len(assertion.received)<int(assertion.expected) else False

def bodylengthmorethan(assertion, request):
	assertion.expected, assertion.received = assertion.value, request.resp_body.strip()
	assertion.passed = True if len(assertion.received)>int(assertion.expected) else False

# Body XPath
def bodyxpathany(assertion, request):
	assertion.expected = 'Any value for query "%s"' % assertion.value
	try:
		assertion.received = xpath.findvalue(assertion.value, minidom.parseString(request.resp_body))
		assertion.passed = True if assertion.received else False
	except:
		assertion.received, assertion.passed = 'Error parsing response XML', False

def bodyxpathequals(assertion, request):
	if 'query' not in assertion.params.keys():
		assertion.expected, assertion.received = '-- Missing assertion attribute "query" --', '-- unable to query --'
		assertion.passed = False
		return
	assertion.expected = 'Query "%s" equals "%s"' % (assertion.params['query'], assertion.value)
	try:
		assertion.received = xpath.findvalues(assertion.params['query'], minidom.parseString(request.resp_body))
		for expected in assertion.value.split('|'):
			if expected in assertion.received:
				assertion.passed = True
				return
		assertion.passed = False
	except:
		assertion.received, assertion.passed = 'Error parsing response XML', False

def bodyxpathcountequals(assertion, request):
	if 'query' not in assertion.params.keys():
		assertion.expected, assertion.received = '-- Missing assertion attribute "query" --', '-- unable to query --'
		assertion.passed = False
		return
	assertion.expected = 'Query "%s" has %s occurrences' % (assertion.params['query'], assertion.value)
	try:
		assertion.received = len(xpath.findvalues(assertion.params['query'], minidom.parseString(request.resp_body)))
		if str(assertion.received) in str(assertion.value).split('|'):
			assertion.passed = True
			return
		assertion.passed = False
	except:
		assertion.received, assertion.passed = 'Error parsing response XML', False

def bodyxpathcountmorethan(assertion, request, operation=">"):
	if 'query' not in assertion.params.keys():
		assertion.expected, assertion.received = '-- Missing assertion attribute "query" --', '-- unable to query --'
		assertion.passed = False
		return
	assertion.expected = 'Query "%s" has %s%s occurrences' % (assertion.params['query'], operation, assertion.value)
	try:
		assertion.received = len(xpath.findvalues(assertion.params['query'], minidom.parseString(request.resp_body)))
		if operation==">":
			assertion.passed = True if assertion.received>int(assertion.value) else False
		else:
			assertion.passed = True if assertion.received<int(assertion.value) else False
	except:
		assertion.received, assertion.passed = 'Error parsing response XML', False

def bodyxpathcountlessthan(assertion, request):
	return bodyxpathcountmorethan(assertion, request, operation="<")

def bodyxpathordered(assertion, request):
	assertion.expected, assertion.received, assertion.passed = '', '', False
	pass

def bodyxpathallcontainsoneof(assertion, request):
	if 'query' not in assertion.params.keys():
		assertion.expected, assertion.received = '-- Missing assertion attribute "query" --', '-- unable to query --'
		assertion.passed = False
		return
	assertion.expected = 'Query "%s" contains "%s"' % (assertion.params['query'], assertion.value)
	try:
		assertion.received = xpath.findvalues(arg, minidom.parseString(request.response.body))
		expectedList = assertion.value.split('|')
		passed = True
		if (len(assertion.received) > 0):
			for r in assertion.received:
				found = False
				for e in expectedList:
					if (e in r):
						found = True
				if (not found):
					passed = False
	except:
		received, passed = 'error parsing response xml', False

def bodyxpathequalscount(assertion, request):
	valuesFound = None
	if 'query' not in assertion.params.keys():
		assertion.expected, assertion.received = '-- Missing assertion attribute "query" --', '-- unable to query --'
		assertion.passed = False
		return
	if 'value' not in assertion.params.keys():
		assertion.expected, assertion.received = '-- Missing assertion attribute "query" --', '-- unable to query --'
		assertion.passed = False
		return
	assertion.expected = 'Query "%s" with Value "%s" has %s occurrences' % (assertion.params['query'], assertion.params['value'], assertion.value)
	try:
		valuesFound = xpath.findvalues(assertion.params['query'], minidom.parseString(request.resp_body))
		assertion.received = valuesFound.count(assertion.params['value'])
		if str(assertion.received) in str(assertion.value).split('|'):
			assertion.passed = True
			return
		assertion.passed = False
	except:
		assertion.received, assertion.passed = 'Error parsing response XML', False

def filesizeeequals(assertion, request, operator='='):
	assertion.expected, assertion.received = assertion.value, '?'
	try:
		assertion.received = int(os.path.getsize('resources/%s' % arg))
		passed = False
		if operator=='=':
			passed = True if int(assertion.expected) == int(assertion.received) else False
		elif operator=='>':
			passed = True if int(assertion.received) > int(assertion.expected) else False
		elif operator=='<':
			passed = True if int(assertion.received) < int(assertion.expected) else False
	except:
		received, passed = 'error accessing file', False

def filesizeemorethan(assertion, request):
	return filesizeeequals(assertion, request, operator='>')

def filesizeelessthan(assertion, request):
	return filesizeeequals(assertion, request, operator='<')

# bodyxpathcontains, bodyxpathallcontains, bodyxpathallequalsoneof, bodyxpathallvaluesordered, bodyxpathallvaluesmorethan
# bodyxpathallvalueslessthan, bodyxpathallvaluesmoreorequalsthan, bodyxpathallvalueslessorequalsthan, bodyxpathallvaluesequalsthan
# bodyxpathvaluemorethan bodyxpathvaluemoreorequalsthan bodyxpathvaluelessthan

# bodyregexequals bodyregexany bodyregexcountequals bodyregexcountlessthan bodyregexcountmorethan

# timelessthan timemorethan bodymatchesschema

# Body JsonPath
def bodyjsonxpathbiggestany(assertion, request): return bodyjsonpathbiggestany(assertion, request)
def bodyjsonpathbiggestany(assertion, request):
	assertion.expected = 'Any value for biggest value in query "%s"' % assertion.value
	try:
		biggest = 0
		for val in jsonpath.jsonpath(json.loads(request.resp_body), assertion.value):
			if val > biggest: biggest = val
		assertion.received = biggest
		assertion.passed = True if assertion.received else False
	except:
		assertion.received, assertion.passed = 'Error parsing response Json', False

def bodyjsonxpathany(assertion, request): return bodyjsonpathany(assertion, request)
def bodyjsonpathany(assertion, request):
	assertion.expected = 'Any value for query "%s"' % assertion.value
	try:
		assertion.received = jsonpath.jsonpath(json.loads(request.resp_body), assertion.value)[0]
		assertion.passed = True if assertion.received else False
	except:
		assertion.received, assertion.passed = 'Error parsing response Json', False

def bodyjsonxpathequals(assertion, request): return bodyjsonpathequals(assertion, request)
def bodyjsonpathequals(assertion, request):
	if 'query' not in assertion.params.keys():
		assertion.expected, assertion.received = '-- Missing assertion attribute "query" --', '-- unable to query --'
		assertion.passed = False
		return
	assertion.expected = 'Query "%s" equals "%s"' % (assertion.params['query'], assertion.value)
	try:
		assertion.received = str(jsonpath.jsonpath(json.loads(request.resp_body), assertion.params['query'])[0])
		for assertion.value in assertion.value.split('|'):
			if assertion.value == assertion.received:
				assertion.passed = True
				return
		assertion.passed = False
	except:
		assertion.received, assertion.passed = 'Error parsing response Json', False

def bodyjsonxpathecontains(assertion, request): return bodyjsonpathcontains(assertion, request)
def bodyjsonxpathcontains(assertion, request): return bodyjsonpathcontains(assertion, request)
def bodyjsonpathcontains(assertion, request):
	if 'query' not in assertion.params.keys():
		assertion.expected, assertion.received = '-- Missing assertion attribute "query" --', '-- unable to query --'
		assertion.passed = False
		return
	assertion.expected = 'Query "%s" contains "%s"' % (assertion.params['query'], assertion.value)
	try:
		assertion.received = jsonpath.jsonpath(json.loads(request.resp_body), assertion.params['query'])
		for assertion.value in assertion.value.split('|'):
			if assertion.value in assertion.received:
				assertion.passed = True
				return
		assertion.passed = False
	except:
		assertion.received, assertion.passed = 'Error parsing response Json', False

def bodyjsonxpathcountequals(assertion, request, operation='='): return bodyjsonpathcountequals(assertion, request, operation)
def bodyjsonpathcountequals(assertion, request, operation='='):
	if 'query' not in assertion.params.keys():
		assertion.expected, assertion.received = '-- Missing assertion attribute "query" --', '-- unable to query --'
		assertion.passed = False
		return
	assertion.expected = 'Query "%s" is %s %s occurrences' % (assertion.params['query'], operation, assertion.value)
	try:
		query = jsonpath.jsonpath(json.loads(unicode(request.resp_body)), assertion.params['query'])
		if not query: assertion.received = 0
		else: assertion.received = len(query)
		if operation == '<': assertion.passed = True if assertion.received < int(assertion.value) else False
		elif operation == '>': assertion.passed = True if assertion.received > int(assertion.value) else False
		else: assertion.passed = True if assertion.received == int(assertion.value) else False
	except:
		assertion.received, assertion.passed = 'Error parsing response Json', False

def bodyjsonxpathcountmorethan(assertion, request): return bodyjsonpathcountmorethan(assertion, request)
def bodyjsonpathcountmorethan(assertion, request):
    bodyjsonxpathcountequals(assertion, request, operation='>')

def bodyjsonxpathcountlessthan(assertion, request): return bodyjsonpathcountlessthan(assertion, request)
def bodyjsonpathcountlessthan(assertion, request):
    bodyjsonxpathcountequals(assertion, request, operation='<')


# Factory for assertions
def run_assertion(assertion, request):
	assertion_type = assertion.type.strip().lower()
	if assertion_type in globals().keys():
		globals()[assertion.type.strip().lower()](assertion, request)
		if assertion.params.get('inverse') == 'true': assertion.passed = not assertion.passed
		if len(str(assertion.received))>200: assertion.received = '%s[...]' % assertion.received[:200]
		return assertion.passed
	else:
		assertion.expected, assertion.received = str(assertion.value), '--Unkown Assertion Type--'
		assertion.passed = False
		return False
