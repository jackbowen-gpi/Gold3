
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "pdflib.h"
#include "color_defs.h"

//1 - template
//2 - destination
//3 - platemaker first letter
//4 - bom
//5 - barcode
//6 - target type (tolerance | crosshairs | mcrosshairs)
//7 - number_colors
//8 - plate order (i.e. 4123)
//9, 10 - platecode1 color1
//11, 12 - platecode2 color2
//13, 14 - platecode3 color3
//15, 16 - platecode4 color4
//./make_template /Volumes/Beverage/templates/backstage_templates/1up/liter.pdf /Volumes/Beverage/templates/backstage_templates/42668_test2.pdf H " " "0 87932 60074" crosshairs 4 4123 148-206-701 Black 148-206-701 130 148-206-701 145 148-206-701 "Orange 021"

int main(int argc, char *argv[]) {
    PDF     *p;
    int     doc, page, die_layer, marks_layer,art_layer;
    int     spot,i,j,k,n,m;
    float x,y,x1,y1,x_offset, y_offset, page_height,x_white,y_white;
    float xc[2],yc[2];
    int     font, row, col,gstate;
    const   int maxrow = 2;
    const   int maxcol = 2;
    char    optlist[128];
    int     endpage;
    int     pageno=1;
    char *infile;
    char *output;
    char *platemaker;
    char color[64];
    char patentfill[64];
    char linecolor[64];
    char backcolor[64];
    char debug[256];
    char plate_label[10];
    char platenum[8];
    char platecount[6];
    char *plateorder;
    char *bom;
    char *barcode_num;
    char *mark_style;
    char *target_type;
    char *named_color[4];
    char *platecode[4];
    char warning[36];
    int plate_num;
    //tolerance box specifications
    float tol_x[3]={.0189,.176,.333};
    float tol_y[2]={.0189,.0862};
    float tol_cross[2]={.1571,.3141};
    float tolrect_x=.4713;
    float tolrect_y=.1572;
    float tol_inrect_x=.1192;
    float tol_inrect_y=.0521;
    //registration cross specifications
    float reg_width=.1624;
    float full_width=.6496;
    float reg_height=.1624;
    float reg_offset[4]={0.0,.2532,.4155,.5779};

    //registration metric cross specifications
    float metric_width=.125;
    float metric_height=.125;
    float metric_full_width=.375;
    float metric_offset[4]={0.0,.2532,.4155,.5779};

    float cross_width;

    int tolerance_true=0;
    int crosshairs_true=0;
    int metric_crosshairs_true=0;
    int no_marks=0;
    int num;

    // Debugging output
    printf("Args:\n");
    for(i=0; i < argc; i++){
        printf(" %d: %s\n", i, argv[i]);
    }

    // Here to help try to avoid using hard-coded argv indices.
    infile = argv[1];
    output = argv[2];
    platemaker = argv[3];
    bom = argv[4];
    barcode_num = argv[5];
    target_type = argv[6];
    num = atoi(argv[7]);
    plateorder = argv[8];
    mark_style = argv[9];

    // 6 - target type (tolerance | crosshairs | mcrosshairs)
    if(strcmp(target_type, "tolerance") == 0 && strcmp(mark_style, "new") == 0) {
       // Tolerance marks are not valid for old marks.
       tolerance_true = 1;
    } else if(strcmp(target_type, "mcrosshairs") == 0) {
        metric_crosshairs_true = 1;
    } else if(strcmp(target_type, "none") == 0 && strcmp(mark_style, "none") == 0) {
    	// Do nothing. Leave all marks false (0).
    	// Currently only the case with sidepanels.
    	no_marks = 1;
    } else {
        crosshairs_true = 1;
    }

    for(i = 0; i < num; i++) {
       // printf("loading colors..");
        platecode[i]=argv[10+2*i];
        named_color[i]=argv[11+2*i];
       // printf("%s - %s\n",platecode[i],named_color[i]);
    }

    /* This is where font/image/PDF input files live. Adjust as necessary. */
    char *searchpath = "../data";
    if ((p = PDF_new()) == (PDF *) 0)
    {
        printf("Couldn't create PDFlib object (out of memory)!\n");
        return(2);
    }
    PDF_set_parameter(p, "license", "M600602-010000-109861-8C200D");

    PDF_TRY(p) {
    if (PDF_begin_document(p, output, 0, "") == -1) {
        printf("Error: %s\n", PDF_get_errmsg(p));
        return(2);
    }

    PDF_set_parameter(p, "SearchPath", searchpath);
    if (no_marks == 0)
    	marks_layer = PDF_define_layer(p,"marks",0," ");
    die_layer = PDF_define_layer(p,"die",0," ");
    doc = PDF_open_pdi(p, infile, "", 0);
    if (doc == -1) {
        printf("Couldn't open PDF template '%s'\n", infile);
        return (1);
    }
    page = PDF_open_pdi_page(p, doc, pageno, "");
    if (page == -1) {
        printf("Couldn't open page %d of PDF template '%s'\n", pageno, infile);
        return (2);
    }

    PDF_begin_page_ext(p, 20, 20, "");
    PDF_begin_layer(p,die_layer);
    PDF_fit_pdi_page(p, page, 0, 0, "adjustpage");
    PDF_set_parameter(p,"spotcolorlookup","false");
    if (no_marks == 0)
    	PDF_begin_layer(p,marks_layer);
    page_height=PDF_get_pdi_value(p,"height",doc, page, 0)/72;

    x=PDF_get_pdi_value(p,"vdp/Blocks/reg_marks/Custom/x_tolerance", doc, page, 0);
    y=PDF_get_pdi_value(p,"vdp/Blocks/reg_marks/Custom/y_tolerance", doc, page, 0);
    xc[0]=72 * PDF_get_pdi_value(p,"vdp/Blocks/reg_marks/Custom/x_crosshairs_top", doc, page, 0);
    yc[0]=72 * PDF_get_pdi_value(p,"vdp/Blocks/reg_marks/Custom/y_crosshairs_top", doc, page, 0);
    xc[1]=72 * PDF_get_pdi_value(p,"vdp/Blocks/reg_marks/Custom/x_crosshairs_bot", doc, page, 0);
    yc[1]=72 * PDF_get_pdi_value(p,"vdp/Blocks/reg_marks/Custom/y_crosshairs_bot", doc, page, 0);

    printf("\n");
    printf("Page height %f\n",page_height);
    printf("Value x,y coordinates (%f, %f)\n", x,y);
    printf("Top x,y coordinates (%f, %f)\n", xc[0]/72,yc[0]/72);
    printf("Bottom x,y coordinates (%f, %f)\n", xc[1]/72,yc[1]/72);

    if(tolerance_true) {
        printf("Tolerance Marks\n");
        PDF_setcolor(p, "fill", "cmyk", 0, 0, 0, 0);
        printf("  Making box @ x,y coordinates (%f, %f)\n", x,y);

        x_white=x * 72;
        y_white=y * 72; //convert to points
        PDF_rect(p,x_white-2,y_white-2,72*tolrect_x+4,72*tolrect_y+4);
        PDF_fill(p);
    } else if(crosshairs_true) {
        printf("Crosshairs");
        PDF_setcolor(p, "fill", "cmyk", 0, 0, 0, 0);
        printf("Making box @ x,y coordinates (%f, %f)\n", xc[0],yc[0]);
        printf("2");
        x_white=xc[0]-(reg_width/2)*72;
        y_white=yc[0]-(reg_height/2)*72;//convert to points
        printf("Making box @ x,y coordinates (%f, %f)\n", x_white,y_white);
        PDF_rect(p,x_white-2,y_white-2,full_width*72+4,reg_height*72+4);
        PDF_fill(p);
    } else if(metric_crosshairs_true) {
        printf("Metric Crosshairs");
        PDF_setcolor(p, "fill", "cmyk", 0, 0, 0, 0);
        printf("Making box @ x,y coordinates (%f, %f)\n", x,y);
        printf("3");
        x_white=x*72;
        y_white=yc[0] - (metric_height / 2) * 72; //convert to points
        PDF_rect(p,x_white - 2,y_white - 2,metric_full_width * 72 + 4,metric_height * 72 + 4);
        PDF_fill(p);
    }

    printf("Looking up colors..\n");

    for(i=0; i<num; i++) {
        sprintf(plate_label,"platecode%d",i+1);
        j = 3000;
        char short_name_match[24];
        for(m=0; m < NUMCOLORS; m++){
            if(strcmp(pmscolors[m].text,named_color[i]) == 0){
                printf("  found the matching color for %s -> %s (%s)\n",
                                        named_color[i],
                                        pmscolors[m].text,
                                        pmscolors[m].short_name);
                sprintf(short_name_match, "%s",
                                        pmscolors[m].short_name);
                j=m;

            }
        }
        if(j == 3000){
            j=NUMCOLORS-1;
            strcpy(warning,"**COULD NOT IDENTIFY ALL COLORS");
        }

        if (j > 7) {
            PDF_setcolor(p, "fill", "cmyk",
                    pmscolors[j].c,
                    pmscolors[j].m,
                    pmscolors[j].y,
                    pmscolors[j].k); // define alternate CMYK values
            spot = PDF_makespotcolor(p, pmscolors[j].name, 0);
            PDF_setcolor(p, "fill", "spot", spot, 1, 0, 0); // set the spot color
            PDF_setcolor(p, "stroke", "spot", spot, 1, 0, 0);
            sprintf(color,"encoding winansi fillcolor {spot %d 1}",spot);
            sprintf(linecolor,"encoding winansi linewidth .5 bordercolor {spot %d 1}",spot);
            sprintf(backcolor,"encoding winansi backgroundcolor {spot %d 1}",spot);
        } else {
            PDF_setcolor(p, "fill", "cmyk",
                    pmscolors[j].c,
                    pmscolors[j].m,
                    pmscolors[j].y,
                    pmscolors[j].k);
            PDF_setcolor(p, "stroke", "cmyk",
                    pmscolors[j].c,
                    pmscolors[j].m,
                    pmscolors[j].y,
                    pmscolors[j].k);
            sprintf(color,"encoding winansi fillcolor {cmyk %.2f %.2f %.2f %.2f}",
                    pmscolors[j].c,
                    pmscolors[j].m,
                    pmscolors[j].y,
                    pmscolors[j].k);
            sprintf(linecolor,"encoding winansi linewidth .5 bordercolor {cmyk %.2f %.2f %.2f %.2f}",
                    pmscolors[j].c,
                    pmscolors[j].m,
                    pmscolors[j].y,
                    pmscolors[j].k);
            sprintf(backcolor,"encoding winansi backgroundcolor {cmyk %.2f %.2f %.2f %.2f}",
                    pmscolors[j].c,
                    pmscolors[j].m,
                    pmscolors[j].y,
                    pmscolors[j].k);

        }
        PDF_setlinewidth(p,.5);
        if(i==0){
            PDF_fill_textblock(p, page, "bomlabel", bom, 0, color);
            PDF_fill_textblock(p, page, "twelve", "12", 0, color);
            PDF_fill_textblock(p, page, "patent", "Evergreen Packaging Inc.", 0, color);
            PDF_fill_textblock(p, page, "platemaker", platemaker, 0, color);

            if(tolerance_true) {
                printf("    Making box @ x,y coordinates (%f, %f)\n", x,y);
                x=x*72;
                y=y*72;//convert to points
                PDF_rect(p,x,y,72*tolrect_x,72*tolrect_y);
                PDF_stroke(p);
                PDF_moveto(p,x+(tol_cross[0]*72),y);
                PDF_lineto(p,x+(tol_cross[0]*72),y+(tolrect_y*72));
                PDF_stroke(p);
                PDF_moveto(p,x+(tol_cross[1]*72),y);
                PDF_lineto(p,x+(tol_cross[1]*72),y+(tolrect_y*72));
                PDF_stroke(p);
            }
        } else {
            if(tolerance_true) {
                PDF_rect(p,x+(tol_x[i-1]*72),y+(tol_y[0]*72),72*tol_inrect_x,72*tol_inrect_y);
                PDF_fill(p);
                PDF_rect(p,x+(tol_x[i-1]*72),y+(tol_y[1]*72),72*tol_inrect_x,72*tol_inrect_y);
                PDF_fill(p);
            }
        }

        plate_num=(int)((char)plateorder[i]-'0');
        //printf(">> %s\r\n",short_name_match);
        //printf("i: %d  Platenum: %d  Platecode: %s \r\n", i, plate_num, platecode[i]);

		if (PDF_fill_textblock(p, page, plate_label, platecode[i], 0, color) == -1) {
			printf("Error #501: filling plate_label: %s\n", PDF_get_errmsg(p));
		}
		if (strcmp(mark_style, "new") == 0) {
			sprintf(platecount,"%d-%s", plate_num, short_name_match);
			sprintf(platenum,"plate%d", i+1);
		} else {
			sprintf(platecount,"%d", plate_num);
			sprintf(platenum,"plate%d", plate_num);
		}
		PDF_fill_textblock(p, page, platenum, platecount, 0, color);

       //make crosshairs
        if(crosshairs_true) {
            for(n=0;n<2;n++) {
                gstate=PDF_create_gstate(p,"overprintstroke true");
                PDF_set_gstate(p,gstate);
                //horizontal
                if(plate_num==1) {
                    cross_width=4.0*reg_width;
                }else{
                    cross_width= reg_width;
                }
                x1=xc[n]+((plate_num-1)*(reg_width))*72;
               // if(n==0) printf("center of target x,y %f,%f\n",x1/72,yc[n]/72);
                PDF_moveto(p,x1-(reg_width/2)*72,yc[n]);
                PDF_lineto(p,x1-(reg_width/2-cross_width)*72,yc[n]);
                PDF_stroke(p);

                //vertical
                PDF_moveto(p,x1,yc[n]-(reg_height/2)*72);
                PDF_lineto(p,x1,yc[n]+(reg_height/2)*72);
                PDF_stroke(p);
            } // end for()
        } else if(metric_crosshairs_true) {
            for(n=0;n<2;n++){
                gstate=PDF_create_gstate(p,"overprintstroke true");
                PDF_set_gstate(p,gstate);
                //horizontal
                if(plate_num==1) {
                    x1=xc[n];
                    cross_width=3.0*metric_width;
                }
                if (plate_num==2){
                    x1=xc[n];
                    cross_width= metric_width;
                }
                if (plate_num==3){
                    x1=xc[n]+((plate_num-2)*(metric_width))*72;
                     cross_width= metric_width;
                }
                if (plate_num==4){
                    x1=xc[n]+((plate_num-2)*(metric_width))*72;
                    cross_width= metric_width;
                }
               // if(n==0) printf("center of target x,y %f,%f\n",x1/72,yc[n]/72);
                PDF_moveto(p,x1-(metric_width/2)*72,yc[n]);
                PDF_lineto(p,x1-(metric_width/2-cross_width)*72,yc[n]);
                PDF_stroke(p);

                //vertical
                PDF_moveto(p,x1,yc[n]-(metric_height/2)*72);
                PDF_lineto(p,x1,yc[n]+(metric_height/2)*72);
                PDF_stroke(p);
            } // end for()
        } // end if()
    } // end for()

    sprintf(debug,"%s %s ",debug,warning);
    PDF_fill_textblock(p, page, "debug", debug, 0, "encoding winansi");
    PDF_fill_textblock(p, page, "barcode", barcode_num, 0, "encoding winansi");
    PDF_end_layer(p);
    PDF_close_pdi_page(p, page);
    PDF_end_page_ext(p, "");
    PDF_end_document(p, "");
    PDF_close_pdi(p, doc);

    PDF_CATCH(p) {
        printf("PDFlib exception occurred in make_template:\n");
        printf("[%d] %s: %s\n",
        PDF_get_errnum(p), PDF_get_apiname(p), PDF_get_errmsg(p));
        PDF_delete(p);
        printf("\n\r");
        return(2);
    }

    PDF_delete(p);

    }
    printf("\n\r");
    return 0;
}
