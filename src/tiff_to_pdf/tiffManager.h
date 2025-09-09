#ifndef TIFFMANAGER_H
#define TIFFMANAGER_H

#include <string>
#include <vector>
#include "tiff.h"
#include "singleton.h"

class TiffManager{
    public:
        TiffManager(){};
        ~TiffManager();
		// file is the file to be added, and filename is what TiffManager will call it
        bool addTiff(const std::string &file, const std::string &filename);
        // delete tiff at i, start at 0
        bool deleteTiff(unsigned int i);
		// delete all tiffs
		bool deleteTiffs();
		// scales one tiff, returns a pointer to the scaled image
		unsigned char* scale(unsigned int x, unsigned int y, unsigned int i);
		// scales all tiffs, returns an array of pointers that point to the scaled images
		unsigned char** scale(unsigned int x, unsigned int y);
		// return a pointer that points to pixels from tiff "i" in 8bit grayscale format
		// of a region defined by x1,y1 and x2,y2 scaled to size x, y
		// Note: This can use alot of memory if you aren't carefull.
        unsigned char* getPixels(int x1, int y1,
								int x2, int y2,
								int x, int y,
								unsigned int i);
        // combines all the active tiffs into one tiff and returns a pointer to it
		// using dpi to scale the image to whatever size needed
        unsigned char* composite(const unsigned int dpi);
		// returns what percent of region defined by x1,y1 and x2,y2 is colored
		float sample(const unsigned int x1, const unsigned int y1,
					const unsigned int x2, const unsigned int y2, unsigned int i);
		// returns x/y of tiff at i
		float aspectRatio(unsigned int i);
		// returns a pointer to rgb data 3 bytes long, you must free it
		unsigned char* getColor(unsigned int i);
		// sets color by copying 3 bytes over to color
		void setColor(unsigned int i, unsigned char* color);
		// returns the number of tiffs
		unsigned int size();
		unsigned int getWidth(unsigned int i = 0);
		unsigned int getHeight(unsigned int i = 0);
		unsigned int getMaxWidth();
		unsigned int getMaxHeight();
		float getXResolution(unsigned int i = 0);
		float getYResolution(unsigned int i = 0);
		std::string getFilename(unsigned int i);
		// returns true if resolution is inches
		bool isInches(unsigned int i = 0);
		// returns true if active
		bool isActive(unsigned int i);
		void setActive(unsigned int i, bool status);
    private:
        struct TiffInfo{
            Tiff* tiff;
			std::string filename;
            bool active; // composite will only use active tiffs
            unsigned char color[4]; // 8bit rgba
        };
        std::vector<TiffInfo*> tiffs;
};

typedef Singleton<TiffManager> TiffManagerSingleton;

#endif
