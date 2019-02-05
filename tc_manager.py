from subprocess import run, PIPE
import re
import logging


logger = logging.getLogger(__name__)


def ip_to_str(tc_ip):
    return str(int(tc_ip[0:2], 16)) + '.' \
         + str(int(tc_ip[2:4], 16)) + '.'  \
         + str(int(tc_ip[4:6], 16)) + '.' \
         + str(int(tc_ip[6:8], 16))


def parse_tc_policy(output):
    matched = re.search('pref (?P<pref>\d+) u32(?: .+)* fh (?P<policy_id>\w+::\w+)', output)
    if matched is not None and matched.group('pref') != '65535':
        policy = {
            'policy_id': matched.group('policy_id'),
            'pref': int(matched.group('pref')),
            'match': {},
            'action': {}
        }
        matched = re.search('match (?P<src_ip>.*)/f{8} at 12', output)
        if matched:
            policy['match']['src_ip'] = ip_to_str(matched.group('src_ip'))
        matched = re.search('match (?P<dst_ip>.*)/f{8} at 16', output)
        if matched:
            policy['match']['dst_ip'] = ip_to_str(matched.group('dst_ip'))
        matched = re.search('match (?P<src_port>\w{4})'
                            '(?P<dst_port>\w{4})/(?P<src_port_mask>\w{4})'
                            '(?P<dst_port_mask>\w{4}) at 20', output)
        if matched:
            if matched.group('src_port_mask') != '0000':
                policy['match']['src_port'] = int(matched.group('src_port'), 16)
            if matched.group('dst_port_mask') != '0000':
                policy['match']['dst_port'] = int(matched.group('dst_port'), 16)
        matched = re.search('police \w+ rate (?P<rate>\w+)', output)
        if matched:
            policy['action']['rate'] = matched.group('rate')
        return policy
    else:
        return None


class NetworkInterfaces:
    def __init__(self, whitelist=None, blacklist=None):
        if whitelist:
            if_names = whitelist
        else:
            completed_process = run(["ip", "link", "show"], stdout=PIPE,  text=True)
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
    def __init__(self, name):
        self.name = name
        cmd = "tc qdisc add dev {} ingress".format(self.name)
        logger.debug("get default rate cmd -> {}".format(cmd))
        run(cmd.split(), stdout=PIPE, stderr=PIPE,  text=True)

    def as_dict(self):
        return {'name': self.name,
                'default_rate': self.default_rate,
                'policies': self.policies}

    @property
    def default_rate(self):
        cmd = "tc filter show dev {} ingress protocol ip pref 65535".format(self.name)
        logger.debug("get default rate cmd -> {}".format(cmd))
        completed_process = run(cmd.split(), stdout=PIPE, stderr=PIPE,  text=True)
        if completed_process.returncode == 0:
            match = re.search('police \w+ rate (?P<rate>\w+)', completed_process.stdout)
            if match:
                return match.group(1)
        return None

    @default_rate.setter
    def default_rate(self, default_rate):
        logger.debug("TC -> removing default rate from {}".format(self.name))
        cmd = "tc filter delete dev {} ingress protocol ip pref 65535 " \
              "u32".format(self.name)
        run(cmd.split(),  text=True)
        if default_rate is not None:
            cmd = "tc filter add dev {} ingress protocol ip pref 65535 " \
                  "u32 match u32 0 0 " \
                  "police rate {} burst 50K action drop".format(self.name, default_rate)
            logger.debug('updating {} default rate to {}: cmd -> {}'.format(self.name, default_rate, cmd))
            # TODO check command exit status
            run(cmd.split(),  text=True)

    @property
    def policies(self):
        policies = []
        cmd = "tc filter show dev {} ingress protocol ip".format(self.name)
        completed_process = run(cmd.split(), stdout=PIPE, stderr=PIPE,  text=True)
        if completed_process.returncode == 0:
            tc_policies = completed_process.stdout.split('\n\n')
            for tc_policy in tc_policies:
                policy = parse_tc_policy(tc_policy)
                if policy is not None:
                    policies.append(policy)
        return policies

    def get_policy(self, policy_id):
        for policy in self.policies:
            if policy['policy_id'] == policy_id:
                return policy
        return None

    def get_policy_by_match(self, match):
        for policy in self.policies:
            if policy['match'] == match:
                return policy
        return None

    def post_policy(self, match, action):
        policy = self.get_policy_by_match(match)
        if policy is not None:
            logger.debug('post_policy of an existing policy. updating old policy {}'.format(policy))
            self.update_policy(policy['policy_id'], action)
        else:
            cmd = "tc filter add dev {} ingress pref 5 protocol ip u32 ".format(self.name)
            if not match:
                match_cmd = "match u32 0 0"
            else:
                match_cmd = ""
                if 'src_ip' in match and match['src_ip'] is not None:
                    match_cmd = match_cmd + "match ip src {}/32 ".format(match['src_ip'])
                if 'dst_ip' in match and match['dst_ip'] is not None:
                    match_cmd = match_cmd + "match ip dst {}/32 ".format(match['dst_ip'])
                if 'src_port' in match and match['src_port'] is not None:
                    match_cmd = match_cmd + "match ip sport {} 0xffff ".format(match['src_port'])
                if 'dst_port' in match and match['dst_port'] is not None:
                    match_cmd = match_cmd + "match ip dport {} 0xffff ".format(match['dst_port'])
            cmd = cmd + match_cmd
            cmd = cmd + " police rate {} burst 50K action drop".format(action['rate'])
            run(cmd.split(), stdout=PIPE, stderr=PIPE,  text=True)
            logger.debug('creating new policy in {}: cmd -> {}'.format(self.name, cmd))

        policy = self.get_policy_by_match(match)
        return policy

    def update_policy(self, policy_id, action):
        if self.get_policy(policy_id):
            cmd = "tc filter replace dev {} ingress pref 5 handle {} " \
                  "protocol ip u32 police rate {} burst 50K action drop".format(self.name, policy_id, action['rate'])
            logger.debug("Sending TC cmd: {}".format(cmd))
            run(cmd.split(),  text=True)
        else:
            raise ValueError("cannot update Not Existing policy_id {}".format(policy_id))

    def update_policy_by_match(self, match, action):
        if self.get_policy_by_match(match):
            policy_id = self.get_policy_by_match(match)['policy_id']
            self.update_policy(policy_id, action)
        else:
            raise ValueError("cannot update Not Existing policy match {}".format(match))

    def delete_policy(self, policy_id):
        if self.get_policy(policy_id):
            cmd = "tc filter del dev {interface} ingress pref 5 " \
                  "handle {policy_id} protocol ip u32".format(interface=self.name, policy_id=policy_id)
            run(cmd.split(),  text=True)
        else:
            raise ValueError("cannot update Not Existing policy_id {}".format(policy_id))

    def delete_policy_by_match(self, match):
        if self.get_policy_by_match(match):
            policy_id = self.get_policy_by_match(match)['policy_id']
            self.delete_policy(policy_id)
        else:
            raise ValueError("cannot delete Not Existing policy match {}".format(match))

