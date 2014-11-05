
# The CallFunction is a simple python function that
# receives a param dictionary and return two values:
# A boolean (for success) and return value (that can be used in the test)

# The CallFunction below can be called using the following code:
# <CallFunction name="callfunction_name" file="sample_callfunctions.py">
#	<param name="my_param">this is a param I'm passing to my CallFunction</param>
# </CallFunction>
def callfunction_name(params={}):
	#code goes here
	passed = True
	return_value = 'Hello test, this is my return value for you'
	return passed, return_value		# this is what the function return to your test
	
# You can have as many CallFunctions as you want, just add more functions here
