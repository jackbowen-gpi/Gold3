"""
Definitions that are specific to the workflow app. This file should never
include other files aside from Django stuff.
"""

# Workflow labels
WORKFLOW_OPTIONS = (
    ("1", "Foodservice"),
    ("2", "Beverage"),
    ("3", "Container"),
    ("4", "Carton"),
)

# Substrate Coating Types
COATING_TYPES = (
    ("C", "Coated"),
    ("U", "Uncoated"),
    ("O", "Other"),
)

PLATE_THICKNESS = (
    ("", "---------"),
    ("0.045", "0.045"),
    ("0.067", "0.067"),
    ("0.107", "0.107"),
)

LOCATION_OPTIONS = (
    ("Outside", "Outside"),
    ("Inside", "Inside"),
)

ITEM_SITUATION_COMPETITOR = 1
ITEM_SITUATION_NEW_JOB = 2
ITEM_SITUATION_SIZE_NOT_NEEDED = 3
ITEM_SITUATION_NO_VOLUME = 4
ITEM_SITUATION_SPECULATIVE = 5
ITEM_SITUATION_WRAPS_ONLY = 6
ITEM_SITUATION_NO_RESPONSE = 7
ITEM_SITUATION_PENDING = 9
ITEM_SITUATION_OTHER = 10
ITEM_SITUATION_COMBO_PACK = 11
SITUATION_OPTIONS = (
    (ITEM_SITUATION_COMPETITOR, "Lost to Competitor"),
    (ITEM_SITUATION_NEW_JOB, "New Job Entered"),
    (ITEM_SITUATION_SIZE_NOT_NEEDED, "Size Not Needed"),
    (ITEM_SITUATION_NO_VOLUME, "Not Enough Volume"),
    (ITEM_SITUATION_SPECULATIVE, "Speculative Art"),
    (ITEM_SITUATION_COMBO_PACK, "Combo Pack Item"),
    (ITEM_SITUATION_WRAPS_ONLY, "Wraps Only"),
    (ITEM_SITUATION_PENDING, "Stalled"),
    (ITEM_SITUATION_NO_RESPONSE, "No Response"),
    (ITEM_SITUATION_OTHER, "Canceled: Other"),
)

JOB_STATUS_PENDING = "Pending"
JOB_STATUS_ACTIVE = "Active"
JOB_STATUS_HOLD = "Hold"
JOB_STATUS_COMPLETE = "Complete"
JOB_STATUS_COMPLETEBILLED = "CompleteBilled"
JOB_STATUS_CANCELLED = "Cancelled"
JOB_STATUS_CLOSEDATP = "ClosedATP"
JOB_STATUS_CLOSEDATS = "ClosedATS"
JOB_STATUS_CLOSEDBTC = "ClosedBTC"
# Job/Item Status
JOB_STATUSES = (
    (JOB_STATUS_PENDING, "Pending"),
    (JOB_STATUS_ACTIVE, "Active"),
    (JOB_STATUS_HOLD, "Hold"),
    (JOB_STATUS_COMPLETE, "Complete"),
    (JOB_STATUS_COMPLETEBILLED, "Complete & Billed"),
    (JOB_STATUS_CANCELLED, "Cancelled"),
    (JOB_STATUS_CLOSEDATP, "Closed - Absorbed to Plant"),
    (JOB_STATUS_CLOSEDATS, "Closed - Absorbed to Sales"),
    (JOB_STATUS_CLOSEDBTC, "Closed - Bill to Customer"),
)

JOB_TYPE_BILLSALES = "BillableSales"
JOB_TYPE_BILLPLANTS = "BillablePlants"
JOB_TYPE_BILLMARKET = "BillableMarketing"
JOB_TYPE_COSTAVOID = "CostAvoidance"
JOB_TYPE_TRANSITION = "Transition"
JOB_TYPE_CREATIVESALES = "CreativeSales"
JOB_TYPE_CREATIVEMARKET = "CreativeMarketing"
# Job types.
JOB_TYPES = (
    (JOB_TYPE_BILLSALES, "Billable - Sales"),
    (JOB_TYPE_BILLPLANTS, "Billable - Plants"),
    (JOB_TYPE_BILLMARKET, "Billable - Marketing"),
    (JOB_TYPE_COSTAVOID, "Cost Avoidance"),
    (JOB_TYPE_TRANSITION, "Transition"),
    (JOB_TYPE_CREATIVESALES, "Creative - Sales"),
    (JOB_TYPE_CREATIVEMARKET, "Creative - Marketing"),
)

CARTON_JOB_TYPE_IMPOSITION = "Imposition"
CARTON_JOB_TYPE_PREPRESS = "Prepress"
# Carton job types.
CARTON_JOB_TYPES = (
    (CARTON_JOB_TYPE_IMPOSITION, "Imposition"),
    (CARTON_JOB_TYPE_PREPRESS, "Prepress"),
)

TODO_LIST_MODE_DEFAULT = 0
TODO_LIST_MODE_STICKIED = 1
TODO_LIST_MODE_HIDDEN = 2
TODO_LIST_MODE_TYPES = (
    (TODO_LIST_MODE_DEFAULT, "Default"),
    (TODO_LIST_MODE_STICKIED, "Stickied"),
    (TODO_LIST_MODE_HIDDEN, "Hidden"),
)
TODO_LIST_MODE_ICONS = {
    TODO_LIST_MODE_DEFAULT: "application_view_list.png",
    TODO_LIST_MODE_STICKIED: "magnifier.png",
    TODO_LIST_MODE_HIDDEN: "zoom_out.png",
}

JOBLOG_BLOCK_ITEMS = 8

# Used to rate a job's relative complexity in FSB ONLY
COMPLEXITY_OPTIONS = (
    ("A", "A"),
    ("B", "B"),
    ("C", "C"),
)

# Indicates the initial state of an FSB job and how much work it will need.
COMPLEXITY_CATEGORIES = (
    ("RebuildNoArt", "Rebuild - No Art"),
    ("RebuildSomeArt", "Rebuild - Some Art"),
    ("NewGPIStraightTemp", "New - GPI Straight Temp"),
    ("NewGPICurvedTemp", "New - GPI Curved Temp"),
    ("NewCompetStraightTemp", "New - Competitor Straight Temp"),
    ("NewCompetCurvedTemp", "New - Competitor Curved Temp"),
    ("RevGPIArt", "Revision - GPI Artwork"),
    ("Creative", "Creative"),
    ("SpecSheet", "Spec Sheet"),
    ("Other", "Other"),
    ("CorrugatedCustom", "Corrugated - Custom"),
    ("CorrugatedAuto", "Corrugated - Auto"),
)

# Used to specify which ink book an item should use.
GCH = 1
PANTONE = 2
OTHER = 3
INKBOOKS = (
    # FSB
    (GCH, "GCH"),
    (PANTONE, "PMS"),
    (OTHER, "OTHER"),
)

# Possibly break this out into another model with fields FK'd to Site?
ITEM_TYPE_HOT_CUP = "HC"
ITEM_TYPE_COLD_CUP = "CC"
ITEM_TYPE_WHITE_PLASTIC = "WP"
ITEM_TYPE_CLEAR_PLASTIC = "CP"
ITEM_TYPE_TRANSLUCENT_PLASTIC = "TP"
ITEM_TYPE_KRAFT = "KB"
ITEM_TYPE_BAG = "BG"
ITEM_TYPE_MISC = "MS"
ITEM_TYPE_CARTON = "CT"
ITEM_TYPE_PANEL = "PN"
ITEM_TYPE_KRAFT_CORRUGATED = "KC"
ITEM_TYPE_WHITE_CORRUGATED = "WC"
ITEM_TYPE_LID = "LD"
ITEM_TYPE_FOOD_TRAY = "FT"
ITEM_TYPE_OTHER = "OT"
ITEM_TYPES = (
    # FSB
    (ITEM_TYPE_HOT_CUP, "Hot Cup"),
    (ITEM_TYPE_COLD_CUP, "Cold Cup"),
    (ITEM_TYPE_WHITE_PLASTIC, "White Plastic"),
    (ITEM_TYPE_CLEAR_PLASTIC, "Clear Plastic"),
    (ITEM_TYPE_TRANSLUCENT_PLASTIC, "Translucent Plastic"),
    (ITEM_TYPE_KRAFT, "Kraft"),
    (ITEM_TYPE_BAG, "Bag"),
    (ITEM_TYPE_MISC, "Misc"),
    # BEV
    (ITEM_TYPE_CARTON, "Carton"),
    (ITEM_TYPE_PANEL, "Panel"),
    # CON
    (ITEM_TYPE_KRAFT_CORRUGATED, "Kraft Corrugated"),
    (ITEM_TYPE_WHITE_CORRUGATED, "White Corrugated"),
    (ITEM_TYPE_LID, "Lid"),
    (ITEM_TYPE_FOOD_TRAY, "Food Tray"),
    (ITEM_TYPE_OTHER, "Other"),
)

# These use variables instead of strings to enforce validity.
COATED_ITEM_TYPES = [ITEM_TYPE_COLD_CUP, ITEM_TYPE_CARTON, ITEM_TYPE_PANEL]
UNCOATED_ITEM_TYPES = [ITEM_TYPE_HOT_CUP]

PRODUCT_CATEGORY_HOT_CUP = 1
PRODUCT_CATEGORY_COLD_CUP = 2
PRODUCT_CATEGORY_FOOD_PACKAGING = 3
PRODUCT_CATEGORY_EVERGREEN_PACKAGING = 4

PRODUCT_CATEGORIES = (
    (PRODUCT_CATEGORY_HOT_CUP, "Hot Cups"),
    (PRODUCT_CATEGORY_COLD_CUP, "Cold Cups"),
    (PRODUCT_CATEGORY_FOOD_PACKAGING, "Food Packaging"),
    (PRODUCT_CATEGORY_EVERGREEN_PACKAGING, "Evergreen Packaging"),
)

# Product substate. Used for FSB Proofing.
PROD_SUBSTRATE_SINGLE_POLY = 1
PROD_SUBSTRATE_DOUBLE_POLY = 2
PROD_SUBSTRATE_CLAY_COAT = 3
PROD_SUBSTRATE_CLEAR_PLASTIC = 4
PROD_SUBSTRATE_WHITE_PLASTIC = 5
PROD_SUBSTRATE_KRAFT = 6
PROD_SUBSTRATE_CLAY_BAG = 7
PROD_SUBSTRATE_NOT_APPLICABLE = 8
PROD_SUBSTRATE_PLA = 9
PROD_SUBSTRATE_CRB = 10
PROD_SUBSTRATE_POST_CONSUMER_FIBER = 11
PROD_SUBSTRATE_TRANSLUCENT_PLASTIC = 12

PROD_SUBSTRATES = (
    (PROD_SUBSTRATE_SINGLE_POLY, "Single Poly"),
    (PROD_SUBSTRATE_DOUBLE_POLY, "Double Poly"),
    (PROD_SUBSTRATE_CLAY_COAT, "Clay Coated"),
    (PROD_SUBSTRATE_CLEAR_PLASTIC, "Clear Plastic"),
    (PROD_SUBSTRATE_WHITE_PLASTIC, "White Plastic"),
    (PROD_SUBSTRATE_TRANSLUCENT_PLASTIC, "Translucent Plastic"),
    (PROD_SUBSTRATE_KRAFT, "Kraft Board"),
    (PROD_SUBSTRATE_CLAY_BAG, "Clay Coated Bag"),
    (PROD_SUBSTRATE_PLA, "PLA"),
    (PROD_SUBSTRATE_CRB, "CRB"),
    (PROD_SUBSTRATE_POST_CONSUMER_FIBER, "Post Consumer Fiber"),
    (PROD_SUBSTRATE_NOT_APPLICABLE, "N/A"),
)

# Product board.
PROD_BOARD_DOUBLE_POLY = 1
PROD_BOARD_SINGLE_POLY = 2
PROD_BOARD_SINGLE_PLA = 3
PROD_BOARD_DOUBLE_PLA = 4
PROD_BOARD_CLAY_COATED = 5
PROD_BOARD_BARE_SBS = 6
PROD_BOARD_KRAFT = 7
PROD_BOARD_CRB = 8
PROD_BOARD_SINGLE_PCF = 9
PROD_BOARD_DOUBLE_PCF = 10
PROD_BOARD_CLEAR_PLASTIC = 11

PROD_BOARDS = (
    (PROD_BOARD_DOUBLE_POLY, "Double Poly"),
    (PROD_BOARD_SINGLE_POLY, "Single Poly"),
    (PROD_BOARD_SINGLE_PLA, "Single PLA"),
    (PROD_BOARD_DOUBLE_PLA, "Double PLA"),
    (PROD_BOARD_CLAY_COATED, "Clay Coated"),
    (PROD_BOARD_BARE_SBS, "Bare SBS"),
    (PROD_BOARD_KRAFT, "Kraft"),
    (PROD_BOARD_CRB, "CRB"),
    (PROD_BOARD_SINGLE_PCF, "Single PCF"),
    (PROD_BOARD_DOUBLE_PCF, "Double PCF"),
    (PROD_BOARD_CLEAR_PLASTIC, "Clear Plastic"),
)

COATED_SUBSTRATES = [PROD_SUBSTRATE_DOUBLE_POLY, PROD_SUBSTRATE_CLAY_COAT]
UNCOATED_SUBSTRATES = [PROD_SUBSTRATE_SINGLE_POLY]

CATEGORIES = {
    "Coated": [PROD_BOARD_DOUBLE_POLY, PROD_BOARD_DOUBLE_PCF, PROD_BOARD_DOUBLE_PLA],
    "Uncoated": [
        PROD_BOARD_SINGLE_POLY,
        PROD_BOARD_SINGLE_PLA,
        PROD_BOARD_SINGLE_PCF,
        PROD_BOARD_BARE_SBS,
    ],
    "Clay_Coated": [PROD_BOARD_CLAY_COATED],
    "Kraft": [PROD_BOARD_KRAFT],
    "CRB": [PROD_BOARD_CRB],
    "Clear_Plastic": [PROD_BOARD_CLEAR_PLASTIC],
}

PLATE_TYPE_CONVENTIONAL_FLEXO = "Conv"
PLATE_TYPE_DIGITAL_FLEXO = "Digi"
PLATE_TYPE_DIGITAL_LUX = "DigiLux"
PLATE_TYPE_DIGITAL_LUX_HD = "DigiLuxHD"
PLATE_TYPE_DIGITAL_LUX_MCD = "DigiLuxMcD"
PLATE_TYPE_RUBBER_FLEXO = "Rub"
PLATE_TYPE_LITHO = "Lth"
PLATE_TYPE_GRAVURE = "Grv"
PLATE_TYPE_OFFSET_FLEXO = "Off"
PLATE_TYPE_OTHER = "Oth"
PLATE_TYPE_NA = "NA"
PLATE_TYPE_CORRUGATED = "Corrugate"
PLATE_TYPE_INTHEROUND = "InTheRound"
PLATE_TYPE_NX = "NX"

PLATE_OPTIONS = (
    (PLATE_TYPE_CONVENTIONAL_FLEXO, "Conventional Flexo"),
    (PLATE_TYPE_DIGITAL_FLEXO, "Digital Flexo"),
    (PLATE_TYPE_DIGITAL_LUX, "Digital Lux"),
    (PLATE_TYPE_DIGITAL_LUX_HD, "Digital Lux HD"),
    (PLATE_TYPE_DIGITAL_LUX_MCD, "Digital Lux McD"),
    (PLATE_TYPE_RUBBER_FLEXO, "Rubber Flexo"),
    (PLATE_TYPE_LITHO, "Litho"),
    (PLATE_TYPE_GRAVURE, "Gravure"),
    (PLATE_TYPE_OFFSET_FLEXO, "Offset Flexo"),
    (PLATE_TYPE_OTHER, "Other"),
    (PLATE_TYPE_NA, "N/A"),
    (PLATE_TYPE_CORRUGATED, "Corrugated"),
    (PLATE_TYPE_INTHEROUND, "InTheRound"),
    (PLATE_TYPE_NX, "NX"),
)

PRINT_PROCESS_FLEXO = "Flexo"
PRINT_PROCESS_OFFSET = "Offset"
PRINT_PROCESS_DRYOFFSET = "Dry Offset"

PRINT_PROCESS_OPTIONS = (
    (PRINT_PROCESS_FLEXO, "Flexo"),
    (PRINT_PROCESS_OFFSET, "Offset"),
    (PRINT_PROCESS_DRYOFFSET, "Dry Offset"),
)

INK_SUPPLIER_SPECIALTY = "Specialty"
INK_SUPPLIER_INX = "INX"

INK_SUPPLIERS = (
    (INK_SUPPLIER_SPECIALTY, "Specialty"),
    (INK_SUPPLIER_INX, "INX"),
)

BILL_TO_TYPES = (
    ("BTC", "Bill To Customer"),
    ("AMO", "Absorbed MFG Operations"),
    ("APR", "Absorbed To Project (2007 RAT)"),
    ("ASN", "Absorbed Sales New"),
    ("ASP", "Absorbed Sales Policy"),
)

BUSINESS_TYPES = (
    ("NEW", "New"),
    ("EXT", "Existing"),
)

PREPRESS_SUPPLIERS = (
    ("OPT", "Optihue"),
    ("PHT", "Phototype"),
    ("SHK", "Schawk"),
    ("SGS", "Southern Graphics"),
)

PREPRESS_SUPPLIERS_EVERGREEN = (("OPT", "Optihue"),)

# Assign stage of production workflow that QC took place -- will help with
# clarification vs. creation date only.
QC_STAGE = (
    ("PR", "Proof"),
    ("RV", "Revision"),
    ("FF", "Final File"),
)

RUSH_TYPES = (
    ("NONE", "None"),
    ("FSBMULTH", "Foodservice High Multiplier"),
    ("FSBMULTL", "Foodservice Low Multiplier"),
)

PROOF_TYPES = (
    ("", "---------"),
    ("COLOR_AND_COPY", "Color and Copy"),
    ("COPY_ONLY", "Copy Only"),
    ("DUPLICATE_PROOF", "Duplicate Proof"),
    ("EDITS_ORIGINAL", "Edits to Original"),
    ("EDITS_ORIGINAL_SWATCHES", "Edits to Original w Swatches"),
)

GDD_ORIGINS = (
    ("", "----"),
    ("CLEMSON", "Clemson"),
    ("CAROL_STREAM", "Carol Stream"),
    ("CONCORD", "Concord"),
)

KD_PRESSES = (
    ("VERNON_5114", "Mt Vernon 5114 42”"),
    ("VERNON_5190", "Mt Vernon 5190 50”"),
    ("LINCOLN", "Lincoln"),
    ("LINCOLN_50", "Lincoln 50”"),
    ("LINCOLN_37_5", "Lincoln 37.5”"),
    ("MARION_5194_50", "Marion 5194 50”"),
    ("SANGER_38", "Sanger 38”"),
    ("SANGER_40", "Sanger 40”"),
    ("SANGER_50", "Sanger 50”"),
    ("SANGER_66", "Sanger 66”"),
    ("WESTROCK_3121", "WestRock 3121 38”"),
    ("WESTROCK_3122", "WestRock 3122 35.4”"),
    ("WESTROCK_3131", "WestRock 3131/32 50”"),
    ("WESTROCK_3133", "WestRock 3133 50”"),
    ("WESTROCK_4521", "WestRock 4521/22 66”"),
)

ART_REC_TYPE_DIGITAL_EMAIL = 1
ART_REC_TYPE_ORIGINAL_ART = 2
ART_REC_TYPE_CLEMSON_CREATE = 3
ART_REC_TYPE_RECREATE_PRINT = 4
ART_REC_TYPE_ISDN_FTP = 5
ART_REC_TYPE_DIGITAL_DISK = 6
ART_REC_TYPE_OTHER = 9
ART_REC_TYPES = (
    (ART_REC_TYPE_DIGITAL_EMAIL, "Digital Art via E-mail"),
    (ART_REC_TYPE_ORIGINAL_ART, "Original Art"),
    (ART_REC_TYPE_CLEMSON_CREATE, "Art to be created by Clemson"),
    (ART_REC_TYPE_RECREATE_PRINT, "Recreate from Print Sample"),
    (ART_REC_TYPE_ISDN_FTP, "ISDN or FTP"),
    (ART_REC_TYPE_DIGITAL_DISK, "Digital art on Disk"),
    (ART_REC_TYPE_OTHER, "Other"),
)
