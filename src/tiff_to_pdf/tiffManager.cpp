#include "tiffManager.h"
#include <iostream>
#include <string.h>

TiffManager::~TiffManager(){
	for(std::vector<TiffInfo*>::iterator i = tiffs.begin(); i!=tiffs.end(); ++i){
		delete (*i)->tiff;
		delete *i;
	}
}

bool TiffManager::addTiff(const std::string &file, const std::string &filename){
	TiffInfo* tiffInfo = new TiffInfo;
	tiffInfo->tiff = new Tiff;
	if(!tiffInfo->tiff->load(file)){
		delete tiffInfo->tiff;
		delete tiffInfo;
		return false;
	}
	tiffInfo->active = true;
	tiffInfo->filename = filename;
	tiffs.push_back(tiffInfo);
	return true;
}

bool TiffManager::deleteTiff(unsigned int i){
	delete tiffs[i]->tiff;
	delete tiffs[i];
	tiffs.erase(tiffs.begin()+i);
	return true;
}

bool TiffManager::deleteTiffs(){
	for(unsigned int i=0; i<tiffs.size(); ++i){
		delete tiffs[i]->tiff;
		delete tiffs[i];
	}
	tiffs.erase(tiffs.begin(), tiffs.end());
	return true;
}

unsigned char* TiffManager::scale(unsigned int x, unsigned int y, unsigned int i){
	return tiffs[i]->tiff->scale(x,y);
}

unsigned char** TiffManager::scale(unsigned int x, unsigned int y){
	unsigned char** scaledTiffs = new unsigned char*[tiffs.size()];
	for(unsigned int i=0; i<tiffs.size(); ++i){
		scaledTiffs[i] = scale(x,y,i);
		// check for error
		if(!scaledTiffs[i]){
			for(unsigned int j=0; j>i; ++j){
				delete[] scaledTiffs[j];
			}
			delete[] scaledTiffs;
			return NULL;
		}
	}
	return scaledTiffs;
}

unsigned char* TiffManager::getPixels(int x1, int y1,
								int x2, int y2,
								int x, int y,
								unsigned int i){
	int xTopLeft = x1<=x2?x1:x2;
	int yTopLeft = y1<=y2?y1:y2;
	int xBottomRight = x1>x2?x1:x2;
	int yBottomRight = y1>y2?y1:y2;
	return tiffs[i]->tiff->getPixels(xTopLeft, yTopLeft, xBottomRight, yBottomRight, x, y);
}

unsigned char* TiffManager::composite(const unsigned int dpi){
	unsigned int maxX = dpi*getMaxWidth()/getXResolution();
	unsigned int maxY = dpi*getMaxHeight()/getYResolution();
	unsigned char* compositedImage = new unsigned char[maxX*maxY*3];
	memset(compositedImage, 0xff, maxX*maxY*3); // make white

	unsigned char** images = new unsigned char*[tiffs.size()]; // allocates memory for all tiffs even unactive ones
	for(unsigned int i=0; i<tiffs.size(); ++i){
		if(tiffs[i]->active){
			unsigned int x = dpi*getWidth(i)/getXResolution();
			unsigned int y = dpi*getHeight(i)/getYResolution();
			images[i] = scale(x,y,i);
			// check for error
			if(!images[i]){
				for(unsigned int j=0; j>i; ++j){
					delete[] images[j];
				}
				delete[] images;
				return compositedImage; // returns solid white image
			}
		}
	}

	// composite images
	unsigned char* compositedImageBegin = compositedImage;
	for(unsigned int i=0; i<size(); ++i){
		if(tiffs[i]->active){
			float red = tiffs[i]->color[0]/255.0;
			float green = tiffs[i]->color[1]/255.0;
			float blue = tiffs[i]->color[2]/255.0;
			unsigned int x = dpi*getWidth(i)/getXResolution();
			unsigned int y = dpi*getHeight(i)/getYResolution();
			for(unsigned int j=0; j < x*y; ++j){
				float source = images[i][j]/255.0;
				if(j%x == 0) compositedImage = compositedImageBegin + (maxX * (j/x) * 3); // j/x will give current row
				*compositedImage = static_cast<unsigned int>(*compositedImage * (red*source + (1.0-source)));
				++compositedImage;
				*compositedImage = static_cast<unsigned int>(*compositedImage * (green*source + (1.0-source)));
				++compositedImage;
				*compositedImage = static_cast<unsigned int>(*compositedImage * (blue*source + (1.0-source)));
				++compositedImage;
			}
			compositedImage = compositedImageBegin;
		}
	}

	// delete scaled image
	for(unsigned int i=0; i<this->size(); ++i){
		delete[] images[i];
	}
	delete[] images;
	//delete[] tmpImage;

	return compositedImage;
}

float TiffManager::sample(const unsigned int x1, const unsigned int y1,
							const unsigned int x2, const unsigned int y2,
							unsigned int i){
	unsigned int xTopLeft = x1<=x2?x1:x2;
	unsigned int yTopLeft = y1<=y2?y1:y2;
	unsigned int xBottomRight = x1>x2?x1:x2;
	unsigned int yBottomRight = y1>y2?y1:y2;
	return tiffs[i]->tiff->sample(xTopLeft, yTopLeft, xBottomRight, yBottomRight);
}

float TiffManager::aspectRatio(unsigned int i){
	return tiffs[i]->tiff->getAspectRatio();
}

unsigned char* TiffManager::getColor(unsigned int i){
	unsigned char* color;
	color = new unsigned char[3];
	memcpy(color, tiffs[i]->color, 3);
	return color;
}

void TiffManager::setColor(unsigned int i, unsigned char* color){
	memcpy(tiffs[i]->color, color, 3);
}

unsigned int TiffManager::size(){
	return tiffs.size();
}

unsigned int TiffManager::getWidth(unsigned int i){
	return tiffs[i]->tiff->getX();
}

unsigned int TiffManager::getHeight(unsigned int i){
	return tiffs[i]->tiff->getY();
}

unsigned int TiffManager::getMaxWidth(){
	unsigned int width = 0;
	for(unsigned int i=0; i<tiffs.size(); ++i){
		if(tiffs[i]->tiff->getX() > width) width = tiffs[i]->tiff->getX();
	}
	return width;
}

unsigned int TiffManager::getMaxHeight(){
	unsigned int height = 0;
	for(unsigned int i=0; i<tiffs.size(); ++i){
		if(tiffs[i]->tiff->getY() > height) height = tiffs[i]->tiff->getY();
	}
	return height;
}

float TiffManager::getXResolution(unsigned int i){
	return tiffs[i]->tiff->getXResolution();
}

float TiffManager::getYResolution(unsigned int i){
	return tiffs[i]->tiff->getYResolution();
}

std::string TiffManager::getFilename(unsigned int i){
	return tiffs[i]->filename;
}

bool TiffManager::isInches(unsigned int i){
	return tiffs[i]->tiff->isInches();
}

bool TiffManager::isActive(unsigned int i){
	return tiffs[i]->active;
}

void TiffManager::setActive(unsigned int i, bool status){
	tiffs[i]->active = status;
}
