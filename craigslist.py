import urllib2
from BeautifulSoup import BeautifulSoup
import re

def read_url(url):
    """Attempts to open a URL and return the contents as BeautifulSoup.

    If an error is encountered, this will print an error
    message, and return None instead
    """
    try:
	response = urllib2.urlopen(url)
	return BeautifulSoup(response.read())
    except urllib2.HTTPError, e:
	print "Error: The server couldn't fulfill the request"
	print 'Reason: ', e.reason
	return None
    except urllib2.URLError, e:
	print 'Error: Could not open URL ', url
	print 'Reason: ', e.reason
	return None

def scrape_index(soup):
    """Scrapes a craigslist index of listings
    
    Returns a list with tuples of the form (title, url)
    """

    listings = []

    for row in soup.findAll('p', { 'class' : 'row' }):
	link = row.find('a')
	url = link['href']
	title = link.contents[0]
	listings.append((title, url))

    return listings

class Listing:
    """Stores information from a craigslist listing"""

    def __init__(self, url='', title='', location=None, description='', price=None, image_urls=[]):
	self.url = url
	self.title = title
	self.location = location
	self.description = description
	self.price = price
	self.image_urls = image_urls

    def has_price(self):
	if self.price:
	    return True
	else:
	    return False
    
    def has_location(self):
	if self.location:
	    return True
	else:
	    return False

    def __str__(self):
	if self.has_price() and self.has_location():
	    return '{0}\n{1} - ${2} ({3})\n{4}\n{5}'.format(self.url, self.title, self.price, self.location, self.description, '\n'.join(self.image_urls))
	elif self.has_location():
	    return '{0}\n{1} ({2})\n{3}\n{4}'.format(self.url, self.title, self.location, self.description, '\n'.join(self.image_urls))
	elif self.has_price():
	    return '{0}\n{1} - ${2}\n{3}\n{4}'.format(self.url, self.title, self.price, self.description, '\n'.join(self.image_urls))
	else:
	    return '{0}\n{1}\n{2}\n{3}'.format(self.url, self.title, self.description, '\n'.join(self.image_urls))



def scrape_listing(url):
    """Scrapes a listing for data
    
    Takes a URL for the listing, and returns a listing object.
    Returns None if there is an error accessing or parsing the listing.
    """

    # Read the HTML, and return None if there's an error
    soup = read_url(url)
    if soup == None:
	return None

    #print soup.prettify()
    
    # Grab the heading. This contains the title, location, and possibly price
    heading = soup.find('h2').contents[0]

    # Try to match two different regular expressions, to see
    # if the description includes price or not
    heading_price_regex = re.compile('(.*) - \$([0-9.].) \((.*)\)')
    heading_no_price_regex = re.compile('(.*) \((.*)\)')
    heading_price_no_location_regex = re.compile('(.*) - \$([0-9.].)')
    heading_no_price_no_location_regex = re.compile('(.*)')

    price_match = heading_price_regex.match(heading)
    no_price_match = heading_no_price_regex.match(heading)
    price_no_location_match = heading_price_no_location_regex.match(heading)
    no_price_no_location_match = heading_no_price_no_location_regex.match(heading)

    # See which expression matches, and extract title and location,
    # and price if they are available. If no expressions match,
    # this is an error, so we return None
    if price_match:
	title, price, location = price_match.group(1, 2, 3)
    elif no_price_match:
	title, location = no_price_match.group(1, 2)
	price = None
    elif price_no_location_match:
	title, price = price_no_location_match.group(1, 2)
	location = None
    elif no_price_no_location_match:
	title = no_price_no_location_match.group(1)
	price = None
	location = None
    else:
	print 'Error: Could not parse heading: ', heading
	return None

    # Find the userbody section, which contains the description,
    # images, as well as some craigslist blurbs
    userbody = soup.find('div', { 'id' : 'userbody' })
    # Extract all the image urls
    image_tags = userbody.findAll('img')
    image_urls = []
    for image in image_tags:
	image_urls.append( image['src'] )

    # Go through the userbody and grab the description.
    # Need to remove newlines, convert <br /> to a newline,
    # and to stop reading once we hit the craigslist blurbs
    description = ''
    for element in userbody.contents:
	# Stop parsing once we hit the craigslist tags
	if element == ' START CLTAGS ':
	    break
	
	# Now map <br /> -> \n and \n -> nothing
	description += str(element).replace('\n', '').replace('<br />', '\n')

    # Create and return our listing
    return Listing(url=url, title=title, location=location, description=description, price=price, image_urls=image_urls)


# The URL of the craigslist page to scrape
craigslist_url = 'http://boston.craigslist.org/msg/'

# Try to open the url
html = read_url(craigslist_url)
# Quit if there was an error
if html == None:
    print 'Quitting...'
    quit()

# Scrape the page
listing_tuples = scrape_index(html)
listings = []
for listing_tuple in listing_tuples:
    listing = scrape_listing(listing_tuple[1])
    if listing:
	listings.append(listing)
    else:
	print 'Could not parse listing, {1} at {2}, skipping...'.format(listing_tuple[0], listing_tuple[1])

