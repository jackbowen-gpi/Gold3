// (c) 2006 International Paper Company.  All Rights Reserved.
// This program (in its entirety, as a collection/combination of its multiple components/files and as individual components/files),
// together with all text, images, logos and design incorporated thereinto, are the copyright of International Paper Company.
// Neither this program in its entirety nor the individual components thereof may be copied and/or redistributed for any commercial
// or non-commercial purpose whatsoever without the prior express, written consent of International Paper Company.  Use of this program
// is subject to the terms of the software license agreement provided herewith and incorporated hereinto by reference.

#include <iostream>
#include <vector>
#include <string>
#include <stdio.h>
#include <time.h>
#include <string.h>
#include <Magick++.h>
#include "colors.h"
#include "tiffManager.h"

// Parameters
// -tiff, tiff name follow by color, format: -tiff cool.tif 348
// -pdf, is the base name of the high(base name_h.pdf) and low(base name_l.pdf) res pdfs,  format: -pdf test
// -high_dpi, dpi of high res pdf, format: -high_dpi 300 is the default if not used
// -low_dpi, dpi of low res pdf, format: -low_dpi 300 is the default if not used
// -crop, crops the low res pdf from the top left by x, y inches, format: is -crop 4.3 6.1 where x=4.3 and y=6.1
// -crop_4up, set the top left to x, y inches for the -crop parameter, format: is -crop 1.0 2.5 where x=1.0 and y=2.5
// -approval, approval box file that is added to the low res pdf, format: -approval approvalbox.pdf
// -side_panel_type, type of side panel used to determine if it should create swatches, format: -side_panel_type carton
// These parameters can come in any order.  A space must between every parameter.

int main(int argc, char* argv[]){
	std::string pdfFilename;
	unsigned int highDpi = 300, lowDpi = 300;
	bool crop = false;
	float xTopLeft = 0, yTopLeft = 0;
	float xBottomRight = 0, yBottomRight = 0;
	bool makeSwatches = true;
	std::string approvalFilename;
	std::string jobInfo;
	std::vector<std::string> tiffFilenames;
	std::vector<std::string> tiffColors;
	std::string timestamp;

	// load parameters
	for(int i=1; i<argc; ++i){
		if(!strcmp(argv[i], "-tiff")){
			if(i+2 > argc-1){
				std::cout<<"Error: Did not give tiff filename and color\n";
				return 0;
			}
			tiffFilenames.push_back(argv[++i]);
			tiffColors.push_back(argv[++i]);
		}else if(!strcmp(argv[i], "-pdf")){\
			if(i+1 > argc-1){
				std::cout<<"Error: Did not give pdf name\n";
				return 0;
			}
			pdfFilename = argv[++i];
		}else if(!strcmp(argv[i], "-low_dpi")){
			if(i+1 > argc-1){
				std::cout<<"Error: Did not give low res dpi\n";
				return 0;
			}
			lowDpi = strtoul(argv[++i], NULL, 0);
		}else if(!strcmp(argv[i], "-high_dpi")){
			if(i+1 > argc-1){
				std::cout<<"Error: Did not give high res dpi\n";
				return 0;
			}
			highDpi = strtoul(argv[++i], NULL, 0);
		}else if(!strcmp(argv[i], "-crop")){
			if(i+2 > argc-1){
				std::cout<<"Error: Did not give crop dimensions\n";
				return 0;
			}
			crop = true;
			xBottomRight = strtof(argv[++i], NULL);
			yBottomRight = strtof(argv[++i], NULL);
		}else if(!strcmp(argv[i], "-crop_4up")){
			if(i+2 > argc-1){
				std::cout<<"Error: Did not give crop dimensions\n";
				return 0;
			}
			crop = true;
			xTopLeft = strtof(argv[++i], NULL);
			yTopLeft = strtof(argv[++i], NULL);
		}else if(!strcmp(argv[i], "-approval")){
			if(i+1 > argc-1){
				std::cout<<"Error: Did not give approval box filename\n";
				return 0;
			}
			approvalFilename = argv[++i];
		}else if(!strcmp(argv[i], "-side_panel_type")){
			if(i+1 > argc-1){
				std::cout<<"Error: Did not give side panel type\n";
				return 0;
			}
			if(strcasecmp(argv[++i], "carton")){ // only make swatches for cartons
				makeSwatches = false;
			}
		// Here's some new stuff being added 6/2010. Customer name and date.
		}else if(!strcmp(argv[i], "-job_info")){
			if(i+1 > argc-1){
				std::cout<<"Error: Did not give job info\n";
				return 0;
			}
			jobInfo = argv[++i];
		}else{
			std::cout<<"Error: Unknown parameter "<<argv[i]<<std::endl;
			return 0;
		}
	}

	// set program Path
	std::string programPath = argv[0];
	unsigned int pos = programPath.rfind("/");
	programPath = programPath.substr(0, pos+1);

	// check to make sure we have tiffs, pdf, approval file, dpi's > 0, crop dimensions > 0, and can load colors file
	if(tiffFilenames.size() < 1){
		std::cout<<"Error: No tiff files were given\n";
		return 0;
	}
	if(tiffFilenames.size() != tiffColors.size()){
		std::cout<<"Error: Number of tiffs does not match number of colors\n";
		return 0;
	}
	if(pdfFilename.size() < 1){
		std::cout<<"Error: No pdf filename was given\n";
		return 0;
	}
	if(approvalFilename.size() < 1){
		std::cout<<"Error: No approval filename was given\n";
	}
	if(lowDpi == 0){
		std::cout<<"Error: Low res dpi was set to zero\n";
		return 0;
	}
	if(highDpi == 0){
		std::cout<<"Error: high res dpi was set to zero\n";
		return 0;
	}
	if(crop){
		if(xBottomRight <= 0){
			std::cout<<"Error: Crop in x direction was set to less than or equal to zero\n";
			return 0;
		}
		if(yBottomRight <= 0){
			std::cout<<"Error: Crop in y direction was set less than or equal to zero\n";
			return 0;
		}
		if(xTopLeft < 0){
			std::cout<<"Error: Crop 4up in x direction was set to less than zero\n";
			return 0;
		}
		if(yTopLeft < 0){
			std::cout<<"Error: Crop 4up in y direction was set less than zero\n";
			return 0;
		}
		if(yTopLeft > yBottomRight || xTopLeft > xBottomRight){
			std::cout<<"Error: Crop 4up is not the top left corner\nError: Crop is not the bottom right corner\n";
			return 0;
		}
	}
	Colors colors;
	if(!colors.init(programPath+"colors.txt")){
		std::cout<<"Error: Cannot find "<<programPath<<"colors.txt\n";
		return 0;
	}

	std::cout<<"Path: "<<argv[0]<<std::endl;
	std::cout<<"Tiffs:\n";
	for(unsigned int i=0; i<tiffFilenames.size(); ++i){
		std::cout<<"\t"<<tiffFilenames[i]<<" ";
		std::cout<<tiffColors[i]<<"\n";
	}
	std::cout<<"PDF: "<<pdfFilename<<std::endl;
	std::cout<<"Low Res DPI: "<<lowDpi<<std::endl;
	std::cout<<"High Res DPI: "<<highDpi<<std::endl;
	std::cout<<"Crop: "<<(crop?"true":"false")<<std::endl;
	std::cout<<"Crop X: "<<xBottomRight<<std::endl;
	std::cout<<"Crop Y: "<<yBottomRight<<std::endl;
	std::cout<<"Crop 4up X: "<<xTopLeft<<std::endl;
	std::cout<<"Crop 4up Y: "<<yTopLeft<<std::endl;
	std::cout<<"Approval: "<<approvalFilename<<std::endl;

	// load tiffs
	TiffManager tiffManager;
	for(unsigned int i=0; i<tiffFilenames.size(); ++i){
		if(!tiffManager.addTiff(tiffFilenames[i], tiffFilenames[i])){
			std::cout<<"Error: Could not load "<<tiffFilenames[i]<<std::endl;
			return 0;
		}
		else{
			// find and set color
			Colors::Color color = colors[tiffColors[i].c_str()];
			tiffManager.setColor(i, reinterpret_cast<unsigned char*>(&color));
		}
	}

	// create high res pdf
	unsigned char* pixels = tiffManager.composite(highDpi);
	unsigned int x = highDpi*tiffManager.getMaxWidth()/tiffManager.getXResolution();
	unsigned int y = highDpi*tiffManager.getMaxHeight()/tiffManager.getYResolution();

	//MagickLib::InitializeMagick(*argv);
	//MagickLib::InitializeMagick("/Users/admin/tiffpdf");
	//(void) MagickLib::SetLogEventMask("all");
	//if (MagickLib::IsMagickInstantiated() == MagickLib::MagickFalse)
	//	std::cout<<"ImageMagick environment not instantiated.\n";
	//else
	//	std::cout<<"ImageMagick environment instantiated.\n";

	// create color swatches if you need them
	Magick::Image swatches(Magick::Geometry(0.9*highDpi, y), Magick::ColorRGB(1.0, 1.0, 1.0));
	if(makeSwatches){
		unsigned int swatchNumber = 0;
		for(unsigned int i=0; i<tiffFilenames.size(); ++i){
			if(strcasecmp(tiffColors[i].c_str(), "die")){ // die layer, don't make swatch
				// create actual swatch
				Colors::Color color = colors[tiffColors[i].c_str()];
				swatches.fillColor(Magick::ColorRGB(color.r/255.0, color.g/255.0, color.b/255.0));
				float xTL = 0.25*highDpi; // distance from left edge of paper
				float yTL = 1.0*highDpi + 1.5*highDpi*swatchNumber; // top margin + distance to next swatch
				float xBR = xTL + 0.5*highDpi; // left edge + swatch width
				float yBR = yTL + 1.0*highDpi; // top edge + swatch height
				swatches.draw(Magick::DrawableRectangle(xTL, yTL, xBR, yBR));
				// put text in swatch
				// Use the default font like the high res proof.
				//swatches.font("Helvetica-Regular");
				swatches.fontPointsize(10.0*(highDpi/72.0));
				swatches.fillColor(Magick::ColorRGB(1, 1, 1));
				swatches.annotate(tiffColors[i],
					Magick::Geometry(xBR-xTL, yBR-yTL, xTL, yTL),
					Magick::GravityType(Magick::CenterGravity), -90.0);
				++swatchNumber;
			}
		}
	}

	Magick::Image image;
	image.read(x, y, "RGB", Magick::CharPixel, pixels);
	image.density(Magick::Geometry(72, 72));
	image.page(Magick::Geometry(x*(72.0/highDpi), y*(72.0/highDpi)));
	if(makeSwatches) image.composite(swatches, 0, 0, Magick::OverCompositeOp);
	image.quality(75);
	image.compressType(Magick::JPEGCompression);
	std::string filename = pdfFilename + "-h.pdf";
	image.write(filename.c_str());

	// create low res pdf
	if(highDpi != lowDpi){ // if dpi for high and low are not the same we must recomposite and scale swatches
		delete[] pixels;
		pixels = tiffManager.composite(lowDpi);
		x = lowDpi*tiffManager.getMaxWidth()/tiffManager.getXResolution();
		y = lowDpi*tiffManager.getMaxHeight()/tiffManager.getYResolution();
		image.read(x, y, "RGB", Magick::CharPixel, pixels);
		if(makeSwatches){
			Magick::Geometry size;
			size.percent(true);
			size.width((static_cast<float>(lowDpi)/static_cast<float>(highDpi))*100.0);
			size.height((static_cast<float>(lowDpi)/static_cast<float>(highDpi))*100.0);
			swatches.sample(size);
		}
	}
	if(crop)image.crop(Magick::Geometry(xBottomRight*lowDpi, yBottomRight*lowDpi, xTopLeft*lowDpi, yTopLeft*lowDpi));
	Magick::Image approvalImage;
	approvalImage.density(Magick::Geometry(lowDpi, lowDpi));
	approvalImage.read(approvalFilename);
	Magick::Geometry lowResSize;
	if(crop){
		lowResSize = Magick::Geometry(xBottomRight*lowDpi+approvalImage.baseColumns(),
			(yBottomRight-yTopLeft)*lowDpi>approvalImage.baseRows()?(yBottomRight-yTopLeft)*lowDpi:approvalImage.baseRows());
	}else{
		lowResSize = Magick::Geometry(x+approvalImage.baseColumns(),
			y>approvalImage.baseRows()?y:approvalImage.baseRows());
	}
	Magick::Image lowResImage(lowResSize, Magick::ColorRGB(1.0, 1.0, 1.0));
	lowResImage.composite(approvalImage, 0, 0, Magick::OverCompositeOp);
	lowResImage.composite(image, Magick::GravityType(Magick::EastGravity), Magick::OverCompositeOp);
	if(makeSwatches && ((highDpi != lowDpi) || (xTopLeft != 0) || (yTopLeft != 0)))
		lowResImage.composite(swatches, approvalImage.baseColumns(), 0, Magick::OverCompositeOp);
	// Add in text information.
	// Format timestamp.
	time_t rawtime;
	struct tm * timeinfo;
	char buffer [80];
	time (&rawtime);
	timeinfo = localtime (&rawtime);
	strftime (buffer, 80, "%m-%d-%Y", timeinfo);
	timestamp = buffer;
	std::list<Magick::Drawable> drawList;
	drawList.push_back(Magick::DrawableRotation(-45.0));
	drawList.push_back(Magick::DrawablePointSize(36));
	drawList.push_back(Magick::DrawableFillColor("black"));
	// These two bits of information are written in the approval box area.
	drawList.push_back(Magick::DrawableText(-1400, 475, timestamp));
	drawList.push_back(Magick::DrawableText(-1000, 475, jobInfo));
	lowResImage.draw(drawList);
	lowResImage.page(Magick::Geometry(lowResSize.width()*(72.0/lowDpi), lowResSize.height()*(72.0/lowDpi)));
	lowResImage.density(Magick::Geometry(72, 72));
	//lowResImage.gaussianBlur(0.3, 0.5);
	lowResImage.quality(75);
	lowResImage.compressType(Magick::JPEGCompression);
	filename = pdfFilename + "-l.pdf";
	lowResImage.write(filename.c_str());
	delete[] pixels;
	return 1;
}
