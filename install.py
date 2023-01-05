import launch

if not launch.is_installed("requests"):
    launch.run_pip("requests", "requirements for automated-fbi-reporter")
