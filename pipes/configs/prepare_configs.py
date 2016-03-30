"""Prepare the Application Configurations."""
import json
import logging
import os

LOG = logging.getLogger(__name__)


def process_configs(runway_dir='', out_file=''):
    """Read the _application.json_ files.

    Args:
        runway_dir (str): Name of runway directory with app.json files.
        out_file (str): Name of INI file to append to.

    Returns:
        True upon successful completion.
    """
    with open(out_file, 'at') as jenkins_vars:
        for env in ('dev', 'stage', 'prod'):
            file_name = os.path.join(runway_dir,
                                     'application-master-{env}.json'.format(
                                         env=env))
            LOG.debug('File to read: %s', file_name)

            try:
                with open(file_name, 'rt') as json_file:
                    configs = json.load(json_file)
                LOG.debug('Application configs:\n%s', configs)
            except FileNotFoundError:
                continue

            for resource, app_properties in sorted(configs.items()):
                try:
                    for app_property, value in sorted(app_properties.items()):
                        variable = '{env}_{resource}_{app_property}'.format(
                            env=env,
                            resource=resource,
                            app_property=app_property).upper()
                        line = '{variable}={value}'.format(
                            variable=variable,
                            value=json.dumps(value))

                        LOG.debug('INI line: %s', line)

                        jenkins_vars.write('{0}\n'.format(line))
                except AttributeError:
                    continue

    return True
