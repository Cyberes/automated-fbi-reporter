import launch

if not launch.is_installed("requests"):
    launch.run_pip("requests netifaces py-cpuinfo psutil", "requirements for automated-fbi-reporter")
