#include "tiff.h"
#include <iostream>
#include <string.h>
#include <stdlib.h>
#include <map>
#include <sstream>
#include <algorithm>
#include <vector>

unsigned int Tiff::oneBitsInChar[256];
Tiff::BitTableInitialiser Tiff::init(Tiff::oneBitsInChar);
inline Tiff::BitTableInitialiser::BitTableInitialiser(unsigned int* bitTable){
	for(unsigned int i=0; i<256; ++i){
		int count=0;
		unsigned int j = i;
		while(j){
			count += j & 0x1;
			j >>= 1;
		}
		bitTable[i] = count;
	}
}

Tiff::~Tiff(){
	if(tiff) TIFFClose(tiff);
	if(pixels) delete pixels;
}

bool Tiff::load(const std::string &file){
    tiff = TIFFOpen(file.c_str(), "r");
    if(!tiff) return false;
    TIFFGetField(tiff, TIFFTAG_IMAGELENGTH, &y);
    TIFFGetField(tiff, TIFFTAG_IMAGEWIDTH, &x);
    TIFFGetField(tiff, TIFFTAG_YRESOLUTION, &yResolution);
    TIFFGetField(tiff, TIFFTAG_XRESOLUTION, &xResolution);
    TIFFGetField(tiff, TIFFTAG_ROWSPERSTRIP, &rowsPerStrip);
	unsigned short unit;
    TIFFGetField(tiff, TIFFTAG_RESOLUTIONUNIT, &unit);
    if(unit == RESUNIT_CENTIMETER) resolutionUnit = CENTIMETERS;
    else resolutionUnit = INCHES;  // if RESUNIT_NONE assume inches
    scanlineSize = TIFFScanlineSize(tiff);
    stripSize = TIFFStripSize(tiff);
    numberOfStrips = TIFFNumberOfStrips(tiff);

	// Esko does not set the flag correctly.  It is always set to min-is-white.
    /*unsigned short photometric;
    TIFFGetField(tiff, TIFFTAG_PHOTOMETRIC, &photometric);
    if(photometric == PHOTOMETRIC_MINISBLACK) zeroWhite = false;
    else zeroWhite = true;*/
	// So we base zeroWhite off the top left hand pixel which should always be white for our tiffs
	unsigned char* data = static_cast<unsigned char*>(_TIFFmalloc(scanlineSize));
	TIFFReadScanline(tiff, data, 0);
	if((data[0] & 0x80) == 0x80) zeroWhite = false;
	else zeroWhite = true;

    return true;
}

unsigned char* Tiff::scale(unsigned int x, unsigned int y){
	// testing
	return getPixels(0,0,Tiff::x-1,Tiff::y-1,x,y);

	// check to see if a tiff is loaded
	if(!tiff) return NULL;

	// scale and convert to 8bit gray scale

/*	unsigned int oneBitsInChar[256];
	for(unsigned int i=0; i<256; ++i){
		int count=0;
		unsigned int j = i;
		while(j){
			count += j & 0x1;
			j >>= 1;
		}
		oneBitsInChar[i] = count;
	}
*/
	// precompute blockX
	unsigned int blockX[x];
	unsigned int incHX = Tiff::x/x;
	unsigned int incLX = Tiff::x-(incHX*x);
	unsigned int accumX = 0;
	for(unsigned int i=0; i<x; ++i){
		accumX += incLX;
		if(accumX >= x) {accumX -= x; blockX[i] = incHX+1;}
		else blockX[i] = incHX;
	}

	// precompute mask
	unsigned char leadingMask[x+1]; // precomputed masks for partial bytes to be counted
	memset(leadingMask, 0, x+1); // init leadingMask
	unsigned char trailingMask[x];
	unsigned int wholeBytes[x]; // number of whole bytes
	memset(wholeBytes, 0, x*sizeof(unsigned int)); // init wholeBytes
	short int leadingBits = 0;
	short int trailingBits = 0;
	unsigned int blockXTmp = 0;
	for(unsigned int i=0; i<x; ++i){
		blockXTmp = blockX[i];
		blockXTmp -= leadingBits;
		while(blockXTmp>7){
			wholeBytes[i]++;
			blockXTmp-=8;
		}
		trailingBits = blockXTmp;
		leadingBits = 8 - trailingBits;
		if(leadingBits == 8) leadingBits = 0;
		leadingMask[i+1] = (unsigned char)pow(2,leadingBits)-1;
		trailingMask[i] = (unsigned char)pow(2,trailingBits)-1;
		trailingMask[i] <<= 8 - trailingBits;
	}

	unsigned int numberOfOnes[x]; // only holds one row
	unsigned char* scaledImage = new unsigned char[x*y];
	unsigned char* data = static_cast<unsigned char*>(_TIFFmalloc(scanlineSize));
	unsigned char* tmpData;

	unsigned int incHY = Tiff::y/y;
	unsigned int incLY = Tiff::y-(incHY*y);
	unsigned int accumY = 0;
	unsigned int blockY = 0; // contains the number of rows in orig image that make up 1 row in scaled image
	unsigned int row = 0; // row index into original tiff

	// start box filter (average pixels) using bitcounting
	// loop though rows of scaled image
	for(unsigned int i=0; i<y; ++i) {
		accumY += incLY;
		if(accumY >= y) {
		    accumY -= y;
		    blockY = incHY+1;
		}
		else
		    blockY = incHY;

		memset(numberOfOnes, 0, x*sizeof(unsigned int));
		for(unsigned int count=0; count<blockY; ++count, ++row) { // count the bits that will make up one row in scaled image
			TIFFReadScanline(tiff, data, row);
			tmpData = data;
			for(unsigned int j=0; j<x; ++j){ // count the bits and store them
				if(leadingMask[j]){
					 numberOfOnes[j] += oneBitsInChar[*tmpData++ & leadingMask[j]];
				}
				// switch statment handles groups of bytes to run faster
				switch(wholeBytes[j]){
					// default handles whole bytes over the largest case, should be rare
					default:
					    for(unsigned int tmp=0; tmp<wholeBytes[j]; ++tmp)
					        numberOfOnes[j] += oneBitsInChar[*tmpData++];
					    break;
					case 4:
					    numberOfOnes[j] += oneBitsInChar[*tmpData++] + oneBitsInChar[*tmpData++] + oneBitsInChar[*tmpData++] + oneBitsInChar[*tmpData++];
					    break;
					case 3:
					    numberOfOnes[j] += oneBitsInChar[*tmpData++] + oneBitsInChar[*tmpData++] + oneBitsInChar[*tmpData++];
					    break;
					case 2:
					    numberOfOnes[j] += oneBitsInChar[*tmpData++] + oneBitsInChar[*tmpData++];
					    break;
					case 1:
					    numberOfOnes[j] += oneBitsInChar[*tmpData++];
					    break;
				}
				if(trailingMask[j]){
					numberOfOnes[j] += oneBitsInChar[*tmpData & trailingMask[j]];
				}
			}
		} // finished counting the bits that will make up one row in scaled image
		// convert to grayscale
		// note: this is inverted so I can make it the correct color later ie. image * color = final image
		for(unsigned int j=0; j<x; ++j){
			// "255 -" is what inverts scaledImage
			if(zeroWhite)
				scaledImage[j+(i*x)] = static_cast<unsigned char>((static_cast<float>(numberOfOnes[j])/(blockY*blockX[j])) * 255);
			else
				scaledImage[j+(i*x)] = static_cast<unsigned char>((255-(static_cast<float>(numberOfOnes[j])/(blockY*blockX[j])) * 255));
			// >= threshold color it, < threshold make it white
			//if(scaledImage[j+(i*x)] >= 0x80) scaledImage[j+(i*x)] = 0xff;
			//else scaledImage[j+(i*x)] = 0x0;
		}
	}

	_TIFFfree(data);

	return scaledImage;
}

unsigned int Tiff::getPixels(unsigned char*& data){
    // check to see if a tiff is loaded
    if(!tiff) return 0;
    // read by strip, alittle faster than reading by scanline
    data = static_cast<unsigned char*>(_TIFFmalloc(stripSize * numberOfStrips));
	if(!data) return 0;
    unsigned char* tmp = data;
	unsigned int bytesRead, totalBytesRead=0;
    for(unsigned int strip=0; strip<numberOfStrips; ++strip){
        bytesRead = TIFFReadEncodedStrip(tiff, strip, tmp, -1);
        tmp += bytesRead;
		totalBytesRead += bytesRead;
    }
	return totalBytesRead;
}

unsigned char* Tiff::getPixels(const unsigned int x1, const unsigned int y1,
								const unsigned int x2, const unsigned int y2,
                                unsigned int x, unsigned int y){
	// check to see if a tiff is loaded
	if(!tiff) return NULL;

	// scale and convert to 8bit gray scale

/*	unsigned int oneBitsInChar[256];
	for(unsigned int i=0; i<256; ++i){
		int count=0;
		unsigned int j = i;
		while(j){
			count += j & 0x1;
			j >>= 1;
		}
		oneBitsInChar[i] = count;
	}
*/
	// precompute blockX (the number of bits in X direction that make up one pixel in the scaled image)
	unsigned int blockX[x];
	unsigned int incHX;
	unsigned int incLX;
	if(x2-x1+1 <= x){ // make it a 1 to 1 pixel mapping from image to scaled image
		incHX = 1;
		incLX = 0;
	}else{
		incHX = (x2-x1+1)/x;
		incLX = (x2-x1+1)-(incHX*x);
	}
	unsigned int accumX = 0;
	for(unsigned int i=0; i<x; ++i){
		accumX += incLX;
		if(accumX >= x) {accumX -= x; blockX[i] = incHX+1;}
		else blockX[i] = incHX;
	}

#ifdef DEBUG
	std::cerr<<"x1: "<<x1<<" y1: "<<y1<<" x2: "<<x2<<" y2: "<<y2<<" x: "<<x<<" y: "<<y<<std::endl;
	std::cerr<<"incHX: "<<incHX<<" incLX: "<<incLX<<std::endl;
	std::cerr<<"blockX:";
	int totalBlockX = 0;
	for(unsigned int i=0; i<x; ++i){
		std::cerr<<" "<<blockX[i];
		totalBlockX += blockX[i];
	}
	std::cerr<<std::endl;
	std::cerr<<"total number of blockX's: "<<totalBlockX<<std::endl;
#endif

	// precompute mask
	unsigned char leadingMask[x]; // precomputed masks for the beginning partial bytes
	memset(leadingMask, 0, x); // init leadingMask
	unsigned char trailingMask[x]; // precomputed masks for the last partial bytes
	memset(trailingMask, 0, x); // init trailingMask
	unsigned int wholeBytes[x]; // number of whole bytes
	memset(wholeBytes, 0, x*sizeof(unsigned int)); // init wholeBytes
	short int leadingBits = x1%8; // find out how many leading bits (bits in first byte) we could need
	if(leadingBits == 0) leadingBits = 8;
	short int trailingBits = 0; // trailing bits (bits in the last byte) that are used for the current blockX
	unsigned int blockXTmp = 0;
	unsigned int remainingBits = leadingBits; // number of bits in current byte not used
	for(unsigned int i=0; i<x; ++i){
		leadingBits = std::min(static_cast<unsigned int>(leadingBits), blockX[i]); // use blockX[i] if we don't need all the remaining bits in the byte
		leadingBits = std::min(static_cast<unsigned int>(leadingBits), remainingBits); // can only us the number of bits remaining in current byte
		remainingBits -= leadingBits;
		leadingMask[i] = (unsigned char)pow(2,leadingBits)-1;
		leadingMask[i] <<= remainingBits;
		blockXTmp = blockX[i];
		blockXTmp -= leadingBits;
		if(blockXTmp > 7) remainingBits = 8; // going to use whole bytes, so remainingBits needs to be reset to 8
		while(blockXTmp > 7){
			wholeBytes[i]++;
			blockXTmp-=8;
		}
		trailingBits = blockXTmp;
		if(remainingBits == 0) remainingBits = 8; // no more bits so move to the next byte
		remainingBits -= trailingBits;
		trailingMask[i] = (unsigned char)pow(2,trailingBits)-1;
		trailingMask[i] <<= 8 - trailingBits;
		leadingBits = 8 - trailingBits;
#ifdef DEBUG
		std::cerr<<"leadingMask: "<<(int)leadingMask[i]
		<<" wholeBytes: "<<(int)wholeBytes[i]
		<<" trailingMask: "<<(int)trailingMask[i]<<"\n";
#endif
	}

	unsigned int numberOfOnes[x]; // only holds one row
	unsigned char* scaledImage = new unsigned char[x*y];
	unsigned char* data = static_cast<unsigned char*>(_TIFFmalloc(scanlineSize));
	unsigned char* tmpData;

	unsigned int incHY;
	unsigned int incLY;
	if(y2-y1+1 <= y){ // make it a 1 to 1 pixel mapping from image to scaled image
		incHY = 1;
		incLY = 0;
	}else{
		incHY = (y2-y1+1)/y;
		incLY = (y2-y1+1)-(incHY*y);
	}
	unsigned int accumY = 0;
	unsigned int blockY = 0; // contains the number of rows in orig image that make up 1 row in scaled image
	unsigned int row = y1; // starting row index into original tiff
	for(unsigned int i=0; i<row; ++i) TIFFReadScanline(tiff, data, i); // move to the correct row (readscanline doesn't support random access)

	// start box filter (average pixels) using bitcounting
	// loop though rows of scaled image
#ifdef DEBUG
	std::cerr<<"blockY: ";
#endif
	for(unsigned int i=0; i<y; ++i){
		accumY += incLY;
		if(accumY >= y) {accumY -= y; blockY = incHY+1;}
		else blockY = incHY;
#ifdef DEBUG
		std::cerr<<blockY<<" ";
#endif
		memset(numberOfOnes, 0, x*sizeof(unsigned int));
		for(unsigned int count=0; count<blockY; ++count, ++row){ // count the bits that will make up one row in scaled image
			TIFFReadScanline(tiff, data, row);
			tmpData = data;
			tmpData += x1/8; // move to correct column
			for(unsigned int j=0; j<x; ++j){ // count the bits and store them
				if(leadingMask[j]){
					numberOfOnes[j] += oneBitsInChar[*tmpData & leadingMask[j]];
				}
				// switch statment handles groups of bytes to run faster
				switch(wholeBytes[j]){
					// default handles whole bytes over the largest case, should be rare
					default: for(unsigned int tmp=0; tmp<wholeBytes[j]; ++tmp) numberOfOnes[j] += oneBitsInChar[*++tmpData]; break;
					case 4: numberOfOnes[j] += oneBitsInChar[*++tmpData] + oneBitsInChar[*++tmpData] + oneBitsInChar[*++tmpData] + oneBitsInChar[*++tmpData]; break;
					case 3: numberOfOnes[j] += oneBitsInChar[*++tmpData] + oneBitsInChar[*++tmpData] + oneBitsInChar[*++tmpData]; break;
					case 2: numberOfOnes[j] += oneBitsInChar[*++tmpData] + oneBitsInChar[*++tmpData]; break;
					case 1: numberOfOnes[j] += oneBitsInChar[*++tmpData]; break;
				}
				if(trailingMask[j]){
					numberOfOnes[j] += oneBitsInChar[*++tmpData & trailingMask[j]];
				}
				// must increment tmpData if there were wholeBytes or leadingBits that ended at the end of a byte and no trailingBits
				// if there are trailingBits we don't increment tmpData because the left over bits will be the leading bits of the
				// next iterations
				if( ((wholeBytes[i]) || (leadingMask[j] & 0x1)) && (!trailingMask[j])) ++tmpData;
#ifdef DEBUG
				if(i==0 && count==0) std::cerr<<"j: "<<j
					<<" bytes used: "<<tmpData-data
					<<" leadingMask: "<<(int)leadingMask[j]
					<<" wholeBytes: "<<(int)wholeBytes[j]
					<<" trailingMask: "<<(int)trailingMask[j]<<"\n";
#endif
			}
		} // finished counting the bits that will make up one row in scaled image
		// convert to grayscale
		// note: this is inverted so I can make it the correct color later ie. image * color = final image
		for(unsigned int j=0; j<x; ++j){
			// "255 -" is what inverts scaledImage
			if(zeroWhite)
				scaledImage[j+(i*x)] = static_cast<unsigned char>((static_cast<float>(numberOfOnes[j])/(blockY*blockX[j])) * 255);
			else
				scaledImage[j+(i*x)] = static_cast<unsigned char>((255-(static_cast<float>(numberOfOnes[j])/(blockY*blockX[j])) * 255));
		}
	}

	_TIFFfree(data);
	return scaledImage;
}

float Tiff::sample(const unsigned int x1, const unsigned int y1,
					const unsigned int x2, const unsigned int y2){
	unsigned char* strip = static_cast<unsigned char*>(_TIFFmalloc(stripSize));
	unsigned int coverage = 0;
	tsize_t currentStripNumber = -1;

	// create bit masks and calculate wholeBytes
	unsigned int totalBits = x2-x1+1;
	unsigned int leadingBits = 8-(x1%8);
	unsigned char leadingMask;
	unsigned int trailingBits;
	unsigned char trailingMask;
	unsigned int wholeBytes;
	if(leadingBits > totalBits){
		leadingBits = totalBits;
		leadingMask = static_cast<unsigned char>(pow(2, leadingBits)-1);
		leadingMask <<= 8-((x1%8)+1);
		trailingMask = 0;
		wholeBytes = 0;
	}else{
		leadingMask = static_cast<unsigned char>(pow(2, leadingBits)-1);
		trailingBits = (x2%8)+1;
		trailingMask = static_cast<unsigned char>(pow(2, trailingBits)-1);
		trailingMask <<= 8 - ((x2%8)+1);
		wholeBytes = (totalBits-leadingBits-trailingBits) / 8;
	}

	// loop through the data and count the bits
	for(unsigned int y=y1; y<y2+1; ++y){
		// find the strip the first pixel is in
		tsize_t stripNumber = TIFFComputeStrip(tiff, y, 0);
		unsigned char* row;
		unsigned char* data;
		if(stripNumber != currentStripNumber){
			TIFFReadEncodedStrip(tiff, stripNumber, strip, -1);
			currentStripNumber = stripNumber;
			// move to the correct row in the strip
			// first strip is number 0
			unsigned int skipRows = currentStripNumber * rowsPerStrip;
			row = strip + scanlineSize * (y-skipRows);
		}else{
			// move to next row
			row += scanlineSize;
		}
		data = row;
		// move to the correct byte in the row
		// first bit is number 0
		data += x1/8;
		// start counting the bits
		// count bits in first byte
		coverage += oneBitsInChar[leadingMask & *data];
		// use oneBitsInChar to count bits in whole bytes
		for(unsigned int i=0; i<wholeBytes; i++){
			coverage += oneBitsInChar[*(++data)];
		}
		// count bits in last byte
		coverage += oneBitsInChar[trailingMask & *(++data)];
	}
	_TIFFfree(strip);
	if(zeroWhite) return (static_cast<float>(coverage)/static_cast<float>((x2-x1+1) * (y2-y1+1))) * 100.0;
	else return (1.0 - static_cast<float>(coverage)/static_cast<float>((x2-x1+1) * (y2-y1+1))) * 100.0;
}

float Tiff::getAspectRatio(){
	return static_cast<float>(x)/static_cast<float>(y);
}

unsigned int Tiff::getX(){
	return x;
}

unsigned int Tiff::getY(){
	return y;
}

float Tiff::getXResolution(){
	return xResolution;
}

float Tiff::getYResolution(){
	return yResolution;
}

unsigned int Tiff::getStripSize(){
	return stripSize;
}

unsigned int Tiff::getRowsPerStrip(){
	return rowsPerStrip;
}

bool Tiff::isInches(){
	return resolutionUnit==INCHES;
}

bool Tiff::isZeroWhite(){
	return zeroWhite;
}

inline bool Tiff::isEqual(const float &x, const float &y, const float &delta){
	return(x <= y+delta && x >= y-delta);
}

inline int Tiff::clamp(int i, int low, int high){
	i = i < low ? low : i;
	i = i > high ? high : i;
	return i;
}
