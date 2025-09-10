"""Calculate the name of the tiff_to_pdf binary for this platform.

This module's sole purpose is to calculate the name of the binary for
tiff_to_pdf when compiling or attempting to run via Popen in GOLD.

Utility used by our build/runtime helpers to determine the tiff_to_pdf binary
name based on platform uname information.
"""

import os


def tiff_to_pdf_bin():
    """Return the expected tiff_to_pdf binary name for the current platform.

    The binary name is constructed from members of os.uname() including the
    kernel version and architecture.
    """
    uname = os.uname()  # type: ignore[attr-defined]
    # Just the kernel version.
    major_kernel = uname[2]
    # Split by the dot number scheme that most follow.
    major_kernel_split = major_kernel.split(".")
    if len(major_kernel_split) >= 3:
        # Looks like a major.minor.patch scheme. Let's just concern
        # ourselves with major and minor.
        major_kernel = ".".join(major_kernel_split[0:2])
    # Form the binary name.
    bin_name = "tiff_to_pdf_%s_%s_%s" % (uname[0], uname[4], major_kernel)
    return bin_name


if __name__ == "__main__":
    # Run this module directly if you'd like to test output.
    print((tiff_to_pdf_bin()))
