import uuid
from xml.dom import minidom
from junit_xml import (TestCase, TestSuite)

def get_block_result(block):
	for step in block.steps:
		if step.__class__.__name__ == 'Request':
			if step.passed is not True: return False
		elif step.__class__.__name__ == 'CallFunction':
			if step.passed is not True: return False
		elif step.__class__.__name__ in ['Block', 'TestCase']:
			if get_block_result(step) is not True: return False
	return True

def stripStr(str):
    strStripped = str.replace('tests\\','')
    strStripped = strStripped.replace('tests/','')
    strStripped = strStripped.replace('.xml','.')
    return strStripped

def testcases_read_block(block, tcs = [], step_summary = '', testcases = ''):
	tcs = []
	for step in block.steps:
		if step.__class__.__name__ == 'TestCase':
			passed = get_block_result(step)
			classTc = stripStr(step_summary+step.id)
			myTC = TestCase(step.desc, classTc, 0.00);
			if (not passed) :
			 myTC.add_failure_info("Message", "Output");
			tcs.append(myTC)
	return tcs


def report(runner):
	testcases = ''
	failedTCs = 0
	totalTCs = 0
	tl = []
	mainClass = runner.steps[0].id
	for block in runner.steps[0].steps:
		if block.__class__.__name__ in ['Block', 'TestCase']:
	   		tcs = testcases_read_block(block, step_summary = mainClass+block.id)
	   		tsName = stripStr(block.id)
	   		ts = TestSuite(tsName, tcs)
	   		tl.append(ts)
	return TestSuite.to_xml_string(tl)