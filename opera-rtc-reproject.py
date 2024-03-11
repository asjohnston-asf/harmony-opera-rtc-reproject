import argparse
import shutil
import os
import requests
from tempfile import mkdtemp
import pystac
from pystac import Asset
from osgeo import gdal

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

        try:
            # Get the data file
            asset = next(v for k, v in item.assets.items() if 'data' in (v.roles or []))

            url = asset.href
            if url.startswith('https://datapool-test.asf.alaska.edu/'):
                response = requests.get(url, allow_redirects=False)
                assert response.status_code == 307
                asset.href = response.headers['Location']

            input_filename = download(asset.href, '.', logger=self.logger, access_token=self.message.accessToken)

            crs = self.message.format.process('crs')

            print(f'Processing item {item.id}')

            # Stage the output file with a conventional filename
            output_filename = os.path.splitext(os.path.basename(input_filename))[0] + '_reprojected.tif'
            gdal.Warp(output_filename, input_filename, dstSRS=crs, format='COG', multithread=True, creationOptions=['NUM_THREADS=all_cpus'])
            url = stage(output_filename, output_filename, 'image/tiff', location=self.message.stagingLocation,
                        logger=self.logger)

            # Update the STAC record
            result.assets['data'] = Asset(url, title=output_filename, media_type='image/tiff', roles=['data'])
            # Other metadata updates may be appropriate, such as result.bbox and result.geometry
            # if a spatial subset was performed

            # Return the STAC record
            return result
        finally:
            # Clean up any intermediate resources
            pass


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
