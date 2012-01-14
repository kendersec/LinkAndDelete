import os
import sys
import imghdr
import xerox

from config import *
from dropbox import client, session

PUBLIC_DIR = '/Public/'
PICS_DIR = PUBLIC_DIR + 'Pics/'

class LinkAndDelete():
    def __init__(self, app_key, app_secret):
        self.sess = StoredSession(app_key, app_secret, access_type=ACCESS_TYPE)
        self.api_client = client.DropboxClient(self.sess)
        self.sess.load_creds()

    def getUID(self):
        return self.api_client.account_info()['uid']

    def upload(self, file):
        dir = PUBLIC_DIR
        f = open(file)
        if(imghdr.what(file)):
            dir = PICS_DIR
        response = self.api_client.put_file(dir + os.path.basename(file), f)
        return response['path']


class StoredSession(session.DropboxSession):
    """a wrapper around DropboxSession that stores a token to a file on disk"""
    TOKEN_FILE = os.environ['HOME'] + "/.getLinkAndDelete.tokens"

    def load_creds(self):
        try:
            stored_creds = open(self.TOKEN_FILE).read()
            self.set_token(*stored_creds.split('|'))
            print "[loaded access token]"
        except IOError:
            self.link()

    def write_creds(self, token):
        f = open(self.TOKEN_FILE, 'w')
        f.write("|".join([token.key, token.secret]))
        f.close()

    def delete_creds(self):
        os.unlink(self.TOKEN_FILE)

    def link(self):
        request_token = self.obtain_request_token()
        url = self.build_authorize_url(request_token)
        print "url:", url
        print "Please authorize in the browser. After you're done, press enter."
        raw_input()

        self.obtain_access_token(request_token)
        self.write_creds(self.token)

    def unlink(self):
        self.delete_creds()
        session.DropboxSession.unlink(self)

class Notifier():
    @staticmethod  
    def notify(title=None, message=None, app_name='python shell'):
        "Provide the user with a notification or fail silently."
        try:
            Notifier._use_pynotify(title=title, message=message, app_name=app_name)
            return
        except ImportError:
            pass

        try:
            Notifier._use_growl(title=title, message=message, app_name=app_name)
        except ImportError:
            pass

    @staticmethod
    def _use_pynotify(app_name=None, title=None, message=None):
        import pynotify
        pynotify.init(app_name)
        n = pynotify.Notification(title, message, "dialog-info")
        n.set_urgency(pynotify.URGENCY_NORMAL)
        n.set_timeout(pynotify.EXPIRES_DEFAULT)
        n.show()
        return

    @staticmethod
    def _use_growl(app_name=None, title=None, message=None):
        import gntp.notifier
        n = gntp.notifier.GrowlNotifier(applicationName=app_name, notifications=['info'])
        n.register()
        n.notify('info', title, message)
        return

def main():
    if (len(sys.argv) != 2):
        exit("Which file?")
    if APP_KEY == '' or APP_SECRET == '':
        exit("You need to set your APP_KEY and APP_SECRET!")
    lnd = LinkAndDelete(APP_KEY, APP_SECRET)
    path = lnd.upload(sys.argv[1])
    if (path):
        path = path.replace(PUBLIC_DIR,"/")
        url = "http://dl.dropbox.com/u/" + repr(lnd.getUID()) + path
        Notifier.notify("LinkAndDelete","Loaded successfuly\n" + url,"GetLinkAndDelete")
        xerox.copy(url)
        os.remove(sys.argv[1])

if __name__ == '__main__':
    main()
