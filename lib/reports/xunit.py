import datetime

def get_block_result(block):
	for step in block.steps:
		if step.__class__.__name__ == 'Request':
			if step.passed is not True: return False
		elif step.__class__.__name__ == 'CallFunction':
			if step.passed is not True: return False
		elif step.__class__.__name__ in ['Block', 'TestCase']:
			if get_block_result(step) is not True: return False
	return True

def read_block(block):
	output, tests, failures, skips = '', 0, 0, 0
	for step in block.steps:
		if step.__class__.__name__ == 'Block':
			r_output, r_tests, r_failures, r_skips = read_block(step)
			output += r_output
			tests += r_tests
			failures += r_failures
			skips += r_skips
		elif step.__class__.__name__ == 'TestCase':
			tests += 1
			passed, failure_output, perf = True, '', datetime.timedelta(0)
			if not step.executed:
				skipped +=1
			else:
				for req in step.steps:
					if req.__class__.__name__ in ['Request', 'CallFunction']:
						if req.__class__.__name__ == 'Request': perf += req.resp_time
						if not req.passed:
							passed = False
							details = ''    # explains what failed
							if req.__class__.__name__ == 'Request':
								name = 'Request %s' % req.id
								details = '<![CDATA[\n'
								for a in req.assertions:
									if not a.passed:
										details += 'Assertion "%s" failed\n\tExpected: "%s"\n\tReceived: "%s"\n\n' % (a.type, a.expected, a.received)
								details += ']]>'
							else:
								name = 'CallFunction %s' % req.name
								details = 'CallFunction %s execution returned Failure' % req.name
							failure_output += '\n<failure type="AssertionFailure" message="%s Failed">%s</failure>\n' % (name, details)
				if not passed: failures += 1
				output += '''\n<testcase classname="%(id)s" name="%(id)s" time="%(perf)s">%(fail)s</testcase>\n''' % {'id' : step.id, 'perf' : perf, 'fail' : failure_output}
	return output, tests, failures, skips


def report(runner):
	block = runner.steps[0]
	output, tests, failures, skips = read_block(block)
	return '''<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="%(name)s" tests="%(tests)s" errors="0" failures="%(failures)s" skip="%(skip)s">
%(output)s
</testsuite>''' % {'name':block.id, 'tests':tests, 'failures':failures, 'skip':skips, 'output':output}