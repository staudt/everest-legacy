
class Assertion:
	def __init__(self, type, value=None, params=None):
		self.type, self.raw_value, self.value, self.params = type, value, value, params
		self.expected, self.received, self.passed = None, None, False
		self.save_var, self.save_global, self.save_file = None, None, None


class Block:
	def __init__(self, id, parent, desc=None):
		self.id, self.parent, self.desc = id, parent, desc
		self.steps = []

class TestCase(Block):
	def __init__(self, id, parent, desc=None):
		Block.__init__(self, id, parent, desc)
		self.tags = []
		self.executed = False

class Command:
	def __init__(self, value):
		self.raw_value, self.value = value, value

class Sleep(Command): pass

class Print(Command): pass

class ClearCookies: pass

class Var(Command):
	def __init__(self, name, value):
		Command.__init__(self, value)
		self.name = name


class CallFunction:
	def __init__(self, filename, name, params={}):
		self.file, self.name, self.params = filename, name, params
		self.raw_param = params
		self.save_var, self.save_global, self.save_file = None, None, None
		self.passed, self.return_value = True, None

class Template:
	def __init__(self, id):
		self.id = id
		self.desc, self.path, self.method, self.body = None, '', 'GET', None
		self.force_no_proxy = False
		self.path_fields = {}
		self.enctype = None
		self.body_files, self.body_file_headers, self.body_fields = {}, {}, {}
		self.path_full, self.base_url = False, None
		self.headers, self.vars, self.context_vars, self.assertions = {}, {}, {}, []
		self.source_code = ''

class Request(Template):
	def __init__(self, id):
		Template.__init__(self, id)
		self.resp_status, self.resp_headers, self.resp_body, self.resp_time = None, {}, None, None
		self.raw_desc, self.raw_path, self.raw_method, self.raw_body = None, None, None, None
		self.raw_headers, self.raw_vars = {}, {}
		self.passed = True
