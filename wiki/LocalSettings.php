<?php
# MediaWiki LocalSettings.php for Gold3 Knowledge Base
$wgSitename = "Gold3 Knowledge Base";
$wgMetaNamespace = "Gold3";

## Server URL (required for MediaWiki)
$wgServer = "http://host.docker.internal:8080";

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

## Manually load Mermaid JavaScript on all pages
$wgHooks['BeforePageDisplay'][] = function( $out, $skin ) {
    $out->addScript( '<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>' );
    $out->addScript( '<script>
        (function() {
            "use strict";

            function initializeMermaid() {
                if (typeof mermaid !== "undefined") {
                    try {
                        mermaid.initialize({
                            startOnLoad: false,
                            theme: "default",
                            securityLevel: "loose"
                        });
                        console.log("Mermaid initialized successfully");

                        // Process all mermaid elements after a short delay
                        setTimeout(function() {
                            var mermaidElements = document.querySelectorAll(".mermaid");
                            if (mermaidElements.length > 0) {
                                console.log("Found " + mermaidElements.length + " mermaid elements");
                                mermaidElements.forEach(function(element, index) {
                                    try {
                                        var id = "mermaid-" + Date.now() + "-" + index;
                                        element.id = id;
                                        mermaid.init(undefined, "#" + id);
                                        console.log("Processed mermaid element:", id);
                                    } catch (error) {
                                        console.error("Error processing mermaid element:", error);
                                    }
                                });
                            }
                        }, 500);
                    } catch (error) {
                        console.error("Mermaid initialization error:", error);
                    }
                } else {
                    console.error("Mermaid library not loaded");
                }
            }

            // Initialize on DOM ready
            if (document.readyState === "loading") {
                document.addEventListener("DOMContentLoaded", initializeMermaid);
            } else {
                initializeMermaid();
            }
        })();
    </script>' );
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
