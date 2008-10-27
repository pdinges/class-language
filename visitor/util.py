class Enum(object):
	"""
	An Enum assigns integer values to string keys.  The values are constant;
	their keys are attributes to the Enum object.  Enums are (namespaced)
	lists to represent constants in the code.
	"""
	def __init__(self, entries):
		val = 0
		try:
			for e in entries:
				if isinstance(e, (tuple, list)) and len(e) >= 2:
					key = str(e[0])
					val = int(e[1])
				else:
					key = str(e)
					val += 1
				
				if val in self.__dict__.itervalues():
					raise ValueError("Value '%i' for key '%s' is ambiguous." % (val, key))
				self.__dict__[key] = val
				
		except ValueError:
			raise TypeError("Expecting a string as key and an integer as value.")

	def __setattr__(self, key, val):
		raise AttributeError("Enums are constant.")
