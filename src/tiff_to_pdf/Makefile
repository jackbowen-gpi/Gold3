all:
	g++ -I/opt/local/include -ltiff -o "tiff_to_pdf_`uname -s`_`uname -m`" tiffToPDF.cpp colors.cpp tiffManager.cpp tiff.cpp `Magick++-config --cppflags --cxxflags --ldflags --libs`
install:
	cp "tiff_to_pdf_`uname -s`_`uname -m`" ../../bin/
clean:
	rm -f *.o
