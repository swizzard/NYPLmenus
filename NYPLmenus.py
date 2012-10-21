def html_pprint(req,decode_unicode=True,pprint=True):
	"""Retrieve & optionally pretty-print html content of requests response
	:param req: response returned by requests.get
	:type req: response <response> object
	:param decode_unicode: whether unicode in the content should be decoded (passed to response
	object's decode_unicode parameter)
	:type decode_unicode: bool
	"""
	lines = req.iter_lines(decode_unicode)
	content = []
	while True:
		try:
			content.append(lines.next())
		except StopIteration:
			break
	if pprint == True:
		for x in content:
			print x
	else:
		return content
class NYPLmenus:
	import requests
	import re
	def __init__(self,token=None):
		"""Initialize the class.
		:param token: Your personal access token.
		:type token: str
		You need a token to access the API. Please see http://nypl.github.com/menus-api/
		for more information."""
		self.token = token or ""	##Add your own token here, then you won't need to put
									##in every time.
		try:
			assert self.token
		except AssertionError:
			print "You forgot your token!"
		self.root = "http://api.menus.nypl.org/"
		
	def get_menus(self,dishes=True,max_pages=None,id=None,menu_timeouts=50,dishes_timeouts=20,*parameters):
		"""Access NYPL's Menus API & retrieves menus & dishes
		menus saved to self.menu, a dictionary whose keys are either location+date (if
		location is available) or menu id #
		:param dishes: if True, information for the menu's dishes will be accessed via get_dishes
		NOTE: get_dishes accesses the API for each menu on the page; each call counts against your daily ratelimit.
		:type dishes: bool
		:param max_pages: maximum number of pages to be accessed. Each page contains 50 menus;
		if max_pages is set to None, get_menus will keep accessing menus until the final page is reached
		or your token's daily ratelimit is reached.* NB: If id is given, only that menu
		:type max_pages: int
		:param id: id of a specific menu
		:type id: int*
		:param menu_timeouts: number of times to try to retrieve menus before giving up
		:type menu_timeouts: int
		:param dishes_timeouts: number of times to try to retrieve a menu's dishes before
		giving up
		type dishes_timeouts: int
		:param parameters: optional query parameters
		:type parameters: str*
		*see http://nypl.github.com/menus-api/ for more information"""
		##individual menus keyed by location+date (if location is given) or
		##id
		self.menus = {}	
		if parameters:
			joiner = "&?"
		else:
			joiner = ""
		if id:
			id_str = "menus/%d/?token="%(id)
		else:
			id_str = "menus?token="
		params = "&?".join([p for p in parameters])
		request = self.root+id_str+self.token+"&?sort_by=date"+joiner+params
		r = self.requests.get(request)
		next_p = self.re.compile(r'<(http://menus.nypl.org/api/menus\?.*?&page=(\d*))>; rel=\"next\"')
		end_p = self.re.compile(r'<(http://menus.nypl.org/api/menus\?.*?&page=(\d*))>; rel=\"last\"')
		if max_pages:
			self.end = max_pages
		else:
			self.end = self.re.match(end_p,r.headers["link"]).group(2)
		self.current = self.re.match(next_p,r.headers["link"]).group(2)
		self.next = r
		while int(self.current) <= int(self.end):
			#if int(self.current) != int(self.re.match(next_p,self.next.headers["link"]).group(2)):
			menus_json = None
			i = 0
			while menus_json == None and i <= menu_timeouts:
				try:
					menus_json = r.json["menus"]
				except:
					menus_json = None
					i += 1
					print "Trying...%d"%(i)
			if menus_json == None:
				return """Error: Timeout trying to access menus on page %s. Please try again later. %d menus retrieved."""%(self.current,len(self.menus))
			else:
				remaining_requests = r.headers["x-ratelimit-remaining"]
				print "Menus on page %s accessed successfully. Your token %s has %s requests left for the day"\
				%(self.current,self.token,remaining_requests)
			for menu in menus_json:
				try:
					md_date = "%02d%02d%02d"%(menu["month"],menu["day"],menu["year"])
				except TypeError:
					md_date = "None"
				if menu["location"] == "[Restaurant And/Or Location Not Given.]":
					md_location = menu["id"]
				else:
					md_location = menu["location"]		
				md_name = "%s_%s"%(md_location,md_date)
				if md_name not in self.menus.keys():
					md = {}
					md["location"] = md_location
					md["date"] = md_date
					md["currency"] = menu["currency"] or "$"
					for link in menu["links"]:
						if link["rel"] == "dishes":
							md["dishes_link"] = link["href"]
					md["event"] = menu["event"] or "None"

					md["id"] = menu["id"]
					md["lang"] = menu["language"] or "None"
					md["place"] = menu["place"] or "None"
					md["dishes"] = None
					if dishes:
						i = 0
						while md["dishes"] == None and i < dishes_timeouts:
							md["dishes"] = self.get_dishes(id=md["id"])
							i += 1
						if md["dishes"] == None:
							print "Error accessing dishes for menu id %s"%(md["id"])
					self.menus[md_name] = md
			if not id:	
				self.next = self.requests.get(self.re.match(next_p, r.headers["link"]).group(1))
				r = self.next
				try:
					self.current = self.re.match(next_p,r.headers["link"]).group(2)
				except TypeError:
					continue
		print "%d menus retrieved." %(len(self.menus))
		self.restaurants = self.menus.keys()
		self.dishes = []
		for x in xrange(len(self.restaurants)):
			dishes = self.restaurants[x].keys()
			for y in xrange(len(dishes)):
				self.dishes.append(dishes[y])
	def tryer(self,source,goal):
		try:
			return source[goal]
		except KeyError:
			return None
		
	def get_dishes(self,id=None):
		"""Access NYPL's Menus API to retrieve the dishes from a given menu
		:param id: id # of the menu to be accessed
		:type id: int
		"""
		r = self.requests.get(self.root+"menus/"+str(id)+"/dishes?token="+self.token)
		try:
			dishes_json = r.json
		except:
			return None
		dishes = {}
		try:
			for dish in dishes_json["dishes"]:
				d = {}
				d["high"] = self.tryer(dish,"high_price")
				d["low"] = self.tryer(dish,"low_price")
				d["price"] = self.tryer(dish,"price")
				d["latest"] = self.tryer(dish,"updated_at")
				dishes[dish["name"]] = d
		except:
			return None
		print "Dishes for menu id # %s accessed successfully."%(id), 
		print "Your token %s has %s requests left for the day."%(self.token,r.headers["x-ratelimit-remaining"])
		return dishes

	def get_dishesDict(self):
		self.dishesDict = {}
		for x in xrange(len(self.menus.items())):
			for y in xrange(len(self.menus.items()[x][1]["dishes"].items())):
				dishName = self.menus.items()[x][1]["dishes"].items()[y][0]
				dishList = self.menus.items()[x][1]["dishes"].items()[y][0].split()
				self.dishesDict[dishName] = dishList

class Wikirecipes:
	import requests
	import re
	def __init__(self):
		self.page_pat = "http://en.wikibooks.org/w/index.php?title=Category:Recipes&pagefrom="
		self.reci_p = self.re.compile(r'title=\"Cookbook:(.*?)\">')
		self.recipes = set()
	def get_recipes(self):
		letters = ["0","A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P",
		"Q","R","S","T","U","V","W","X","Y","Z"]
		for x in xrange(len(letters)):
			print "Retrieving Wikibooks recipes starting with %s..."%(letters[x]),
			url = "%s%s"%(self.page_pat,letters[x])
			while True:
				r = self.requests.get(url)
				if self.re.search(self.reci_p,r.content):
					recs = self.re.finditer(self.reci_p,r.content)
					break
				else:
					continue
			while True:
				try:
					self.recipes.add(recs.next().group(1))
				except StopIteration:
					break
			print "Done"
class Allrecipes:
	"""A class to retrieve recipes from Allrecipes.com."""
	import requests
	import re
	import htmlentitydefs
	def __init__(self):
		self.root="http://allrecipes.com"
		self.courses_pat = self.re.compile(r'<li>COURSES</li>(?P<courses>.*?)<li>INGREDIENTS AND METHODS</li>',self.re.S)
		self.course_pat = self.re.compile(r'title=\"(?P<title>.*?)\" href=\"(?P<link>.*?)main\.aspx\"')
		self.title_pat=self.re.compile(r'</style>\s+<title>\s+(?P<title>.*?) Recipes - Allrecipes\.com \(Pg\. (?P<pageno>\d+)\)')
		self.rec_pat=self.re.compile(r"""href=\"http://allrecipes\.com/recipe/.*?
									/detail\.aspx\">(?P<name>.*?)</a>\s+</h3> #group "name": name as it appears in plaintext
									""",self.re.X)
									#not clear yet whether linkname or name will be
									#more helpful/easier to deal with
		self.cont_pat=self.re.compile(r'<a href=\"http://allrecipes\.com/recipes/.*?/ViewAll\.aspx\?Page=\d+">NEXT',self.re.U)
	def main(self,**kwargs):
		self.get_courses()
		self.recipes=self.to_dict([self.get_recipes(course,**kwargs) for course in self.courses])
	def get_courses(self,*courses):
		"""Retrieve list of courses from Allrecipes.com
		:param *courses: variable parameter of courses to include. get_courses will retrieve
		all available courses, but if you know the names of the specific courses you'd like
		to deal with, you can specify them.
		:type *courses: str(s)
		"""
		url = "%s/%s"%(self.root,"recipes/main.aspx")
		while True:
			self.main = self.requests.get(url)
			if "200" in repr(self.main):
				break
		self.m = self.re.search(self.courses_pat,self.main.content)
		if self.m:
			courses_generator = self.re.finditer(self.course_pat,self.m.group())
		else:
			raise Exception("Can't find courses in content of %s"%(url)) 
		self.courses = []
		while True:
			try:
				course = courses_generator.next()
				print "Found course %s" %(course.group("title"))
				self.courses.append((course.group("title"),course.group("link")))
			except StopIteration:
				break
		if courses:
			for course in self.courses:
				if course[0] not in courses:
					self.courses.remove(course)	
	def get_recipes(self,course,maxpage=None,verbose=True,escape=True):
		"""Retrieves recipes from a supplied course category from Allrecipes.com.
		:param course: course category (usu. supplied from get_courses)
		:type course: tuple (fmt: (coursename,courselink)
		:param maxpage: maximum page to retrieve. Allrecipes has A LOT of recipes, so it
		might be worth only retrieving some of it.
		:type maxpage: int or None
		:param verbose: run get_recipes as verbose, printing out the category name and
		page number of every page of recipes retrieved by the function.
		:type verbose: bool
		:param escape: if True, escape HTML entities (&#34;,etc.) as text/unicode
		:type escape: bool
		"""
		while True:
			r = self.requests.get("%s/%s/ViewAll.aspx"%(self.root,course[1]))
			if "200" in repr(r):
				break
			else:
				continue
		title = course[0]
		recs_iter = self.re.finditer(self.rec_pat,r.content)
		recs = []
		while True:
			try:
				next = recs_iter.next()
				recs.append(self.unescape(next.group("name")))
			except StopIteration:
				break
		print "Retrieved recipes for category %s on page 1"%(course[0])
		i = 2
		while True:
			while True:
				url = "%s/%s/ViewAll.aspx?Page=%d"%(self.root,course[1],i)
				new_r = self.requests.get(url)
				if "200" in repr(new_r):
					break
				else:
					continue
			m = self.re.search(self.title_pat,new_r.content)
			if m:
				pageno = self.re.search(self.title_pat,new_r.content).group("pageno")
			else:
				self.current=new_r
				print "Stopping...current page saved as .current"
				raise Exception("pattern %s failed on page %s"%(self.title_pat.pattern,url))
			recs_iter = self.re.finditer(self.rec_pat,r.content)
			while True:
				try:
					next = recs_iter.next()
					if escape == True:
						recs.append(self.unescape(next.group("name")))
					else:
						recs.append(next.group("name"))
				except StopIteration:
					break
			print "Retrieved recipes for category %s on page %d"%(course[0],i)
			if maxpage == 1:
				break
			i += 1
			if maxpage:
				if i > maxpage or not self.re.search(self.cont_pat,new_r.content):
					break
				else:
					continue
			elif not self.re.search(self.cont_pat,new_r.content):
				break
			else:
				continue
		return title,recs
	def to_dict(self,funcs):
		"""Takes functions that return (str,list) and translates them into a dictionary
		whose keys are the returned str(s) and whose values are the returned list(s)
		:param *funcs: variable parameter of the functions to translate.
		:type *funcs: iterable of functions
		"""
		d = {}
		for func in funcs:
			returned = func
			d[returned[0]] = returned[1]
		return d
		
	def unescape(self,text):
	##Adapted from original written by Fredrik Lundh. Taken from http://effbot.org/zone/re-sub.htm#unescape-html
	##via http://stackoverflow.com/questions/57708/convert-xml-html-entities-into-unicode-string-in-python
	# Removes HTML or XML character references and entities from a text string.
	#
	# @param text The HTML (or XML) source text.
	# @return The plain text, as a Unicode string, if necessary.	
		def fixup(m):
			text = m.group(0)
			if text[:2] == "&#":
				# character reference
				try:
					if text[:3] == "&#x":
						return unichr(int(text[3:-1], 16))
					else:
						return unichr(int(text[2:-1]))
				except ValueError:
					pass
			else:
				# named entity
				try:
					text = unichr(self.htmlentitydefs.name2codepoint[text[1:-1]])
				except KeyError:
					pass
			return text # leave as is
		return self.re.sub("&#?\w+;", fixup, text)