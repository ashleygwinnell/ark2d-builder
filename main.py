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

from Game import *
from Builder import *
from Util import *

util = Util();

#
# Windows requires MinGW 3.4.5 with includes:
# 	AL/
#		al.h, alc.h, alext.h, alut.h
#	GL/
#		gl.h, glew.h, glext.h, glu.h, glxew.h, glxext.h, wglew.h, wglext.h
#
#	... and probably some others which I don't remember right now.
#
#
# Python 2.7?
#
#
# Mac requires you do not install OpenAL from their website
#  - i.e. you should not have Library/Frameworks/OpenAL.framework
#  - Add Tools/ to path
# 		http://architectryan.com/2012/10/02/add-to-the-path-on-mac-os-x-mountain-lion/#.Uvn-EEJ_vPY
#

#
# Windows Phone builds...
# http://software.intel.com/en-us/articles/using-winrt-apis-from-desktop-applications
# 	-	Add /ZW
# 	-	Remove /Gm
#
#	Add xaudio2.lib to library dependencies.
#	Add vendor/wp8/gl2dx to compile files.
#
# Windows 8 (vs) builds...
# 	Add /LIBPATH:folder (linker)
#		%(AdditionalLibraryDirectories); $(VCInstallDir)\lib\store; $(VCInstallDir)\lib
# 	Add libs to linker
#		d2d1.lib
#		d3d11.lib
#		dxgi.lib
#		dwrite.lib
#		advapi32.lib - for controllers
# 		user32.lib
#		gdi32.lib
#		shell32.lib
#

#
# Linux bits
# 	X11. 			sudo apt-get install libx11-dev
#	X11 Xinerama	sudo apt-get install libxinerama-dev
#	GL. 			sudo apt-get install mesa-common-dev
#	OpenAL. 		sudo apt-get install libalut-dev
#	cURL. 			sudo apt-get install libcurl4-openssl-dev
#	SDL2?			sudo apt-get install libsdl2-dev
#

# HTML5 / Emscripten bits.
#	Tutorial: https://developer.mozilla.org/en-US/docs/Mozilla/Projects/Emscripten/Introducing/Emscripten_beginners_tutorial
#	Download & install: https://developer.mozilla.org/en-US/docs/Mozilla/Projects/Emscripten/Download_and_install
#	Run ./emsdk update
#	Run ./emsdk install latest
#	Run ./emsdk activate latest

# Build Line examples
# python /Users/ashleygwinnell/Dropbox/ark2d/ARK2D/build.py type=game dir=/Users/ashleygwinnell/Dropbox/Projects/C++/ToastTime/ spritesheets=true target=xcode


def printPair(l, param1, param2):
	print(("%-" + str(l) + "s%-" + str(l) + "s") % (param1, param2));

##
# TODO:
##
# 1)
# 	copy build_release\libARK2D.dll
# 	copy lib\alut.dll
# 	copy lib\glew32.dll
# 	copy/merge data directory
# 2)
# 	when compiling games, check to see if the library needs updating and compile that too (before the game).
#
#
# 	params:
#		NAME 		DESC 												OPTIONS 						REQUIRED
#		type 		building a game or the framework?					library | game 					defaults to "game"
#		target 		the platform to build for.							default | android | ios 		defaults to "default"
#		dir 		directory of the game. must not contain spaces. 	directory						defaults to cwd
#		clean 		clean project or not. 								true | false
#		debug 		debug project or not. 								true | false
#
##
if __name__ == "__main__":

	print("---------------------");
	print("ARK2D Project Builder");
	print("---------------------");
	print("Starting");

	type = "library";
	target = "default";
	dir = sys.path[0] + "/..";
	use_dir = False;
	clean = False;
	debug = False;
	onlyspritesheets = False;
	onlygeneratestrings = False;
	onlyassets = False;
	dogradle = False;
	newconfig = False;
	compileproj = False;
	selecttarget = False;

	count = 0;
	print("Args: " + str(len(sys.argv)));
	for item in sys.argv:
		print("Item: " + item);
		if count == 0:
			count += 1;
			continue;

		parts = item.split("=");
		if len(parts) > 2:
			print("item " + item + " is invalid");
			continue;
		if parts[0] == "type":
			type = parts[1];
		elif parts[0] == "target":
			target = parts[1];
		elif parts[0] == "dir":
			dir = parts[1];
			use_dir = True;
		elif parts[0] == "debug":
			if (parts[1]=="true"):
				debug = True;
			else:
				debug = False
		elif parts[0] == "clean":
			if (parts[1]=="true"):
				clean = True;
		elif parts[0] == "spritesheets":
			if (parts[1]=="true"):
				onlyspritesheets = True;
			else:
				onlyspritesheets = False;
		elif parts[0] == "strings":
			if (parts[1]=="true"):
				onlygeneratestrings = True;
			else:
				onlygeneratestrings = False;

		elif parts[0] == "assets":
			if (parts[1]=="true"):
				onlyassets = True;
			else:
				onlyassets = False;

		elif parts[0] == "newconfig":
			if(parts[1] == "true"):
				newconfig = True;
			else:
				newconfig = False;

		elif parts[0] == "compileproj":
			if(parts[1] == "true"):
				compileproj = True;
			else:
				compileproj = False;

		elif parts[0] == "selecttarget":
			if(parts[1] == "true"):
				selecttarget = True;
			else:
				selecttarget = False;

		count += 1;

	print("---");
	printPair(20, "type:", type);
	printPair(20, "target:", target);
	printPair(20, "dir: ", dir);
	printPair(20, "use_dir: ", str(use_dir));
	printPair(20, "debug: ", str(debug));
	printPair(20, "clean: ", str(clean));
	printPair(20, "newconfig: ", str(newconfig));
	printPair(20, "onlyspritesheets: ", str(onlyspritesheets));

	if (sys.platform == "win32"):
		arkPlatform = "windows";
	elif(sys.platform == "darwin"):
		arkPlatform = "osx";
	elif(sys.platform == "linux2"):
		arkPlatform = "linux";
	else:
		print("platform " + sys.platform + " not supported");
		exit(0);



	# have to read json and override some values for back-compatibility.
	ark2d_dir = os.path.dirname(os.path.realpath(__file__)) +"/..";
	if (sys.platform == "win32"):
		if (ark2d_dir[len(ark2d_dir)-2:len(ark2d_dir)] == ".."):
			ark2d_dir = ark2d_dir[0:ark2d_dir.rfind("\\")];

	if ((newconfig or selecttarget) and type == "game"):
		try:
			if (use_dir == False):
				dir = os.getcwd();

			print("---");
			print("Current file: " + ark2d_dir);
			print("Current working directory: " + dir);

			print("---");
			print("Opening ark2d config file: ");
			f = open(ark2d_dir + "/config.json");
			fcontents = f.read();
			f.close();
			ark_config = json.loads(fcontents);
			print("Done.");

			print("---");
			print("Opening game config file: ");
			print(dir + "/configs/game.json");
			f = open(dir + "/configs/game.json");
			fcontents = f.read();
			f.close();
			game_config = json.loads(fcontents);
			print("Done.");

			if (selecttarget == True):
				print("---");
				print("Select compile target:");

				targetConfigsDirectory = dir + "/configs/";
				targetConfigsPre = util.listFiles(targetConfigsDirectory);

				targetConfigsPost = [];
				for tc in targetConfigsPre:
					tcn = util.get_str_filename2(tc);
					if (tcn == "game.json"):
						continue;
					else:
						targetConfigsPost.extend([tcn]);

				tcindex = 0;
				for tc in targetConfigsPost:
					print("" + str(tcindex+1)+ ". " + tc);
					tcindex += 1;

				t = raw_input("> ")
				targetIndex = int(t)-1;
				target = targetConfigsPost[targetIndex];

				print("Clean? [Y/N]");
				t = raw_input("> ");
				clean = True if t.lower() == "y" else False;

				print("Only spritesheets? [Y/N]");
				t = raw_input("> ");
				onlyspritesheets = True if t.lower() == "y" else False;








			print("---");
			print("Opening target config file: ");
			print(dir + "/configs/" + target);

			f = open(dir + "/configs/" + target);
			fcontents = f.read();
			f.close();
			target_config = json.loads(fcontents);
			print("Done.");

			#print(game_config);
			#print(target_config);
			#print(game_config['game']['name']);
			#if (target_config["platform"] == "windows"):

			a = Builder();
			a.newconfig = True;
			a.compileproj = compileproj;
			a.debug = debug;
			a.platform = target_config['platform'] if 'platform' in target_config else 'game';
			a.output = target_config['folder'] if 'folder' in target_config else 'game';

			a.ark2d_dir = ark2d_dir;
			a.game_dir = dir;
			a.game_src_dir = dir + "/src/";
			a.game_name = game_config['game']['name'];
			a.game_name_safe = game_config['game']['name_safe'];
			#a.game_short_name = game_config['game']['class_name'];
			a.game_class_name = game_config['game']['class_name'];
			a.game_description = game_config['game']['description'];
			a.game_resources_dir = a.game_dir + a.ds + game_config['game']['folders']['resources'];
			a.game_preproduction_dir = a.game_dir + a.ds + game_config['game']['folders']['preproduction'];
			a.game_clear_color = game_config['game']['clearcolor'];
			a.game_orientation = game_config['game']['orientation'];
			a.game_version = game_config['game']['version'] or "0.1.0";
			a.developer_name = game_config['developer']['name'];
			a.developer_name_safe = game_config['developer']['name_safe'];


			a.src_files.extend(game_config["src_files"]);
			a.game_mkdirs = game_config['mkdirs'];
			a.build_artifact = "";
			a.config = game_config;
			a.ark_config = ark_config
			a.game_config = game_config;
			a.target_config_file = target;
			a.target_config_name = util.strip_extension(a.target_config_file);
			a.target_config = target_config;

			a.gamePreInit();

			a.tag_replacements = [
				("%PREPRODUCTION_DIR%", a.game_preproduction_dir),
				("%ARK2D_DIR%", a.ark2d_dir),
				("%ARK2D_CURRENT_CONFIG%", a.target_config_name),
				("%COMPANY_NAME%", a.developer_name),
				("%COMPANY_NAME_SAFE%", a.developer_name_safe),
				("%GAME_DIR%", a.game_dir),
				("%GAME_NAME%", a.game_name),
				("%GAME_NAME_SAFE%", a.game_name_safe),
				("%GAME_VERSION%", a.game_version),
				("%GAME_SHORT_NAME%", a.game_class_name),
				("%GAME_CLASS_NAME%", a.game_class_name),
				("%GAME_CLEAR_COLOR%", a.game_clear_color),
				("%GAME_ORIENTATION%", a.game_orientation)#,
				#("%GAME_WIDTH%", str(0))
				#("%GAME_HEIGHT%", str(0))
			];

			if (onlyspritesheets):
				a.generateSpriteSheets();
				exit(0);

			if (onlygeneratestrings):
				a.generateStrings();
				exit(0);

			dogradle = False;
			if (a.platform == "android"):
				print("Gradle build? [Y/N]");
				t = raw_input("> ");
				dogradle = True if t.lower() == "y" else False;

			if (clean == True or target_config['clean'] == True):
				a.clean();
				#exit(0);


			a.mingw_link = "";

			# Add libs to ark2d build system
			if ("libs" in target_config):
				for lib in target_config['libs']:
					lib2 = util.str_replace(lib, a.tag_replacements);
					lib2 = a.fixLocalPath(lib2);
					a.libs.extend([lib2]);

			if ("include_dirs" in game_config):
				a.include_dirs.extend(game_config['include_dirs']);

			if ("include_dirs" in target_config):
				for idir in target_config['include_dirs']:
					idir = util.str_replace(idir, a.tag_replacements);
					idir = a.fixLocalPath(idir);
					a.include_dirs.extend([idir]);

			if ("defines" in game_config):
				a.preprocessor_definitions.extend(game_config['defines']);

			if ("defines" in target_config):
				a.preprocessor_definitions.extend(target_config['defines']);

			if (a.platform == "firetv"):
				a.firetv = True;

			if (a.platform == "ouya"):
				a.ouya = True;
				a.ouya_config = game_config['ouya'];

			if (a.platform == "ios" or a.platform == "iphone" or a.platform == "ipad"):
				a.ios_config = target_config['ios'];

			if (a.platform == "android" or a.platform == "ouya" or a.platform == "firetv"):
				print("Opening android.json");
				f = open(dir + "/configs/android.json");
				fcontents = f.read();
				f.close();
				a.android_config = json.loads(fcontents)['android'];

				a.android_sdkdir = a.android_config['sdk_dir'];
				a.android_ndkdir = a.android_config['ndk_dir'];
				a.android_srcfiles = [];
				a.android_libs = [];
				a.android_libraryprojects = [];

				if "src_files" in a.android_config:
					for src in a.android_config['src_files']:
						src_actual = util.str_replace(src, a.tag_replacements);
						a.android_srcfiles.extend([src_actual]);

				if "libs" in a.android_config:
					for lib in a.android_config['libs']:
						lib_actual = util.str_replace(lib, a.tag_replacements);
						a.android_libs.extend([lib_actual]);

				# library projects
				if "library_projects" in a.android_config:
					for libproj in a.android_config['library_projects']:
						libproj_actual = util.str_replace(libproj, a.tag_replacements);
						a.android_libraryprojects.extend([libproj_actual]);

				if "android" in target_config and "library_projects" in target_config['android']:
					for libproj in target_config['android']['library_projects']:
						print("library project: " + libproj);
						libproj_actual = util.str_replace(libproj, a.tag_replacements);
						a.android_libraryprojects.extend([libproj_actual]);

				if "override_activity" in a.android_config:
					a.android_config["override_activity"] = util.str_replace(a.android_config["override_activity"], a.tag_replacements);

				if "override_manifest" in a.android_config:
					a.android_config["override_manifest"] = util.str_replace(a.android_config["override_manifest"], a.tag_replacements);

				if "override_ids" in a.android_config:
					a.android_config["override_ids"] = util.str_replace(a.android_config["override_ids"], a.tag_replacements);

				if "override_strings" in a.android_config:
					a.android_config["override_strings"] = util.str_replace(a.android_config["override_strings"], a.tag_replacements);

			# Windows Phone 8 config.
			if (a.platform == "windows-phone"):
				print("Opening windows-phone.json");
				f = open(dir + "/configs/windows-phone.json");
				fcontents = f.read();
				f.close();
				a.wp8_config = json.loads(fcontents)['windows-phone'];


			"""if(sys.platform=="win32"):
				a.dll_files.append(a.ark2d_dir + a.ds + a.build_folder + a.ds + a.platform + a.ds + 'libARK2D.dll');
				a.linkingFlags += "-mwindows ";
				#a.linkingFlags += "-static-libgcc -static-libstdc++ ";
				a.linkingFlags += "-enable-auto-import ";
			elif(sys.platform=="darwin"):
				a.dll_files.append(a.ark2d_dir + a.ds + a.build_folder + a.ds + a.platform + a.ds + 'libARK2D.dylib');

				if ('mac_game_icns' in config[arkPlatform]):
					a.mac_game_icns = config[arkPlatform]['mac_game_icns'];


			if ('game_resources_dir' in config[arkPlatform]):
				a.game_resources_dir = config[arkPlatform]['game_resources_dir'];
			"""



			a.gamePostInit();



			if (onlyassets):
				a.processAssets();
				exit(0);

			a.start();

			if (dogradle):
				subprocess.call(["build/android/project-intellij/gradlew -p build/android/project-intellij/ assembleDebug"], shell=True);
				subprocess.call(["build/android/project-intellij/gradlew -p build/android/project-intellij/ installDebug"], shell=True);


			print("---");
			print("Done");
			print("---");

		except Exception as exc:
			print("configs/" + target + " is invalid or does not exist.");
			print(exc);
			util.printException();
			exit(1);
		except SystemExit as exc:
			pass;
		except:
			print("configs/" + target + " is invalid or does not exist.");
			print( sys.exc_info()[0] );
			exit(1);

		exit(0);



	if (type == "library"):

		print("---");
		print("Building Library");
		print("Target: " + target);

		a = Builder();
		a.compileproj = compileproj;
		a.debug = debug;
		a.ark2d_dir = ark2d_dir;

		if (target=='iphone' or target=="ios"):
			a.platform = 'ios';
		elif (target=='android'):
			a.platform = 'android';
		elif (target=='ouya'):
			a.platform = 'android';
			a.ouya = True;
		elif (target=='flascc'):
			a.platform = 'flascc';
		elif (target=='xcode' or target == "osx"):
			a.platform = 'osx';
		elif (target=='windows' or target =="windows-vs"):
			a.platform = 'windows';
		elif (target=='windows-phone'):
			a.platform = 'windows-phone';
		elif (target=='windows-store'):
			a.platform = 'windows-store';
		elif (target=='xbox-one'):
			a.platform = 'xbone';
		elif (target=='linux' or target=='ubuntu-linux'):
			a.platform = 'linux';
		elif (target=='html5' or target=='emscripten'):
			a.platform = 'html5';

		a.output = a.platform;

		print("---");
		print("Opening config file: " + dir + "/config.json");
		f = open(dir + "/config.json", "r");
		fcontents = f.read();
		f.close();
		config = False;

		try:
			a.config = json.loads(fcontents);
			a.ark_config = a.config;
			a.android_config = a.config['android'];
			a.android_sdkdir = a.config[a.platformOn]['android']['sdk_dir'];
			a.android_ndkdir = a.config[a.platformOn]['android']['ndk_dir'];
		except:
			print("Config.json invalid.");
			exit(1);

		a.dllInit();

		if (clean):
			a.clean();
			#exit(0);

		a.start();

	else:

		print("---");
		print("Must use new configs for game building? ");
		exit(0);

		"""
		print("---");
		print("Building game");

		print("---");
		print("Opening config file: " + dir + "/config.json");
		f = open(dir + "/config.json", "r");
		fcontents = f.read();
		f.close();

		#print(fcontents);
		config = False;

		try:
			config = json.loads(fcontents);
			blah = config["game_name"];

			if (config == False):
				print("Config.json invalid or trying to build game from framework path.");
				exit(1);

			a = ARK2DBuildSystem();
			a.debug = debug;

			if (target=='iphone' or target=="ios"):
				a.platform = 'ios';
			elif (target=='android'):
				a.platform = 'android';
			elif (target=='ouya'):
				a.platform = 'android';
				a.ouya = True;
			elif (target=='flascc'):
				a.platform = 'flascc';
			elif (target=='xcode' or target=='osx'):
				a.platform = 'osx';
			elif (target=='windows-vs'):
				a.platform = 'windows';
			elif (target=='windows-store'):
				a.platform = 'windows-store';
			elif (target=='windows-phone'):
				a.platform = 'windows-phone';
			elif (target=='ubuntu-linux'):
				a.platform = 'ubuntu-linux';
			elif (target=='html5' or target=='emscripten'):
				a.platform = 'html5';

			a.output = a.platform;

			a.ark2d_dir = config[arkPlatform]["ark2d_dir"];
			a.game_name = config["game_name"];
			a.game_short_name = config['game_short_name'];
			a.game_dir  = config[arkPlatform]["game_dir"];
			a.src_files.extend(config["game_src_files"]);
			a.game_mkdirs = config['game_mkdirs'];
			a.build_artifact = "";
			a.config = config;

			if ("libs" in config[arkPlatform]):
				a.libs.extend(config[arkPlatform]["libs"]);
			if ("include_dirs" in config[arkPlatform]):
				a.include_dirs.extend(config[arkPlatform]['include_dirs']);

			if (clean == True):
				a.clean();
				#exit(0);

			a.gamePreInit();

			a.mingw_link = "";

			if(sys.platform=="win32"):
				a.dll_files.append(a.ark2d_dir + a.ds + a.build_folder + a.ds + a.platform + a.ds + 'libARK2D.dll');
				a.linkingFlags += "-mwindows ";
				#a.linkingFlags += "-static-libgcc -static-libstdc++ ";
				a.linkingFlags += "-enable-auto-import ";
			elif(sys.platform=="darwin"):
				a.dll_files.append(a.ark2d_dir + a.ds + a.build_folder + a.ds + a.platform + a.ds + 'libARK2D.dylib');

				if ('mac_game_icns' in config[arkPlatform]):
					a.mac_game_icns = config[arkPlatform]['mac_game_icns'];


			if ('game_resources_dir' in config[arkPlatform]):
				a.game_resources_dir = config[arkPlatform]['game_resources_dir'];


			a.gamePostInit();

			if (onlyspritesheets):
				a.generateSpriteSheets();
				print('done');
				exit(0);

			if (onlyassets):
				a.processAssets();
				exit(0);

			a.start();

		except Exception as exc:
			print(exc);
			print("Config.json invalid or trying to build game from framework path.");
			exit(1);
		except:
			print("Done");
			pass;
		"""





