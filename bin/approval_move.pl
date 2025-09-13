#!/usr/bin/perl

$rootDir = "./";
@fileArray = </Volumes/pdf_drop_local/approval_scans/*.jpg>;
@fileArray2 = </Volumes/pdf_drop_local/approval_scans/*.pdf>;
@fileArray = (@fileArray, @fileArray2);

# loop through files
foreach $file (@fileArray){

	#Make sure the file has stopped being written to before converting and moving
	$copy_check = 0;

	while ($copy_check == 0){

	$file_size = (-s $file);
	sleep 2;
	$file_size2 = (-s $file);

	# If bytes match after 2 second delay copy is complete. Go to next step

	if ($file_size == $file_size2){
	if ($file_size2 > 100){
	$copy_check = 1;
	}
	}

	}

	# strip off leading path
	$fileName = (split(/\//,$file))[-1];

	print "$fileName\n";

	$item_num = substr($fileName,6,-4);
	$jobnum = substr($fileName,0,5);

	print "JOBNUM: $jobnum\n";

	if ($item_recid !~ /error/)
	{
	#Create url string to update GOLD


	$edit_str = "http://172.23.8.16/workflow/item/" . $jobnum . "/" . $item_num . "/do_item_approval/";

	# Check to see if the file is already a PDF
	if ($fileName =~ /.pdf/)
	{
	$output = "/Volumes/JobStorage/" . $jobnum . "/Database_Documents/Approval_Scans/" . $fileName;
	`cp "$file" $output`;
	`chmod a+r $output`;
	}
	else
	{
	# convert the file
	$input = $file;
	$output = "/Volumes/JobStorage/" . $jobnum . "/Database_Documents/Approval_Scans/" . $fileName;
	$output =~ s/.jpg/.pdf/;

	`/usr/local/bin/convert "$input" $output`;
	`chmod a+r $output`;

	}

	print "$edit_str\n";
	#Update GOLD V3 to show item approved
	`curl -s "$edit_str"`;
	}

	#remove old jpg
        unlink($file);
}
