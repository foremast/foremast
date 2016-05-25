import argparse
import logging

from ..consts import LOGGING_FORMAT
from ..args import add_app, add_debug, add_properties, add_env
from .slack_notification import SlackNotification

def main():
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


    info = { 'env': args.env,
             'app': args.app 
           }

    if "prod" not in info['env']:
        log.info('No slack message sent, not a production environment')
    else:
        log.info("Sending slack message, production environment")
        slacknotify = SlackNotification(info=info)


if __name__ == "__main__":
    main()
