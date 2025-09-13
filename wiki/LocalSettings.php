<?php
# MediaWiki LocalSettings.php for Gold3 Knowledge Base
$wgSitename = "Gold3 Knowledge Base";
$wgMetaNamespace = "Gold3";

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
$wgDefaultSkin = "vector";

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

## Enable user preferences
$wgHiddenPrefs[] = 'realname';
$wgHiddenPrefs[] = 'nickname';

## Security settings
$wgGroupPermissions['*']['createaccount'] = false;
$wgGroupPermissions['*']['read'] = true;
$wgGroupPermissions['*']['edit'] = false;

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

## End of LocalSettings.php
