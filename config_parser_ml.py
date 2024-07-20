#!/usr/bin/env python3
import os
import configparser
import pwd
import grp
import subprocess

# Redefined the  optionxform method of the configparser that is responsible
# changing all configuration variables to lowercase


class MyConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr: str) -> str:
        return (optionstr)

# Create an object from MyConfigParser


config = MyConfigParser()

# Gets the user and group group information

user_id = os.getuid()  # Retrieves the current user ID
group_id = os.getgid()  # Retrieves the current group ID

user_info = pwd.getpwuid(user_id)  # Retrieves detailed user information
group_info = grp.getgrgid(group_id)  # Retrieves detailed group information

user_name = user_info.pw_name  # Gets the user's name
group_name = group_info.gr_name  # Gets the group's name


# Current script directory
script_dir = os.path.dirname(os.path.abspath(__file__))


# Create the the configuration variables
config["Unit"] = {'Description': "Gunicorn instance to server app",
                  'After': "network.target"}

config['Service'] = {"ExecStart":  f"{os.path.join(script_dir, 'venv/bin/gunicorn --workers 3 --bind unix:app.sock -m 007 wsgi:app')}",  # Path to execute and start the service
                     # Writes output and log to terminal (for debuging purposes)
                     #  "Environment": "PYTHONUNBUFFERED=1",
                     "User": user_name,
                     "Group": group_name,
                     "Environment": f"\"{os.path.join(script_dir, 'venv/bin')}\"",
                     "Restart": "always",
                     "WorkingDirectory": f"{os.path.join(script_dir, '')}"}

config['Install'] = {"WantedBy": "multi-user.target"}


# Writes configuration into file
with open('config.ini', 'w') as configfile:
    config.write(configfile)
    print("Configuration file created and saved")
configfile.close()

# Change permission of file
file_path = 'config.ini'
permissions = 0o775
os.chmod(file_path, permissions)
print("File permission changed to 775")


# Use sudo to copy the file
src = os.path.join(
    str(script_dir), 'config.ini')
dst = '/etc/systemd/system/ml-app.service'
try:
    subprocess.run(['sudo', 'cp', src, dst], check=True)
    print("File copied successfully")
    print("File ml-app.service is located in /etc/systemd/system/")
except subprocess.CalledProcessError as e:
    print(f"Error copying file: {e}")
