import subprocess

# subprocess.check_call("cb data:clean".split())
subprocess.check_call(
    "cb -c docker=aexpy/aexpy -c provider=default -c project=click data:work".split())
