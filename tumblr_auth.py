import cherrypy
import urllib
import json
import tumblpy


class OAuthApp:

    def read_config( self ):
        fh = open( "tumblr_config.json")
        tumblr_config = json.load( fh )
        fh.close()
        return tumblr_config

    @cherrypy.expose
    def index( self ):

        callback_url = cherrypy.url("oauth_callback")

        tumblr_config = self.read_config()

        t = tumblpy.Tumblpy( app_key = tumblr_config[ "consumer_key" ],
            app_secret = tumblr_config[ "consumer_secret" ],
            callback_url = callback_url )

        auth_props = t.get_authentication_tokens()
        auth_url = auth_props['auth_url']

        # get token for this session from auth_props
        oauth_token = auth_props['oauth_token']
        oauth_token_secret = auth_props['oauth_token_secret']
        
        # write token for this session to temp file
        fh = open( "tumblr_authsession_token", "w")
        out = "%s\n%s" % (oauth_token,oauth_token_secret)
        fh.write( out )
        fh.close()

        raise cherrypy.HTTPRedirect( auth_url ) 

    @cherrypy.expose
    def oauth_callback( self, oauth_token=None, oauth_verifier=None ):
        if oauth_verifier is not None:

            # read session token from temp file
            fh = open( "tumblr_authsession_token")
            token_lines = fh.readlines()
            # oauth_token = token_lines[0]
            oauth_token_secret = token_lines[1]
            fh.close()

            tumblr_config = self.read_config()

            t = tumblpy.Tumblpy( app_key = tumblr_config[ "consumer_key" ],
                app_secret = tumblr_config[ "consumer_secret" ],
                oauth_token=oauth_token,
                oauth_token_secret=oauth_token_secret )

            # get oauth token
            authorized_tokens = t.get_authorized_tokens(oauth_verifier)
            final_oauth_token = authorized_tokens['oauth_token']
            final_oauth_token_secret = authorized_tokens['oauth_token_secret']

            # read exisitng config json
            fh = open( "tumblr_config.json")
            tumblr_config = json.load( fh )
            fh.close()

            # add oauth token
            tumblr_config[ "oauth_token" ] = final_oauth_token
            tumblr_config[ "oauth_secret" ] = final_oauth_token_secret

            # write back out again
            fh = open( "tumblr_config.json", "w" )
            json.dump( tumblr_config, fh )
            fh.close()


        else:
            return "Auth callback didn't get a verifier :("



if __name__ == "__main__":
    cherrypy.config.update( {'server.socket_host':"0.0.0.0", 'server.socket_port':1413 } )
    cherrypy.quickstart( OAuthApp() )