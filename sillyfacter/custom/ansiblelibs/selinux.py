#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Derek Carter<goozbach@friocorte.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: selinux
short_description: Change policy and state of SELinux
description:
  - Configures the SELinux mode and policy. A reboot may be required after usage. Ansible will not issue this reboot but will let you know when it is required.
version_added: "0.7"
options:
  policy:
    description:
      - "name of the SELinux policy to use (example: C(targeted)) will be required if state is not C(disabled)"
    required: false
    default: null
  state:
    description:
      - The SELinux mode
    required: true
    default: null
    choices: [ "enforcing", "permissive", "disabled" ]
  conf:
    description:
      - path to the SELinux configuration file, if non-standard
    required: false
    default: "/etc/selinux/config"
notes:
   - Not tested on any debian based system
requirements: [ libselinux-python ]
author: Derek Carter <goozbach@friocorte.com>
'''

EXAMPLES = '''
- selinux: policy=targeted state=enforcing
- selinux: policy=targeted state=permissive
- selinux: state=disabled
'''

import re
import sys

try:
    import selinux
except ImportError:
    print "failed=True msg='libselinux-python required for this module'"
    sys.exit(1)


# getter subroutines
def get_config_state(configfile):
    myfile = open(configfile, "r")
    lines = myfile.readlines()
    myfile.close()
    for line in lines:
        stateline = re.match('^SELINUX=.*$', line)
        if (stateline):
            return(line.split('=')[1].strip())


def get_config_policy(configfile):
    myfile = open(configfile, "r")
    lines = myfile.readlines()
    myfile.close()
    for line in lines:
        stateline = re.match('^SELINUXTYPE=.*$', line)
        if (stateline):
            return(line.split('=')[1].strip())


# setter subroutines
def set_config_state(state, configfile):
    #SELINUX=permissive
    # edit config file with state value
    stateline = 'SELINUX=%s' % state
    myfile = open(configfile, "r")
    lines = myfile.readlines()
    myfile.close()
    myfile = open(configfile, "w")
    for line in lines:
        myfile.write(re.sub(r'^SELINUX=.*', stateline, line))
    myfile.close()


def set_state(state):
    if (state == 'enforcing'):
        selinux.security_setenforce(1)
    elif (state == 'permissive'):
        selinux.security_setenforce(0)
    elif (state == 'disabled'):
        pass
    else:
        msg = 'trying to set invalid runtime state %s' % state
        #module.fail_json(msg=msg)
        raise Exception(msg)


def set_config_policy(policy, configfile):
    # edit config file with state value
    #SELINUXTYPE=targeted
    policyline = 'SELINUXTYPE=%s' % policy
    myfile = open(configfile, "r")
    lines = myfile.readlines()
    myfile.close()
    myfile = open(configfile, "w")
    for line in lines:
        myfile.write(re.sub(r'^SELINUXTYPE=.*', policyline, line))
    myfile.close()
