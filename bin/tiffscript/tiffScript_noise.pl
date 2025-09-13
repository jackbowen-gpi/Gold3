#!/usr/bin/perl

#
# This script applies pre-determined noise to simulate areas on cups where
# ink may be spotty or fails to cover. The inkjet proofers tend to have
# much more even, solid coverage than what would be seen on a press.
#

# real directories
$outFolder = "/Volumes/Promise/Data2/Shares/Container/Tiff_out";
$inFolder  = "/Volumes/Promise/Data2/Shares/Container/tmp_tiff";

# test directories
#$outFolder = "/Users/admin/gchub/bin/tiffscript/output";
#$inFolder = "/Users/admin/gchub/bin/tiffscript/input";

# get all folders

@folders = <$inFolder/*>;

# loop though all files in inFolder
foreach $folder (@folders) {
    # check and see if it is a folder
    if ( -d $folder ) {
        # get all the tiffs
        @files = <$folder/*.tif>;

        # get folder name
        $folder = `basename '$folder'`;
        chomp $folder;

        # loop though all the tiffs
        foreach $file (@files) {
            print "$file\n";

            $file_size = -s "$file";

            # Create log name. Will generate new log each day based on the date changing
            my ( $sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst ) =
              localtime time;
            $year += 1900;
            $mon  += 1;

            $log_name =
                "/Volumes/Server HD/var/log/tiff_file_size/tiffs_"
              . $mon . "_"
              . $mday . "_"
              . $year . ".log";

            # change file name
            $file = `basename '$file'`;
            chomp $file;

            #open/create log and append file size
            open( OPENLOG, ">> $log_name" );

            print OPENLOG "\n$file\t$file_size";

            close(OPENLOG);

            $processedFile = $file;
            $processedFile =~ s/_designer_/_/g;
            $processedFile =~ s/_eps_/_/g;
            $processedFile =~ s/_pms1000c_black/_black 1/g;
            $processedFile =~ s/_pms1000c_yellow/_yellow 1/g;
            $processedFile =~ s/_pms1000c_/_/g;
            $processedFile =~ s/_ai_/_/g;
            $processedFile =~ s/_pantone_(?!yellow)/_/g;
            $processedFile =~ s/_pantone_(?!black)/_/g;
            $processedFile =~ s/_process_(magenta|yellow|black|cyan)/_$1/g;
            $processedFile =~ s/u.tif/.tif/g;
            $processedFile =~ s/c.tif/.tif/g;

            #Apply noise filter based upon value from GOLD
            $job_number  = substr( $file, 0, 5 );
            $item_number = substr( $file, 6, 1 );

            #remove spaces because url code after this doesn't like spaces
            $job_number  =~ s/ /%20/g;
            $item_number =~ s/ /%20/g;

            use LWP::Simple;
            $noise_filter_applied = "Yes";

            # rename and move the file
            $outsub_folder = $folder;
            $outsub_folder =~ s/^n_//g;

            # does the file already exist, if so add -1 to it
            if ( -e "$outFolder/$outsub_folder/$processedFile" ) {
                $processedFile =~ s/.tif/-1.tif/g;
                print "file already exist, so change the name\n";
            }
            print "$outFolder/$outsub_folder/$processedFile\n";

            if (   $noise_filter_applied =~ /Yes/
                && $folder =~ /^n_/
                && $file !~ /template.tif$/ )
            {
                print "Applying Noise Filter\n";
                if ( $folder =~ /Hot/i ) {
                    $noise_file = "noise_hot.tif";
                } else {
                    $noise_file = "noise_not_hot.tif";
                }
                `./Tiff_Noise '$inFolder/$folder/$file' '$noise_file' '$outFolder/$outsub_folder/$processedFile'`;
                `rm -f '$inFolder/$folder/$file'`;
            } else {
                `mv -f '$inFolder/$folder/$file' '$outFolder/$outsub_folder/$processedFile'`;
            }

            # Copy tiff file into Online_PDFs hot folder to create a PDF for the VR system
            $pdf_name = $processedFile;
            $pdf_name =~ s/ /|/g;

            #print "file =      $inFolder/$folder/$file\n";
            #print "processed = $outFolder/$folder/$processedFile\n";
        } # end of file loop
    } # end of folder test
} # end of folder loop
