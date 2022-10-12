import subprocess

subprocess.run("docker stop aexpy".split())
subprocess.check_call("cb build:docker".split())
subprocess.check_call("cb serve:docker".split())
