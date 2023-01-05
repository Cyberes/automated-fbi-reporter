import launch

launch.run_pip('requests~=2.28.1 py-cpuinfo~=9.0.0 psutil~=5.9.4', "requirements for automated-fbi-reporter")

# Do this seperatly since it will fail if python3-dev isn't installed.
launch.run_pip("netifaces==0.11.0", "requirements for automated-fbi-reporter")
