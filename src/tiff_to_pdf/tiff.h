#ifndef TIFF_H
#define TIFF_H

#include <string>
#include <vector>
#include <tiffio.h>
#include <cmath>

// Notes:
// This class can only read 1bit strip based tiffs.
// Resolution in this context means dots per unit.

class Tiff{
    public:
        Tiff():
			tiff(NULL),
			pixels(NULL),
			x(0),
			y(0),
			scanlineSize(0),
			stripSize(0),
			numberOfStrips(0),
			rowsPerStrip(0),
			resolutionUnit(INCHES),
			xResolution(0),
			yResolution(0),
			zeroWhite(true)
		{}
		~Tiff();
        // load tiff, returns true on success
        bool load(const std::string &file);
        // scale the whole image to x, y, in pixels and keep same resolution
        unsigned char* scale(unsigned int x,unsigned int y);
        // gets all pixels in 1bit b/w format, can be pretty big
		// returns number of bytes read, buffer is actually numberOfStrips*stripSize,
		// which is greater than or equal to what is returned
        unsigned int getPixels(unsigned char*& data);
        // return pixels in 8bit grayscale format from a rectangle at x1, y1 (top left) and
		// x2, y2 (bottom right) scaled to size x, y
		// Note: This can use alot of memory if you aren't carefull.
        unsigned char* getPixels(const unsigned int x1, const unsigned int y1,
								const unsigned int x2, const unsigned int y2,
								unsigned int x, unsigned int y);
		// returns percentage of ink coverage in the selected rectangle
		// x1, y1 (top left), x2, y2 (bottom right)
		// top left hand corner pixel is 0,0
		float sample(const unsigned int x1, const unsigned int y1,
					const unsigned int x2, const unsigned int y2);

		// returns x/y
		float getAspectRatio();
		unsigned int getX();
		unsigned int getY();
		float getXResolution();
		float getYResolution();
		unsigned int getStripSize();
		unsigned int getRowsPerStrip();
		// returns true if resolution is inches
		bool isInches();
		// returns true if 0 is white
		bool isZeroWhite();
    private:
		// returns true if x is within +/- delta of y
		bool isEqual(const float &x, const float &y, const float &delta);
		int clamp(int i, int low, int high);
        enum ResolutionUnit{
            INCHES,
            CENTIMETERS
        };
        TIFF* tiff;
        unsigned char* pixels;
        unsigned int x; // width
        unsigned int y; // height
        unsigned int scanlineSize;
        unsigned int stripSize;
        unsigned int numberOfStrips;
        unsigned int rowsPerStrip;
        ResolutionUnit resolutionUnit;
        float xResolution;
        float yResolution;
        bool zeroWhite; // true if zero is white

		// Below is some static stuff used to speed up the scaling of multiple tiffs
		static unsigned int oneBitsInChar[256]; // precomputed bits set to 1 in a 8bit char
		struct BitTableInitialiser{ // struct that is used to precompute the bit table before it is used
			BitTableInitialiser(unsigned int* bitTable); // the constructor
		};
		static BitTableInitialiser init; // the actual object to precompute the bit table
};
#endif
