#!/usr/bin/env python
import os
import sys
import json
import MMC.settings as settings

class scipion_template:

    def __init__(self):
        with open(os.path.join(settings.env.template_files, 'workflow_template.json')) as f:
            self.template = json.load(f)

    def set_scope_defaults(self, scope):
        scopes = {'niehs_arctica': settings.niehs_arctica, 'niehs_krios_epu': settings.niehs_Krios_EPU, 'niehs_krios': settings.niehs_Krios}
        scope_defaults = scopes[scope]

        for key, val in self.template.items():
            for k, v in val.items():
                if k in scope_defaults.keys() and v == -1:
                    self.template[key][k] = scope_defaults[k]

    def set_value(self, job, key, value):
        if key in self.template[job].keys():
            self.template[job][key] = value
        else:
            print(f'Key: {key} does not exist in {job}')
            sys.exit(1)

    def set_values(self, values):
        # List of tuples of (job,key,value)
        for v in values:
            self.set_value(*v)

    def save_template(self, location):
        joblist = [val for _, val in self.template.items()]
        with open(location, 'w') as f:
            json.dump(joblist, f, indent=3)
        return location

    def check_completion(self):
        complete = True
        for key, val in self.template.items():
            for k, v in val.items():
                if v == -1:
                    print(f'missing {key}:{k}')
                    complete = False
        return complete
