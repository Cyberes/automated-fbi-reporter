import launch

launch.run_pip('install requests~=2.28.1 py-cpuinfo~=9.0.0 psutil~=5.9.4 Pillow~=9.4.0 ipcalc==1.99.0 six==1.16.0 gitpython==3.1.30', "requirements for automated-fbi-reporter")

# Do this seperatly since they're a little unreliable.
launch.run_pip("install netifaces==0.11.0", "volatile requirements for automated-fbi-reporter")  # will fail if python3-dev isn't installed
launch.run_pip("install opencv-python~=4.7.0.68", "volatile requirements for automated-fbi-reporter")
