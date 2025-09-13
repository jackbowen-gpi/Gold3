#ifndef COLORS_H
#define COLORS_H

#include <fstream>
#include <string>
#include <map>

// The color.txt file that this object loads
// has the following format:
// Color code followed by "=" followed by the color in hex
// ex. cool color 12=003b11

class Colors{
        public:
				struct Color{
					unsigned char r,g,b;
				};
                Colors();
                ~Colors();
				// loads colors.txt file or any file given and returns true if successfull
				bool init(std::string colorsFile = "colors.txt");
                Color operator[](std::string s);
        private:
                std::map<std::string, Color, std::less<std::string> > colorMap;
};


#endif
