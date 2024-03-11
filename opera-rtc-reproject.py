import argparse

import harmony
import pystac
from harmony.util import stage

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

        filename = 'cat.jpg'
        mimetype = 'image/jpeg'
        url = stage(filename, filename, mime=mimetype, location=self.message.stagingLocation, logger=self.logger)
        result.assets['data'] = pystac.Asset(url, title=filename, media_type=mimetype, roles=['data'])
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

    if (harmony.is_harmony_cli(args)):
        harmony.run_cli(parser, args, ExampleAdapter)
    else:
        run_cli(args)


if __name__ == "__main__":
    main()
