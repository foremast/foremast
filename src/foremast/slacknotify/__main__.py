#   Foremast - Pipeline Tooling
#
#   Copyright 2018 Gogo, LLC
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
"""CLI entry point for sending Slack notifications.

Help: ``python -m src.foremast.slacknotify -h``
"""
import argparse
import logging

from ..args import add_app, add_debug, add_env, add_properties
from ..consts import LOGGING_FORMAT
from .slack_notification import SlackNotification


def main():
    """Send Slack notification to a configured channel."""
    logging.basicConfig(format=LOGGING_FORMAT)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    add_debug(parser)
    add_app(parser)
    add_env(parser)
    add_properties(parser)

    args = parser.parse_args()

    logging.getLogger(__package__.split(".")[0]).setLevel(args.debug)
    log.debug('Parsed arguements: %s', args)

    if "prod" not in args.env:
        log.info('No slack message sent, not a production environment')
    else:
        log.info("Sending slack message, production environment")
        slacknotify = SlackNotification(app=args.app, env=args.env, prop_path=args.properties)
        slacknotify.post_message()


if __name__ == "__main__":
    main()
