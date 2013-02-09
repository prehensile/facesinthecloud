import cherrypy
import urllib
import hashlib
import json

def sig_for_params( params, api_secret ):
    concat = api_secret
    keys = sorted( params.keys() )
    for key in keys:
        val = params[ key ]
        concat += "%s%s" % (key, val)
    return hashlib.md5( concat ).hexdigest()

def sign_params( params, api_secret ):
    sig = sig_for_params( params, api_secret )
    params[ "api_sig" ] = sig
    return( params )


class FlickrAuthApp:

    def read_config( self ):
        fh = open( "flickr_config.json")
        tumblr_config = json.load( fh )
        fh.close()
        return tumblr_config

    @cherrypy.expose
    def index( self ):

        config = self.read_config()
        params = { "api_key" : config["api_key"],
                    "perms" : "write" }
        params = sign_params( params )
        auth_url = "http://flickr.com/services/auth/?%s" % urllib.urlencode( params )
        raise cherrypy.HTTPRedirect( auth_url ) 

    @cherrypy.expose
    def recieve_frob( self, frob ):
        if frob is not None:

            config = self.read_config()

            resp = u"<html><body>"
            resp += "Recieved frob: %s<br/>" % frob

            params = { "method" : "flickr.auth.getToken",
                        "api_key" : config["api_key"],
                        "format" : "json",
                        "frob" : frob }
            params = sign_params( params, config["api_secret"] )
            auth_url = "http://api.flickr.com/services/rest/"
            h = urllib.urlopen( auth_url, urllib.urlencode( params ) )
            payload = h.read()
            
            resp += auth_url
            resp += payload

            config["token"] = payload["auth"]["token"]["_content"]
            fh = open( "flickr_config.json", "w" )
            json.dump( config, fh )
            fh.close()

            resp += "</body></html>"

            return resp

if __name__ == "__main__":
    cherrypy.config.update( {'server.socket_host':"0.0.0.0", 'server.socket_port':1413 } )
    cherrypy.quickstart( FlickrAuthApp() )