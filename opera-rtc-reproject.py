import argparse
import os
import tempfile

import harmony
import pystac
from osgeo import gdal


gdal.UseExceptions()


class ExampleAdapter(harmony.BaseHarmonyAdapter):

    def process_item(self, item: pystac.Item, source: harmony.message.Source) -> pystac.Item:
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
        self.logger.debug(f'Processing item {item.id}')
        crs = self.message.format.process('crs')

        result = item.clone()
        result.assets = {}

        for key, asset in item.assets.items():
            if 'data' in (asset.roles or []) and asset.href.endswith('tif'):
                self.logger.debug(f'Reprojecting {asset.title} to {crs}')

                with tempfile.TemporaryDirectory() as temp_dir:
                    input_filename = harmony.util.download(
                        url=asset.href,
                        destination_dir=temp_dir,
                        logger=self.logger,
                        access_token=self.message.accessToken,
                    )

                    # TODO: Investigate proper way of generating filename. Look into `generate_output_filename` in harmony-service-lib-py.
                    output_filename = os.path.splitext(os.path.basename(asset.title))[0] + '_reprojected.tif'
                    gdal.Warp(
                        destNameOrDestDS=f'{temp_dir}/{output_filename}',
                        srcDSOrSrcDSTab=input_filename,
                        dstSRS=crs,
                        format='COG',
                        multithread=True,
                        creationOptions=['NUM_THREADS=all_cpus'],
                    )
                    url = harmony.util.stage(
                        local_filename=f'{temp_dir}/{output_filename}',
                        remote_filename=output_filename,
                        mime='image/tiff',
                        location=self.message.stagingLocation,
                        logger=self.logger,
                    )

                result.assets[key] = pystac.Asset(url, title=output_filename, media_type='image/tiff', roles=['data'])

        return result


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

    if harmony.is_harmony_cli(args):
        harmony.run_cli(parser, args, ExampleAdapter)
    else:
        run_cli(args)


if __name__ == "__main__":
    main()
