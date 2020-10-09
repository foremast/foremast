import argparse
import logging

from ..args import add_app, add_debug, add_env, add_properties, add_region
from ..consts import LOGGING_FORMAT
from .awsglue import GlueJob


def main():
    """Create Glue Job"""
    logging.basicConfig(format=LOGGING_FORMAT)
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description=main.__doc__)
    add_debug(parser)
    add_app(parser)
    add_env(parser)
    add_properties(parser)
    add_region(parser)
    args = parser.parse_args()

    logging.getLogger(__package__.split('.')[0]).setLevel(args.debug)

    log.debug('Parsed arguments: %s', args)

    glue_job = GlueJob(app=args.app, env=args.env, region=args.region, prop_path=args.properties)

    glue_job.create_glue_job()

if __name__ == "__main__":
    main()
