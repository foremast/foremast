#   Foremast - Pipeline Tooling
#
#   Copyright 2016 Gogo, LLC
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

"""Generate various filenames."""


def generate_packer_filename(provider, region, builder):
    """Generate a filename to be used by packer.

    Args:
        provider (str): Name of Spinnaker provider.
        region (str): Name of provider region to use.
        builder (str): Name of builder process type.

    Returns:
        str: Generated filename based on parameters.
    """
    filename = '{0}_{1}_{2}.json'.format(provider, region, builder)
    return filename
