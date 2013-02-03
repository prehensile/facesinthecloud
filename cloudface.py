import cv 
import sys
import random
import os
import urlparse
import urllib2
import subprocess
import BeautifulSoup as Soup
import logging
import flickrapi
import json
import datetime
import xml.etree.ElementTree as ElementTree
import re

class FlickrSource:

    def __init__( self, api ):
        self.photo = None
        self.api = api
        self.photo_id = None

    def get_image_url( self ):
        image_url = None
        logger.info( "Fetching from Flickr..." )
        photos = self.api.photos_search( license="1,2,4,5" )
        photos = photos.findall("photos/photo")
        photo = random.choice( photos )
        photo_id = photo.attrib['id']
        sizes = self.api.photos_getSizes( photo_id=photo_id ).findall("sizes/size")
        
        # step though photo sizes
        max_size_found = 0
        max_size_usable = 1024
        for size in sizes:
            w = int(size.attrib['width'])
            if w > max_size_found and w < max_size_usable:
                image_url = size.attrib['source']
                max_size_found = w

        self.photo_id = photo_id
        return image_url
    
    def get_credit( self ):
        credit = None
        photo_info = self.api.photos_getInfo( photo_id=self.photo_id )
        if photo_info is not None:
            author_name = photo_info.find( "photo/owner" ).attrib['username']
            author_link = "http://www.flickr.com/people/%s/" % photo_info.find( "photo/owner" ).attrib['nsid']
            item_link = photo_info.find( "photo/urls/url[@type='photopage']" ).text
            credit = """After an <a href="%s">original</a> by <a href="%s">%s</a>.""" % ( item_link, author_link, author_name )
        return credit


class ffffoundSource:

    def __init__( self ):
        self.item = None

    def get_image_url( self ):
        image_url = None
        logger.info( "Fetching from ffffound..." )
        h = urllib2.urlopen( "http://feeds.feedburner.com/ffffound/everyone" )
        soup = Soup.BeautifulStoneSoup( h.read(), selfClosingTags=['media:content'] )
        items = soup.findAll( "item" )
        item = random.choice( items )
        if item: 
            self.item = item
            media_entity = item.find( "media:content" )
            if media_entity:
                image_url = media_entity["url"]
            else:
                logger.info( "-> no media found in chosen entity" )
        else:
            logger.error( "-> no entries in feed, bailing..." )
        return image_url 
    
    def get_credit( self ):
        credit = None
        if self.item is not None:
            link = self.item.find("link").string
            author = self.item.find("author").string
            author_link = "http://ffffound.com/home/%s/found/" % author
            credit = """After a <a href="%s">ffffinding</a> by <a href="%s">%s</a>.""" % ( link, author_link, author )
        return credit

def dump_file( pth, contents ):
    fh = open( pth, 'w')
    fh.write( contents )
    fh.close()


class InstagramSource:

    def __init__( self ):
        self.item = None
        self.photopage_soup = None

    def get_description_soup( self ):
        if( self.item ):
            description = item.find("description")
            if self._description_soup is None:
                self._description_soup = Soup.BeautifulSoup( description.contents[1] )
            return self._description_soup

    def get_image_url( self ):
        image_url = None
        logger.info( "Fetching from Instagram..." )
        h = urllib2.urlopen( "http://widget.stagram.com/rss/popular/" )
        soup = Soup.BeautifulStoneSoup( h.read() )
        items = soup.findAll( "item" )
        item = random.choice( items )
        if item: 
            self.item = item
            link = item.find( "image" ).find("link").string
            photopage_soup = Soup.BeautifulSoup( urllib2.urlopen(link) )
            self.photopage_soup = photopage_soup
            image_urls = photopage_soup.findAll( "a", href=re.compile( "^http://distilleryimage" ), recursive=True )
            for this_image_url in image_urls:
                if this_image_url.string == "Large":
                    image_url = this_image_url['href']
                    break
        return image_url 
    
    def get_credit( self ):
        credit = None
        if self.item is not None:
            photo_link = self.photopage_soup.find( "a", href=re.compile( "^http://instagr.am" ), recursive=True )['href']
            author_name = self.photopage_soup.find( "div", "infolist" ).find( "a", recursive=True, href=re.compile( "^/n/" ) ).text
            author_link = "http://instagram.com/%s" % author_name
            credit = """After an <a href="%s">Instagram</a> by <a href="%s">%s</a> (via <a href="http://web.stagram.com/">Webstagram</a>).""" % ( photo_link, author_link, author_name )
        return credit

def dump_file( pth, contents ):
    fh = open( pth, 'w')
    fh.write( contents )
    fh.close()


###
# START THE FANS, PLEASE!
##

# setup some paths
home_dir = os.path.expanduser("~")
cloudface_dir = os.path.join( home_dir, ".cloudface" )
if not os.path.exists( cloudface_dir ):
    os.makedirs( cloudface_dir )
image_path = None
commandline_image = False
pth_offline_face = os.path.join( home_dir, "bin/offline_face" )
## temp dir
temp_dir = os.path.join( cloudface_dir, "temp" )
if not os.path.exists( temp_dir ):
    os.makedirs( temp_dir )

# set up logging
logger = logging.getLogger( 'cloudface' )
logger.setLevel( logging.DEBUG )
log_path = os.path.join( cloudface_dir, 'cloudface.log' )
fh = logging.FileHandler( log_path )
fh.setLevel( logging.DEBUG )
formatter = logging.Formatter('%(asctime)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# load flickr keys
fh = open( "flickr_config.json")
flickr_config = json.load( fh )
fh.close()
flickr = flickrapi.FlickrAPI( flickr_config[ "api_key" ], flickr_config[ "api_secret" ], token=flickr_config[ "token" ] )

# parse commandline arguments, if any
la = len(sys.argv) 
image_source = None
if la > 1:
    image_path = sys.argv[2]
    commandline_image = True
    if la > 2:
        pth_offline_face = sys.argv[3]
else:
    
    sources = [ FlickrSource(flickr), ffffoundSource(), InstagramSource() ]
    image_source = random.choice( sources )
    image_url = image_source.get_image_url()

    # exit if we haven't got an image url
    if image_url is None:
        logger.error( "No image url found in chosen source. Bailing..." )
        exit(1)

    logger.info( "Using image at %s" % image_url )

    # construct local path for downloaded file
    image_filename = os.path.basename( urlparse.urlsplit( image_url ).path )
    image_path = os.path.join( temp_dir, image_filename )

    # download image to a local file
    u = urllib2.urlopen( image_url )
    dump_file( image_path, u.read() )

if image_path is None:
    logger.error( "No image to work on, bailing..." )
    exit(1) 

# check image for an almost-face
hc = cv.Load("haarcascade_frontalface_default.xml")
img = cv.LoadImage( image_path, cv.CV_LOAD_IMAGE_GRAYSCALE)
faces = cv.HaarDetectObjects(img, hc, cv.CreateMemStorage(), 1.1, 1 )
if faces is None or len(faces) < 1:
    logger.error( "No matches found in image, bailing..." )
    exit(1)

NEIGHBOUR_UPPER_THRESHOLD = 18  # any matches with more neighbours than this are too good
NEIGHBOUR_LOWER_THRESHOLD = 3  # any matches with fewer neighbours than this are no good
highest_score = 0
for (x,y,w,h),n in faces:
    if n > highest_score:
        highest_score = n

logger.info( "Highest face score is %d" % highest_score )
if highest_score > NEIGHBOUR_UPPER_THRESHOLD:   
    logger.error( "Image appears to contain actual faces. Bailing..." )
    exit(1)
elif highest_score < NEIGHBOUR_LOWER_THRESHOLD:
    logger.error( "Only matches are too vague. Bailing.." )
    exit(1)

# pass image to offline_face for drawing
# TODO: pass region containing best match to offline_face
pth_offline_face_exe = os.path.join( pth_offline_face, "bin/offline_face" )
pth_tracker = os.path.join( pth_offline_face, "model/face2.tracker" )
pth_conn = os.path.join( pth_offline_face, "model/face.con" )
pth_tri = os.path.join( pth_offline_face, "model/face.tri" )
pth_outfile = os.path.join( temp_dir, "out.jpg" )

args = [ pth_offline_face_exe,
            "-m", pth_tracker,
            "-c", pth_conn,
            "-t", pth_tri,
            "-i", image_path,
            "-o", pth_outfile,
            "-b", "3" ]

retcode = subprocess.call( args )

# remove source image if we downloaded it
if commandline_image is False: 
    os.remove( image_path ) 

if retcode > 0:
    logger.error( "offline_face failed. Bailing..." )
    exit(1)

# upload to flickr
logger.info( "Uploading to Flickr..." )
machine_tag = "fitc:neighborcount=%d" % highest_score 
tags = [ "notaphoto", "facesinthecloud", machine_tag ]
title = datetime.datetime.now().strftime('%A, %d %B %Y at %H:%M:%S')
response = flickr.upload( filename=pth_outfile, title=title, description=image_source.get_credit(), tags=" ".join(tags) )

logger.info( "Upload complete, photoid is %s" % response.find("photoid").text )

os.remove( pth_outfile )
