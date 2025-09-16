<?php
# MediaWiki LocalSettings.php for Gold3 Knowledge Base
$wgSitename = "Gold3 Knowledge Base";
$wgMetaNamespace = "Gold3";

## Server URL (required for MediaWiki)
$wgServer = "http://localhost:8080";

## Force the server URL to be used
$wgForceHTTPS = false;

## Script path
$wgScriptPath = "/";

## Article path (for pretty URLs)
$wgArticlePath = "/index.php/$1";

## Database settings
$wgDBtype = "postgres";
$wgDBserver = "db";
$wgDBport = "5432";
$wgDBname = "wiki_db";
$wgDBuser = "wiki_user";
$wgDBpassword = "wiki_password";

## Shared memory settings
$wgMainCacheType = CACHE_ACCEL;
$wgMemCachedServers = [];

## Image upload settings
$wgEnableUploads = true;
$wgUseImageMagick = true;
$wgImageMagickConvertCommand = "/usr/bin/convert";

## Email settings
$wgEnableEmail = true;
$wgEmergencyContact = "admin@gold3.local";
$wgPasswordSender = "wiki@gold3.local";

## Time zone
$wgLocaltimezone = "America/New_York";

## Language
$wgLanguageCode = "en";

## Secret key (generate a new one for production)
$wgSecretKey = "your-secret-key-change-this-in-production-" . rand();

## Upgrade key (remove after setup)
$wgUpgradeKey = "upgrade-key-change-this-" . rand();

## Enable pretty URLs
$wgUsePathInfo = true;

## Enable subpages
$wgNamespacesWithSubpages[NS_MAIN] = true;

## Enable file uploads
$wgFileExtensions = array( 'png', 'gif', 'jpg', 'jpeg', 'pdf', 'doc', 'xls', 'ppt', 'docx', 'xlsx', 'pptx', 'txt' );

## Enable syntax highlighting
$wgSyntaxHighlightDefaultLang = 'php';

## Enable RSS feeds
$wgFeed = true;

## Enable API
$wgEnableAPI = true;

## Enable write API
$wgEnableWriteAPI = true;

## Skin settings
$wgDefaultSkin = "Timeless";

## Logo (you can add a custom logo later)
# $wgLogo = "/images/logo.png";

## Footer links
$wgFooterIcons = array(
    "poweredby" => array(
        "mediawiki" => array(
            "src" => null,
            "url" => "https://www.mediawiki.org/",
            "alt" => "Powered by MediaWiki",
        )
    )
);

## Enable user tool links
$wgUseAjax = true;

## Enable enhanced recent changes
$wgRCShowChangedSize = true;

## Enable watchlist
$wgUseWatchlist = true;

## Enable anonymous editing for documentation purposes
$wgGroupPermissions['*']['edit'] = true;
$wgGroupPermissions['*']['createpage'] = true;
$wgGroupPermissions['*']['createtalk'] = true;
$wgHiddenPrefs[] = 'nickname';

## Security settings
$wgGroupPermissions['*']['createaccount'] = false;
$wgGroupPermissions['*']['read'] = true;
# Removed conflicting edit permission - using the one above
# $wgGroupPermissions['*']['edit'] = false;

## Allow registered users to edit
$wgGroupPermissions['user']['edit'] = true;

## Allow sysops to do everything
$wgGroupPermissions['sysop']['*'] = true;

## Enable extensions (uncomment as needed)
# wfLoadExtension( 'Cite' );
# wfLoadExtension( 'SyntaxHighlight_GeSHi' );
# wfLoadExtension( 'ParserFunctions' );
# wfLoadExtension( 'WikiEditor' );
# wfLoadExtension( 'VisualEditor' );

## Enable Mermaid extension for diagrams
wfLoadExtension( 'Mermaid' );

## Simple Mermaid configuration - load from CDN
$wgHooks['BeforePageDisplay'][] = function( $out, $skin ) {
    $out->addScript( '<script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>' );
    $out->addScript( '<script>mermaid.initialize({startOnLoad:true,theme:"default",securityLevel:"loose"});</script>' );
    return true;
};

## Load skins
wfLoadSkin( 'MinervaNeue' );
wfLoadSkin( 'MonoBook' );
wfLoadSkin( 'Timeless' );
wfLoadSkin( 'Vector' );

## Timeless skin configuration
$wgTimelessBackdropImage = 'cat';  # Options: 'cat', 'geek', 'mountain', 'ocean', 'custom'
$wgTimelessLogo = null;  # Set to custom logo path if desired
$wgTimelessShowFooterIcons = true;
$wgTimelessEnableClientSideComponents = true;

## General skin configurations - RE-ENABLED for proper display
$wgSkipSkins = [];  # Allow all skins
$wgAllowUserCss = true;
$wgAllowUserJs = true;
$wgUseSiteCss = true;
$wgUseSiteJs = true;
## Essential MediaWiki paths and URLs
$wgResourceBasePath = "http://localhost:8080";
$wgLoadScript = "http://localhost:8080/load.php";
$wgScriptPath = "/";
$wgArticlePath = "/index.php/$1";

## Fix preload issues by disabling problematic resource hints
$wgResourceHints = false;

## Disable preloading of modules that cause issues
$wgPreloadModules = [];

## Configure resource loader for proper functionality
$wgResourceLoaderEnableJS2PHP = true;
$wgResourceLoaderValidateJS = true;  // Re-enable for proper validation
$wgResourceLoaderExperimentalAsyncLoading = false;
$wgResourceLoaderMaxQueryLength = false;
$wgResourceLoaderDebug = false;

## Essential resource loader configuration - COMMENTED OUT PROBLEMATIC ONES
# $wgResourceLoaderSources = [];  // Commented out - may cause array/int type errors
# $wgResourceLoaderLESSVars = [];  // Commented out - may cause issues
# $wgResourceLoaderLESSImportPaths = [];  // Commented out - may cause issues

## Ensure core modules are available - DO NOT DISABLE
# $wgResourceModules = [];  // Commented out - let MediaWiki handle core modules

## Configure resource loader caching
# $wgResourceLoaderMaxage = [
#     'versioned' => [
#         'server' => 30 * 24 * 3600, // 30 days
#         'client' => 30 * 24 * 3600, // 30 days
#     ],
#     'unversioned' => [
#         'server' => 5 * 60, // 5 minutes
#         'client' => 5 * 60, // 5 minutes
#     ],
# ];

## Disable resource loader source map generation
$wgResourceLoaderEnableSourceMapLinks = false;

## Enable detailed error reporting for debugging
$wgShowExceptionDetails = true;
$wgShowDBErrorBacktrace = true;

## Disable problematic extensions that might cause preload issues
# wfLoadExtension( 'Cite' );
# wfLoadExtension( 'SyntaxHighlight_GeSHi' );
# wfLoadExtension( 'ParserFunctions' );
# wfLoadExtension( 'WikiEditor' );
# wfLoadExtension( 'VisualEditor' );

## Additional skin configurations to prevent preload issues
$wgDefaultSkin = "Timeless";
$wgSkipSkins = [];
$wgAllowUserCss = true;
$wgAllowUserJs = true;
$wgUseSiteCss = true;
$wgUseSiteJs = true;

## Disable link preload headers
$wgLinkHeader = false;

## Additional configurations to prevent preload warnings
$wgResourceLoaderEnableJS2PHP = false;  // Disable JS2PHP to prevent preload issues
$wgResourceLoaderExperimentalAsyncLoading = false;
$wgResourceLoaderMaxQueryLength = false;
$wgResourceLoaderDebug = false;

## Disable problematic resource hints completely
$wgResourceHints = false;
$wgPreloadModules = [];

## Disable DNS prefetch and preconnect hints
$wgResourceLoaderDisablePreconnect = true;
$wgResourceLoaderDisableDNS = true;

## Sidebar configuration
$wgSidebar = array(
    'navigation' => array(
        'Documentation' => 'Wiki_Navigation',
        'Table of Contents' => 'Table_of_Contents',
        '*' => 'mainpage-description',
        'recentchanges-url' => 'RecentChanges',
        'randompage-url' => 'Random',
        'helppage' => 'Help:Contents'
    ),
    'TOOLBOX',
    'LANGUAGES'
);
