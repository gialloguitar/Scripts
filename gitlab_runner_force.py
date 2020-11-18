#!/usr/bin/python
import os
import requests
import json
from ansible.module_utils.basic import AnsibleModule


ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'supported_by': 'markule@mail.ru'
}

DOCUMENTATION = '''
---
module: gitlab_runner_force

short_description: This module helping manage of GitLab runners via native API

version_added: "1.0"

description:
    - "For managing GitLab runners use this module in cases of register a new, unregister runner and clean up all orphaned runners."

options:
    name:
        description:
            - Name of runner that need to manage, from API response wil be available with a 'description' JSON attr.
        default: None
        required: false
    gitlab_url:
        description:
            - URL to your GitLab installation
        default: gitlab.stripchat.dev
        required: false
    api_token:
        description:
            - GitLab token for accessing to API with read/write permissions.
        default: None
        required: true
    reg_token:
        description:
            - A project, group or global token for registration new runners.
        default: None
        required: false
    tag_list:
        description:
            - Comma separated string of apllied to runner tags, from API response wil be available with a 'tag_list' JSON attr
        default: None
        required: false
    state:
        description:
            - Allow to manage with three different runners state 'present', 'absent', 'cleanup'
        default: None
        required: true
    run_untagged:
        description:
            - Allow or prevent run untagged jobs with a runner
        default: True
        requred: false
author:
    - Vladimir Pereskokov (@markule)
'''

EXAMPLES = '''
- name: Create and registrate new runner via API on your GitLab instance, ensure that you have registered output for runner's auth token (neccesarry in config.toml)
  gitlab_runner_force:
     gitlab_url: 'gitlab.example.com'
     name: "build-runner-01"
     api_token: "abc123"
     reg_token: 'xyz456'
     tag_list: 'test, build, deploy'
     state: present
  register: output

- name: Update and apply new tags to runner and prevent run untagged jobs from default GitLab URL (gitlab.stripchat.dev)
  gitlab_runner_force:
     name: "build-runner-01"
     api_token: "abc123"
     tag_list: 'test, build'
     run_untagged: False
     state: present

- name: Cleanup API from orphaned runners which in 'not_connected' and 'offline' status, for avoiding extra requests call module with 'run_once: true' feature.
  gitlab_runner_force:
     api_token: "abc123"
     state: cleanup
  run_once: true

- name: Remove and unregistrate from API of your GitLab installation runner with 'name'
  gitlab_runner_force:
     gitlab_url: "gitlab.example.com"
     name: "test-runner-01"
     api_token: "abc123"
     state: absent
'''

RETURN = '''
message: Registration of new runner with a next tags: 'build'
    response:
        id: 588
        token: abcdef12345
        runner: test-runner-01
'''

GITLAB_URL = 'gitlab.com'
RUNNERS_ENDPOINT = '/api/v4/runners'
MSG = {
    'reg_token'       : 'For creating a new runner you have to provide valid registration token \'reg_token\' from your Gitlab installation and \'name\' of runner',
    'del_status'      : 'With the successful deletion of runner, status code has to equal 204, but obtained:',
    'check_mode'      : 'Any API write operations is unavailable in check mode',
    'create'          : 'Registration of new runner with a next tags:',
    'update'          : 'Update runner\'s tags:',
    'exist'           : 'Runner\'s already exist with a following tags:',
    'delete'          : 'Runner was unregistered and deleted, tags:',
    'absent'          : 'Runner doesn\'t exist with tags:',
    'orph_detect'     : 'Following oprhaned runners IDs have been deleted from Gitlab:',
    'orph_not_detect' : 'Orphaned runners hasn\'t been discovered',
    'no_changes'      : 'No changes'
  }

def gitlab_runner():

    module = AnsibleModule(
        argument_spec = dict(
            gitlab_url      = dict(required = False, default = GITLAB_URL),
            name            = dict(required = False, default = ''),
            api_token       = dict(required = True),
            reg_token       = dict(required = False, default = ''),
            run_untagged    = dict(required = False, default = True, type = 'bool' ),
            tag_list        = dict(required = False, default = ''),
            state           = dict(required = True, choices = ['present', 'absent', 'cleanup'] )
        ),
        supports_check_mode = True
    )

    gitlab_url      = str(module.params['gitlab_url'])
    name            = str(module.params['name'])
    api_token       = str(module.params['api_token'])
    reg_token       = str(module.params['reg_token'])
    run_untagged    = bool(module.params['run_untagged'])
    tag_list        = str(module.params['tag_list'])
    state           = str(module.params['state']).lower()

    api_url    = 'https://{url}{api}'.format(url = gitlab_url, api = RUNNERS_ENDPOINT)

    result = dict(
        changed  = False,
        runner   = name,
        message  = '',
        response = ''
    )

    runner_id  = get_id(name, get_runners(api_url, api_token))


    if state == 'present':
        if runner_id == 0:
            # Create a new
            if len(reg_token.strip()) == 0 or len(name.strip()) == 0:
                module.fail_json(msg = MSG['reg_token'])
            result['changed']  = True
            result['message']  = '{msg} \'{tags}\''.format(msg = MSG['create'], tags = tag_list)
            result['response'] = MSG['check_mode'] if module.check_mode else create_runner(module, api_url, api_token, name, runner_id, reg_token, tag_list, run_untagged)
        else:
            details    = get_runner_details(api_url, api_token, runner_id)
            old_run_untagged = details['run_untagged']
            old_tags_lst     = details['tag_list']
            old_tags         = ",".join(old_tags_lst)

            tag_list_lst = tag_list.split(',')
            tag_list_lst = [ i.strip(' ') for i in tag_list_lst ]

            if set(old_tags_lst) != set(tag_list_lst):
                # Update tags
                result['changed']  = True
                result['message']  = '{msg} \'{old_tags}\' to \'{tags}\''.format(msg = MSG['update'], old_tags = old_tags, tags = tag_list)
                result['response'] = MSG['check_mode'] if module.check_mode else  update_tags(api_url, api_token, runner_id, tag_list)

            elif set(old_tags_lst) == set(tag_list_lst):
                # Already exist
                result['changed']  = False
                result['message']  = '{msg} \'{tags}\''.format(msg = MSG['exist'], tags = tag_list)

            if  old_run_untagged != run_untagged:
                result['untagged'] =  MSG['check_mode'] if module.check_mode else  set_run_untagged(api_url, api_token, runner_id, run_untagged)


    if state == 'absent':
        if runner_id > 0:
            # Delete runner
            result['changed']  = True
            result['message']  = '{msg} \'{tags}\''.format(msg = MSG['delete'], tags = tag_list)
            result['response'] = MSG['check_mode'] if module.check_mode else  delete_runner(api_url, api_token, runner_id)
            if result['response'] != 204 and not module.check_mode:
                module.fail_json(msg = MSG['del_status'])
        else:
            # Runner doesn't exist
            result['changed'] = False
            result['message'] = '{msg} \'{tags}\''.format(msg = MSG['absent'], tags = tag_list)

    if state == 'cleanup':
        orphaned_runners = get_orph_runners(api_url, api_token)
        if len(orphaned_runners) > 0:
            # Some oprhaned runners have been deleted
            result['changed']  = True
            result['message']  = '{msg} \'{runners}\''.format(msg = MSG['orph_detect'], runners = ", ".join(orphaned_runners))
            result['response'] = MSG['check_mode'] if module.check_mode else  delete_orph_runners(api_url, api_token, orphaned_runners)

            if not module.check_mode:
                wrong_status_dict = {}
                for runner_id in result['response']:
                    if result['response'][runner_id] != '204':
                        rid  = 'Runner_{id}'.format(id = runner_id)
                        st   = str(result['response'][runner_id])
                        wrong_status_dict = { rid: st }
                if len(wrong_status_dict) > 0:
                    fail_msg = '{msg} {runners}'.format(msg = MSG['del_status'], runners = wrong_status_dict )
                    module.fail_json(msg = fail_msg)
        else:
            # Orphaned runners hasn't been discovered
            result['changed']  = False
            result['message']  = MSG['orph_not_detect']
            result['response'] = MSG['check_mode'] if module.check_mode else delete_orph_runners(api_url, api_token, orphaned_runners)

    module.exit_json(**result)

def create_runner(module, api_url, api_token, name, runner_id, reg_token, tag_list, run_untagged):
    r = requests.post(api_url, headers = { 'PRIVATE-TOKEN': api_token }, data = { 'token': reg_token, 'description': name, 'tag_list': tag_list , 'run_untagged': run_untagged } )
    js = json.loads(r.text)
    return js

def update_tags(api_url, api_token, runner_id, tag_list):
    api_query = '{api_url}/{id}'.format(api_url = api_url, id = runner_id)
    r = requests.put(api_query, headers = { 'PRIVATE-TOKEN': api_token }, data = { 'tag_list': tag_list } )
    js = json.loads(r.text)
    return js

def set_run_untagged(api_url, api_token, runner_id, run_untagged):
    api_query = '{api_url}/{id}'.format(api_url = api_url, id = runner_id)
    requests.put(api_query, headers = { 'PRIVATE-TOKEN': api_token }, data = { 'run_untagged': run_untagged } )
    resp = "Run untagged jobs set to: {untagged}".format(untagged = run_untagged)
    return resp

def delete_runner(api_url, api_token, runner_id):
    api_query = '{api_url}/{id}'.format(api_url = api_url, id = runner_id)
    r = requests.delete(api_query, headers = { 'PRIVATE-TOKEN': api_token } )
    return r.status_code

def delete_orph_runners(api_url, api_token, orphaned_runners):
    delete_status_codes = {}
    for runner_id in orphaned_runners:
        api_query = '{api_url}/{id}'.format(api_url = api_url, id = runner_id)
        r = requests.delete(api_query, headers={ 'PRIVATE-TOKEN': api_token })
        rid = 'Runner_{id}'.format( id = runner_id )
        st  = str(r.status_code)
        delete_status_codes[rid] = st
    return delete_status_codes

def get_orph_runners(api_url, api_token ):
    api_query = '{api_url}/all?per_page=500'.format(api_url = api_url)
    r = requests.get(api_query, headers={ 'PRIVATE-TOKEN': api_token } )
    js = json.loads(r.text)
    all_orph_runners = []

    for node in js:
        if node['status'] == 'not_connected' or node['status'] == 'offline':
            all_orph_runners.append(str(node['id']))

    return all_orph_runners

def get_runners(api_url, api_token):
    api_query = '{api_url}/all?per_page=500'.format(api_url = api_url)
    r = requests.get(api_query, headers={ 'PRIVATE-TOKEN': api_token } )
    js = json.loads(r.text)
    all_runners = {}

    for node in js:
        all_runners[node['description']] = node['id']

    return all_runners

def get_runner_details(api_url, api_token, runner_id,):
    api_query = '{api_url}/{id}'.format(api_url = api_url, id = runner_id)
    r = requests.get(api_query, headers={ 'PRIVATE-TOKEN': api_token } )
    js = json.loads(r.text)
    return js

def get_id(name, all_runners):
    runner_id = 0
    if name in all_runners:
        runner_id = all_runners[name]
    return runner_id

def main():
    gitlab_runner()

if __name__ == "__main__":
    main()
