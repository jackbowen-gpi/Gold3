"""Noise generation for tiffs."""

import math
import os
import shutil

from django.conf import settings
from PIL import Image


def apply_flexo_noise(tiff_path, noise_mode, saving_path, dest_path):
    """
    tiff_path: (str) Full path to the tiff to apply noise to.
    noise_mode: (str) Either 'heavy' or 'light. Applies different noise tiffs.
    saving_path: (str) The full path to where the tiff with noise should
                       be saved to. This is not the final path for the tiff,
                       it is merely placed here while it's in the process of
                       being saved/written to disk. This prevents Backstage
                       from picking the file up prematurely before it's done.
    dest_path: (str) The final destination path for the tiff with noise.
                     It is moved here after it finishes saving in
                     the saving_path, where Backstage picks it up.
    """
    im = Image.open(tiff_path)
    # print "--> Format/dims/mode:",im.format, im.size, im.mode
    # print "Colors", im.getcolors()

    if noise_mode == "heavy":
        noise_tiff = "noise_hot_inverted.tif"
    else:
        noise_tiff = "noise_not_hot_inverted.tif"

    noise_tiff_path = os.path.join(
        settings.MAIN_PATH, "apps", "noise_generator", "noise_tiffs", noise_tiff
    )
    noise = Image.open(noise_tiff_path)
    # print noise.format, noise.size, noise.mode

    horiz_steps = int(math.ceil(float(im.size[0]) / noise.size[0]))
    vert_steps = int(math.ceil(float(im.size[1]) / noise.size[1]))

    # print horiz_steps, vert_steps

    for vert_step in range(0, vert_steps):
        for horiz_step in range(0, horiz_steps):
            top_x = horiz_step * noise.size[0]
            top_y = vert_step * noise.size[1]
            im.paste(noise, box=(top_x, top_y), mask=noise)

    im.save(saving_path)
    shutil.move(saving_path, dest_path)
    # im.show()
