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

class MacBuild:

	def __init__(self, builder):
		self.builder = builder;
		pass;

	def start(self):
		print("Building for XCode");

		# open config
		f = open(self.builder.ark2d_dir + "/config.json", "r");
		fcontents = f.read();
		f.close();
		config = json.loads(fcontents);

		self.ark2d_config = config;



		gyp_executable = config['osx']['gyp_executable'];

		#f = open(self.game_dir + "/config.json", "r");
		#fcontents = f.read();
		#f.close();
		#config = json.loads(fcontents);

		print('hello');
		ds = "/";
		#self.builder

		if (self.builder.building_library):

			print("making directories");
			flascc_folder = self.builder.ark2d_dir + ds + self.builder.build_folder + "/osx"; #config['osx']['ark2d_dir'] + "/build/xcode";
			mkdirs = [];
			mkdirs.extend(self.builder.mkdirs);
			util.makeDirectories(mkdirs);

			#projectname ark2d
			projectname = "ark2d";

			# generate gyp file.
			print("creating gyp file");
			gyp_template_file = self.builder.ark2d_dir + ds + "lib" + ds + "osx" + ds + "ark2d-gyp.json";
			gyp_module_template_file = self.builder.ark2d_dir + ds + "lib" + ds + "osx" + ds + "ark2d-gyp-module.json";
			gyp_export_file = self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.output + ds + projectname + ".gyp";

			gyp_template_data = self.builder.getJsonFile( gyp_template_file, True );
			gyp_template_data['targets'][0]['sources'] = [];

			for srcfile in config['src_files']['osx']:
				gyp_template_data['targets'][0]['sources'].extend(["../../"+srcfile]);

				#check if src file has a corresponding .h file. add that to the project...
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newfh = srcfile[0:findex] + ".h";
				newfhfull = self.builder.game_dir + ds + newfh;
				if (os.path.exists(newfhfull)):
					gyp_template_data['targets'][0]['sources'].extend(["../../"+newfh]);

			for srcfile in config['src_files']['all']:
				gyp_template_data['targets'][0]['sources'].extend(["../../"+srcfile]);

				#check if src file has a corresponding .h file. add that to the project...
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newfh = srcfile[0:findex] + ".h";
				newfhfull = self.builder.game_dir + ds + newfh;
				if (os.path.exists(newfhfull)):
					gyp_template_data['targets'][0]['sources'].extend(["../../"+newfh]);

			# Debug modifiers
			if (self.builder.debug):
				gyp_template_data['targets'][0]['conditions'][0][1]['defines'].extend(["ARK2D_DEBUG"]);
				gyp_template_data['targets'][0]['conditions'][0][1]['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] += " ARK2D_DEBUG ";

			# modules
			for index, module in enumerate( config['modules'] ):

				moduleName = module;
				module = config['modules'][moduleName];
				moduleTemplate = self.builder.getJsonFile( gyp_module_template_file, False );
				moduleTemplate['target_name'] = "ark2d_" + moduleName;

				print(moduleName);

				for srcfile in module['sources']:
					srcfile = "../../" + srcfile;
					moduleTemplate['sources'].extend( [srcfile] );

				for index, dependency in enumerate( config['modules'][moduleName]['dependencies'] ):
					dependencyName = dependency;
					#print(dependencyName);
					dependency = config['modules'][moduleName]['dependencies'][index];
					if (util.get_str_extension(dependencyName) == "framework"):
						newdependency = dependencyName;
					else:
						newdependency = "libARK2D_" + dependencyName + ".dylib"

					moduleTemplate['conditions'][0][1]['link_settings']['libraries'].extend( [newdependency] );

				gyp_template_data['targets'].extend([moduleTemplate]);

			print("saving gyp file: " + gyp_export_file);
			f = open(gyp_export_file, "w")
			f.write(json.dumps(gyp_template_data, sort_keys=True, indent=4));
			f.close();

			#exit(0);
			#pchfilename = self.game_dir + ds + "lib/iphone/" + projectname + "-Prefix.pch";
			pchfilename = self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.output + ds + projectname + "-Prefix.pch";
			xcconfigfile = self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.output + ds + projectname + ".xcconfig";

			#delete xcode project?
			try:
				print("deleting xcode project");
				os.system("rm -r -d " + pchfilename);
				os.system("rm -r -d " + xcconfigfile);
				os.system("rm -r -d " + self.builder.build_folder + ds + self.builder.output + ds + "DerivedData");
			except:
				print("could not delete xcode project");

			# run gyp file.
			os.system("python " + gyp_executable + "_main.py " + gyp_export_file + " --depth=../../src");

			# add precompiled headers file
			print("generating pch file");

			nl = "\r\n";
			pcheaderfile = "";
			#pcheaderfile += "#ifdef __OBJC__" + nl;
			pcheaderfile += "	#import <Foundation/Foundation.h>" + nl;
			pcheaderfile += "	#import <CoreFoundation/CoreFoundation.h>" + nl + nl;

			#pcheaderfile += "	#import <UIKit/UIKit.h>" + nl + nl;

			pcheaderfile += "	#import <OpenAL/al.h>" + nl;
			pcheaderfile += "	#import <OpenAL/alc.h>" + nl + nl

			#pcheaderfile += "	#import <QuartzCore/QuartzCore.h>" + nl + nl;

			#pcheaderfile += "	#import <OpenGL/OpenGL.h>" + nl;
			pcheaderfile += "	#import <OpenGL/gl3.h>" + nl;
			#pcheaderfile += "	#import <OpenGL/gltypes.h>" + nl;
			#pcheaderfile += "	#import <OpenGL/glu.h>" + nl;
			pcheaderfile += "	#import <OpenGL/gl3ext.h>" + nl + nl;

			#pcheaderfile += "	#import <CoreFoundation/CFBundle.h>" + nl;
			#pcheaderfile += "	#import <CoreFoundation/CoreFoundation.h>" + nl;

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
			xcconfigfilecontents += "GCC_PREFIX_HEADER = " + pchfilename + ";" + nl;
			xcconfigfilecontents += "SRCROOT = " + self.builder.game_dir + ds + "src" + ds + "ARK2D" + nl;
			xcconfigfilecontents += "HEADERMAP_INCLUDES_FLAT_ENTRIES_FOR_TARGET_BEING_BUILT = NO;" + nl;
			xcconfigfilecontents += "HEADERMAP_INCLUDES_PROJECT_HEADERS = NO;" + nl;
			xcconfigfilecontents += "HEADERMAP_INCLUDES_FRAMEWORK_ENTRIES_FOR_ALL_PRODUCT_TYPES = NO;" + nl;
			xcconfigfilecontents += "ALWAYS_SEARCH_USER_PATHS = NO;" + nl;
			xcconfigfilecontents += "OTHER_CFLAGS = -x objective-c;" + nl;
			xcconfigfilecontents += "OTHER_CPLUSPLUSFLAGS = -x objective-c++;" + nl;
			#xcconfigfilecontents += "OTHER_LDFLAGS = -L/usr/lib -L" + self.builder.ark2d_dir + "/lib/osx -L" + self.builder.ark2d_dir + "/lib/osx/freetype -lbz2 -lcurl -lz -lfreetype -install_name @executable_path/../Resources/data/ark2d/libark2d.dylib " + nl;
			xcconfigfilecontents += "OTHER_LDFLAGS = -L" + self.builder.ark2d_dir + "/lib/osx -L" + self.builder.ark2d_dir + "/lib/osx/system -L" + self.builder.ark2d_dir + "/lib/osx/freetype -lbz2 -lcurl -lz -lfreetype -install_name @executable_path/../Resources/data/ark2d/libark2d.dylib " + nl;




			print("saving xcconfig file: " + xcconfigfile);
			f = open(xcconfigfile, "w")
			f.write(xcconfigfilecontents);
			f.close();

			print("done. now compile with the xcode project.");

			exit(0);

		else:




			mkdirs = [];
			mkdirs.extend(self.builder.mkdirs);
			#mkdirs.extend([self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.platform + ds + "data" + ds + "ark2d"]);
			#mkdirs.extend()
			self.makeDirectories(mkdirs);

			#projectname ark2d
			projectname = self.game_name_safe; #config['game_short_name'];
			projectnameunsafe = self.game_name; #config['game_name'];

			# generate gyp file.
			print("creating gyp file");
			gypfilename = self.game_dir + ds + self.build_folder + ds + self.output + ds + projectname + ".gyp";

			gypfile = {};
			gypfile['defines'] = []; #'ARK2D_IPHONE'];
			gypfile['defines'].extend(["ARK_INCLUDES_HEADER="+self.builder.ark2d_dir + "/src/ARK.h"]);
			gypfile['defines'].extend(self.preprocessor_definitions);

			gypfile['targets'] = [];

			gypfiletarget = {};
			gypfiletarget['target_name'] = projectnameunsafe;# + "-OSX"; # we know it's OSX. HAH.
			gypfiletarget['type'] = "executable";
			gypfiletarget['mac_bundle'] = 1;
			#'mac_bundle': 1,
			gypfiletarget['include_dirs'] = [];
			for includedir in self.include_dirs:
				gypfiletarget['include_dirs'].extend([includedir]);
			gypfiletarget['sources'] = [];

			for srcfile in self.src_files: #config['game_src_files']:
				gypfiletarget['sources'].extend(["../../"+srcfile]);

				#check if src file has a corresponding .h file. add that to the project...
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newfh = srcfile[0:findex] + ".h";
				newfhfull = self.game_dir + ds + newfh;
				if (os.path.exists(newfhfull)):
					gypfiletarget['sources'].extend(["../../"+newfh]);



			gypfiletarget['sources!'] = [];
			gypfiletarget['dependencies'] = [];
			gypfiletarget['conditions'] = [];
			gypfiletargetcondition = {};
			gypfiletargetcondition['defines'] = ['ARK2D_MACINTOSH', 'ARK2D_DESKTOP']; #, 'CF_EXCLUDE_CSTD_HEADERS'];
			gypfiletargetcondition['defines'].extend(self.preprocessor_definitions);
			gypfiletargetcondition['sources'] = [];

			"""
			gypfiletargetcondition['actions'] = [
			{
				'variables': {
					'arraylist': [
						'value1',
						'value2',
						'value3',
					],
				},
				'action_name': 'test',
				'inputs': [
				 	#'<@(arraylist)',
				],
				'outputs': [ ],
				'action': ['osascript', '-e', 'tell app "Finder" to display dialog "Hello World"'],
				'message': 'hello world'
			} ];
			"""

			gypfiletargetcondition['actions'] = [
				# python /Users/username/ark2d/ARK2D/build.py spritesheets=true
				{
					'action_name': 'generate spritesheets',
					'inputs': [],
					'outputs': [],
					'action': [
						'python',
						self.builder.ark2d_dir + '/build.py',
						'dir=' + self.builder.game_dir,
						'spritesheets=true',
						'newconfig=true',
						'type=game',
						'target=' + self.builder.target_config_file
					],
					'message': 'generate spritesheets'
				},
				{
					'action_name': 'generate localised strings table',
					'inputs': [],
					'outputs': [],
					'action': [
						'python',
						self.builder.ark2d_dir + '/build.py',
						'dir=' + self.builder.game_dir,
						'strings=true',
						'newconfig=true',
						'type=game',
						'target=' + self.builder.target_config_file
					],
					'message': 'generate localised strings table'
				},
				{
					'action_name': 'Copy game assets into Xcode project',
					'inputs': [],
					'outputs': [],
					'action': [
						'cp',
						'-r',
						self.builder.game_resources_dir + '/',
						self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.output + ds + "data/"
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
						self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.output + ds + 'data/ark2d/'
					],
					'message': 'copy ark2d assets'
				},
				{
					'action_name': 'Copy ark2d library into Xcode project',
					'inputs': [],
					'outputs': [],
					'action': [
						'cp',
						self.builder.ark2d_dir + '/build/osx/DerivedData/ark2d/Build/Products/Default/libark2d-OSX.dylib',
						self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.output + ds + 'data/ark2d/libark2d.dylib'
					],
					'message': 'copy ark2d library'
				},

			];

			# https://buckbuild.com/javadoc/com/facebook/buck/apple/xcode/xcodeproj/PBXCopyFilesBuildPhase.Destination.html
			gypfiletargetcondition['sources!'] = [];
			gypfiletargetcondition['link_settings'] = {};
			gypfiletargetcondition['copies'] = [{
				"destination": '$(EXECUTABLE_FOLDER_PATH)',
				"files": []
			}];
			gypfiletargetcondition['link_settings']['libraries'] = [
				'$(SDKROOT)/System/Library/Frameworks/IOKit.framework',
				'$(SDKROOT)/System/Library/Frameworks/Cocoa.framework',
				'$(SDKROOT)/System/Library/Frameworks/CoreFoundation.framework',
				'$(SDKROOT)/System/Library/Frameworks/QuartzCore.framework',
				'$(SDKROOT)/System/Library/Frameworks/OpenGL.framework',
				'$(SDKROOT)/System/Library/Frameworks/OpenAL.framework',
				'$(SDKROOT)/System/Library/Frameworks/QTKit.framework',

	          	#'../../lib/iphone/libfreetype.a'
	          	#config['osx']['ark2d_dir'] + '/lib/osx/freetype/libfreetype.a',
	          	#config['osx']['ark2d_dir'] + '/lib/osx/libcurl.a',
	          	#config['osx']['ark2d_dir'] + '/build/xcode/XcodeData/ark2d/Build/Products/Default/libark2d-OSX.dylib'
	          	#self.builder.ark2d_dir + '/lib/osx/libangelscript.a',

	          	# in current project
	          	self.builder.game_dir + '/build/' + self.builder.output + '/data/ark2d/libark2d.dylib'
	          	# in ark2d dir -- we copy the latest in now!
	          	# self.ark2d_dir + '/build/osx/DerivedData/ark2d/Build/Products/Default/libark2d-OSX.dylib'
			];
			gypfiletargetcondition['link_settings']['libraries'] = self.builder.addLibrariesToArray(gypfiletargetcondition['link_settings']['libraries'], self.builder.libs);
			#gypfiletargetcondition['link_settings']['libraries'].extend( self.builder.target_config['libs'] );
			for lib in self.builder.libs:
				if util.get_str_extension(lib) == "framework":
					gypfiletargetcondition['link_settings']['libraries'].extend(["$(SDKROOT)/System/Library/Frameworks/" + lib]);
				else:
					gypfiletargetcondition['link_settings']['libraries'].extend([lib]);

					lib = util.str_replace(lib, [(self.builder.game_dir, "../..")]);
					gypfiletargetcondition['copies'][0]['files'].extend([lib]);


			if (self.builder.debug):
				gypfiletargetcondition['defines'].extend(['ARK2D_DEBUG']);

			gypfiletargetcondition['ldflags'] = [ ];

			gypfiletargetcondition['link_settings!'] = [];

			ark2ddir = self.builder.ark2d_dir + "/src/ARK2D"; #config['osx']['ark2d_dir'] + "/src/ARK2D";
			gypfiletargetcondition['include_dirs'] = [
				self.builder.ark2d_dir + "/src/",
				self.builder.ark2d_dir + "/src/ARK2D",
				self.builder.ark2d_dir + "/src/ARK2D/vendor/iphone",
				self.builder.ark2d_dir + "/src/ARK2D/vendor/spine/includes"
			];

			# custom include dirs
			#if "include_dirs" in config['osx']:
			#	for includedir in config['osx']['include_dirs']:
			#		includedir_actual = util.str_replace(includedir, [("%PREPRODUCTION_DIR%", config['osx']['game_preproduction_dir']), ("%ARK2D_DIR%", config['osx']['ark2d_dir'])]);
			#		gypfiletargetcondition['include_dirs'].extend([includedir_actual]);
			gypfiletargetcondition['include_dirs'].extend(self.builder.include_dirs);

			# we can set any of these!
			# https://developer.apple.com/library/mac/documentation/DeveloperTools/Reference/XcodeBuildSettingRef/1-Build_Setting_Reference/build_setting_ref.html
			gypfiletargetcondition['xcode_settings'] = {};
			gypfiletargetcondition['xcode_settings']['ARCHS'] = "$(ARCHS_STANDARD)"; #"i386 x86_64"; # or  $(ARCHS_STANDARD_32_64_BIT)
			gypfiletargetcondition['xcode_settings']['SDKROOT'] = "macosx";
			gypfiletargetcondition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] = "ARK2D_MACINTOSH ARK2D_DESKTOP";
			gypfiletargetcondition['xcode_settings']['GCC_OPTIMIZATION_LEVEL'] = "0";
			gypfiletargetcondition['xcode_settings']['MACOSX_DEPLOYMENT_TARGET'] = "10.7";
			gypfiletargetcondition['xcode_settings']['LD_RUNPATH_SEARCH_PATHS'] = "@executable_path/";

			# force c++11!
			gypfiletargetcondition['xcode_settings']['CLANG_CXX_LANGUAGE_STANDARD'] = "c++0x";
			gypfiletargetcondition['xcode_settings']['CLANG_CXX_LIBRARY'] 			= "libc++";
			gypfiletargetcondition['xcode_settings']['GCC_C_LANGUAGE_STANDARD'] 	= "c11";

			if (self.builder.debug):
				gypfiletargetcondition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] += " ARK2D_DEBUG ";

			xcconfigfilesimple = projectname + ".xcconfig";
			xcconfigfile = self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.output + ds + xcconfigfilesimple;

			gypfiletargetcondition['xcode_config_file'] = xcconfigfilesimple;
			gypfiletargetcondition['mac_bundle_resources'] = [
				"data/"#,				#ark2d and game data

				# "Icon.png",				#iphone
				# "Icon@2x.png",			#iphone-retina
				# "Icon-Small.png",			#iphone-spotlight
				# "Icon-Small@2x.png",		#iphone-spotlight-retina

				# "Default.png" 			#iphone-launch-image (320x480)
				# "Default@2x.png"			#iphone-launch-image-retina (640x960)
				# "Default-568h@2x.png" 	#iphone5-launch-image-retina (640x1136)

				# "Icon-72.png",			#ipad
				# "Icon-72@2x.png",			#ipad-retina
				# "Icon-Small-50.png",		#ipad-spotlight
				# "Icon-Small-50@2x.png",	#ipad-spotlight-retina

				# "Default-Portrait.png" 		#ipad-launch-image-portrait (768x1024)
				# "Default-Landscape.png" 		#ipad-launch-image-landscape (1024x768)
				# "Default-Portrait@2x.png" 	#ipad-launch-image-portrait (1536x2048)
				# "Default-Landscape@2x.png" 	#ipad-launch-image-landscape (2048x1536)

				# "iTunesArtwork", 		#app-store-icon
				# "iTunesArtwork@2x", 	#app-store-icon-retina
			];

			iphonecondition = [];
			iphonecondition.extend(["OS == 'mac'"]);
			iphonecondition.extend([gypfiletargetcondition]);
			gypfiletarget['conditions'].extend([iphonecondition]);

			gypfile['targets'].extend([gypfiletarget]);

			print("saving gyp file: " + gypfilename);
			f = open(gypfilename, "w")
			f.write(json.dumps(gypfile, sort_keys=True, indent=4));
			f.close();



			#delete xcode project?
			pchfilename = self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.output + ds + projectname + "-Prefix.pch";
			info_plist_filename = self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.output + ds + projectname + "-Info.plist";
			try:
				print("deleting xcode project");
				os.system("rm -r -d " + pchfilename);
				os.system("rm -r -d " + info_plist_filename);
				os.system("rm -r -d " + xcconfigfile);
				os.system("rm -r -d " + self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.output + ds + "DerivedData");
			except:
				print("could not delete xcode project");

			# run gyp file.
			print("run gyp file");
			os.system("python " + gyp_executable + "_main.py " + gypfilename + " --depth=../../src --debug=all");

			# hack into xcode project to add steam / other libs that need to go next to the executable.
			#if "libs" in config['osx']:
			"""
			if (len(self.builder.libs) > 0):

				f = open(self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.output + ds + projectname + ".xcodeproj" + ds + "project.pbxproj", "r");
				pbxproj = f.read();
				f.close();

				copyFilesId = "FFFFFFF3198988B100BDD086";

				PBXBuildFileExtraContents = "";
				libfilecount = 0;
				for libfile in
				libs: #config['osx']['libs']:
					libfilename = util.get_str_filename(libfile);

					PBXBuildFileExtraContents += "		FFFFFFFFFFFF00000000000" + str(libfilecount) + " /* " + libfilename + " in CopyFiles */ = {isa = PBXBuildFile; fileRef = FFFFFFFEFFFF00000000000" + str(libfilecount) + " /* " + libfilename + " */; };\n";
					libfilecount += 1;

				pbjxprojCopyLibs_contents = "";
				pbjxprojCopyLibs_contents += PBXBuildFileExtraContents;
				pbjxprojCopyLibs_contents += "/* End PBXBuildFile section */\n";
				pbjxprojCopyLibs_contents += "/* Begin PBXCopyFilesBuildPhase section */\n";
				pbjxprojCopyLibs_contents += copyFilesId + " /* CopyFiles */ = {\n";
				pbjxprojCopyLibs_contents += "	isa = PBXCopyFilesBuildPhase;\n";
				pbjxprojCopyLibs_contents += "	buildActionMask = 2147483647;\n";
				pbjxprojCopyLibs_contents += "	dstPath = \"\";\n";
				pbjxprojCopyLibs_contents += "	dstSubfolderSpec = 6;\n";
				pbjxprojCopyLibs_contents += "	files = (\n";

				libfilecount = 0;
				for libfile in self.builder.libs: #config['osx']['libs']:
					libfilename = util.get_str_filename(libfile);
					pbjxprojCopyLibs_contents += "		FFFFFFFFFFFF00000000000" + str(libfilecount) + " /* " + libfilename + " in CopyFiles */,\n";
					libfilecount += 1;

				pbjxprojCopyLibs_contents += "	);\n";
				pbjxprojCopyLibs_contents += "	runOnlyForDeploymentPostprocessing = 0;\n";
				pbjxprojCopyLibs_contents += "};\n";
				pbjxprojCopyLibs_contents += "/* End PBXCopyFilesBuildPhase section */\n\n";

				pbxproj = util.str_replace(pbxproj, [("/* End PBXBuildFile section */", pbjxprojCopyLibs_contents)]);
				pbxproj = util.str_replace(pbxproj, [("buildPhases = (", "buildPhases = (\n 	" + copyFilesId + " /* CopyFiles */,")]);

				things2 = "";
				libfilecount = 0;
				addplace3index = pbxproj.find("/* Source */,") - 1 - 24;
				for libfile in self.builder.libs: #config['osx']['libs']:
					libfilename = util.get_str_filename(libfile);
					things2 += "FFFFFFFEFFFF00000000000" + str(libfilecount) + " /* " + libfilename + " */,\n";
					libfilecount += 1;

				newpbxproj = pbxproj[0:addplace3index] + things2 + "				" + pbxproj[addplace3index:];

				# add file references
				libfilecount = 0;
				PBXFileReferenceExtraContents = "";
				for libfile in self.builder.libs: #config['osx']['libs']:
					libfilename = util.get_str_filename(libfile);
					libfile_actual = libfile;
					libfile_actual_relative = os.path.relpath(libfile_actual, self.builder.game_dir + ds + self.builder.build_folder + ds + projectname + "xcodeproj" + ds);
					PBXFileReferenceExtraContents += "FFFFFFFEFFFF00000000000" + str(libfilecount) + " /* " + libfilename + " */ = {isa = PBXFileReference; lastKnownFileType = \"compiled.mach-o.dylib\"; name = " + libfilename + "; path = " + libfile_actual_relative + "; sourceTree = \"<group>\"; };";

				newpbxproj = util.str_replace(newpbxproj, [("/* End PBXFileReference section */", PBXFileReferenceExtraContents)]);

				f = open(self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.platform + ds + projectname + ".xcodeproj" + ds + "project.pbxproj", "w")
				f.write(newpbxproj);
				f.close();
			"""

			# add precompiled headers file
			print("generating pch file");

			nl = "\r\n";
			pcheaderfile = "";
			#pcheaderfile += "#ifdef __OBJC__" + nl;
			# pcheaderfile += "	#import <Foundation/Foundation.h>" + nl;
			# pcheaderfile += "	#import <UIKit/UIKit.h>" + nl + nl;


			# pcheaderfile += "	#import <OpenAL/al.h>" + nl;
			# pcheaderfile += "	#import <OpenAL/alc.h>" + nl + nl

			# pcheaderfile += "	#import <OpenGLES/EAGL.h>" + nl;
			# pcheaderfile += "	#import <QuartzCore/QuartzCore.h>" + nl + nl;

			# pcheaderfile += "	#import <OpenGLES/ES1/gl.h>" + nl;
			# pcheaderfile += "	#import <OpenGLES/ES1/glext.h>" + nl;
			# pcheaderfile += "	#import <OpenGLES/ES2/gl.h>" + nl;
			# pcheaderfile += "	#import <OpenGLES/ES2/glext.h>" + nl;
			# pcheaderfile += "	#import <OpenGLES/EAGLDrawable.h>" + nl + nl;

			# pcheaderfile += "	#import <CoreFoundation/CFBundle.h>" + nl;
			# pcheaderfile += "	#import <CoreFoundation/CoreFoundation.h>" + nl;

			pcheaderfile += "	#import <Foundation/Foundation.h>" + nl;

			pcheaderfile += "	#import <OpenAL/al.h>" + nl;
			pcheaderfile += "	#import <OpenAL/alc.h>" + nl + nl

			#pcheaderfile += "	#import <QuartzCore/QuartzCore.h>" + nl + nl;

			#pcheaderfile += "	#import <OpenGL/OpenGL.h>" + nl;
			pcheaderfile += "	#import <OpenGL/gl3.h>" + nl;
			#pcheaderfile += "	#import <OpenGL/gltypes.h>" + nl;
			#pcheaderfile += "	#import <OpenGL/glu.h>" + nl;
			pcheaderfile += "	#import <OpenGL/gl3ext.h>" + nl + nl;

			#pcheaderfile += "	#import <CoreFoundation/CFBundle.h>" + nl;
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
			info_plist_contents += '	<key>CFBundleDevelopmentRegion</key>' + nl;
			info_plist_contents += '	<string>en</string>' + nl;
			info_plist_contents += '	<key>CFBundleDisplayName</key>' + nl;
			info_plist_contents += '	<string>' + self.builder.game_name + '</string>' + nl;
			info_plist_contents += "	<key>CFBundleGetInfoString</key>" + nl;
			info_plist_contents += "	<string>" + self.builder.game_name + ". Copyright " + self.builder.developer_name + "</string>" + nl;
			info_plist_contents += '	<key>CFBundleExecutable</key>' + nl;
			info_plist_contents += '	<string>${EXECUTABLE_NAME}</string>' + nl;

			# info_plist_contents += '	<key>CFBundleIconFiles</key>' + nl;
			# info_plist_contents += '	<array>' + nl;
			# info_plist_contents += '		<string></string>' + nl;
			# info_plist_contents += '		<string>Icon.png</string>' + nl;					#iphone
			# info_plist_contents += '		<string>Icon@2x.png</string>' + nl;					#iphone-retina
			# info_plist_contents += '		<string>Icon-Small.png</string>' + nl;				#iphone-spotlight
			# info_plist_contents += '		<string>Icon-Small@2x.png</string>' + nl;			#iphone-spotlight-retina
			# info_plist_contents += '		<string>Icon-72.png</string>' + nl;					#ipad
			# info_plist_contents += '		<string>Icon-72@2x.png</string>' + nl;				#ipad-retina
			# info_plist_contents += '		<string>Icon-Small-50.png</string>' + nl;			#ipad-spotlight
			# info_plist_contents += '		<string>Icon-Small-50@2x.png</string>' + nl;		#ipad-spotlight-retina
			# info_plist_contents += '	</array>' + nl;

			# info_plist_contents += '	<key>CFBundleIcons</key>' + nl;
			# info_plist_contents += '	<dict>' + nl;
			# info_plist_contents += '		<key>CFBundlePrimaryIcon</key>' + nl;
			# info_plist_contents += '		<dict>' + nl;
			# info_plist_contents += '			<key>CFBundleIconFiles</key>' + nl;
			# info_plist_contents += '			<array>' + nl;
			# info_plist_contents += '				<string></string>' + nl;
			# info_plist_contents += '				<string>Icon.png</string>' + nl;				#iphone
			# info_plist_contents += '				<string>Icon@2x.png</string>' + nl;				#iphone-retina
			# info_plist_contents += '				<string>Icon-Small.png</string>' + nl;			#iphone-spotlight
			# info_plist_contents += '				<string>Icon-Small@2x.png</string>' + nl;		#iphone-spotlight-retina
			# info_plist_contents += '				<string>Icon-72.png</string>' + nl;				#ipad
			# info_plist_contents += '				<string>Icon-72@2x.png</string>' + nl;			#ipad-retina
			# info_plist_contents += '				<string>Icon-Small-50.png</string>' + nl;		#ipad-spotlight
			# info_plist_contents += '				<string>Icon-Small-50@2x.png</string>' + nl;	#ipad-spotlight-retina
			# info_plist_contents += '			</array>' + nl;
			# info_plist_contents += '		</dict>' + nl;
			# info_plist_contents += '	</dict>' + nl;

			info_plist_contents += '	<key>CFBundleIconFile</key>' + nl;
			info_plist_contents += '	<string>data/icon.icns</string>' + nl;
			info_plist_contents += '	<key>CFBundleIdentifier</key>' + nl;
			info_plist_contents += '	<string>org.' + self.builder.developer_name_safe + '.' + projectname + '</string>' + nl;
			info_plist_contents += '	<key>CFBundleInfoDictionaryVersion</key>' + nl;
			info_plist_contents += '	<string>6.0</string>' + nl;
			info_plist_contents += '	<key>CFBundleName</key>' + nl;
			info_plist_contents += '	<string>${PRODUCT_NAME}</string>' + nl;
			info_plist_contents += '	<key>CFBundlePackageType</key>' + nl;
			info_plist_contents += '	<string>APPL</string>' + nl;
			info_plist_contents += '	<key>CFBundleShortVersionString</key>' + nl;
			info_plist_contents += '	<string>1.0</string>' + nl;
			info_plist_contents += '	<key>CFBundleSignature</key>' + nl;
			info_plist_contents += '	<string>????</string>' + nl;
			info_plist_contents += '	<key>CFBundleVersion</key>' + nl;
			info_plist_contents += '	<string>1.0</string>' + nl;


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
			xcconfigfilecontents += "GCC_PREFIX_HEADER = " + pchfilename + ";" + nl;
			xcconfigfilecontents += "SRCROOT = " + self.builder.game_dir + ds + "src" + ds + "ARK2D" + nl;
			xcconfigfilecontents += "HEADERMAP_INCLUDES_FLAT_ENTRIES_FOR_TARGET_BEING_BUILT = NO;" + nl;
			xcconfigfilecontents += "HEADERMAP_INCLUDES_PROJECT_HEADERS = NO;" + nl;
			xcconfigfilecontents += "HEADERMAP_INCLUDES_FRAMEWORK_ENTRIES_FOR_ALL_PRODUCT_TYPES = NO;" + nl;
			xcconfigfilecontents += "ALWAYS_SEARCH_USER_PATHS = NO;" + nl;
			xcconfigfilecontents += "OTHER_CFLAGS = -x objective-c;" + nl;
			xcconfigfilecontents += "OTHER_CPLUSPLUSFLAGS = -x objective-c++;" + nl;
			#xcconfigfilecontents += "OTHER_LDFLAGS = -lbz2 -lcurl -lz;" + nl;
			xcconfigfilecontents += "INFOPLIST_FILE = " + info_plist_filename;
			# -L" + self.builder.ark2d_dir + "/lib/osx -L" + self.builder.ark2d_dir + "/lib/osx/system -L" + self.builder.ark2d_dir + "/lib/osx/freetype


			print("saving xcconfig file: " + xcconfigfile);
			f = open(xcconfigfile, "w")
			f.write(xcconfigfilecontents);
			f.close();

			print("generating/updating spritesheets");
			self.builder.generateSpriteSheets();

			print("generating/updating strings");
			self.builder.generateStrings();

			#copy ark2d resources in to project data folder.
			#print("Copy game resources in to xcode dir");
			#game_resources_copy = "cp -r " + self.builder.game_resources_dir + "/ " + self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.output + ds + "data/";
			#print(game_resources_copy);
			#subprocess.call([game_resources_copy], shell=True); #libark2d

			#print("Copy ark2d resources in to xcode dir");
			#ark2d_resources_copy_line = "cp -r " + self.builder.ark2d_dir + "/data/ " + self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.output + ds + "data/ark2d/";
			#print(ark2d_resources_copy_line);
			#subprocess.call([ark2d_resources_copy_line], shell=True); #libark2d

			#print("Copy ark2d dylib in to xcode dir");
			#subprocess.call(["cp " + self.builder.ark2d_dir + "/build/osx/DerivedData/ark2d/Build/Products/Default/libark2d-OSX.dylib " + self.builder.game_dir + ds + self.builder.build_folder + ds + self.builder.output + ds + "data/ark2d/libark2d.dylib"], shell=True); #libark2d

			#generate icons
			"""
			if "iphone" in config:
				if "master_icon" in config['iphone']:
					if (config['iphone']['use_master_icon'] == True):
						iconinterpolation = config['iphone']['master_icon_interpolation'];
						icongenarr = [];
						icongenobj = {};
						icongenobj['from'] = config['iphone']['master_icon'];
						icongenobj['from'] = util.str_replace(icongenobj['from'], [("%PREPRODUCTION_DIR%", config['osx']['game_preproduction_dir'])]);
						icongenobj['to'] = [
							# iPhone Icon
							{
								"filename": self.game_dir + ds + self.build_folder + ds + self.platform + ds + "Icon.png",
								"width" : 57,
								"height": 57,
								"interpolation": iconinterpolation
							},
							{
								"filename": self.game_dir + ds + self.build_folder + ds + self.platform + ds + "Icon@2x.png",
								"width" : 114,
								"height": 114,
								"interpolation": iconinterpolation
							},
							# iPhone Spotlight Icon
							{
								"filename": self.game_dir + ds + self.build_folder + ds + self.platform + ds + "Icon-Small.png",
								"width" : 29,
								"height": 29,
								"interpolation": iconinterpolation
							},
							{
								"filename": self.game_dir + ds + self.build_folder + ds + self.platform + ds + "Icon-Small@2x.png",
								"width" : 58,
								"height": 58,
								"interpolation": iconinterpolation
							},
							# iPad Icon
							{
								"filename": self.game_dir + ds + self.build_folder + ds + self.platform + ds + "Icon-72.png",
								"width" : 72,
								"height": 72,
								"interpolation": iconinterpolation
							},
							{
								"filename": self.game_dir + ds + self.build_folder + ds + self.platform + ds + "Icon-72@2x.png",
								"width" : 144,
								"height": 144,
								"interpolation": iconinterpolation
							},
							# iPad Spotlight Icon
							{
								"filename": self.game_dir + ds + self.build_folder + ds + self.platform + ds + "Icon-Small-50.png",
								"width" : 50,
								"height": 50,
								"interpolation": iconinterpolation
							},
							{
								"filename": self.game_dir + ds + self.build_folder + ds + self.platform + ds + "Icon-Small-50@2x.png",
								"width" : 100,
								"height": 100,
								"interpolation": iconinterpolation
							},
							# app store icon
							{
								"filename": self.game_dir + ds + self.build_folder + ds + self.platform + ds + "iTunesArtwork",
								"width" : 512,
								"height": 512,
								"interpolation": iconinterpolation
							},
							{
								"filename": self.game_dir + ds + self.build_folder + ds + self.platform + ds + "iTunesArtwork@2x",
								"width" : 1024,
								"height": 1024,
								"interpolation": iconinterpolation
							}


						];
						icongenarr.extend([icongenobj]);
						#icongenstr = json.dumps(icongenarr, sort_keys=True, indent=0, new);


						icongenstr = str(json.dumps(icongenarr, separators=(',',':'))).replace("\"", "\\\"");
						icongenLINE = "java -jar " + self.ark2d_dir + "/../Tools/Image\ Resizer/build/jar/Resizer.jar \"" + icongenstr + "\"";
						print(icongenLINE);
						subprocess.call([icongenLINE], shell=True);


						#os.system();
						pass;
					pass;
				pass;
			"""


			pass;
