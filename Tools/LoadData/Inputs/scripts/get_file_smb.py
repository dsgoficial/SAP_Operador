import smbc, os, sys

smb_file_path = sys.argv[1] 
local_file_path = sys.argv[2]
user = sys.argv[3]
passwd = sys.argv[4]
domain = sys.argv[5]


def do_auth (server, share, workgroup, username, password):
    return (domain, user, passwd)

ctx = smbc.Context() 
ctx.optionNoAutoAnonymousLogin = True
ctx.functionAuthData = do_auth
sfile = ctx.open(smb_file_path, os.O_RDONLY)
dfile = open(local_file_path, 'wb')
dfile.write(sfile.read())
sfile.close()
dfile.close()