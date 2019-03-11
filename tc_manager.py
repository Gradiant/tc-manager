from subprocess import run, PIPE
import re
import logging


logger = logging.getLogger(__name__)


def ip_to_str(tc_ip):
    return str(int(tc_ip[0:2], 16)) + '.' \
         + str(int(tc_ip[2:4], 16)) + '.'  \
         + str(int(tc_ip[4:6], 16)) + '.' \
         + str(int(tc_ip[6:8], 16))


def extract_policy(tc_filter):
    matched = re.search('pref (?P<pref>\d+) u32 chain 0 fh (?P<handle>\w+::\w+)(?: .+)* flowid 1:(?P<policy_id>\d+)', tc_filter)
    if matched is not None:
        policy = {
            'policy_id': int(matched.group('policy_id')),
            'handle': matched.group('handle'),
            'pref': int(matched.group('pref')),
            'match': {},
            'action': {}
        }
        matched = re.search('match (?P<src_ip>.*)/f{8} at 12', tc_filter)
        if matched:
            policy['match']['src_ip'] = ip_to_str(matched.group('src_ip'))
        matched = re.search('match (?P<dst_ip>.*)/f{8} at 16', tc_filter)
        if matched:
            policy['match']['dst_ip'] = ip_to_str(matched.group('dst_ip'))
        matched = re.search('match (?P<src_port>\w{4})'
                            '(?P<dst_port>\w{4})/(?P<src_port_mask>\w{4})'
                            '(?P<dst_port_mask>\w{4}) at 20', tc_filter)
        if matched:
            if matched.group('src_port_mask') != '0000':
                policy['match']['src_port'] = int(matched.group('src_port'), 16)
            if matched.group('dst_port_mask') != '0000':
                policy['match']['dst_port'] = int(matched.group('dst_port'), 16)
        return policy
    else:
        return None

def run_command(cmd):
    logger.info("running command '{}'".format(cmd))
    completed_process = run(cmd.split(), stdout=PIPE, stderr=PIPE, encoding='UTF8')
    if completed_process.stderr != '':
        logger.warning("command respond with error {}".format(completed_process.stderr))
    return completed_process



class NetworkInterfaces:
    def __init__(self, whitelist=None, blacklist=None):
        if whitelist:
            if_names = whitelist
        else:
            completed_process = run(["ip", "link", "show"], stdout=PIPE,  encoding='UTF8')
            if_names = re.findall('\d+: ([\w-]+)(?:@\w+)?:', completed_process.stdout)
            if_names = [if_name for if_name in if_names]
        if blacklist is not None:
            for blacklist_if in blacklist:
                if blacklist_if in if_names:
                    if_names.remove(blacklist_if)
        self.interfaces = dict()
        for if_name in if_names:
            logger.debug("adding interface {} for managing".format(if_name))
            self.interfaces[if_name] = Interface(if_name)

    def set_default_rate(self, default_rate):
        for interface_name in self.interfaces:
            self.interfaces[interface_name].default_rate = default_rate

    def post_policy(self, match, action):
        for interface_name in self.interfaces:
            self.interfaces[interface_name].post_policy(match, action)

    def delete_policy_by_match(self, match):
        for interface_name in self.interfaces:
            self.interfaces[interface_name].delete_policy_by_match(match)


class Interface:
    def __init__(self, name, default_rate='1mbit'):
        self.name = name
        logger.info("Setting tc redirection {} -> ifb0".format(self.name))
        run_command("tc qdisc add dev {} ingress".format(self.name))
        run_command("tc filter add dev {} ingress pref 10 protocol "
                    "ip u32 match u32 0 0 action mirred egress redirect dev ifb0".format(self.name))
        run_command("tc qdisc add dev ifb0 root handle 1: htb default 10")
        self.default_rate = default_rate

    def as_dict(self):
        return {'name': self.name,
                'default_rate': self.default_rate,
                'policies': list(self.policies.values())}

    @property
    def default_rate(self):
        completed_process = run_command("tc class show dev ifb0 classid 1:6500".format(self.name))
        if completed_process.returncode == 0:
            match = re.search('rate (?P<rate>\w+)', completed_process.stdout)
            if match:
                return match.group(1)
        return None

    @default_rate.setter
    def default_rate(self, default_rate):
        if default_rate is not None:
            if self.default_rate is None:
                logger.info("Setting {} new default rate = {}".format(self.name, default_rate))
                run_command("tc class add dev ifb0 parent 1: classid 1:6500 htb rate {}".format(default_rate))
                run_command("tc filter add dev ifb0 parent 1: protocol ip pref 65535 u32 match u32 0 0 flowid 1:6500")
            else:
                logger.info("Setting {} default rate to {}".format(self.name, default_rate))
                run_command("tc class replace dev ifb0 classid 1:6500 htb rate {}".format(default_rate))
        else:
            if self.default_rate is not None:
                logger.info("Removing {} default rate".format(self.name))
                #completed_process = run_command("tc filter show dev ifb0 pref 65535")
                #match = re.search('fh (?P<handle>\w+::\w+)', completed_process.stdout).group('handle')
                #default_filter_handle = match.group
                cmd = "tc filter del dev ifb0 protocol ip pref 65535 "
                #      "handle {} protocol ip u32".format(default_filter_handle)
                run_command(cmd)
                cmd = "tc class del dev ifb0 classid 1:6500"
                run_command(cmd)

    @property
    def policies(self):
        policies = dict()
        completed_process = run_command("tc filter show dev ifb0")
        if completed_process.returncode == 0:
            tc_filters = [flow for flow in completed_process.stdout.split("filter")
                          if 'flowid' in flow and 'pref 65535' not in flow]
            for tc_filter in tc_filters:
                policy = extract_policy(tc_filter)
                logger.debug("extracted policy {}".format(policy))
                if policy is not None:
                    completed_process = run_command("tc class show dev ifb0 classid 1:{}".format(policy['policy_id']))
                    matched = re.search('rate (?P<rate>\w+)', completed_process.stdout)
                    if matched:
                        policy['action']['rate'] = matched.group('rate')
                    policies[policy['policy_id']] = policy
        return policies

    def get_free_policy_id(self):
        policy_id = 1
        while policy_id in self.policies:
            policy_id = policy_id + 1
        logger.debug("Getting the free policy id {}".format(policy_id))
        return policy_id

    def get_policy(self, policy_id):
        return self.policies.get(policy_id, None)

    def get_policy_by_match(self, match):
        for policy in self.policies.values():
            if policy['match'] == match:
                return policy
        return None

    def post_policy(self, match, action):
        policy = self.get_policy_by_match(match)
        if policy is not None:
            logger.debug('post_policy of an existing policy. updating old policy {}'.format(policy))
            self.update_policy(policy['policy_id'], action)
        else:
            policy_id = self.get_free_policy_id()
            pref = 15
            run_command("tc class add dev ifb0 parent 1: classid 1:{} htb rate {}".format(
                policy_id, action['rate']))
            if not match:
                match_cmd = "match u32 0 0"
            else:
                match_cmd = ""
                if 'src_ip' in match and match['src_ip'] is not None:
                    pref = pref - 3
                    match_cmd = match_cmd + "match ip src {}/32 ".format(match['src_ip'])
                if 'dst_ip' in match and match['dst_ip'] is not None:
                    pref = pref - 3
                    match_cmd = match_cmd + "match ip dst {}/32 ".format(match['dst_ip'])
                if 'src_port' in match and match['src_port'] is not None:
                    pref = pref - 1
                    match_cmd = match_cmd + "match ip sport {} 0xffff ".format(match['src_port'])
                if 'dst_port' in match and match['dst_port'] is not None:
                    pref = pref - 1
                    match_cmd = match_cmd + "match ip dport {} 0xffff ".format(match['dst_port'])
            cmd = "tc filter add dev ifb0 parent 1:0 pref {} protocol ip u32 {} flowid 1:{}"\
                .format(pref, match_cmd, policy_id)
            run_command(cmd)
        policy = self.get_policy_by_match(match)
        return policy

    def update_policy(self, policy_id, action):
        policy = self.get_policy(policy_id)
        if policy is not None:
            cmd = "tc class replace dev ifb0 classid 1:{} htb rate {}".format(policy_id, action['rate'])
            logger.debug("Sending TC cmd: {}".format(cmd))
            run(cmd.split(),  encoding='UTF8')
        else:
            raise ValueError("cannot update Not Existing policy_id {}".format(policy_id))

    def update_policy_by_match(self, match, action):
        if self.get_policy_by_match(match):
            policy_id = self.get_policy_by_match(match)['policy_id']
            self.update_policy(policy_id, action)
        else:
            raise ValueError("cannot update Not Existing policy match {}".format(match))

    def delete_policy(self, policy_id):
        policy = self.get_policy(policy_id)
        if policy is not None:
            cmd = "tc filter del dev ifb0 pref {} " \
                  "handle {} protocol ip u32".format(policy['pref'], policy['handle'])
            run_command(cmd)
            cmd = "tc class del dev ifb0 classid 1:{}".format(policy['policy_id'])
            run_command(cmd)
        else:
            raise ValueError("cannot delete update Not Existing policy_id {}".format(policy_id))

    def delete_policy_by_match(self, match):
        if self.get_policy_by_match(match):
            policy_id = self.get_policy_by_match(match)['policy_id']
            self.delete_policy(policy_id)
        else:
            raise ValueError("cannot delete Not Existing policy match {}".format(match))

