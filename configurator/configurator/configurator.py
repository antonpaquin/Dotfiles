import json
import os
import shutil
from argparse import ArgumentParser

import cerberus
import yaml


PROG_NAME = 'configurator'


user_config_schema = {
    'editor': {
        'type': 'string',
        'required': False,
        'default': os.getenv('EDITOR', 'nano')
    },
    'configurations': {
        'type': 'dict',
        'required': True,
        'keysrules': {
            'type': 'string',
        },
        'valuesrules': {
            'type': 'list',
            'schema': {
                'type': 'dict',
                'schema': {
                    'name': {
                        'type': 'string',
                        'required': False,
                    },
                    'source': {
                        'type': 'string',
                        'required': True,
                    },
                    'dest': {
                        'type': 'string',
                        'required': True,
                    },
                    'root': {
                        'type': 'boolean',
                        'required': False,
                        'default': False,
                    },
                },
            },
        },
    },
}


def edit(user_conf, target, subtarget):
    unit_cfg = get_target_unit(user_conf, target, subtarget)
    fname = dest_file(unit_cfg)

    if unit_cfg['root']:
        cmd = shutil.which('sudo')
        args = [cmd, user_conf['editor'], fname]
    else:
        editor = shutil.which(user_conf['editor'])
        if not editor:
            print('Could not find editor: "{}"'.format(user_conf['editor']))
            exit(1)
        cmd = editor
        args = [cmd, fname]

    os.execv(cmd, args)


def list_config(user_conf):
    for key, val in user_conf['configurations'].items():
        print(key)


def which_config(user_conf, target, subtarget):
    unit_cfg = get_target_unit(user_conf, target, subtarget)
    print(dest_file(unit_cfg))


def deploy_config(user_conf):
    for target, subconfigs in user_conf.items():
        for subconfig in subconfigs:
            deploy_file(target, subconfig)


def deploy_file(target, unit_cfg):
    pass  # TODO
    # what to do about the refind problem?
    # hardlinks won't work
    # symlinks out of refind won't (?) work
    # probably copy is all we've got


def sudo_deploy_file(target, unit_cfg):
    pass  # TODO


def gather_config(user_conf):
    for target, subconfigs in user_conf['configurations'].items():
        for subconfig in subconfigs:
            gather_file(target, subconfig)


def gather_file(target, unit_cfg):
    src = source_file(target, unit_cfg)
    dest = dest_file(unit_cfg)
    os.makedirs(os.path.dirname(src), exist_ok=True)
    if os.path.islink(dest):
        return  # TODO ?
    elif os.path.islink(src):
        return  # ???
    else:
        shutil.copy(dest, src)  # note: reversed intentionally


def source_file(target, unit_cfg):
    configurator_root = os.path.abspath(__file__)
    for _ in range(3):
        configurator_root = os.path.dirname(configurator_root)
    fname = os.path.join(configurator_root, target, unit_cfg['source'])
    fname = os.path.expandvars(fname)
    fname = os.path.abspath(fname)
    return fname


def dest_file(unit_cfg):
    fname = os.path.expandvars(unit_cfg['dest'])
    fname = os.path.abspath(fname)
    return fname


def get_target_unit(user_conf, target, subtarget):
    if target not in user_conf['configurations']:
        print('Unknown configuration: "{}"'.format(target))
        exit(1)

    opts = user_conf['configurations'][target]
    if len(opts) == 0:
        print('No configurations for "{}"'.format(target))
        exit(1)

    if len(opts) == 1 and subtarget is None:
        return opts[0]

    names = []
    for opt in opts:
        if 'name' in opt:
            names.append(opt['name'])
        else:
            names.append(opt['source'])

    if subtarget is None:
        for idx, name in enumerate(names):
            print('   {}. {}'.format(idx + 1, name))
        subtarget = input('Which file do you want to edit? [1] ')
        if not subtarget:
            subtarget = '1'

    if subtarget.isdigit():
        subtarget = int(subtarget) - 1
        return opts[subtarget]

    if subtarget in names:
        subtarget = names.index(subtarget)
        return opts[subtarget]

    print('No such file "{}"'.format(subtarget))
    

def get_user_config():
    home_dir = os.getenv('HOME')
    if not home_dir:
        print('Could not find home directory')
        exit(1)

    config_fpath = os.path.join(home_dir, '.config', PROG_NAME, PROG_NAME + '.yaml') 
    if not os.path.isfile(config_fpath):
        print('Could not find configuration file at "{}"'.format(config_fpath))
        exit(1)

    with open(config_fpath, 'r') as in_f:
        try:
            user_config = yaml.safe_load(in_f)
        except yaml.parser.ParserError as e:
            print('Failed to read yaml at "{fname}", line {line} column {column}. Error was: \n\t{error_msg}'.format(
                fname=e.problem_mark.name,
                line=e.problem_mark.line + 1,  # in code, indexed at 0
                column=e.problem_mark.column + 1,
                error_msg=e.problem,
            ))
            exit(1)

    v = cerberus.Validator(user_config_schema)
    if not v.validate(user_config):
        print('Invalid user config. Errors: ')
        print(json.dumps(v.errors, indent=4))
        exit(1)

    return v.document


def cli_args():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='cmd', required=True)

    parser_edit = subparsers.add_parser('edit')
    parser_edit.add_argument('target', help='What config to edit?')
    parser_edit.add_argument('subtarget', nargs='?', help='specifically which file?')

    parser_list = subparsers.add_parser('list')

    parser_help = subparsers.add_parser('help')
    parser_help.set_defaults(help_fn=lambda: parser.print_help())

    parser_which = subparsers.add_parser('which')
    parser_which.add_argument('target', help='What config to find?')
    parser_which.add_argument('subtarget', nargs='?', help='specifically which file?')

    parser_deploy = subparsers.add_parser('deploy')

    parser_gather = subparsers.add_parser('gather')

    return parser.parse_args()


def main():
    user_config = get_user_config()
    args = cli_args()

    if args.cmd == 'edit':
        edit(user_config, args.target, args.subtarget)
    elif args.cmd == 'list':
        list_config(user_config)
    elif args.cmd == 'which':
        which_config(user_config, args.target, args.subtarget)
    elif args.cmd == 'deploy':
        deploy_config(user_config)
    elif args.cmd == 'gather':
        gather_config(user_config)
    elif args.cmd == 'help':
        args.help_fn()
    

if __name__ == '__main__':
    main()
