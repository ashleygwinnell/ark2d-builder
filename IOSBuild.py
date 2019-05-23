import sys
import os
import errno
import subprocess
import json
import platform
import zlib
import base64
import binascii
import shutil

from Util import *
util = Util();

from Module import *

class IOSBuild:

	def __init__(self, builder):
		self.builder = builder;
		self.deployment_target = "12.1";
		pass;

	def start(self):
		print("Building iOS");

		# open ARK2d config
		f = open(self.builder.ark2d_dir + "/config.json", "r");
		fcontents = f.read();
		f.close();
		ark2dconfig = json.loads(fcontents);

		util.makeDirectories([self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output]);

		gyp_executable = ark2dconfig['osx']['gyp_executable']; #"/Users/ashleygwinnell/Documents/gyp-read-only/gyp";

		if (self.builder.building_library):

			#projectname ark2d
			projectname = "ark2d";

			# generate gyp file.
			print("creating gyp file");
			gypfilename = self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.platform + self.builder.ds + projectname + ".gyp";

			gypfile = {};
			gypfile['defines'] = []; #'ARK2D_IPHONE'];

			gypfile['targets'] = [];

			gypfiletarget = {};
			gypfiletarget['target_name'] = "ark2d-iPhone";
			gypfiletarget['type'] = "static_library";
			gypfiletarget['include_dirs'] = [];
			gypfiletarget['sources'] = [];

			for srcfile in ark2dconfig['src_files']['ios']:
				gypfiletarget['sources'].extend(["../../"+srcfile]);

			for srcfile in ark2dconfig['src_files']['all']:
				gypfiletarget['sources'].extend(["../../"+srcfile]);

			gypfiletarget['sources!'] = [];
			gypfiletarget['dependencies'] = [];
			gypfiletarget['conditions'] = [];
			gypfiletargetcondition = {};
			gypfiletargetcondition['defines'] = [
				'ARK2D_IPHONE',
				"ARK2D_CURRENT_CONFIG=" + self.builder.target_config_name,
				"ARK2D_IOS",
				"PNG_ARM_NEON_OPT=0"
			]; #, 'CF_EXCLUDE_CSTD_HEADERS'];

			if self.builder.debug:
				gypfiletargetcondition['defines'].extend(["ARK2D_DEBUG"]);


			gypfiletargetcondition['sources'] = [];
			gypfiletargetcondition['sources!'] = [];
			gypfiletargetcondition['link_settings'] = {};
			gypfiletargetcondition['link_settings']['libraries'] = [
				#'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/CoreFoundation.framework',
	          	'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/CoreGraphics.framework',
	          	#'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/CoreText.framework',
	          	#'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/UIKit.framework',
	          	"/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk/System/Library/Frameworks/UIKit.framework",
	          	'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/Foundation.framework',
	          	'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/QuartzCore.framework',
	          	'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/OpenGLES.framework'
					              ];
					              #'../../lib/iphone/libfreetype.a


			gypfiletargetcondition['ldflags'] = [
				"-lbz2",
				"-lcurl",
				"-lz",
				"-L" + self.builder.ark2d_dir + "/lib/iphone",
				"-L" + self.builder.ark2d_dir + "/lib/osx",
				"-L/usr/lib"
			];

			gypfiletargetcondition['link_settings!'] = [
				'$(SDKROOT)/System/Library/Frameworks/Cocoa.framework',
	        	'$(SDKROOT)/System/Library/Frameworks/Foundation.framework',
	        	'$(SDKROOT)/System/Library/Frameworks/QuartzCore.framework',
	        	'$(SDKROOT)/System/Library/Frameworks/OpenGL.framework',
	        	'$(SDKROOT)/System/Library/Frameworks/ApplicationServices.framework'
	        	'$(SDKROOT)/System/Library/Frameworks/AVFoundation.framework',
	        	'$(SDKROOT)/System/Library/Frameworks/CoreAudio.framework',
	        	'$(SDKROOT)/System/Library/Frameworks/AudioToolbox.framework'
	        ];

			ark2ddir = self.builder.ark2d_dir + "/src/ARK2D";
			gypfiletargetcondition['include_dirs'] = [
				ark2ddir + '/vendor/iphone',
				ark2ddir + '/vendor/spine/includes',
				ark2ddir + '/vendor/angelscript'
			];

			gypfiletargetcondition['xcode_settings'] = {};
			gypfiletargetcondition['xcode_settings']['ARCHS'] = "$(ARCHS_STANDARD)"; #"armv6 armv7 arm64";
			gypfiletargetcondition['xcode_settings']['IPHONEOS_DEPLOYMENT_TARGET'] = self.deployment_target;
			gypfiletargetcondition['xcode_settings']['SDKROOT'] = "iphoneos";
			gypfiletargetcondition['xcode_settings']['TARGETED_DEVICE_FAMILY'] = "1,2";
			gypfiletargetcondition['xcode_settings']['CLANG_CXX_LANGUAGE_STANDARD'] = "c++0x";
			gypfiletargetcondition['xcode_settings']['CLANG_CXX_LIBRARY'] = "libc++";
			gypfiletargetcondition['xcode_settings']['GCC_C_LANGUAGE_STANDARD'] = "c11";
			gypfiletargetcondition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] = "ARK2D_IPHONE ARK2D_IOS ARK2D_CURRENT_CONFIG=" + self.builder.target_config_name + " PNG_ARM_NEON_OPT=0";
			gypfiletargetcondition['xcode_settings']['GCC_OPTIMIZATION_LEVEL'] = "0";

			if self.builder.debug:
				gypfiletargetcondition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] += " ARK2D_DEBUG";

			#cflags -DNS_BLOCK_ASSERTIONS=1

			#'xcode_settings': {
	        #  'INFOPLIST_FILE' : '../experimental/iOSSampleApp/iOSSampleApp-Info.plist',
	        #  'ARCHS' : 'armv6 armv7',
	        #  'IPHONEOS_DEPLOYMENT_TARGET' : self.deployment_target,
	        #  'SDKROOT' : 'iphoneos',
	        #  'TARGETED_DEVICE_FAMILY' : '1,2',
	        #  'USER_HEADER_SEARCH_PATHS' : '../../gpu/include/** ../../include/**',
	        #  'CODE_SIGN_IDENTITY' : 'iPhone Developer',
	        #  'GCC_PREPROCESSOR_DEFINITIONS' : 'ARK2D_IPHONE',
	        #  'GCC_OPTIMIZATION_LEVEL' : '0',
			#},
			#xcconfigfile = self.builder.game_dir + self.builder.ds + "lib/iphone/ARK2D-Base.xcconfig";
			xcconfigfilesimple = projectname + ".xcconfig";
			xcconfigfile = self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.platform + self.builder.ds + xcconfigfilesimple;

			gypfiletargetcondition['xcode_config_file'] = xcconfigfilesimple;
			gypfiletargetcondition['mac_bundle_resources'] = [];

			iphonecondition = [];
			iphonecondition.extend(["OS == 'mac'"]);
			iphonecondition.extend([gypfiletargetcondition]);
			gypfiletarget['conditions'].extend([iphonecondition]);

			gypfile['targets'].extend([gypfiletarget]);

			print("saving gyp file: " + gypfilename);
			f = open(gypfilename, "w")
			f.write(json.dumps(gypfile, sort_keys=True, indent=4));
			f.close();

			#exit(0);
			#pchfilename = self.builder.game_dir + self.builder.ds + "lib/iphone/" + projectname + "-Prefix.pch";
			pchfilename = self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.platform + self.builder.ds + projectname + "-Prefix.pch";

			#delete xcode project?
			try:
				print("deleting xcode project");
				os.system("rm -r -d " + pchfilename);
				os.system("rm -r -d " + xcconfigfile);
				#os.system("rm -r -d " + self.builder.build_folder + self.builder.ds + self.builder.platform + self.builder.ds + "XcodeData");
				os.system("rm -r -d " + self.builder.build_folder + self.builder.ds + self.builder.platform + self.builder.ds + "DerivedData");
			except:
				print("could not delete xcode project");

			# run gyp file.
			#os.system("python " + gyp_executable + " " + gypfilename + " --depth=../../src");
			os.system("python " + gyp_executable + "_main.py " + gypfilename + " --depth=../../src");

			# add precompiled headers file
			print("generating pch file");

			nl = "\r\n";
			pcheaderfile = "";
			#pcheaderfile += "#ifdef __OBJC__" + nl;
			pcheaderfile += "	#import <Foundation/Foundation.h>" + nl;
			pcheaderfile += "	#import <AVFoundation/AVFoundation.h>" + nl;
			pcheaderfile += "	#import <UIKit/UIKit.h>" + nl + nl;


			pcheaderfile += "	#import <OpenAL/al.h>" + nl;
			pcheaderfile += "	#import <OpenAL/alc.h>" + nl + nl

			pcheaderfile += "	#import <OpenGLES/EAGL.h>" + nl;
			pcheaderfile += "	#import <QuartzCore/QuartzCore.h>" + nl + nl;

			pcheaderfile += "	#import <OpenGLES/ES1/gl.h>" + nl;
			pcheaderfile += "	#import <OpenGLES/ES1/glext.h>" + nl;
			pcheaderfile += "	#import <OpenGLES/ES2/gl.h>" + nl;
			pcheaderfile += "	#import <OpenGLES/ES2/glext.h>" + nl;
			pcheaderfile += "	#import <OpenGLES/EAGLDrawable.h>" + nl + nl;

			pcheaderfile += "	#import <CoreFoundation/CFBundle.h>" + nl;
			pcheaderfile += "	#import <CoreFoundation/CoreFoundation.h>" + nl;

			#pcheaderfile += "#endif";

			print("saving pch file: " + pchfilename);
			f = open(pchfilename, "w")
			f.write(pcheaderfile);
			f.close();

			#print("set the pch manually in xcode, under Apple LLVM compiler 4.1 - Language...");
			#print("set YES and ../../lib/iphone/" + projectname + "-Prefx.pch");

			#create xcconfig file
			print("generating xcconfig file:");
			xcconfigfilecontents = "";
			xcconfigfilecontents += "GCC_PRECOMPILE_PREFIX_HEADER = YES;" + nl;
			#xcconfigfilecontents += "GCC_PREFIX_HEADER = " + pchfilename + ";" + nl;
			xcconfigfilecontents += "SRCROOT = " + self.builder.game_dir + self.builder.ds + "src" + self.builder.ds + "ARK2D" + nl;
			xcconfigfilecontents += "HEADERMAP_INCLUDES_FLAT_ENTRIES_FOR_TARGET_BEING_BUILT = NO;" + nl;
			xcconfigfilecontents += "HEADERMAP_INCLUDES_PROJECT_HEADERS = NO;" + nl;
			xcconfigfilecontents += "HEADERMAP_INCLUDES_FRAMEWORK_ENTRIES_FOR_ALL_PRODUCT_TYPES = NO;" + nl;
			xcconfigfilecontents += "ALWAYS_SEARCH_USER_PATHS = NO;" + nl;
			xcconfigfilecontents += "OTHER_CFLAGS = -x objective-c -fembed-bitcode;" + nl;
			xcconfigfilecontents += "OTHER_CPLUSPLUSFLAGS = -x objective-c++ -fembed-bitcode;" + nl;



			print("saving xcconfig file: " + xcconfigfile);
			f = open(xcconfigfile, "w")
			f.write(xcconfigfilecontents);
			f.close();

			print("done. now compile with the xcode project.");

			exit(0);

		else:
			# building game.
			if "ios" not in self.builder.target_config:
				print("no iOS configuration details");
				return;

			#mkdirs
			try:
				util.makeDirectories([self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output]);
				util.makeDirectories([self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output + self.builder.ds + "data"]);
				util.makeDirectories([self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output + self.builder.ds + "build-cache"]);
			except OSError as exc:
				print("could not mkdirs (iphone) ");
				exit(0);
				pass;

			#projectname ark2d
			projectname = self.builder.game_name_safe; # config['game_short_name'];
			companynamesafe = self.builder.developer_name_safe; #config['company_name_safe'];

			# generate gyp file.
			print("creating gyp file");
			gypfilename = self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output + self.builder.ds + projectname + ".gyp";

			gypfile = {};
			gypfile['defines'] = []; #'ARK2D_IPHONE'];

			gypfile['targets'] = [];

			gypfiletarget = {};
			gypfiletarget['target_name'] = projectname + "-iPhone";
			gypfiletarget['type'] = "executable";
			gypfiletarget['mac_bundle'] = 1;
			#'mac_bundle': 1,
			gypfiletarget['include_dirs'] = [];
			gypfiletarget['sources'] = [];
			gypfiletarget['xcode_framework_dirs'] = [];

			for srcfile in self.builder.game_config['src_files']:
				gypfiletarget['sources'].extend(["../../"+srcfile]);

			gypfiletarget['sources!'] = [];
			gypfiletarget['dependencies'] = [];
			gypfiletarget['conditions'] = [];
			gypfiletargetcondition = {};
			gypfiletargetcondition['defines'] = [
				'ARK2D_IPHONE',
				'ARK2D_IOS',
				"ARK2D_CURRENT_CONFIG=" + self.builder.target_config_name,
				"GAME_MAJOR_VERSION=" + self.builder.game_version_major,
				"GAME_MINOR_VERSION=" + self.builder.game_version_minor,
				"GAME_PATCH_VERSION=" + self.builder.game_version_patch,
				'PNG_ARM_NEON_OPT=0'
			]; #, 'CF_EXCLUDE_CSTD_HEADERS'];

			if self.builder.debug:
				gypfiletargetcondition['defines'].extend(["ARK2D_DEBUG"]);

			gypfiletargetcondition['sources'] = [];

			gypfiletargetcondition['actions'] = [
				{
					'action_name': 'Copy game assets into Xcode project',
					'inputs': [],
					'outputs': [],
					'action': [
						'cp',
						'-r',
						self.builder.game_resources_dir + '/',
						self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output + self.builder.ds + "data/"
					],
					'message': 'copy game assets'
				},
				{
					'action_name': 'Copy ark2d assets into Xcode project',
					'inputs': [],
					'outputs': [],
					'action': [
						'cp',
						'-r',
						self.builder.ark2d_dir + '/data/',
						self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output + self.builder.ds + 'data/ark2d/'
					],
					'message': 'copy ark2d assets'
				}
			];
			# TODO above is similar to MacBuild.


			gypfiletargetcondition['sources!'] = [];
			gypfiletargetcondition['link_settings'] = {};
			gypfiletargetcondition['link_settings']['libraries'] = [
				'$(SDKROOT)/System/Library/Frameworks/AVFoundation.framework',
				'$(SDKROOT)/System/Library/Frameworks/CoreAudio.framework',
				'$(SDKROOT)/System/Library/Frameworks/AudioToolbox.framework',
				'$(SDKROOT)/System/Library/Frameworks/CoreFoundation.framework',
	          	'$(SDKROOT)/System/Library/Frameworks/CoreGraphics.framework',
	          	'$(SDKROOT)/System/Library/Frameworks/Foundation.framework',
	          	'$(SDKROOT)/System/Library/Frameworks/QuartzCore.framework',
	          	'$(SDKROOT)/System/Library/Frameworks/OpenAL.framework',
	          	'$(SDKROOT)/System/Library/Frameworks/GameKit.framework',
	          	'$(SDKROOT)/System/Library/Frameworks/SystemConfiguration.framework',
	          	'$(SDKROOT)/System/Library/Frameworks/CoreData.framework',
	          	'$(SDKROOT)/System/Library/Frameworks/OpenGLES.framework',
	          	'$(SDKROOT)/System/Library/Frameworks/UIKit.framework',
	          	'$(SDKROOT)/System/Library/Frameworks/StoreKit.framework',
	          	self.builder.ark2d_dir + '/lib/iphone/libfreetype.a',
	          	self.builder.ark2d_dir + '/lib/iphone/libfreetype-simulator.a',
	          	self.builder.ark2d_dir + '/lib/iphone/libangelscriptd.a',
	          	'$(SDKROOT)/System/usr/lib/libsqlite3.tbd', #requried for GA
	          	self.builder.ark2d_dir + '/lib/iphone/libGoogleAnalyticsServices.a',
	          	self.builder.ark2d_dir + '/build/ios/DerivedData/ark2d-ios/Build/Products/Default-iphoneos/libark2d-iPhone.a',
	          	self.builder.ark2d_dir + '/build/ios/DerivedData/ark2d-ios/Build/Products/Default-iphonesimulator/libark2d-iPhonesimulator.a'
			];



			gypfiletargetcondition['ldflags'] = [ ];

			gypfiletargetcondition['link_settings!'] = [];

			ark2ddir = self.builder.ark2d_dir + "/src/ARK2D";
			gypfiletargetcondition['include_dirs'] = [
				self.builder.ark2d_dir + "/src",
				ark2ddir,
				ark2ddir + '/vendor/iphone',
				ark2ddir + '/vendor/spine/includes',
				ark2ddir + '/vendor/angelscript'
			];
			gypfiletargetcondition['xcode_framework_dirs'] = [];

			gypfiletargetcondition['xcode_settings'] = {};
			gypfiletargetcondition['xcode_settings']['ARCHS'] = "$(ARCHS_STANDARD)";#"armv6 armv7 arm64";
			gypfiletargetcondition['xcode_settings']['IPHONEOS_DEPLOYMENT_TARGET'] = self.deployment_target;
			gypfiletargetcondition['xcode_settings']['SDKROOT'] = "iphoneos";
			gypfiletargetcondition['xcode_settings']['TARGETED_DEVICE_FAMILY'] = "1,2";
			gypfiletargetcondition['xcode_settings']['CLANG_CXX_LANGUAGE_STANDARD'] = "c++0x";
			gypfiletargetcondition['xcode_settings']['CLANG_CXX_LIBRARY'] = "libc++";
			gypfiletargetcondition['xcode_settings']['GCC_C_LANGUAGE_STANDARD'] = "c11";
			gypfiletargetcondition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] = "";
			gypfiletargetcondition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] += "ARK2D_IPHONE ";
			gypfiletargetcondition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] += "ARK2D_IOS ";
			gypfiletargetcondition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] += "ARK2D_CURRENT_CONFIG=" + self.builder.target_config_name + " ";
			gypfiletargetcondition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] += "GAME_MAJOR_VERSION=" + self.builder.game_version_major + " ";
			gypfiletargetcondition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] += "GAME_MINOR_VERSION=" + self.builder.game_version_minor + " ";
			gypfiletargetcondition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] += "GAME_PATCH_VERSION=" + self.builder.game_version_patch + " ";
			gypfiletargetcondition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] += "PNG_ARM_NEON_OPT=0";
			gypfiletargetcondition['xcode_settings']['GCC_OPTIMIZATION_LEVEL'] = "0";
			gypfiletargetcondition['xcode_settings']['FRAMEWORK_SEARCH_PATHS'] = []

			if self.builder.debug:
				gypfiletargetcondition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] += " ARK2D_DEBUG";

			xcconfigfilesimple = projectname + ".xcconfig";
			xcconfigfile = self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output + self.builder.ds + xcconfigfilesimple;

			gypfiletargetcondition['xcode_config_file'] = xcconfigfilesimple;
			gypfiletargetcondition['mac_bundle_resources'] = [
				#self.builder.game_name_safe + "-iPhone/Images.xcassets",

				"data/",				#ark2d and game data
				"Images.xcassets/",		#icons/launchimages
				"Launch.storyboard",#launch-storyboard

				# "Icon.png",				#iphone
				# "Icon@2x.png",			#iphone-retina
				# "Icon-Small.png",		#iphone-spotlight
				# "Icon-Small@2x.png",	#iphone-spotlight-retina

				# "Icon-72.png",			#ipad
				# "Icon-72@2x.png",		#ipad-retina
				# "Icon-Small-50.png",	#ipad-spotlight
				# "Icon-Small-50@2x.png",	#ipad-spotlight-retina

				# "Icon-40.png", 			#ios7
				# "Icon-80.png", 			#ios7
				# "Icon-120.png", 		#ios7

				# "Icon-76.png", 			#ios7
				# "Icon-152.png", 		#ios7
				# "Icon-167.png", 		#ios...9?

				# "iTunesArtwork", 		#app-store-icon
				# "iTunesArtwork@2x", 	#app-store-icon-retina
				# "iTunesArtwork@2x", 	#app-store-icon-retina
			];
			if "icloud" in self.builder.ios_config and self.builder.ios_config["icloud"] == True:
				gypfiletargetcondition['mac_bundle_resources'].extend(["Settings.bundle"]);

			iphonecondition = [];
			iphonecondition.extend(["OS == 'mac'"]);
			iphonecondition.extend([gypfiletargetcondition]);
			gypfiletarget['conditions'].extend([iphonecondition]);

			gypfile['targets'].extend([gypfiletarget]);


			# simulator target
			"""
			gypfiletarget_simulator = {};
			gypfiletarget_simulator['target_name'] = projectname + "-iPhoneSimulator";
			gypfiletarget_simulator['type'] = "executable";
			gypfiletarget_simulator['mac_bundle'] = 1;
			#'mac_bundle': 1,
			gypfiletarget_simulator['include_dirs'] = [];
			gypfiletarget_simulator['sources'] = [];

			for srcfile in config['game_src_files']:
				gypfiletarget_simulator['sources'].extend(["../../"+srcfile]);

			gypfiletarget_simulator['sources!'] = [];
			gypfiletarget_simulator['dependencies'] = [];
			gypfiletarget_simulator['conditions'] = [];
			gypfiletarget_simulator_condition = {};
			gypfiletarget_simulator_condition['defines'] = ['ARK2D_IPHONE']; #, 'CF_EXCLUDE_CSTD_HEADERS'];

			if self.builder.debug:
				gypfiletarget_simulator_condition['defines'].extend(["ARK2D_DEBUG"]);

			gypfiletarget_simulator_condition['sources'] = [];
			gypfiletarget_simulator_condition['sources!'] = [];
			gypfiletarget_simulator_condition['link_settings'] = {};
			gypfiletarget_simulator_condition['link_settings']['libraries'] = [
				'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/AVFoundation.framework',
				'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/CoreAudio.framework',
				'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/AudioToolbox.framework',
				'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/CoreFoundation.framework',
	          	'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/CoreGraphics.framework',
	          	'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/UIKit.framework',
	          	'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/Foundation.framework',
	          	'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/QuartzCore.framework',
	          	'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/OpenGLES.framework',
	          	'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/OpenAL.framework',
	          	'/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS4.3.sdk/System/Library/Frameworks/GameKit.framework',
	          	#'../../lib/iphone/libfreetype.a'
	          	config['osx']['ark2d_dir'] + '/lib/iphone/libfreetype.a',
	          	config['osx']['ark2d_dir'] + '/lib/osx/libcurl.a',

	          	config['osx']['ark2d_dir'] + '/build/iphone/DerivedData/ark2d/Build/Products/Default-iphonesimulator/libark2d-iPhone.a'
					              ];
					              #'../../lib/iphone/libfreetype.a


			gypfiletarget_simulator_condition['ldflags'] = [ ];

			gypfiletarget_simulator_condition['link_settings!'] = [];

			ark2ddir = config['osx']['ark2d_dir'] + "/src/ARK2D";
			gypfiletarget_simulator_condition['include_dirs'] = [
				ark2ddir,
				ark2ddir + '/vendor/iphone'
			];

			gypfiletarget_simulator_condition['xcode_settings'] = {};
			gypfiletarget_simulator_condition['xcode_settings']['ARCHS'] = "armv6 armv7";
			gypfiletarget_simulator_condition['xcode_settings']['IPHONEOS_DEPLOYMENT_TARGET'] = self.deployment_target;
			gypfiletarget_simulator_condition['xcode_settings']['SDKROOT'] = "iphonesimulator";
			gypfiletarget_simulator_condition['xcode_settings']['TARGETED_DEVICE_FAMILY'] = "1,2";
			gypfiletarget_simulator_condition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] = "ARK2D_IPHONE";
			gypfiletarget_simulator_condition['xcode_settings']['GCC_OPTIMIZATION_LEVEL'] = "0";

			if self.builder.debug:
				gypfiletarget_simulator_condition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] += " ARK2D_DEBUG";

			xcconfigfilesimple = projectname + ".xcconfig";
			xcconfigfile = self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.platform + self.builder.ds + xcconfigfilesimple;

			gypfiletarget_simulator_condition['xcode_config_file'] = xcconfigfilesimple;
			gypfiletarget_simulator_condition['mac_bundle_resources'] = [
				"data/",				#ark2d and game data

				"Icon.png",				#iphone
				"Icon@2x.png",			#iphone-retina
				"Icon-Small.png",		#iphone-spotlight
				"Icon-Small@2x.png",	#iphone-spotlight-retina

				"Icon-72.png",			#ipad
				"Icon-72@2x.png",		#ipad-retina
				"Icon-Small-50.png",	#ipad-spotlight
				"Icon-Small-50@2x.png",	#ipad-spotlight-retina

				"iTunesArtwork", 		#app-store-icon
				"iTunesArtwork@2x", 	#app-store-icon-retina
			];

			iphonecondition_simulator = [];
			iphonecondition_simulator.extend(["OS == 'mac'"]);
			iphonecondition_simulator.extend([gypfiletarget_simulator_condition]);
			gypfiletarget_simulator['conditions'].extend([iphonecondition_simulator]);

			gypfile['targets'].extend([gypfiletarget_simulator]);
			"""

			gypfiletarget['sources'].extend( [self.builder.ds + "Images.xcassets"] );
			# = gypfiletarget['source'];


			# add custom modules to GYP
			self.moduleLinkerFlags = "";

			print("Add external modules to project")
			if "external_modules" in self.builder.target_config:
				for module in self.builder.target_config['external_modules']:
					print module

					try:
						moduleJsonFilename = module + self.builder.ds + "module.json"
						f = open(moduleJsonFilename, "r")
						fcontents = f.read();
						f.close();
						fjson = json.loads(fcontents);

						print  (fjson);

						moduleObj = Module(self.builder, module);
						moduleObj.initFromConfig(fjson);

						print (moduleObj);

						moduleObj.addToGypConfig('ios', gypfiletarget, gypfiletargetcondition);
						ModuleUtil.addToIOSBuild(moduleObj, self);

					except OSError as exc:
						print("Module config was not valid.");
						print(exc);
						exit(0);


					#####

			#if "onesignal" in self.builder.ios_config:
			#	gypfiletargetcondition['link_settings']['libraries'].extend( [ self.builder.ios_config['onesignal']['sdk_dir'] ] );
				#gypfiletargetcondition['link_settings']['libraries'].extend( [ "$(SDKROOT)/System/Library/Frameworks/SystemConfiguration.framework" ] );

			#print("Add libraries to project ")
			"""
			if "game_libraries" in config:
				for gamelibrary in config['game_libraries']:
					gamelibraryname = gamelibrary['name'];
					if "iphone" in gamelibrary:
						if "os" in gamelibrary['iphone']:
							gypfiletargetcondition['link_settings']['libraries'].extend([self.builder.game_dir + self.builder.ds + gamelibrary['iphone']['os']]);
			"""
			# if "native_libraries" in self.builder.ios_config:
			# 	for nativelib in self.builder.ios_config['native_libraries']:
			# 		if "os" in nativelib:
			# 			for lib in nativelib['os']:
			# 				gypfiletargetcondition['link_settings']['libraries'].extend([self.builder.game_dir + self.builder.ds + lib]);





			print("saving gyp file: " + gypfilename);
			f = open(gypfilename, "w")
			f.write(json.dumps(gypfile, sort_keys=True, indent=4));
			f.close();



			#delete xcode project?
			pchfilename = self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output + self.builder.ds + projectname + "-Prefix.pch";
			info_plist_filename = self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output + self.builder.ds + projectname + "-Info.plist";
			try:
				print("deleting xcode project");
				os.system("rm -r -d " + pchfilename);
				os.system("rm -r -d " + info_plist_filename);
				os.system("rm -r -d " + xcconfigfile);
				os.system("rm -r -d " + self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output + self.builder.ds + "DerivedData");
			except:
				print("could not delete xcode project");

			# run gyp file.
			#os.system("python " + gyp_executable + " " + gypfilename + " --depth=../../src");
			os.system("python " + gyp_executable + "_main.py " + gypfilename + " --depth=../../src");

			# add precompiled headers file
			print("generating pch file");

			nl = "\r\n";
			pcheaderfile = "";
			#pcheaderfile += "#ifdef __OBJC__" + nl;
			pcheaderfile += "	#import <Foundation/Foundation.h>" + nl;
			pcheaderfile += "	#import <AVFoundation/AVFoundation.h>" + nl;
			pcheaderfile += "	#import <UIKit/UIKit.h>" + nl + nl;


			pcheaderfile += "	#import <OpenAL/al.h>" + nl;
			pcheaderfile += "	#import <OpenAL/alc.h>" + nl + nl

			pcheaderfile += "	#import <OpenGLES/EAGL.h>" + nl;
			pcheaderfile += "	#import <QuartzCore/QuartzCore.h>" + nl + nl;

			pcheaderfile += "	#import <OpenGLES/ES1/gl.h>" + nl;
			pcheaderfile += "	#import <OpenGLES/ES1/glext.h>" + nl;
			pcheaderfile += "	#import <OpenGLES/ES2/gl.h>" + nl;
			pcheaderfile += "	#import <OpenGLES/ES2/glext.h>" + nl;
			pcheaderfile += "	#import <OpenGLES/EAGLDrawable.h>" + nl + nl;

			pcheaderfile += "	#import <CoreFoundation/CFBundle.h>" + nl;
			pcheaderfile += "	#import <CoreFoundation/CoreFoundation.h>" + nl;

			#pcheaderfile += "#endif";

			print("saving pch file: " + pchfilename);
			f = open(pchfilename, "w")
			f.write(pcheaderfile);
			f.close();

			print ("generating project-Info.plist file");
			info_plist_contents = "";
			info_plist_contents += '<?xml version="1.0" encoding="UTF-8"?>' + nl;
			info_plist_contents += '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">' + nl;
			info_plist_contents += '<plist version="1.0">' + nl;
			info_plist_contents += '<dict>' + nl;
			info_plist_contents += '	<key>UIViewControllerBasedStatusBarAppearance</key>' + nl;
			info_plist_contents += '	<false/>' + nl;
			info_plist_contents += '	<key>CFBundleDevelopmentRegion</key>' + nl;
			info_plist_contents += '	<string>en</string>' + nl;
			info_plist_contents += '	<key>CFBundleDisplayName</key>' + nl;
			info_plist_contents += '	<string>' + self.builder.game_name + '</string>' + nl;
			info_plist_contents += '	<key>CFBundleExecutable</key>' + nl;
			info_plist_contents += '	<string>${EXECUTABLE_NAME}</string>' + nl;

			info_plist_contents += '	<key>UILaunchStoryboardName</key>' + nl;
			info_plist_contents += '	<string>Launch</string>' + nl;

			info_plist_contents += '	<key>CFBundleIconFile</key>' + nl;
			info_plist_contents += '	<string></string>' + nl;

			info_plist_contents += '	<key>CFBundleIconFiles</key>' + nl;
			info_plist_contents += '	<array>' + nl;
			info_plist_contents += '		<string></string>' + nl;
			info_plist_contents += '		<string>Icon.png</string>' + nl;					#iphone
			info_plist_contents += '		<string>Icon@2x.png</string>' + nl;					#iphone-retina
			info_plist_contents += '		<string>Icon-Small.png</string>' + nl;				#iphone-spotlight
			info_plist_contents += '		<string>Icon-Small@2x.png</string>' + nl;			#iphone-spotlight-retina
			info_plist_contents += '		<string>Icon-72.png</string>' + nl;					#ipad
			info_plist_contents += '		<string>Icon-72@2x.png</string>' + nl;				#ipad-retina
			info_plist_contents += '		<string>Icon-Small-50.png</string>' + nl;			#ipad-spotlight
			info_plist_contents += '		<string>Icon-Small-50@2x.png</string>' + nl;		#ipad-spotlight-retina
			info_plist_contents += '		<string>Icon-40.png</string>' + nl;					#ios7
			info_plist_contents += '		<string>Icon-80.png</string>' + nl;					#ios7
			info_plist_contents += '		<string>Icon-120.png</string>' + nl;				#ios7
			info_plist_contents += '		<string>Icon-76.png</string>' + nl;					#ios7
			info_plist_contents += '		<string>Icon-152.png</string>' + nl;				#ios7
			info_plist_contents += '		<string>Icon-167.png</string>' + nl;				#ios7
			info_plist_contents += '	</array>' + nl;

			info_plist_contents += '	<key>CFBundleIcons</key>' + nl;
			info_plist_contents += '	<dict>' + nl;
			info_plist_contents += '		<key>CFBundlePrimaryIcon</key>' + nl;
			info_plist_contents += '		<dict>' + nl;
			info_plist_contents += '			<key>CFBundleIconFiles</key>' + nl;
			info_plist_contents += '			<array>' + nl;
			info_plist_contents += '				<string></string>' + nl;
			info_plist_contents += '				<string>Icon.png</string>' + nl;				#iphone
			info_plist_contents += '				<string>Icon@2x.png</string>' + nl;				#iphone-retina
			info_plist_contents += '				<string>Icon-Small.png</string>' + nl;			#iphone-spotlight
			info_plist_contents += '				<string>Icon-Small@2x.png</string>' + nl;		#iphone-spotlight-retina
			info_plist_contents += '				<string>Icon-72.png</string>' + nl;				#ipad
			info_plist_contents += '				<string>Icon-72@2x.png</string>' + nl;			#ipad-retina
			info_plist_contents += '				<string>Icon-Small-50.png</string>' + nl;		#ipad-spotlight
			info_plist_contents += '				<string>Icon-Small-50@2x.png</string>' + nl;	#ipad-spotlight-retina
			info_plist_contents += '				<string>Icon-40.png</string>' + nl;					#ios7
			info_plist_contents += '				<string>Icon-80.png</string>' + nl;					#ios7
			info_plist_contents += '				<string>Icon-120.png</string>' + nl;				#ios7
			info_plist_contents += '				<string>Icon-76.png</string>' + nl;					#ios7
			info_plist_contents += '				<string>Icon-152.png</string>' + nl;				#ios7
			info_plist_contents += '				<string>Icon-167.png</string>' + nl;				#ios7
			info_plist_contents += '			</array>' + nl;

			info_plist_contents += '			<key>UIPrerenderedIcon</key>' + nl;
			if self.builder.ios_config['icon']['prerendered']:
				info_plist_contents += '			<true/>' + nl;

			info_plist_contents += '		</dict>' + nl;
			info_plist_contents += '	</dict>' + nl;


			info_plist_contents += '	<key>CFBundleIdentifier</key>' + nl;
			info_plist_contents += '	<string>org.' + companynamesafe + '.' + projectname + '</string>' + nl;
			info_plist_contents += '	<key>CFBundleInfoDictionaryVersion</key>' + nl;
			info_plist_contents += '	<string>' + self.deployment_target + '</string>' + nl;
			info_plist_contents += '	<key>CFBundleName</key>' + nl;
			info_plist_contents += '	<string>${PRODUCT_NAME}</string>' + nl;
			info_plist_contents += '	<key>CFBundlePackageType</key>' + nl;
			info_plist_contents += '	<string>APPL</string>' + nl;
			info_plist_contents += '	<key>CFBundleShortVersionString</key>' + nl;
			info_plist_contents += '	<string>' + self.builder.game_version + '</string>' + nl;
			info_plist_contents += '	<key>CFBundleSignature</key>' + nl;
			info_plist_contents += '	<string>????</string>' + nl;
			info_plist_contents += '	<key>CFBundleVersion</key>' + nl;
			info_plist_contents += '	<string>' + self.builder.game_version + '</string>' + nl;
			info_plist_contents += '	<key>LSRequiresIPhoneOS</key>' + nl;
			info_plist_contents += '	<true/>' + nl;
			info_plist_contents += '	<key>UIPrerenderedIcon</key>' + nl;
			if self.builder.ios_config['icon']['prerendered']:
				info_plist_contents += '		<true/>' + nl;
			else:
				info_plist_contents += '		<false/>' + nl;

			if "onesignal" in self.builder.ios_config:
				info_plist_contents += '	<key>UIBackgroundModes</key>' + nl;
				info_plist_contents += '	<array>' + nl;
				info_plist_contents += '		<string>remote-notification</string>' + nl;
				info_plist_contents += '	</array>' + nl;

			info_plist_contents += '	<key>UIRequiredDeviceCapabilities</key>' + nl;
			info_plist_contents += '	<array>' + nl;
			info_plist_contents += '		<string>gamekit</string>' + nl;
			info_plist_contents += '	</array>' + nl;

			info_plist_contents += '	<key>UIStatusBarHidden</key>' + nl;
			info_plist_contents += '	<true/>' + nl;

			info_plist_contents += '	<key>UIRequiresFullScreen</key>' + nl;
			info_plist_contents += '	<true/>' + nl;

			info_plist_contents += '	<key>UISupportedInterfaceOrientations</key>' + nl;
			info_plist_contents += '	<array>' + nl;
			if (self.builder.game_orientation == "portrait"):
				info_plist_contents += '	<string>UIInterfaceOrientationPortrait</string>' + nl;
			elif(self.builder.game_orientation == "landscape"):
				info_plist_contents += '	<string>UIInterfaceOrientationLandscapeRight</string>' + nl;

			info_plist_contents += '	</array>' + nl;

			info_plist_contents += '	<key>NSAppTransportSecurity</key>' + nl;
			info_plist_contents += '	<dict>' + nl;
			info_plist_contents += '		<!--Include to allow all connections (DANGER)-->' + nl;
			info_plist_contents += '		<key>NSAllowsArbitraryLoads</key>' + nl;
			info_plist_contents += '		<true/>' + nl;
			info_plist_contents += '	</dict>' + nl;

			info_plist_contents += '</dict>' + nl;
			info_plist_contents += '</plist>';

			print("saving project-Info.plist file");
			f = open(info_plist_filename, "w")
			f.write(info_plist_contents);
			f.close();


			#print("set the pch manually in xcode, under Apple LLVM compiler 4.1 - Language...");
			#print("set YES and ../../lib/iphone/" + projectname + "-Prefx.pch");

			#create xcconfig file
			print("generating xcconfig file:");
			xcconfigfilecontents = "";
			xcconfigfilecontents += "GCC_PRECOMPILE_PREFIX_HEADER = YES;" + nl;
			#xcconfigfilecontents += "GCC_PREFIX_HEADER = " + pchfilename + ";" + nl;
			xcconfigfilecontents += "SRCROOT = " + self.builder.game_dir + self.builder.ds + "src" + self.builder.ds + "ARK2D" + nl;
			xcconfigfilecontents += "HEADERMAP_INCLUDES_FLAT_ENTRIES_FOR_TARGET_BEING_BUILT = NO;" + nl;
			xcconfigfilecontents += "HEADERMAP_INCLUDES_PROJECT_HEADERS = NO;" + nl;
			xcconfigfilecontents += "HEADERMAP_INCLUDES_FRAMEWORK_ENTRIES_FOR_ALL_PRODUCT_TYPES = NO;" + nl;
			xcconfigfilecontents += "ALWAYS_SEARCH_USER_PATHS = NO;" + nl;
			xcconfigfilecontents += "OTHER_CFLAGS = -x objective-c -fembed-bitcode;" + nl;
			xcconfigfilecontents += "OTHER_CPLUSPLUSFLAGS = -x objective-c++ -fembed-bitcode;" + nl;
			xcconfigfilecontents += "OTHER_LDFLAGS = " + self.moduleLinkerFlags + " -lbz2 -lcurl -lz;" + nl;
			xcconfigfilecontents += "INFOPLIST_FILE = " + info_plist_filename  + nl;
			xcconfigfilecontents += "ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon" + nl;
			xcconfigfilecontents += "ASSETCATALOG_COMPILER_LAUNCHIMAGE_NAME = LaunchImage" + nl;


			print("saving xcconfig file: " + xcconfigfile);
			f = open(xcconfigfile, "w")
			f.write(xcconfigfilecontents);
			f.close();

			# build settings bundle file.
			print("generating Settings.bundle file...");
			xc_settings_folder = self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output + self.builder.ds + "Settings.bundle";
			util.makeDirectories([xc_settings_folder]);
			util.makeDirectories([xc_settings_folder + self.builder.ds + "en.lproj"]);

			xc_settings_rootstrings_file = xc_settings_folder + self.builder.ds + "en.lproj" + self.builder.ds + "Root.strings";
			xc_settings_rootstrings_contents = "/* A single strings file, whose title is specified in your preferences schema. The strings files provide the localized content to display to the user for each of your preferences. */" + nl;
			xc_settings_rootstrings_contents = "/* Warning: generating by ark2d-build */" + nl;
			xc_settings_rootstrings_contents += "\"Group\" = \"Group\";" + nl;
			xc_settings_rootstrings_contents += "\"General\" = \"General\";" + nl;
			xc_settings_rootstrings_contents += "\"iCloud\" = \"iCloud\";" + nl;
			xc_settings_rootstrings_contents += "\"Name\" = \"Name\";" + nl;
			xc_settings_rootstrings_contents += "\"none given\" = \"none given\";" + nl;
			xc_settings_rootstrings_contents += "\"Enabled\" = \"Enabled\";" + nl;
			f = open(xc_settings_rootstrings_file, "w"); f.write(xc_settings_rootstrings_contents); f.close();

			xc_settings_rootplist_file = xc_settings_folder + self.builder.ds + "Root.plist";
			xc_settings_rootplist_contents = "";
			xc_settings_rootplist_contents += '<?xml version="1.0" encoding="UTF-8"?>' + nl;
			xc_settings_rootplist_contents += '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">' + nl;
			xc_settings_rootplist_contents += '<plist version="1.0">' + nl;
			xc_settings_rootplist_contents += '<dict>' + nl;
			xc_settings_rootplist_contents += '	<key>StringsTable</key>' + nl;
			xc_settings_rootplist_contents += '	<string>Root</string>' + nl;
			xc_settings_rootplist_contents += '	<key>PreferenceSpecifiers</key>' + nl;
			xc_settings_rootplist_contents += '	<array>' + nl;
			xc_settings_rootplist_contents += '		<dict>' + nl;
			xc_settings_rootplist_contents += '			<key>Type</key>' + nl;
			xc_settings_rootplist_contents += '			<string>PSGroupSpecifier</string>' + nl;
			xc_settings_rootplist_contents += '			<key>Title</key>' + nl;
			xc_settings_rootplist_contents += '			<string>General</string>' + nl;
			xc_settings_rootplist_contents += '		</dict>' + nl;

			if "icloud" in self.builder.ios_config and self.builder.ios_config["icloud"] == True:
				xc_settings_rootplist_contents += '		<dict>' + nl;
				xc_settings_rootplist_contents += '			<key>Type</key>' + nl;
				xc_settings_rootplist_contents += '			<string>PSToggleSwitchSpecifier</string>' + nl;
				xc_settings_rootplist_contents += '			<key>Title</key>' + nl;
				xc_settings_rootplist_contents += '			<string>iCloud</string>' + nl;
				xc_settings_rootplist_contents += '			<key>Key</key>' + nl;
				xc_settings_rootplist_contents += '			<string>setting_icloud</string>' + nl;
				xc_settings_rootplist_contents += '			<key>DefaultValue</key>' + nl;
				xc_settings_rootplist_contents += '			<true/>' + nl;
				xc_settings_rootplist_contents += '		</dict>' + nl;

			xc_settings_rootplist_contents += '	</array>' + nl;
			xc_settings_rootplist_contents += '</dict>' + nl;
			xc_settings_rootplist_contents += '</plist>' + nl;
			f = open(xc_settings_rootplist_file, "w"); f.write(xc_settings_rootplist_contents); f.close();

			# copy game resources in to project data folder.
			#subprocess.call(["cp -r " + config['osx']['game_resources_dir'] + " " + self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output + self.builder.ds + "data/"], shell=True); #libark2d
			self.builder.processAssets();

			# copy game resources in to project data folder
			subprocess.call(["cp -r " + self.builder.ark2d_dir + "/data " + self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output + self.builder.ds + "data/ark2d/"], shell=True); #libark2d


			self.generateAppIcons();
			self.generateLaunchImages();



			#exit(0);
			pass;


		pass;

	def generateAppIcons(self):
		print("Generating app icons...")

		startdir = self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output + self.builder.ds;
		appIcons_dir = startdir + self.builder.ds + "Images.xcassets" + self.builder.ds + "AppIcon.appiconset" + self.builder.ds;

		util.makeDirectories([appIcons_dir]);

		size_requirements = [
			{ "w": 20, "h": 20, "n": "Icon-Notification-20x20" },
			{ "w": 40, "h": 40, "n": "Icon-Notification-20x20@2x" },
			{ "w": 60, "h": 60, "n": "Icon-Notification-20x20@3x" },

			{ "w": 29, "h": 29, "n": "Icon-29x29" },
			{ "w": 58, "h": 58, "n": "Icon-29x29@2x" },
			{ "w": 87, "h": 87, "n": "Icon-29x29@3x" },

			{ "w": 40, "h": 40,   "n": "Icon-40x40" },
			{ "w": 80, "h": 80,   "n": "Icon-40x40@2x" },
			{ "w": 120, "h": 120, "n": "Icon-40x40@3x" },

			{ "w": 57, "h": 57,   "n": "Icon-57x57" },
			{ "w": 114, "h": 114, "n": "Icon-57x57@2x" },

			{ "w": 120, "h": 120, "n": "Icon-60x60@2x" },
			{ "w": 180, "h": 180, "n": "Icon-60x60@3x" },

			# iPad Spotlight Icon
			{ "w": 50, "h": 50,   "n": "Icon-50x50" },
			{ "w": 100, "h": 100, "n": "Icon-50x50@2x" },

			{ "w": 72, "h": 72,   "n": "Icon-72x72" },
			{ "w": 144, "h": 144, "n": "Icon-72x72@2x" },

			{ "w": 76, "h": 76,   "n": "Icon-76x76" },
			{ "w": 152, "h": 152, "n": "Icon-76x76@2x" },

			# iPad Pro Icon
			{ "w": 167, "h": 167, "n": "Icon-83.5x83.5@2x" },

			# App Store icon
			{ "w": 1024, "h": 1024, "n": "iTunesArtwork@2x" }
		];

		if "icon" in self.builder.ios_config:
			if "master_icon" in self.builder.ios_config['icon'] and "use_master_icon" in self.builder.ios_config['icon'] and self.builder.ios_config['icon']['use_master_icon'] == True:

				iconinterpolation = self.builder.ios_config['icon']['master_icon_interpolation'];
				icongenarr = [];
				icongenobj = {};
				icongenobj['from'] = self.builder.ios_config['icon']['master_icon'];
				icongenobj['from'] = util.str_replace(icongenobj['from'], [("%PREPRODUCTION_DIR%", self.builder.game_preproduction_dir), ("%ARK2D_DIR%", self.builder.ark2d_dir)]);
				icongenobj['to'] = []

				for req in size_requirements:
					icongenobj['to'].extend([
						{
							"filename": appIcons_dir + req["n"] + ".png",
							"width" : req["w"],
							"height": req["h"],
							"interpolation": iconinterpolation
						}
					]);

				icongenarr.extend([icongenobj]);
				#icongenstr = json.dumps(icongenarr, sort_keys=True, indent=0, new);

				icongenstr = str(json.dumps(icongenarr, separators=(',',':'))).replace("\"", "\\\"");
				icongenLINE = "java -jar -Xmx512m " + self.builder.ark2d_dir + "/../Tools/Image\ Resizer/build/jar/ImageResizer.jar \"" + icongenstr + "\"";
				print(icongenLINE);
				subprocess.call([icongenLINE], shell=True);

				#else:
				pass;
					#	if (config['osx']['android']['icon'] != ''):
					#	subprocess.call(['cp ' + config['osx']['android']['icon'] + " " + rootPath+"/build/android/project/res/drawable/ic_launcher.png"], shell=True);
					#else:
					#	subprocess.call(['cp ' + ark2ddir + "/__preproduction/icon/512.png " + rootPath+"/build/android/project/res/drawable/ic_launcher.png"], shell=True);
			else:

				# copy individual files

				folder = self.builder.ios_config['icon']['folder'];
				folder = util.str_replace(folder, [("%PREPRODUCTION_DIR%", self.builder.game_preproduction_dir), ("%ARK2D_DIR%", self.builder.ark2d_dir)]);

				print("Looking in folder '" + folder + "' for individual icon files.");

				files = util.listFiles(folder, False);
				for req in size_requirements:
					foundSize = False;
					foundImage = "";
					for f in files:
						ext = util.get_str_extension(f);
						if (util.is_image_extension(ext)):
							#print f;
							sz = util.get_image_size(folder + f);
							#print f + " " + sz;
							if (sz[0] == req["w"] and sz[1] == req["h"]):
								foundSize = True;
								foundImage = f;

					if foundImage:
						print("found " + foundImage + " for icon size " + str(req["w"]) + "x" + str(req["h"]));
						subprocess.call(["cp -r " + folder + foundImage + " " + appIcons_dir + req["n"] + ".png"], shell=True);
					else:
						print("missing icon size: " + str(req["w"]) + "x" + str(req["h"]));
						exit(0);

		contentsJsonData  = {
			"images" : [
				{
				  "size" : "20x20",
				  "idiom" : "iphone",
				  "filename" : "Icon-Notification-20x20@2x.png",
				  "scale" : "2x"
				},
				{
				  "size" : "20x20",
				  "idiom" : "iphone",
				  "filename" : "Icon-Notification-20x20@3x.png",
				  "scale" : "3x"
				},
				{
				  "size" : "29x29",
				  "idiom" : "iphone",
				  "filename" : "Icon-29x29.png",
				  "scale" : "1x"
				},
				{
				  "size" : "29x29",
				  "idiom" : "iphone",
				  "filename" : "Icon-29x29@2x.png",
				  "scale" : "2x"
				},
				{
				  "size" : "29x29",
				  "idiom" : "iphone",
				  "filename" : "Icon-29x29@3x.png",
				  "scale" : "3x"
				},
				{
				  "size" : "40x40",
				  "idiom" : "iphone",
				  "filename" : "Icon-40x40@2x.png",
				  "scale" : "2x"
				},
				{
				  "size" : "40x40",
				  "idiom" : "iphone",
				  "filename" : "Icon-40x40@3x.png",
				  "scale" : "3x"
				},
				{
				  "size" : "57x57",
				  "idiom" : "iphone",
				  "filename" : "Icon-57x57.png",
				  "scale" : "1x"
				},
				{
				  "size" : "57x57",
				  "idiom" : "iphone",
				  "filename" : "Icon-57x57@2x.png",
				  "scale" : "2x"
				},
				{
				  "size" : "60x60",
				  "idiom" : "iphone",
				  "filename" : "Icon-60x60@2x.png",
				  "scale" : "2x"
				},
				{
				  "size" : "60x60",
				  "idiom" : "iphone",
				  "filename" : "Icon-60x60@3x.png",
				  "scale" : "3x"
				},
				{
				  "size" : "20x20",
				  "idiom" : "ipad",
				  "filename" : "Icon-Notification-20x20.png",
				  "scale" : "1x"
				},
				{
				  "size" : "20x20",
				  "idiom" : "ipad",
				  "filename" : "Icon-Notification-20x20@2x.png",
				  "scale" : "2x"
				},
				{
				  "size" : "29x29",
				  "idiom" : "ipad",
				  "filename" : "Icon-29x29.png",
				  "scale" : "1x"
				},
				{
				  "size" : "29x29",
				  "idiom" : "ipad",
				  "filename" : "Icon-29x29@2x.png",
				  "scale" : "2x"
				},
				{
				  "size" : "40x40",
				  "idiom" : "ipad",
				  "filename" : "Icon-40x40.png",
				  "scale" : "1x"
				},
				{
				  "size" : "40x40",
				  "idiom" : "ipad",
				  "filename" : "Icon-40x40@2x.png",
				  "scale" : "2x"
				},
				{
				  "size" : "50x50",
				  "idiom" : "ipad",
				  "filename" : "Icon-50x50.png",
				  "scale" : "1x"
				},
				{
				  "size" : "50x50",
				  "idiom" : "ipad",
				  "filename" : "Icon-50x50@2x.png",
				  "scale" : "2x"
				},
				{
				  "size" : "72x72",
				  "idiom" : "ipad",
				  "filename" : "Icon-72x72.png",
				  "scale" : "1x"
				},
				{
				  "size" : "72x72",
				  "idiom" : "ipad",
				  "filename" : "Icon-72x72@2x.png",
				  "scale" : "2x"
				},
				{
				  "size" : "76x76",
				  "idiom" : "ipad",
				  "filename" : "Icon-76x76.png",
				  "scale" : "1x"
				},
				{
				  "size" : "76x76",
				  "idiom" : "ipad",
				  "filename" : "Icon-76x76@2x.png",
				  "scale" : "2x"
				},
				{
				  "size" : "83.5x83.5",
				  "idiom" : "ipad",
				  "filename" : "Icon-83.5x83.5@2x.png",
				  "scale" : "2x"
				},
				{
				  "size" : "1024x1024",
				  "idiom" : "ios-marketing",
				  "filename" : "iTunesArtwork@2x.png",
				  "scale" : "1x"
				}
			  ],
			"info" : {
				"version" : 1,
				"author" : "xcode"
			}
		};


		print ("writing AppIcon Contents.json");
		f = open(appIcons_dir + "Contents.json", "w");
		f.write(json.dumps(contentsJsonData, sort_keys=True, indent=4));
		f.close();
		print ("Done!");


	def generateLaunchImages(self):

		startdir = self.builder.game_dir + self.builder.ds + self.builder.build_folder + self.builder.ds + self.builder.output + self.builder.ds;

		print("Copying storyboard from ark2d lib...")
		print (self.builder.ark2d_dir + "/lib/iphone/Launch.storyboard");
		print (startdir + "Launch.storyboard");
		util.copyfileifdifferent(
			self.builder.ark2d_dir + "/lib/iphone/Launch.storyboard",
			startdir + "Launch.storyboard"
		);

		print("Generating launchimages...")
		if "defaults" in self.builder.ios_config:
			if "use_master" in self.builder.ios_config['defaults']:
				if (self.builder.ios_config['defaults']['use_master'] == True):
					# do
					launchImages_dir = startdir + self.builder.ds + "Images.xcassets" + self.builder.ds + "LaunchImage.launchimage" + self.builder.ds;

					util.makeDirectories([launchImages_dir]);

					defaultsgenarr = [];
					defaultsgenobj = {};
					defaultsgenobj['from'] = self.builder.ios_config['defaults']['master'];
					defaultsgenobj['from'] = util.str_replace(defaultsgenobj['from'], [("%PREPRODUCTION_DIR%", self.builder.game_preproduction_dir), ("%ARK2D_DIR%", self.builder.ark2d_dir)]);
					defaultsgenobj['to'] = [
						{
							"filename": launchImages_dir + "Default-Portrait-IPhone-320x480.png",
							"width" : 320,
							"height": 480,
							"interpolation": "nearest_neighbour"
						},
						# {
						# 	"filename": launchImages_dir + "Default-Landscape-IPhone-480x320.png",
						# 	"width" : 480,
						# 	"height": 320,
						# 	"interpolation": "nearest_neighbour"
						# },
						{
							"filename": launchImages_dir + "Default-Portrait-IPhone-640x960.png",
							"width" : 640,
							"height": 960,
							"interpolation": "nearest_neighbour"
						},
						# {
						# 	"filename": launchImages_dir + "Default-Landscape-IPhone-960x640.png",
						# 	"width" : 960,
						# 	"height": 640,
						# 	"interpolation": "nearest_neighbour"
						# },
						{
							"filename": launchImages_dir + "Default-Portrait-Retina4-640x1136.png",
							"width" : 640,
							"height": 1136,
							"interpolation": "nearest_neighbour"
						},
						# {
						# 	"filename": launchImages_dir + "Default-Landscape-Retina4-1136x640.png",
						# 	"width": 1136,
						# 	"height" : 640,
						# 	"interpolation": "nearest_neighbour"
						# },
						{
							"filename": launchImages_dir + "Default-Portrait-IPad-768x1024.png",
							"width" : 768,
							"height": 1024,
							"interpolation": "nearest_neighbour"
						},
						{
							"filename": launchImages_dir + "Default-Landscape-IPad-1024x768.png",
							"width" : 1024,
							"height": 768,
							"interpolation": "nearest_neighbour"
						},
						{
							"filename": launchImages_dir + "Default-Portrait-IPad-1536x2048.png",
							"width" : 1536,
							"height": 2048,
							"interpolation": "nearest_neighbour"
						},
						{
							"filename": launchImages_dir + "Default-Landscape-IPad-2048x1536.png",
							"width" : 2048,
							"height": 1536,
							"interpolation": "nearest_neighbour"
						},
						{
							"filename": launchImages_dir + "Default-Portrait-RetinaHD47-750x1334.png",
							"width" : 750,
							"height": 1334,
							"interpolation": "nearest_neighbour"
						},
						{
							"filename": launchImages_dir + "Default-Portrait-RetinaHD55-1242x2208.png",
							"width" : 1242,
							"height": 2208,
							"interpolation": "nearest_neighbour"
						},
						{
							"filename": launchImages_dir + "Default-Landscape-RetinaHD55-2208x1242.png",
							"width" : 2208,
							"height": 1242,
							"interpolation": "nearest_neighbour"
						},
						{
							"filename": launchImages_dir + "Default-Portrait-IPhoneX-1125x2436.png",
							"width" : 1125,
							"height": 2436,
							"interpolation": "nearest_neighbour"
						},
						{
							"filename": launchImages_dir + "Default-Landscape-IPhoneX-2436x1125.png",
							"width" : 2436,
							"height": 1125,
							"interpolation": "nearest_neighbour"
						},
						{
							"filename": launchImages_dir + "Default-Portrait-IPhoneXR-828x1792.png",
							"width" : 828,
							"height": 1792,
							"interpolation": "nearest_neighbour"
						},
						{
							"filename": launchImages_dir + "Default-Landscape-IPhoneXR-1792x828.png",
							"width" : 1792,
							"height": 828,
							"interpolation": "nearest_neighbour"
						},
						{
							"filename": launchImages_dir + "Default-Portrait-IPhoneXSMax-1242x2688.png",
							"width" : 1242,
							"height": 2688,
							"interpolation": "nearest_neighbour"
						},
						{
							"filename": launchImages_dir + "Default-Landscape-IPhoneXSMax-2688x1242.png",
							"width" : 2688,
							"height": 1242,
							"interpolation": "nearest_neighbour"
						}
					];
					defaultsgenarr.extend([defaultsgenobj]);

					defaultsgenstr = str(json.dumps(defaultsgenarr, separators=(',',':'))).replace("\"", "\\\"");
					defaultsgenLINE = "java -jar -Xmx512m " + self.builder.ark2d_dir + "/../Tools/Image\ Resizer/build/jar/ImageResizer.jar \"" + defaultsgenstr + "\"";
					print(defaultsgenLINE);
					subprocess.call([defaultsgenLINE], shell=True);


					#make the LaunchImage.launchimage folder and Contents.json config
					launchImages_data = {
						"images" : [
							{
								"extent" : "full-screen",
								"idiom" : "iphone",
								"subtype" : "2688h",
								"filename" : "Default-Portrait-IPhoneXSMax-1242x2688.png",
								"minimum-system-version" : "12.0",
								"orientation" : "portrait",
								"scale" : "3x"
							},
							{
								"extent" : "full-screen",
								"idiom" : "iphone",
								"subtype" : "2688h",
								"filename" : "Default-Landscape-IPhoneXSMax-2688x1242.png",
								"minimum-system-version" : "12.0",
								"orientation" : "landscape",
								"scale" : "3x"
							},
							{
								"extent" : "full-screen",
								"idiom" : "iphone",
								"subtype" : "1792h",
								"filename" : "Default-Portrait-IPhoneXR-828x1792.png",
								"minimum-system-version" : "12.0",
								"orientation" : "portrait",
								"scale" : "2x"
							},
							{
								"extent" : "full-screen",
								"idiom" : "iphone",
								"subtype" : "1792h",
								"filename" : "Default-Landscape-IPhoneXR-1792x828.png",
								"minimum-system-version" : "12.0",
								"orientation" : "landscape",
								"scale" : "2x"
							},
							{
								"extent" : "full-screen",
								"idiom" : "iphone",
								"subtype" : "2436h",
								"filename" : "Default-Portrait-IPhoneX-1125x2436.png",
								"minimum-system-version" : "11.0",
								"orientation" : "portrait",
								"scale" : "3x"
							},
							{
								"extent" : "full-screen",
								"idiom" : "iphone",
								"subtype" : "2436h",
								"filename" : "Default-Landscape-IPhoneX-2436x1125.png",
								"minimum-system-version" : "11.0",
								"orientation" : "landscape",
								"scale" : "3x"
							},
							{
								"extent" : "full-screen",
								"idiom" : "iphone",
								"subtype" : "736h",
								"filename" : "Default-Portrait-RetinaHD55-1242x2208.png",
								"minimum-system-version" : "8.0",
								"orientation" : "portrait",
								"scale" : "3x"
							},
							{
								"extent" : "full-screen",
								"idiom" : "iphone",
								"subtype" : "736h",
								"filename" : "Default-Landscape-RetinaHD55-2208x1242.png",
								"minimum-system-version" : "8.0",
								"orientation" : "landscape",
								"scale" : "3x"
							},
							{
								"extent" : "full-screen",
								"idiom" : "iphone",
								"subtype" : "667h",
								"filename" : "Default-Portrait-RetinaHD47-750x1334.png",
								"minimum-system-version" : "8.0",
								"orientation" : "portrait",
								"scale" : "2x"
							},
							{
								"orientation" : "portrait",
								"idiom" : "iphone",
								"filename" : "Default-Portrait-IPhone-640x960.png",
								"extent" : "full-screen",
								"minimum-system-version" : "7.0",
								"scale" : "2x"
							},
							{
								"orientation" : "portrait",
								"idiom" : "iphone",
								"filename" : "Default-Portrait-IPhone-640x960.png",
								"extent" : "full-screen",
								"scale" : "2x"
							},
							# {
							# 	"orientation" : "landscape",
							# 	"idiom" : "iphone",
							# 	"filename" : "Default-Landscape-IPhone-960x640.png",
							# 	"extent" : "full-screen",
							# 	"minimum-system-version" : "7.0",
							# 	"scale" : "2x"
							# },
							# {
							# 	"orientation" : "landscape",
							# 	"idiom" : "iphone",
							# 	"filename" : "Default-Landscape-IPhone-960x640.png",
							# 	"extent" : "full-screen",
							# 	"scale" : "2x"
							# },
							{
								"orientation" : "portrait",
								"idiom" : "iphone",
								"filename" : "Default-Portrait-IPhone-320x480.png",
								"extent" : "full-screen",
								"scale" : "1x"
							},
							# {
							# 	"orientation" : "landscape",
							# 	"idiom" : "iphone",
							# 	"filename" : "Default-Landscape-IPhone-480x320.png",
							# 	"extent" : "full-screen",
							# 	"scale" : "1x"
							# },
							{
								"extent" : "full-screen",
								"idiom" : "iphone",
								"subtype" : "retina4",
								"filename" : "Default-Portrait-Retina4-640x1136.png",
								"minimum-system-version" : "7.0",
								"orientation" : "portrait",
								"scale" : "2x"
							},
							{
								"extent" : "full-screen",
								"idiom" : "iphone",
								"subtype" : "retina4",
								"filename" : "Default-Portrait-Retina4-640x1136.png",
								"orientation" : "portrait",
								"scale" : "2x"
							},
							# {
							# 	"extent" : "full-screen",
							# 	"idiom" : "iphone",
							# 	"subtype" : "retina4",
							# 	"filename" : "Default-Landscape-Retina4-1136x640.png",
							# 	"minimum-system-version" : "7.0",
							# 	"orientation" : "landscape",
							# 	"scale" : "2x"
							# },
							{
								"orientation" : "portrait",
								"idiom" : "ipad",
								"filename" : "Default-Portrait-IPad-768x1024.png",
								"extent" : "full-screen",
								"minimum-system-version" : "7.0",
								"scale" : "1x"
							},
							{
								"orientation" : "landscape",
								"idiom" : "ipad",
								"filename" : "Default-Landscape-IPad-1024x768.png",
								"extent" : "full-screen",
								"minimum-system-version" : "7.0",
								"scale" : "1x"
							},
							{
								"orientation" : "portrait",
								"idiom" : "ipad",
								"filename" : "Default-Portrait-IPad-1536x2048.png",
								"extent" : "full-screen",
								"minimum-system-version" : "7.0",
								"scale" : "2x"
							},
							{
								"orientation" : "landscape",
								"idiom" : "ipad",
								"filename" : "Default-Landscape-IPad-2048x1536.png",
								"extent" : "full-screen",
								"minimum-system-version" : "7.0",
								"scale" : "2x"
							},

							{
								"orientation" : "portrait",
								"idiom" : "ipad",
								"filename" : "Default-Portrait-IPad-768x1024.png",
								"extent" : "full-screen",
								"scale" : "1x"
							},
							{
								"orientation" : "landscape",
								"idiom" : "ipad",
								"filename" : "Default-Landscape-IPad-1024x768.png",
								"extent" : "full-screen",
								"scale" : "1x"
							},
							{
								"orientation" : "portrait",
								"idiom" : "ipad",
								"filename" : "Default-Portrait-IPad-1536x2048.png",
								"extent" : "full-screen",
								"scale" : "2x"
							},
							{
								"orientation" : "landscape",
								"idiom" : "ipad",
								"filename" : "Default-Landscape-IPad-2048x1536.png",
								"extent" : "full-screen",
								"scale" : "2x"
							}
						],
						"info" : {
							"version" : 1,
							"author" : "xcode"
						}
					};

					print ("writing LaunchImage Contents.json");
					f = open(launchImages_dir + "Contents.json", "w");
					f.write(json.dumps(launchImages_data, sort_keys=True, indent=4));
					f.close();


				pass;
			pass;
		print("Done generating defaults.");
