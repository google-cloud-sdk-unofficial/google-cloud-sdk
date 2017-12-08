import sys
x=sys.modules['containerregistry.client']
  

from containerregistry.client import typing_
setattr(x, 'typing', typing_)


from containerregistry.client import docker_name_
setattr(x, 'docker_name', docker_name_)


from containerregistry.client import docker_creds_
setattr(x, 'docker_creds', docker_creds_)


