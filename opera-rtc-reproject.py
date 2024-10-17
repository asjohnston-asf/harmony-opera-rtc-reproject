import argparse
import tempfile
from pathlib import Path

import harmony
import numpy as np
import pystac
from osgeo import gdal


gdal.UseExceptions()


def normalize_image_array(
    input_array: np.ndarray, vmin: float | None = None, vmax: float | None = None
) -> np.ndarray:
    """Function to normalize a browse image band.
    Modified from OPERA-ADT/RTC.

    Args:
        input_array: The array to normalize.
        vmin: The minimum value to normalize to.
        vmax: The maximum value to normalize to.

    Returns
        The normalized array.
    """
    input_array = input_array.astype(float)

    if vmin is None:
        vmin = np.nanpercentile(input_array, 3)

    if vmax is None:
        vmax = np.nanpercentile(input_array, 97)

    # gamma correction: 0.5
    is_not_negative = input_array - vmin >= 0
    is_negative = input_array - vmin < 0
    input_array[is_not_negative] = np.sqrt((input_array[is_not_negative] - vmin) / (vmax - vmin))
    input_array[is_negative] = 0
    input_array[np.isnan(input_array)] = 0
    normalized_array = np.round(np.clip(input_array, 0, 1) * 255).astype(np.uint8)
    return normalized_array


def create_browse_array(co_pol_array: np.ndarray, cross_pol_array: np.ndarray) -> np.ndarray:
    """Create a browse image array for an OPERA S1 RTC granule.
    Bands are normalized and follow the format: [co-pol, cross-pol, co-pol, no-data].

    Args:
        co_pol_array: Co-pol image array.
        cross_pol_array: Cross-pol image array.

    Returns:
       Browse image array.
    """
    co_pol_nodata = ~np.isnan(co_pol_array)
    co_pol = normalize_image_array(co_pol_array, 0, 0.15)

    cross_pol_nodata = ~np.isnan(cross_pol_array)
    cross_pol = normalize_image_array(cross_pol_array, 0, 0.025)

    no_data = (np.logical_and(co_pol_nodata, cross_pol_nodata) * 255).astype(np.uint8)
    browse_image = np.stack([co_pol, cross_pol, co_pol, no_data], axis=-1)
    return browse_image


def create_browse_image(co_pol_path: Path, cross_pol_path: Path, working_dir: Path) -> Path:
    """Create a browse image for an OPERA S1 RTC granule meeting GIBS requirements.

    Args:
        co_pol_path: Path to the co-pol image.
        cross_pol_path: Path to the cross-pol image.
        working_dir: Working directory to store intermediate files.

    Returns:
        Path to the created browse image.
    """
    co_pol_ds = gdal.Open(str(co_pol_path))
    co_pol = co_pol_ds.GetRasterBand(1).ReadAsArray()

    cross_pol_ds = gdal.Open(str(cross_pol_path))
    cross_pol = cross_pol_ds.GetRasterBand(1).ReadAsArray()

    browse_array = create_browse_array(co_pol, cross_pol)

    browse_path = working_dir / f'{co_pol_path.stem[:-3]}_rgb.tif'
    driver = gdal.GetDriverByName('GTiff')
    browse_ds = driver.Create(str(browse_path), browse_array.shape[1], browse_array.shape[0], 4, gdal.GDT_Byte)
    browse_ds.SetGeoTransform(co_pol_ds.GetGeoTransform())
    browse_ds.SetProjection(co_pol_ds.GetProjection())
    for i in range(4):
        browse_ds.GetRasterBand(i + 1).WriteArray(browse_array[:, :, i])

    co_pol_ds = None
    cross_pol_ds = None
    browse_ds = None

    return browse_path


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
        self.logger.info(f'Processing item {item.id}')

        with tempfile.TemporaryDirectory() as temp_dir:

            for asset in item.assets.values():
                if 'data' in (asset.roles or []) and asset.href.endswith('VV.tif'):
                    co_pol_filename = harmony.util.download(
                        url=asset.href,
                        destination_dir=temp_dir,
                        logger=self.logger,
                        access_token=self.message.accessToken,
                    )
                if 'data' in (asset.roles or []) and asset.href.endswith('VH.tif'):
                    cross_pol_filename = harmony.util.download(
                        url=asset.href,
                        destination_dir=temp_dir,
                        logger=self.logger,
                        access_token=self.message.accessToken,
                    )

            rgb_path = create_browse_image(Path(co_pol_filename), Path(cross_pol_filename), Path(temp_dir))
            url = harmony.util.stage(
                local_filename=str(rgb_path),
                remote_filename=rgb_path.stem,
                mime='image/tiff',
                location=self.message.stagingLocation,
                logger=self.logger,
            )

            result = item.clone()
            result.assets = {
                'rgb_browse': pystac.Asset(url, title=rgb_path.stem, media_type='image/tiff', roles=['visual'])
            }

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
