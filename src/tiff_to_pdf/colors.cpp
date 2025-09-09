#include "colors.h"
#include <cstdlib>
#include <algorithm>
#include <cctype>
#include <string>

Colors::Colors(){
}

bool Colors::init(std::string colorsFile){
	std::ifstream file;
	file.open(colorsFile.c_str());

	if(!file) return false;

	// parse color file
	std::string line;
	while(getline(file, line)){
		int pos = line.find("=");
		// get color code
		std::string code;
		code = line.substr(0, pos);
		std::transform(code.begin(), code.end(), code.begin(), ::tolower);
		// get color
		std::string hex = line.substr(pos+1, 6);
		unsigned int num = strtoul(hex.c_str(), NULL, 16);
		Color color;
		color.r = (num>>16) & 0x000000ff;
		color.g = (num>>8) & 0x000000ff;
		color.b = num & 0x000000ff;
		// load into map
		colorMap[code] = color;
	}

	file.close();
	return true;
}

Colors::~Colors(){
}

Colors::Color Colors::operator[](std::string s){
	std::transform(s.begin(), s.end(), s.begin(), ::tolower);
	Color color;
	std::map<std::string, Color, std::less<std::string> >::iterator i;
    i = colorMap.find(s);
	if(i == colorMap.end()){ // not found, so set it to neon pink
		color.r = 0xff;
		color.g = 0x6e;
		color.b = 0xc7;
	}else{
		color = (*i).second;
	}
	return color;
}
