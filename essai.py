import shlex
import subprocess

commande=shlex.split('sudo mount -t "ntfs" -o rw,user,auto,exec,gid=100,uid=1000,umask=002,utf8,codepage=850,shortname=mixed  /dev/sdb5 ~/Programme/sauvegarde/dest/')
 
        
process = subprocess.Popen(
    commande, 
    stdout=subprocess.PIPE, 
    stderr=subprocess.PIPE
)
process_output, process_erreur =  process.communicate()

pass
