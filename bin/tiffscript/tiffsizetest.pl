#!/usr/bin/perl

#input tiff
$monkey = `tiffinfo noise_hot.tif`;

#find and extract length
$monkey =~ /(Length:) (\d{1,})/;
$length = "$2";

#find and extract width
$monkey =~ /(Width:) (\d{1,})/;
$width = "$2";

#find and extract resolution
$monkey =~ /(Resolution:) (\d{1,})/;
$resolution = "$2";

#calculation res in inches
$width = $width/$resolution;
$width = sprintf("%.2f", $width);
$length = $length/$resolution;
$length = sprintf("%.2f", $length);

print "Resolution is $resolution\n";
print "Width is $width inches\n";
print "Length is $length inches\n";
