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
		assert self.token != (None or "")
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
				return "Error: Timeout trying to access menus on page %s. Please try again later."%(self.current)
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
		except KeyError:
			return None
		print "Dishes for menu id # %s accessed successfully."%(id), 
		print "Your token %s has %s requests left for the day."%(self.token,r.headers["x-ratelimit-remaining"])
		return dishes

			