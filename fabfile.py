import sys, os
from fabric.api import env, run, put, open_shell, local

# step 1: git clone git@github.com:iandennismiller/droptato.git ./somewhere

# step 2: edit these SSH values

env.user = ''
env.key_filename = ['']
env.hosts = ['']

# step 3: cd somewhere; fab shell; fab init

def help():
    "print usage information"

    print """
Clone a copy of the droptato instance:
    git clone %s@%s:~/droptato.git

Test locally:
    fab build serve

Publish changes to the live site:
    git commit -am "change message"; git push
""" % (env.user, env.hosts[0])

def virtualenv_init():
    "set up virtualenvwrapper"

    cmd = """
cd ~; wget --no-clobber https://raw.github.com/pypa/virtualenv/master/virtualenv.py;
python ./virtualenv.py --distribute --no-site-packages ~/.virtualenv;
rm virtualenv.py* distribute*
. ~/.virtualenv/bin/activate;
pip install virtualenvwrapper;
export WORKON_HOME=~/Envs; mkdir -p $WORKON_HOME;
source `which virtualenvwrapper.sh`;
"""
    run(cmd)    

def init():
    "set up blogofile on remote host"

    virtualenv_init()
    put("remote/.bashrc", "/home/private", mode=0744)
    put("remote/.bash_profile", "/home/private", mode=0744)
    put("remote/requirements.txt", "/home/private", mode=0644)
    run("mkvirtualenv blogofile; pip install -r /home/private/requirements.txt")
    run("rm /home/private/requirements.txt")

def hook_install():
    "update git post-install hooks on remote master repository"

    put("remote/post-receive", "/home/private/droptato.git/hooks", mode=0744)

def git_put():
    "create new master repository based on this one"
    
    local("git clone --bare . /tmp/droptato.git")
    put("/tmp/droptato.git","/home/private")
    os.system("rm -rf /tmp/droptato.git")
    local("git remote rm origin; git remote add origin %s@%s:/home/private/droptato.git" % (env.user, env.hosts[0]))
    local("git push -u origin master")
    help()

def git_init():
    "initialize an empty remote master repository: droptato.git"

    cmd = """
mkdir /home/private/droptato.git; cd /home/private/droptato.git; git init --bare;
mkdir /home/tmp/blog; cd /home/tmp/blog; git init;
git remote add origin /home/private/droptato.git;
git config branch.master.remote origin; git config branch.master.merge refs/heads/master;
touch notes.md; git add notes.md; git commit -m 'initial import'; git push origin master
"""
    run(cmd)
    hook_install()
    help()

def shell():
    "open a shell on the remote host"

    os.system("ssh %s@%s" % (env.user, env.hosts[0]))

def serve():
    "run a web server in the local blogofile/_site directory"

    import SimpleHTTPServer
    import SocketServer
    os.chdir("blogofile/_site")
    PORT = 8000
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("", PORT), Handler)
    print "serving at port", PORT
    httpd.serve_forever()

def build():
    "run a local build of blogofile and scss"

    local("scss -m theme.css blogofile/style/theme.css")
    local("cd blogofile && blogofile -v build")

def debug():
    "run a debug build of blogofile and scss"

    local("scss theme.css blogofile/style/theme.css")
    local("cd blogofile && blogofile -v build")

def deploy(source_dir, dest_dir):
    """install from source_dir to dest_dir
    e.g deploy:"/home/tmp/blog/blogofile/_site/","/home/public"
    """
    cmd = "rsync -acv --delete '%s' '%s' |grep -v \/\$" % (source_dir, dest_dir)
    print(cmd)
    os.system(cmd)

def js_init():
    "download and install javascript libraries"

    local("mkdir -p blogofile/js")
    os.chdir("blogofile/js")
    local("wget %s" % "https://ajax.googleapis.com/ajax/libs/jquery/1.6.4/jquery.min.js")
    # http://documentcloud.github.com/underscore/
    local("wget %s" % "http://documentcloud.github.com/underscore/underscore-min.js")
