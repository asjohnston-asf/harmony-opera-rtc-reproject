import argparse
import shutil
import os
import requests
from tempfile import mkdtemp
from pystac import Asset

import harmony
from harmony.util import generate_output_filename, stage, download


class ExampleAdapter(harmony.BaseHarmonyAdapter):

    def process_item(self, item: pystac.Item, source) -> pystac.Item:
        """
        Processes a single input item.

        Parameters
        ----------
        item : pystac.Item
            the item that should be processed
        source : harmony.message.Source
            the input source defining the variables, if any, to subset from the item

        Returns
        -------
        pystac.Item
            a STAC catalog whose metadata and assets describe the service output
        """

        result = item.clone()
        result.assets = {}

        # Create a temporary dir for processing we may do
        workdir = mkdtemp()
        try:
            # Get the data file
            asset = next(v for k, v in item.assets.items() if 'data' in (v.roles or []))

            url = asset.href
            if url.startswith('https://datapool-test.asf.alaska.edu/'):
                response = requests.get(url, allow_redirects=False)
                assert response.status_code == 307
                asset.href = response.headers['Location']

            input_filename = download(asset.href, workdir, logger=self.logger, access_token=self.message.accessToken)

            # # Mark any fields the service processes so later services do not repeat work
            # dpi = self.message.format.process('dpi')
            # # Variable subsetting
            # variables = source.process('variables')

            # # Do the work here!
            # var_names = [v.name for v in variables]
            print(f'Processing item {item.id}')
            # working_filename = os.path.join(workdir, 'tmp.txt')
            # shutil.copyfile(input_filename, working_filename)

            # Stage the output file with a conventional filename
            output_filename = generate_output_filename(asset.href, ext=None, variable_subset=None,
                                                       is_regridded=False, is_subsetted=False)
            url = stage(input_filename, output_filename, 'image/tiff', location=self.message.stagingLocation,
                        logger=self.logger)

            # Update the STAC record
            result.assets['data'] = Asset(url, title=output_filename, media_type='image/tiff', roles=['data'])
            # Other metadata updates may be appropriate, such as result.bbox and result.geometry
            # if a spatial subset was performed

            # Return the STAC record
            return result
        finally:
            # Clean up any intermediate resources
            shutil.rmtree(workdir)


def run_cli(args):
    """
    Runs the CLI.  Presently stubbed to demonstrate how a non-Harmony CLI fits in and allow
    future implementation or removal if desired.

    Parameters
    ----------
    args : Namespace
        Argument values parsed from the command line, presumably via ArgumentParser.parse_args

    Returns
    -------
    None
    """
    print("TODO: You can implement a non-Harmony CLI here.")
    print('To see the Harmony CLI, pass `--harmony-action=invoke '
          '--harmony-input="$(cat example/example_message.json)" '
          '--harmony-sources=example/source/catalog.json --harmony-output-dir=tmp/`')



def main():
    """
    Parses command line arguments and invokes the appropriate method to respond to them

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(prog='example', description='Run an example service')

    harmony.setup_cli(parser)

    args = parser.parse_args()

    if (harmony.is_harmony_cli(args)):
        harmony.run_cli(parser, args, ExampleAdapter)
    else:
        run_cli(args)


if __name__ == "__main__":
    main()
