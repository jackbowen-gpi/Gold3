Missing font used by auto-corrugated PDF generation

Some parts of the auto-corrugated PDF generation expect the VAG Rounded BT TrueType
font to be present under the CORRUGATED_MEDIA_DIR (production path). If the font is
missing you'll see a runtime message similar to:

    Font file not found at: /mnt/Production/autocorr_elements/VAG Rounded BT.ttf

To install the font locally for development:

1. Obtain 'VAG Rounded BT.ttf' from your design assets or licensed font source.
2. Create the autocorr elements directory referenced by your settings, for example:

   On Windows PowerShell (from project root):

       mkdir -Force "C:\path\to\production\autocorr_elements"

   Or on Unix-like systems:

       mkdir -p /mnt/Production/autocorr_elements

3. Copy the TTF file into that directory and ensure Django can read it.

4. Restart the devserver and re-run the health check:

    python scripts/health_check.py

The code now guards font registration and will print the exact path it tried, which
helps troubleshooting when running in different environments.
