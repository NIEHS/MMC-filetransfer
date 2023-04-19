#!/usr/bin/env python
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Callable
from pydantic.utils import deep_update
import MMC.settings as settings

class scipion_template:

    def __init__(self, template:str = 'workflow_template.json'):
        with open(settings.env.template_files / template) as f:
            self.template = json.load(f)

    def set_scope_defaults(self, scope):
        
        scope_defaults = settings.scopes[scope]

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
    


class new_scipion_template:

    def __init__(self, template:str = 'workflow_full.json', values_file:str = "workflow.yaml"):
        self.template = yaml.safe_load(Path(settings.env.template_files / values_file).read_text())
        self.full_template = json.loads(Path(settings.env.template_files / template).read_text())

    def set_scope_defaults(self, scope_defaults:Dict):
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

    def update_full_template(self):
        self.full_template = deep_update(self.full_template, self.template)

    def save_template(self, location):
        joblist = [val for _, val in self.full_template.items()]
        with open(location, 'w') as f:
            json.dump(joblist, f, indent=3)
        return location

    def check_completion(self):
        complete = True
        for key, val in self.template.items():
            for k, v in val.items():
                if v == -1 or (isinstance(v,str) and "{{" in v):
                    print(f'missing {key}:{k}')
                    complete = False
        return complete
    
    def _walk_and_calculate(self,flag:str, calculate_func:Callable):
        #find all values with the PARTICLE_SIZE flag
        for job_key, job in self.template.items():
            for key,val in job.items():
                if isinstance(val,str) and flag in val:
                    cleaned_val = val[2:-2].split(' ')[-1]
                    calculated_val = calculate_func(cleaned_val)
                    self.template[job_key][key] = calculated_val
    
    def set_particle_size(self, particle_size) -> None:
        def calculate(multipliers):
            multipliers = multipliers.split(",")
            calculated = particle_size
            for mult in multipliers:
                if not mult.startswith('val.'):
                    calculated *= float(mult)
                    continue
                split = mult.split('.')[1:]
                val = self.template
                for i in split:
                    val = val[i]
                calculated *= val
            return int(calculated)
        self._walk_and_calculate(flag="PARTICLE_SIZE",calculate_func=calculate)

    def set_gpu_ids(self, gpus_list:List[int]) -> None:
        assert len(gpus_list) >= 4, f"Must allocate at least 4 GPUs for the workflow, Received {gpus_list}"
        def set_gpu(value):
            split_val = [str(gpus_list[int(v)-1]) for v in value.split(',')]
            return ' '.join(split_val)
        self._walk_and_calculate(flag="GPU", calculate_func=set_gpu)
