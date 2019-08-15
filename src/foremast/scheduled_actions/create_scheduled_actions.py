#   Foremast - Pipeline Tooling
#
#   Copyright 2019 Redbox Automated Retail, LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""Manages AWS ASG Scheduled Actions in Spinnaker. Can find, create, and delete.
"""
import logging
import os

from ..utils import get_latest_server_group, get_properties, get_template, wait_for_task


class ScheduledActions:
    """Manages scheduled actions in Spinnaker

    Args:
        app (str): Application name
        prop_path (str): Path of rendered property files
        env (str): Environment/Account to add scheduled actions to
        region (str): AWS region for scheduled actions

    Attributes:
        log (str): Logger name
        settings (dict): Properties imported from prop_path
    """

    def __init__(self, app='', prop_path='', env='', region=''):

        self.log = logging.getLogger(__name__)

        self.here = os.path.dirname(os.path.realpath(__file__))
        self.env = env
        self.region = region
        self.app = app

        self.settings = get_properties(properties_file=prop_path, env=self.env, region=self.region)

    def prepare_scheduled_actions_template(self, scheduled_actions, server_group):
        """Renders scheduled actions templates based on configs and variables.
        After rendering, POSTs the json to Spinnaker for creation.

        Args:
            server_group (str): The name of the server group to render template for
        """
        template_kwargs = {
            'app': self.app,
            'env': self.env,
            'region': self.region,
            'server_group': server_group,
            'scheduled_actions': scheduled_actions
        }

        rendered_template = get_template(template_file='infrastructure/scheduled_actions.json.j2', **template_kwargs)
        self.log.info('Creating scheduled actions in %s for %s', self.env, self.app)
        wait_for_task(rendered_template)
        self.log.info('Successfully created scheduled actions in %s for %s', self.env, self.app)

    def create_scheduled_actions(self):
        """Wrapper function. Gets the latest server group and then runs
        self.prepare_scheduled_actions_template for scheduled actions. This
        function acts as the main driver for the scheduled actions creation.
        """
        if not self.settings['asg']['scheduled_actions']:
            self.log.info("No scheduled actions found, skipping...")
            return

        server_group = get_latest_server_group(self.env, self.app)
        scheduled_actions = self.settings['asg']['scheduled_actions']
        self.prepare_scheduled_actions_template(scheduled_actions, server_group)
