#!/usr/bin/env python3
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=unused-import

import json
import os
import subprocess
import sys

import adcm.init_django  # DO NOT DELETE !!!
from cm import config
from cm.ansible_plugin import finish_check
import cm.job
from cm.logger import log
from cm.models import LogStorage, JobLog, Prototype, ServiceComponent
from cm.status_api import Event
from cm.upgrade import bundle_switch
from cm.errors import AdcmEx


def open_file(root, tag, job_id):
    fname = f'{root}/{job_id}/{tag}.txt'
    f = open(fname, 'w', encoding='utf_8')
    return f


def read_config(job_id):
    fd = open(f'{config.RUN_DIR}/{job_id}/config.json', encoding='utf_8')
    conf = json.load(fd)
    fd.close()
    return conf


def set_job_status(job_id, ret, pid, event):
    if ret == 0:
        cm.job.set_job_status(job_id, config.Job.SUCCESS, event, pid)
        return 0
    elif ret == -15:
        cm.job.set_job_status(job_id, config.Job.ABORTED, event, pid)
        return 15
    else:
        cm.job.set_job_status(job_id, config.Job.FAILED, event, pid)
        return ret


def set_pythonpath(env, stack_dir):
    pmod_path = f'./pmod:{stack_dir}/pmod'
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = pmod_path + ':' + env["PYTHONPATH"]
    else:
        env["PYTHONPATH"] = pmod_path
    return env


def set_ansible_config(env, job_id):
    env['ANSIBLE_CONFIG'] = os.path.join(config.RUN_DIR, f'{job_id}/ansible.cfg')
    return env


def env_configuration(job_config):
    job_id = job_config['job']['id']
    stack_dir = job_config['env']['stack_dir']
    env = os.environ.copy()
    env = set_pythonpath(env, stack_dir)
    # This condition is intended to support compatibility.
    # Since older bundle versions may contain their own ansible.cfg
    if not os.path.exists(os.path.join(stack_dir, 'ansible.cfg')):
        env = set_ansible_config(env, job_id)
        log.info('set ansible config for job:%s', job_id)
    return env


def post_log(job_id, log_type, log_name):
    l1 = LogStorage.objects.filter(job__id=job_id, type=log_type, name=log_name).first()
    if l1:
        cm.status_api.post_event(
            'add_job_log',
            'job',
            job_id,
            {
                'id': l1.id,
                'type': l1.type,
                'name': l1.name,
                'format': l1.format,
            },
        )


def get_venv(job_id: int) -> str:
    return JobLog.objects.get(id=job_id).action.venv


def run_ansible(job_id):
    log.debug("job_runner.py starts to run ansible job %s", job_id)
    conf = read_config(job_id)
    playbook = conf['job']['playbook']
    out_file = open_file(config.RUN_DIR, 'ansible-stdout', job_id)
    err_file = open_file(config.RUN_DIR, 'ansible-stderr', job_id)
    post_log(job_id, 'stdout', 'ansible')
    post_log(job_id, 'stderr', 'ansible')
    event = Event()

    os.chdir(conf['env']['stack_dir'])
    cmd = [
        '/adcm/python/job_venv_wrapper.sh',
        get_venv(int(job_id)),
        'ansible-playbook',
        '--vault-password-file',
        f'{config.CODE_DIR}/ansible_secret.py',
        '-e',
        f'@{config.RUN_DIR}/{job_id}/config.json',
        '-i',
        f'{config.RUN_DIR}/{job_id}/inventory.json',
        playbook,
    ]
    if 'params' in conf['job']:
        if 'ansible_tags' in conf['job']['params']:
            cmd.append('--tags=' + conf['job']['params']['ansible_tags'])
    if 'verbose' in conf['job'] and conf['job']['verbose']:
        cmd.append('-vvvv')

    log.info("job run cmd: %s", ' '.join(cmd))
    proc = subprocess.Popen(cmd, env=env_configuration(conf), stdout=out_file, stderr=err_file)
    cm.job.set_job_status(job_id, config.Job.RUNNING, event, proc.pid)
    event.send_state()
    log.info("run ansible job #%s, pid %s, playbook %s", job_id, proc.pid, playbook)
    ret = proc.wait()
    finish_check(job_id)
    ret = set_job_status(job_id, ret, proc.pid, event)
    event.send_state()

    out_file.close()
    err_file.close()

    log.info("finish ansible job #%s, pid %s, ret %s", job_id, proc.pid, ret)
    sys.exit(ret)


def switch_hc(task, action):
    cluster = task.task_object
    old_hc = cm.api.get_hc(cluster)
    new_hc = [*task.post_upgrade_hc_map, *old_hc]
    task.hostcomponentmap = old_hc
    task.post_upgrade_hc_map = None
    for hc in new_hc:
        if "component_prototype_id" in hc:
            proto = Prototype.objects.get(type='component', id=hc.pop('component_prototype_id'))
            comp = ServiceComponent.objects.get(cluster=cluster, prototype=proto)
            hc['component_id'] = comp.id
            hc['service_id'] = comp.service.id
    host_map, _ = cm.job.check_hostcomponentmap(cluster, action, new_hc)
    cm.api.save_hc(cluster, host_map)


def main(job_id):
    log.debug("job_runner.py called as: %s", sys.argv)
    job = JobLog.objects.get(id=job_id)
    if job.sub_action and job.sub_action.script_type == 'internal':
        event = Event()
        cm.job.set_job_status(job_id, config.Job.RUNNING, event)
        try:
            task = job.task
            bundle_switch(task.task_object, job.action.upgrade)
            if task.post_upgrade_hc_map:
                switch_hc(task, job.action)
        except AdcmEx:
            cm.job.set_job_status(job_id, config.Job.FAILED, event)
            sys.exit(1)
        cm.job.set_job_status(job_id, config.Job.SUCCESS, event)
        event.send_state()
        sys.exit(0)
    else:
        run_ansible(job_id)


def do():
    if len(sys.argv) < 2:
        print(f"\nUsage:\n{os.path.basename(sys.argv[0])} job_id\n")
        sys.exit(4)
    else:
        main(sys.argv[1])


if __name__ == '__main__':
    do()
