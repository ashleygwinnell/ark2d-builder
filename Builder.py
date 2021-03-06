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
import time
import hashlib

from Util import *
from Module import *
from MacBuild import *
from IOSBuild import *

util = Util();

class Builder:

	def __init__(self):

		self.building_library = False;
		self.building_game = True;

		self.ark2d_dir = "";

		#self.game = ARK2DGame();
		self.game_dir = "";
		self.game_name = "";
		self.game_short_name = "";
		self.game_resources_dir = "";
		self.libs = [];
		self.include_dirs = [];
		self.preprocessor_definitions = [];
		self.aars = [];
		self.aar_paths = [];
		#self.mac_game_icns = "";

		self.build_folder = "build";
		self.arch = platform.machine();

		self.resourceCompiler = "windres";

		self.ouya = False;
		self.firetv = False;
		if ((len(sys.argv)==3 and sys.argv[2] == "android") or (len(sys.argv)==2 and sys.argv[1] == "android")):
			self.platform = "android";
			if (sys.platform == "win32"):
				self.platformOn = "windows";
				self.ds = "\\";
			elif(sys.platform == "darwin"):
				self.platformOn = "osx";
				self.ds = "/";
			pass;

		elif ((len(sys.argv)==3 and sys.argv[2] == "iphone") or (len(sys.argv)==2 and "iphone" in sys.argv[1])):
			self.platform = "ios";
			self.ds = "/";

			self.varPLATFORM = "iPhoneSimulator"; #"iPhoneSimulator"; #iPhoneOS
			self.varPLATFORMsml = "iphoneos"; #"iphonesimulator"; #iphoneos

			self.gccCompiler = "/Developer/Platforms/iPhoneOS.platform/Developer/usr/bin/gcc-4.2"; #i686-apple-darwin11-llvm-gcc-4.2 ";
			self.gppCompiler = "/Developer/Platforms/iPhoneOS.platform/Developer/usr/bin/g++-4.2"; #i686-apple-darwin11-llvm-g++-4.2 ";
			self.objcCompiler = "/Developer/Platforms/iPhoneOS.platform/Developer/usr/bin/g++-4.2";# i686-apple-darwin11-llvm-g++-4.2 ";
			self.build_artifact = self.build_folder + self.ds + self.platform + self.ds + "libARK2D.dylib";

			self.platformOn = "osx";

			pass;
		elif (sys.platform == "win32"):
			self.ds = "\\";
			self.platform = "windows";
			self.mingw_dir = "C:\\MinGW";
			self.mingw_link = "-L" + self.mingw_dir + self.ds + "lib"
			self.gccCompiler = "gcc";
			self.gppCompiler = "g++";
			self.objcCompiler = "g++";
			self.build_artifact = self.build_folder + self.ds + self.platform + self.ds + "libARK2D.dll";

			self.platformOn = "windows";

		elif (sys.platform == "linux2"):
			self.ds = "/";
			self.platform = "linux";
			self.gccCompiler = "gcc";
			self.gppCompiler = "g++";
			self.platformOn = "linux";
			self.build_artifact = self.build_folder + self.ds + self.platform + self.ds + "libark2d.so";

		elif(sys.platform == "darwin"):
			self.ds = "/";
			self.platform = "osx";
			self.mingw_dir = ""; #/usr";
			self.mingw_link = ""; #-L" + self.mingw_dir + self.ds + "lib"

			# lion
			self.gccCompiler = "i686-apple-darwin11-llvm-gcc-4.2 ";
			self.gppCompiler = "i686-apple-darwin11-llvm-g++-4.2 ";
			self.objcCompiler = "i686-apple-darwin11-llvm-g++-4.2 ";

			# mountain lion
			#self.gccCompiler = "/Developer/usr/llvm-gcc-4.2/bin/i686-apple-darwin11-llvm-gcc-4.2 ";
			#self.gppCompiler = "/Developer/usr/llvm-gcc-4.2/bin/i686-apple-darwin11-llvm-g++-4.2 ";
			#self.objcCompiler = "/Developer/usr/llvm-gcc-4.2/bin/i686-apple-darwin11-llvm-g++-4.2 ";

			#self.gccCompiler = "/Developer/usr/bin/i686-apple-darwin11-gcc-4.2.1 ";
			#self.gppCompiler = "/Developer/usr/bin/i686-apple-darwin11-g++-4.2.1 ";
			#self.objcCompiler = "/Developer/usr/bin/i686-apple-darwin11-g++-4.2.1 ";

			# apple break things every release. run this if
			# sudo ln -s /Developer/SDKs/MacOSX10.6.sdk/usr/lib/crt1.10.6.o /Developer/usr/llvm-gcc-4.2/lib


			#self.gccCompiler = "llvm-gcc-4.2";
			#self.gppCompiler = "llvm-g++-4.2";
			#self.gccCompiler = "gcc";
			#self.gppCompiler = "g++";

			self.platformOn = "osx";

			self.build_artifact = self.build_folder + self.ds + self.platform + self.ds + "libARK2D.dylib";
			self.mac_game_icns = '';

		self.windresources = [];
		self.compilerOptions = "";

		self.mkdirs = [];
		self.game_mkdirs = [];
		self.src_files = [];
		self.dll_files = [];
		self.static_libraries = [];
		self.linkingFlags = "";

	def getTargetPlatform(self):
		if ((len(sys.argv)==3 and sys.argv[2] == "android") or (len(sys.argv)==2 and sys.argv[1] == "android")):
			return "android";
		elif ((len(sys.argv)==3 and sys.argv[2] == "iphone") or (len(sys.argv)==2 and sys.argv[1] == "iphone")):
			return "ios";
		elif (sys.platform == "win32"):
			return "windows";
		elif(sys.platform == "darwin"):
			return "osx";
		return "error";

	def dllInit(self):

		config = self.config;

		self.building_library = True;
		self.building_game = False;

		""" TODO: put this in config."""
		self.mkdirs.extend([
			self.build_folder,
			self.build_folder + self.ds + self.output,
			self.build_folder + self.ds + self.output + self.ds + "build-cache", # cache folder
			self.build_folder + self.ds + self.output + self.ds + "src",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Audio",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Controls",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "Controls",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "Font",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "Geometry",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "Graphics",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "Graphics" + self.ds + "HLSL",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "Graphics" + self.ds + "ImageIO",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "Graphics" + self.ds + "Shaders",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "Math",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "Platform",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "SceneGraph",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "State",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "State" + self.ds + "Transition",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "Threading",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "Tween",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "Util",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Core" + self.ds + "Vendor",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Font",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Geometry",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "GJ",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "GJ" + self.ds + "Next",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Math",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Net",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Particles",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Path",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Pathfinding",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "SceneGraph",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "State",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "State" + self.ds + "Transition",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Tests",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Threading",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Tiled",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Tools",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Tween",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "UI",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "UI" + self.ds + "Util",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Util",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Util" + self.ds + "Containers",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "Util" + self.ds + "LocalMultiplayer",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "angelscript",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "angelscript" + self.ds + "add_on",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "angelscript" + self.ds + "add_on" + self.ds + "scriptarray",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "angelscript" + self.ds + "add_on" + self.ds + "scriptbuilder",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "angelscript" + self.ds + "add_on" + self.ds + "scriptstdstring",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "libJSON",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "lpng151",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "mersennetwister",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "ogg130",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "tinyxml",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "spine",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "spine" + self.ds + "src",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "submodules",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "submodules" + self.ds + "libpng15",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "vorbis132",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "vorbis132" + self.ds + "modes",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "utf8",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "utf8" + self.ds + "utf8",
			self.build_folder + self.ds + self.output + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "zlib123"
		]);


		#self.src_files.extend(config['src_files']['all']);

		if (self.platform == "flascc"):
			self.src_files.extend(config['src_files']['flascc']);
			self.ark2d_dir = config[self.platformOn]['ark2d_dir'];

		elif (self.platform == "android"):
			self.src_files.extend(config['src_files']['android']);
			self.ark2d_dir = config[self.platformOn]['ark2d_dir'];

		elif (self.platform == "linux"):
			self.src_files.extend(config['src_files']['linux']);
			self.ark2d_dir = config[self.platformOn]['ark2d_dir'];
			self.config = config;

		elif (self.platform == "html5"):
			self.src_files.extend(config['src_files']['html5']);
			self.ark2d_dir = config[self.platformOn]['ark2d_dir'];
			self.config = config;

		elif (self.platform == "ios"):
			self.src_files.extend(config['src_files']['ios']);
			self.ark2d_dir = config["osx"]['ark2d_dir'];

			self.static_libraries.extend(config['static_libraries']['ios']);
		elif (self.platform == "windows-old"):

			self.src_files.extend(config['src_files']['windows']);
			self.dll_files.extend(config['dynamic_libraries']['windows']);
			self.static_libraries.extend(config['static_libraries']['windows']);
			self.linkingFlags = " -mwindows -shared ";

			self.ark2d_dir = config["windows"]['ark2d_dir'];
			self.ark2d_tmpdir = "C:\\a2d\\l";

		elif (self.platform=="windows"):
			self.src_files.extend(config['src_files']['windows']);
			self.dll_files.extend(config['dynamic_libraries']['windows']);
			self.static_libraries.extend(config['static_libraries']['windows']);

			#self.ark2d_dir = ""; #config["windows"]['ark2d_dir'];
			self.ark2d_tmpdir = "C:\\a2dvs\\l";

		elif (self.platform=="windows-phone"):
			self.src_files.extend(config['src_files']['windows-phone']);
			#self.dll_files.extend(config['dynamic_libraries']['windows']);
			#self.static_libraries.extend(config['static_libraries']['windows']);

			self.ark2d_dir = config["windows"]['ark2d_dir'];
			self.ark2d_tmpdir = "C:\\a2dwpvs\\l";

		elif (self.platform=="windows-store"):
			self.src_files.extend(config['src_files']['windows-store']);
			#self.dll_files.extend(config['dynamic_libraries']['windows']);
			#self.static_libraries.extend(config['static_libraries']['windows']);

			self.ark2d_dir = config["windows"]['ark2d_dir'];
			self.ark2d_tmpdir = "D:\\a2dws10vs\\l";

		elif (self.platform == "osx"):

			self.build_artifact = self.build_folder + self.ds + self.platform + self.ds + "libARK2D.dylib";

			self.src_files.extend(config['src_files']['osx']);
			self.dll_files.extend(config['dynamic_libraries']['osx']);
			self.static_libraries.extend(config['static_libraries']['osx']);
			self.linkingFlags = "";

			self.ark2d_dir = config["osx"]['ark2d_dir'];
			self.ark2d_tmpdir = "/ark2d/lib";

		elif (self.platform == "xcode"):

			self.build_artifact = self.build_folder + self.ds + self.platform + self.ds + "libARK2D.dylib";

			self.src_files.extend(config['src_files']['osx']);
			self.dll_files.extend(config['dynamic_libraries']['osx']);
			self.static_libraries.extend(config['static_libraries']['osx']);
			self.linkingFlags = "";

			self.ark2d_dir = config["osx"]['ark2d_dir'];
			self.ark2d_tmpdir = "/ark2d/lib";

		self.game_dir = self.ark2d_dir;
		self.src_files.extend(config['src_files']['all']);



	def gamePreInit(self):

		self.building_library = False;
		self.building_game = True;

		#self.src_files[:] = []; # clear the lists.
		self.dll_files[:] = [];
		self.static_libraries[:] = [];

		#self.build_folder = self.game_dir + "/" + self.build_folder;

		self.mkdirs.extend([
			self.build_folder,
			self.build_folder + self.ds + self.output,
			self.build_folder + self.ds + self.output + self.ds + "src",
			self.build_folder + self.ds + self.output + self.ds + "build-cache" # cache folder

		]);
		print  self.mkdirs;
		print  self.game_mkdirs;
		print  self.game_version;
		if (self.game_mkdirs and len(self.game_mkdirs) > 0):
			self.mkdirs.extend(self.game_mkdirs);

		versionCodePieces = self.game_version.split('.');
		self.game_version_major = str(versionCodePieces[0]);
		self.game_version_minor = str(versionCodePieces[1]) if len(versionCodePieces) > 1 else "0";
		self.game_version_patch = str(versionCodePieces[2]) if len(versionCodePieces) > 2 else "0";

		if (self.platform == "windows-old"):
			self.ark2d_tmpdir = "C:\\a2d\\gm";
		else:
			self.ark2d_tmpdir = "/ark2d/gm";

	def gamePostInit(self):

		if (sys.platform == "win32"):
			self.build_artifact = self.build_folder + self.ds + self.platform + self.ds + self.game_name.replace(" ", "_") + ".exe";
		elif(sys.platform == "darwin"):
			self.build_artifact = self.build_folder + self.ds + self.game_name.replace(" ", "_");


		# open config
		"""f = open(self.game_dir + "/config.json", "r");
		fcontents = f.read();
		f.close();
		config = json.loads(fcontents);
		"""
		#create ARK.h file
		self.generateARKH(self.game_dir + self.ds + "src" + self.ds + "ARK.h");

		#self.config = config;




	def generateARKH(self, floc):
		"""if (self.newconfig == True):
			# rewrite this for compatibility with new config layout.
			# must take into account all config files somehow...
			# do something like...
			# 	#include ARK_INCLUDE_H
			# and set this variable here in the build script depending on the platform!?
			print("Generating ARK.h file at " + floc);
			nl = " \r\n";
			if (sys.platform == "win32"):
				nl = "\n";

			arkh = " #include <ARK.h> " + nl;
			f = open(floc, "w");
			f.write(arkh);
			f.close();

		else:
		"""
		print("---");
		print("Generating ARK.h file at " + floc);
		nl = " \r\n";
		if (sys.platform == "win32"):
			nl = "\n";

		"""
		arkh  = "";
		arkh += "#if defined(ARK2D_WINDOWS) || defined(ARK2D_ANDROID_ON_WINDOWS) || defined(ARK2D_WINDOWS_PHONE_8) " + nl;
		arkh += "	#include \"" + util.str_replace(self.ark_config['windows']['ark2d_dir'], [("\\", "\\\\")]) + "\\\\src\\\\ARK.h\"" + nl;
		arkh += "#elif defined(ARK2D_MACINTOSH) || defined(ARK2D_ANDROID_ON_MACINTOSH) || defined(ARK2D_EMSCRIPTEN_JS_ON_MACINTOSH) || defined(ARK2D_IPHONE) " + nl;
		arkh += "	#include \"" + self.ark_config['osx']['ark2d_dir'] + "/src/ARK.h\"" + nl;
		arkh += "#elif defined(ARK2D_UBUNTU_LINUX) " + nl;
		#if "linux" in config:
		arkh += "	#include \"" + self.ark_config['linux']['ark2d_dir'] + "/src/ARK.h\"" + nl;
		arkh += "#endif" + nl;
		"""

		#arkh = "#include <ARK.h>" + nl;
		arkh = "";

		f = open(floc, "w");
		f.write(arkh);
		f.close();

		pass;


	def createCacheFile(self, path):
		try:
			f = open(path, "r");
			f.close();
		except IOError as e:
			f = open(path, "w");
			f.write("{}");
			f.close();
		print("created cache file " + path);

	def openCacheFile(self, file):
		self.createCacheFile(file);
		f = open(file, "r")
		fcontents = f.read();
		f.close();
		fjson = json.loads(fcontents);
		print("opened cache file " + file);
		return fjson;

	def rmdir_recursive(self, dir):
	    """Remove a directory, and all its contents if it is not already empty."""
	    for name in os.listdir(dir):
	        full_name = os.path.join(dir, name);
	        # on Windows, if we don't have write permission we can't remove
	        # the file/directory either, so turn that on
	        if not os.access(full_name, os.W_OK):
	           # os.chmod(full_name, 0600);
	           pass;
	        if os.path.isdir(full_name):
	            self.rmdir_recursive(full_name);
	        else:
	            os.remove(full_name);
	    os.rmdir(dir);

	def startWindowsPhone(self):
		# open config
		f = open(self.ark2d_dir + "/config.json", "r");
		fcontents = f.read();
		f.close();
		self.config = json.loads(fcontents);

		if (self.building_library):
			print("Building Windows Phone dll.");

			# output directory
			output_folder = self.ark2d_dir + "/build/windows-phone";

			# make directories
			mkdirs = [];
			mkdirs.extend(self.mkdirs);
			util.makeDirectories(mkdirs);

			sln_contents = ""; ####
			vcxproj_contents = "";

			# dll sln and vcxproj files
			f1 = open(self.ark2d_dir + "/lib/windows-phone/dll-template/dll-template.sln", "r");
			f2 = open(self.ark2d_dir + "/lib/windows-phone/dll-template/dll-template.vcxproj", "r");
			sln_contents = f1.read();
			vcxproj_contents = f2.read();
			f1.close();
			f2.close();

			# modify sln/vcxproj files
			vcxproj_headerfiles = "";
			vcxproj_sourcefiles = "";
			for srcfile in self.src_files:

				if "lpng151" in srcfile:
					continue;

				#check if src file has a corresponding .h file. add that to the project...
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newfh = srcfile[0:findex] + ".h";
				newfhfull = self.ark2d_dir + self.ds + newfh;
				if (os.path.exists(newfhfull)):
					vcxproj_headerfiles += "<ClInclude Include=\"../../"+newfh+"\" /> \n";

				if "lpng1251" in srcfile:
					continue;
				if "zlib123" in srcfile:
					continue;

				if h_ext == "c":
					vcxproj_sourcefiles += "<ClCompile Include=\"../../"+srcfile+"\" > \n";
					vcxproj_sourcefiles += "<CompileAsWinRT Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">false</CompileAsWinRT>\n";
					vcxproj_sourcefiles += "<CompileAsWinRT Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">false</CompileAsWinRT>\n";
					vcxproj_sourcefiles += "<CompileAsWinRT Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">false</CompileAsWinRT>\n";
					vcxproj_sourcefiles += "<CompileAsWinRT Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">false</CompileAsWinRT>\n";

					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;ARK2D_WINDOWS_DLL;ARK2D_DEBUG;PSAPI_VERSION=2;WINAPI_FAMILY=WINAPI_FAMILY_PHONE_APP;_UITHREADCTXT_SUPPORT=0;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;ARK2D_WINDOWS_DLL;PSAPI_VERSION=2;WINAPI_FAMILY=WINAPI_FAMILY_PHONE_APP;_UITHREADCTXT_SUPPORT=0;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;ARK2D_WINDOWS_DLL;ARK2D_DEBUG;PSAPI_VERSION=2;WINAPI_FAMILY=WINAPI_FAMILY_PHONE_APP;_UITHREADCTXT_SUPPORT=0;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;ARK2D_WINDOWS_DLL;PSAPI_VERSION=2;WINAPI_FAMILY=WINAPI_FAMILY_PHONE_APP;_UITHREADCTXT_SUPPORT=0;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";

					#if "ogg130" in srcfile:
					#	continue;
					#if "vorbis132" in srcfile:
					#	continue;

					vcxproj_sourcefiles += "</ClCompile> \n";
				elif h_ext == "hlsl":
					hlsltype = "";
					if "pixel" in srcfile:
						hlsltype = "Pixel";
					elif "vertex" in srcfile:
						hlsltype = "Vertex";

					vcxproj_sourcefiles += "	<FxCompile Include=\"../../"+srcfile+"\"> \n ";
					vcxproj_sourcefiles += "		<FileType>Document</FileType> \n";
					vcxproj_sourcefiles += "		<DisableOptimizations Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">false</DisableOptimizations>\n"; # was true...
					vcxproj_sourcefiles += "		<DisableOptimizations Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">false</DisableOptimizations>\n";
					vcxproj_sourcefiles += "		<EnableDebuggingInformation Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">false</EnableDebuggingInformation>\n";
					vcxproj_sourcefiles += "		<EnableDebuggingInformation Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">false</EnableDebuggingInformation>\n";
					vcxproj_sourcefiles += "		<ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">" + hlsltype + "</ShaderType>\n";
					vcxproj_sourcefiles += "		<ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">" + hlsltype + "</ShaderType>\n";
					vcxproj_sourcefiles += "		<ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">" + hlsltype + "</ShaderType>\n";
					vcxproj_sourcefiles += "		<ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">" + hlsltype + "</ShaderType>\n";
					vcxproj_sourcefiles += "	</FxCompile> \n";

				elif h_ext == "cpp":
					vcxproj_sourcefiles += "<ClCompile Include=\"../../"+srcfile+"\" > \n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;ARK2D_WINDOWS_DLL;ARK2D_DEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;ARK2D_WINDOWS_DLL;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;ARK2D_WINDOWS_DLL;ARK2D_DEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;ARK2D_WINDOWS_DLL;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";

					vcxproj_sourcefiles += "</ClCompile> \n";


				else:
					vcxproj_sourcefiles += "<ClCompile Include=\"../../"+srcfile+"\" /> \n";



			vcxproj_contents = util.str_replace(vcxproj_contents, [("%COMPILE_HEADER_FILES%", vcxproj_headerfiles)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%COMPILE_SOURCE_FILES%", vcxproj_sourcefiles)]);

			# write sln file
			print("Write sln file...");
			f1 = open(output_folder + "/ARK2D.sln", "w");
			f1.write(sln_contents);
			f1.close();

			# write vcxproj file
			print("Write vcxproj file...");
			f1 = open(output_folder + "/ARK2D.vcxproj", "w");
			f1.write(vcxproj_contents);
			f1.close();

			# copy pch.h file/s
			print("Write pch.cpp file...");
			f1 = open(self.ark2d_dir + "/lib/windows-phone/dll-template/pch.cpp", "r");
			pch_cpp_contents = f1.read();
			f1.close();
			f1 = open(output_folder + "/pch.cpp", "w");
			f1.write(pch_cpp_contents);
			f1.close();

			# copy pch.h file/s
			print("Write pch.h file...");
			f1 = open(self.ark2d_dir + "/lib/windows-phone/dll-template/pch.h", "r");
			pch_h_contents = f1.read();
			f1.close();
			f1 = open(output_folder + "/pch.h", "w");
			f1.write(pch_h_contents);
			f1.close();

			# copy target versionh file/s
			print("Write targetver.h file...");
			f1 = open(self.ark2d_dir + "/lib/windows-phone/dll-template/targetver.h", "r");
			targetver_h_contents = f1.read();
			f1.close();
			f1 = open(output_folder + "/targetver.h", "w");
			f1.write(targetver_h_contents);
			f1.close();



		else:
			print("Building Windows Phone game.");

			# output directory
			output_folder = self.game_dir + "/build/" + self.output;
			game_name = self.game_name; #['game_name'];
			game_name_safe = self.game_name_safe; #config['game_name_safe'];
			game_short_name = self.game_class_name; #config['game_short_name'];
			game_description = self.game_description; #config['game_description'];
			game_resources_dir = self.game_resources_dir; #config['windows']['game_resources_dir'];


			# make directories
			print("Making directories...");
			mkdirs = [];
			mkdirs.extend(self.mkdirs);
			util.makeDirectories(mkdirs);

			sln_contents = "";
			vcxproj_contents = "";

			windowsPhone81 = True;
			projectTemplateFolder = "project-template";
			projectTemplateClassName = "WindowsPhone8Game";
			projectTemplateManifest = "WMAppManifest.xml";
			projectTemplateShortFolder = "wp8";
			if windowsPhone81 == True:
				projectTemplateFolder = "project-template-wp81";
				projectTemplateClassName = "WindowsPhone81Game";
				projectTemplateManifest = "Package.appxmanifest";
				projectTemplateShortFolder = "wp81";


			# dll sln and vcxproj files
			print("Making sln and vcxproj...");
			f1 = open(self.ark2d_dir + "/lib/windows-phone/" + projectTemplateFolder + "/" + projectTemplateFolder + ".sln", "r");
			f2 = open(self.ark2d_dir + "/lib/windows-phone/" + projectTemplateFolder + "/" + projectTemplateFolder + ".vcxproj", "r");
			sln_contents = f1.read();#.encode('ascii');
			vcxproj_contents = f2.read();
			f1.close();
			f2.close();

			# modify sln strings
			print("Configuring sln file...");
			sln_contents = util.str_replace(sln_contents, [("%GAME_SHORT_NAME%", game_short_name)]);
			sln_contents = util.str_replace(sln_contents, [("%GAME_NAME_SAFE%", game_name_safe)]);



			# resources to copy to game project. gotta do this early to generate the VS project
			print("sort game resources");
			game_resources_list = [];
			image_resources = [];
			audio_resources = [];
			document_resources = [];
			filesToCopy = util.listFiles(game_resources_dir, False);
			#print(filesToCopy);
			for file in filesToCopy:
				fromfile = game_resources_dir + self.ds + file;
				tofile = output_folder + "/data/" + file;

				game_resources_list.extend(["data\\" + file]);

				file_ext = util.get_str_extension(file);
				if (util.is_image_extension(file_ext)):
					image_resources.extend(["data\\" + file]);
				elif (util.is_audio_extension(file_ext)):
					# what do we do when it's an audio file idon't know?!
					pass;
				else:
					document_resources.extend(["data\\" + file]);


			# make list of dlls/libs
			extra_dlls_arm = [];
			extra_libs_arm = [];
			extra_dlls_x86 = [];
			extra_libs_x86 = [];

			if "native_libraries" in self.wp8_config:
				for native_lib in self.wp8_config['native_libraries']:
					print("Adding native library: " + native_lib['name']);
					if "arm" in native_lib:
						for native_lib_arm in native_lib['arm']:
							if (util.get_str_extension(native_lib_arm) == "dll"):
								extra_dlls_arm.extend([native_lib_arm]);
							elif (util.get_str_extension(native_lib_arm) == "lib"):
								extra_libs_arm.extend([native_lib_arm]);

					if "x86" in native_lib:
						for native_lib_x86 in native_lib['x86']:
							if (util.get_str_extension(native_lib_x86) == "dll"):
								extra_dlls_x86.extend([native_lib_x86]);
							elif (util.get_str_extension(native_lib_x86) == "lib"):
								extra_libs_x86.extend([native_lib_x86]);

			# print(extra_dlls_arm);
			# print(extra_libs_arm);

			# list of game resources in .data dir
			game_resources_str = "";
			game_image_resources_str = "";
			if len(game_resources_list) > 0:
				print("Generating resource list...");
				for item in game_resources_list:

					file_ext = util.get_str_extension(item);
					if (util.is_image_extension(file_ext)):
						game_image_resources_str += "<Image Include=\"" + item + "\" /> \n";
					else:
						game_resources_str += "<None Include=\"" + item + "\"> \n";
						game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">true</DeploymentContent> \n";
						game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">true</DeploymentContent> \n";
						game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">true</DeploymentContent> \n";
						game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">true</DeploymentContent> \n";
						game_resources_str += "</None> \n";

			# need to put dlls in here too.
			for nativelib in extra_dlls_arm:
				nativelib_name = util.get_str_filename2(nativelib);
				game_resources_str += "<None Include=\"" + nativelib_name + "\"> \n";
				game_resources_str += "	<FileType>Document</FileType> \n";
				game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">true</DeploymentContent> \n";
				game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">true</DeploymentContent> \n";
				game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">false</DeploymentContent> \n";
				game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">false</DeploymentContent> \n";
				game_resources_str += "</None> \n";

			for nativelib in extra_dlls_x86:
				nativelib_name = util.get_str_filename2(nativelib);
				game_resources_str += "<None Include=\"" + nativelib_name + "\"> \n";
				game_resources_str += "	<FileType>Document</FileType> \n";
				game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">false</DeploymentContent> \n";
				game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">false</DeploymentContent> \n";
				game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">true</DeploymentContent> \n";
				game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">true</DeploymentContent> \n";
				game_resources_str += "</None> \n";


			# list of sourcefiles
			print("Creating list of Source Files...");
			vcxproj_headerfiles = "";
			vcxproj_sourcefiles = "";
			for srcfile in self.src_files:

				#check if src file has a corresponding .h file. add that to the project...
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newfh = srcfile[0:findex] + ".h";
				newfhfull = self.ark2d_dir + self.ds + newfh;
				if (os.path.exists(newfhfull)):
					vcxproj_headerfiles += "<ClInclude Include=\"../../"+newfh+"\" /> \n";

				if h_ext == "c":
					vcxproj_sourcefiles += "<ClCompile Include=\"../../"+srcfile+"\" > \n";
					vcxproj_sourcefiles += "<CompileAsWinRT Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">false</CompileAsWinRT>\n";
					vcxproj_sourcefiles += "<CompileAsWinRT Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">false</CompileAsWinRT>\n";
					vcxproj_sourcefiles += "<CompileAsWinRT Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">false</CompileAsWinRT>\n";
					vcxproj_sourcefiles += "<CompileAsWinRT Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">false</CompileAsWinRT>\n";

					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;ARK2D_DEBUG;PSAPI_VERSION=2;WINAPI_FAMILY=WINAPI_FAMILY_PHONE_APP;_UITHREADCTXT_SUPPORT=0;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;PSAPI_VERSION=2;WINAPI_FAMILY=WINAPI_FAMILY_PHONE_APP;_UITHREADCTXT_SUPPORT=0;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;ARK2D_DEBUG;PSAPI_VERSION=2;WINAPI_FAMILY=WINAPI_FAMILY_PHONE_APP;_UITHREADCTXT_SUPPORT=0;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;PSAPI_VERSION=2;WINAPI_FAMILY=WINAPI_FAMILY_PHONE_APP;_UITHREADCTXT_SUPPORT=0;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";

					vcxproj_sourcefiles += "</ClCompile> \n";
				elif h_ext == "hlsl":
					hlsltype = "";
					if "pixel" in srcfile:
						hlsltype = "Pixel";
					elif "vertex" in srcfile:
						hlsltype = "Vertex";

					vcxproj_sourcefiles += "	<FxCompile Include=\"../../"+srcfile+"\"> \n ";
					vcxproj_sourcefiles += "		<FileType>Document</FileType> \n";
					vcxproj_sourcefiles += "		<DisableOptimizations Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">false</DisableOptimizations>\n"; # was true...
					vcxproj_sourcefiles += "		<DisableOptimizations Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">false</DisableOptimizations>\n";
					vcxproj_sourcefiles += "		<EnableDebuggingInformation Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">false</EnableDebuggingInformation>\n";
					vcxproj_sourcefiles += "		<EnableDebuggingInformation Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">false</EnableDebuggingInformation>\n";
					vcxproj_sourcefiles += "		<ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">" + hlsltype + "</ShaderType>\n";
					vcxproj_sourcefiles += "		<ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">" + hlsltype + "</ShaderType>\n";
					vcxproj_sourcefiles += "		<ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">" + hlsltype + "</ShaderType>\n";
					vcxproj_sourcefiles += "		<ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">" + hlsltype + "</ShaderType>\n";
					vcxproj_sourcefiles += "	</FxCompile> \n";

				elif h_ext == "cpp":
					vcxproj_sourcefiles += "<ClCompile Include=\"../../"+srcfile+"\" > \n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;ARK2D_DEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;ARK2D_DEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_PHONE_8;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";

					vcxproj_sourcefiles += "</ClCompile> \n";


				else:
					vcxproj_sourcefiles += "<ClCompile Include=\"../../"+srcfile+"\" /> \n";


			print("add libs")

			# extra include dirs
			vcxproj_AdditionalIncludeDirs = "";
			for includedir in self.include_dirs:
				includedir_actual = util.str_replace(includedir, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir), ("%ARK2D_DIR%", self.ark2d_dir)]);
				vcxproj_AdditionalIncludeDirs += includedir_actual + ";";

			# extra defines
			vcxproj_AdditionalPreprocessorDefinitions = "";
			for ppdefinition in self.preprocessor_definitions:
				vcxproj_AdditionalPreprocessorDefinitions += ppdefinition + ";";

			# additional lib files
			vcxproj_AdditionalX86DotLibs = "";
			for extra_lib in extra_libs_x86:
				extra_lib2 = util.str_replace(extra_lib, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir), ("%GAME_DIR%", self.game_dir), ("%ARK2D_DIR%", self.ark2d_dir)]);
				extra_lib2 = self.fixLocalPath(extra_lib2);
				vcxproj_AdditionalX86DotLibs += ";" + extra_lib2;

			vcxproj_AdditionalARMDotLibs = "";
			for extra_lib in extra_libs_arm:
				extra_lib2 = util.str_replace(extra_lib, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir), ("%GAME_DIR%", self.game_dir), ("%ARK2D_DIR%", self.ark2d_dir)]);
				extra_lib2 = self.fixLocalPath(extra_lib2);

				vcxproj_AdditionalARMDotLibs += ";" + extra_lib2;


			# modify vcxproj strings
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%GAME_SHORT_NAME%", game_short_name)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%GAME_NAME_SAFE%", game_name_safe)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%GAME_RESOURCES%", game_resources_str)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%GAME_IMAGE_RESOURCES%", game_image_resources_str)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%COMPILE_HEADER_FILES%", vcxproj_headerfiles)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%COMPILE_SOURCE_FILES%", vcxproj_sourcefiles)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ADDITIONAL_INCLUDE_DIRECTORIES%", vcxproj_AdditionalIncludeDirs)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ADDITIONAL_PREPROCESSOR_DEFINITIONS%", vcxproj_AdditionalPreprocessorDefinitions)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ADDITIONAL_DOTLIB_FILES_X86%", vcxproj_AdditionalX86DotLibs)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ADDITIONAL_DOTLIB_FILES_ARM%", vcxproj_AdditionalARMDotLibs)]);

			# write sln file
			print("Write sln file...");
			f1 = open(output_folder + "/" + game_name_safe + ".sln", "w");
			f1.write(sln_contents);
			f1.close();

			# write vcxproj file
			print("Write vcxproj file...");
			f1 = open(output_folder + "/" + game_name_safe + ".vcxproj", "w");
			f1.write(vcxproj_contents);
			f1.close();

			# copy pch.h file/s
			print("Write pch.cpp file...");
			f1 = open(self.ark2d_dir + "/lib/windows-phone/" + projectTemplateFolder + "/pch.cpp", "r");
			pch_cpp_contents = f1.read();
			f1.close();
			f1 = open(output_folder + "/pch.cpp", "w");
			f1.write(pch_cpp_contents);
			f1.close();

			# copy pch.h file/s
			print("Write pch.h file...");
			f1 = open(self.ark2d_dir + "/lib/windows-phone/" + projectTemplateFolder + "/pch.h", "r");
			pch_h_contents = f1.read();
			f1.close();
			f1 = open(output_folder + "/pch.h", "w");
			f1.write(pch_h_contents);
			f1.close();

			# icons
			wp8_iconTypes = [
				'square_44x44_scale100',
				'square_44x44_scale140',
				'square_44x44_scale240',
				'square_71x71_scale100',
				'square_71x71_scale140',
				'square_71x71_scale240',
				'square_150x150_scale100',
				'square_150x150_scale140',
				'square_150x150_scale240',
				'wide_310x150_scale100',
				'wide_310x150_scale140',
				'wide_310x150_scale240',
				'store_scale100',
				'store_scale140',
				'store_scale240',
				'badge_scale100',
				'badge_scale140',
				'badge_scale240',
				'splash_scale100',
				'splash_scale140',
				'splash_scale240'
			];
			wp8_iconTypeMap = {
				"square_44x44_scale100" : "SmallLogo.scale-100.png",
				"square_44x44_scale140" : "SmallLogo.scale-140.png",
				"square_44x44_scale240" : "SmallLogo.scale-240.png",
				"square_71x71_scale100" : "Square71x71Logo.scale-100.png",
				"square_71x71_scale140" : "Square71x71Logo.scale-140.png",
				"square_71x71_scale240" : "Square71x71Logo.scale-240.png",
				"square_150x150_scale100" : "Logo.scale-100.png",
				"square_150x150_scale140" : "Logo.scale-140.png",
				"square_150x150_scale240" : "Logo.scale-240.png",
				"wide_310x150_scale100" : "WideLogo.scale-100.png",
				"wide_310x150_scale140" : "WideLogo.scale-140.png",
				"wide_310x150_scale240" : "WideLogo.scale-240.png",
				"store_scale100" : "StoreLogo.scale-100.png",
				"store_scale140" : "StoreLogo.scale-140.png",
				"store_scale240" : "StoreLogo.scale-240.png",
				"badge_scale100" : "BadgeLogo.scale-100.png",
				"badge_scale140" : "BadgeLogo.scale-140.png",
				"badge_scale240" : "BadgeLogo.scale-240.png",
				"splash_scale100" : "SplashScreen.scale-100.png",
				"splash_scale140" : "SplashScreen.scale-140.png",
				"splash_scale240" : "SplashScreen.scale-240.png"
			};

			# manifest file
			print("Create " + projectTemplateManifest + " file...");
			f1 = open(self.ark2d_dir + "/lib/windows-phone/" + projectTemplateFolder + "/" + projectTemplateManifest, "r");
			pch_h_contents = f1.read();
			f1.close();

			pch_h_contents = util.str_replace(pch_h_contents, [("%GAME_NAME%", game_name)]);
			pch_h_contents = util.str_replace(pch_h_contents, [("%GAME_SHORT_NAME%", game_short_name)]);
			pch_h_contents = util.str_replace(pch_h_contents, [("%GAME_NAME_SAFE%", game_name_safe)]);
			pch_h_contents = util.str_replace(pch_h_contents, [("%GAME_DESCRIPTION%", game_description)]);
			pch_h_contents = util.str_replace(pch_h_contents, [("%COMPANY_NAME%", self.developer_name)]);
			pch_h_contents = util.str_replace(pch_h_contents, [("%COMPANY_NAME_SAFE%", self.developer_name_safe)]);
			pch_h_contents = util.str_replace(pch_h_contents, [("%GAME_ORIENTATION%", self.game_orientation)]);
			pch_h_contents = util.str_replace(pch_h_contents, [("%GAME_CLEAR_COLOR%", self.game_clear_color)]);





			f1 = open(output_folder + "/" + projectTemplateManifest, "w");
			f1.write(pch_h_contents);
			f1.close();

			# win8 game source file
			print("Create WP8 Game Class...");
			f1 = open(self.ark2d_dir + "/lib/windows-phone/" + projectTemplateFolder + "/" + projectTemplateClassName + ".cpp", "r");
			game_cpp_contents = f1.read();
			f1.close();

			game_cpp_contents = util.str_replace(game_cpp_contents, [("%GAME_NAME%", game_name)]);
			game_cpp_contents = util.str_replace(game_cpp_contents, [("%GAME_CLASS_NAME%", self.game_class_name)]);
			game_cpp_contents = util.str_replace(game_cpp_contents, [("%GAME_CLEAR_COLOR%", self.game_clear_color)]);
			game_cpp_contents = util.str_replace(game_cpp_contents, [("%GAME_WIDTH%", str(self.wp8_config['game_width']))]);
			game_cpp_contents = util.str_replace(game_cpp_contents, [("%GAME_HEIGHT%", str(self.wp8_config['game_height']))]);

			f1 = open(output_folder + "/" + projectTemplateClassName + ".cpp", "w");
			f1.write(game_cpp_contents);
			f1.close();

			# win8 game source file
			print("Create WP8 Game Header...");
			f1 = open(self.ark2d_dir + "/lib/windows-phone/" + projectTemplateFolder + "/" + projectTemplateClassName + ".h", "r");
			pch_h_contents = f1.read();
			f1.close();
			f1 = open(output_folder + "/" + projectTemplateClassName + ".h", "w");
			f1.write(pch_h_contents);
			f1.close();

			# copy resources in to wp8 game project folder.
			print("Copying data in...");
			shutil.copytree(game_resources_dir, output_folder + "/data/");

			# copy ark2d.dll in
			print("Copying ARK2D data in...");

			# WP8 Live tiles
			shutil.copytree(self.ark2d_dir + "\\lib\\windows-phone\\" + projectTemplateFolder + "\\" + projectTemplateShortFolder, output_folder + "/data/ark2d/" + projectTemplateShortFolder + "/");

				# custom icon / live tile
			if "icon" in self.wp8_config:
				for icontype in wp8_iconTypes:
					if icontype in self.wp8_config['icon']:
						icontype_full = self.wp8_config['icon'][icontype];
						icontype_filename = wp8_iconTypeMap[icontype]; #util.get_str_filename2(icontype_name);
						icontype_full = util.str_replace(icontype_full, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir), ("%GAME_DIR%", self.game_dir), ("%ARK2D_DIR%", self.ark2d_dir)]);
						shutil.copy(icontype_full, output_folder + "/data/ark2d/" + projectTemplateShortFolder + "/" + icontype_filename);

			# Shaders!
			mkdirs = [];
			mkdirs.extend([output_folder + "\\data\\ark2d\\shaders"]);
			mkdirs.extend([output_folder + "\\ARM"]);
			util.makeDirectories(mkdirs);
			shutil.copy(self.ark2d_dir + "\\build\\windows-phone\\ARM\\Debug\\ARK2D\\geometry-dx11-pixel.cso", output_folder + "/data/ark2d/shaders/geometry-dx11-pixel.cso");
			shutil.copy(self.ark2d_dir + "\\build\\windows-phone\\ARM\\Debug\\ARK2D\\geometry-dx11-vertex.cso", output_folder + "/data/ark2d/shaders/geometry-dx11-vertex.cso");
			shutil.copy(self.ark2d_dir + "\\build\\windows-phone\\ARM\\Debug\\ARK2D\\texture-dx11-pixel.cso", output_folder + "/data/ark2d/shaders/texture-dx11-pixel.cso");
			shutil.copy(self.ark2d_dir + "\\build\\windows-phone\\ARM\\Debug\\ARK2D\\texture-dx11-vertex.cso", output_folder + "/data/ark2d/shaders/texture-dx11-vertex.cso");

			# DLLs
			shutil.copy(self.ark2d_dir + "\\build\\windows-phone\\ARM\\Debug\\ARK2D\\ARK2D_arm.dll", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_arm.dll");
			shutil.copy(self.ark2d_dir + "\\build\\windows-phone\\ARM\\Debug\\ARK2D\\ARK2D_arm.lib", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_arm.lib");

			shutil.copy(self.ark2d_dir + "\\build\\windows-phone\\Debug\\ARK2D\\ARK2D_x86.dll", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_x86.dll");
			shutil.copy(self.ark2d_dir + "\\build\\windows-phone\\Debug\\ARK2D\\ARK2D_x86.lib", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_x86.lib");

			# Copy in additional DLLs.
			# for (extra_dll in extra_dlls_arm):
			#	shutil.copy(extra_dll, self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + );#extra_dll);

			# copy any other dll dependencies...
			for extradll in extra_dlls_arm:
				print(extradll);
				extradll_name = util.get_str_filename2(extradll);
				print(extradll_name);

				extradll2 = util.str_replace(extradll, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir), ("%GAME_DIR%", self.game_dir), ("%ARK2D_DIR%", self.ark2d_dir)]);
				extradll2 = self.fixLocalPath(extradll2);
				print(extradll2);

				shutil.copy(extradll2, self.game_dir + self.ds + self.build_folder + self.ds + self.output + self.ds + extradll_name);

			#for extradll in extra_dlls_x86:
			#	print(extradll);
			#	extradll_name = util.get_str_filename(extradll);
			#	shutil.copy(extradll, self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\X86\\" + extradll_name);


			print("One final header...");
			self.generateARKH(output_folder + "/ARK.h");

			print("Done!");

	def startWindowsStore(self):
		print("Building for Current Platform (" + self.platform + ")");

		if (self.building_library):
			self.doVSDllTemplate("windows-store");

			# copy pch.h file/s
			output_folder = self.ark2d_dir + "/build/windows-store";# + self.output;

			print("Write pch.cpp file (if no hash match)...");
			util.copyfileifdifferent(self.ark2d_dir + "/lib/windows-store/dll-template/pch.cpp", output_folder + "/pch.cpp");

			# copy pch.h file/s
			print("Write pch.h file...");
			util.copyfileifdifferent(self.ark2d_dir + "/lib/windows-store/dll-template/pch.h", output_folder + "/pch.h");

			# copy target versionh file/s
			print("Write targetver.h file...");
			util.copyfileifdifferent(self.ark2d_dir + "/lib/windows-store/dll-template/targetver.h", output_folder + "/targetver.h");

			if (self.compileproj == True):
				self.msbuildproj(self.ark2d_dir + "/build/windows-store/libARK2D.vcxproj");
				pass;

			pass;
		else:
			print("Universal Windows Program.");

			output_folder = self.game_dir + "/build/windows-store";

			print("Making directories...");
			mkdirs = [];
			mkdirs.extend(self.mkdirs);
			mkdirs.extend([output_folder + "/data/ark2d/shaders/basic-geometry"])
			mkdirs.extend([output_folder + "/data/ark2d/shaders/basic-texture"])
			util.makeDirectories(mkdirs);

			# dll sln and vcxproj files
			print("Making sln and vcxproj...");
			f1 = open(self.ark2d_dir + "/lib/windows-store/project-template/project-template.sln", "r");
			f2 = open(self.ark2d_dir + "/lib/windows-store/project-template/project-template.vcxproj", "r");
			sln_contents = f1.read();#.encode('ascii');
			vcxproj_contents = f2.read();
			f1.close();
			f2.close();

			# modify sln strings
			print("Configuring sln file...");
			sln_contents = util.str_replace(sln_contents, self.tag_replacements);
			vcxproj_contents = util.str_replace(vcxproj_contents, self.tag_replacements);

			# resources to copy to game project. gotta do this early to generate the VS project
			print("sort game resources");
			game_resources_list = [];
			image_resources = [];
			audio_resources = [];
			document_resources = [];
			filesToCopy = util.listFiles(self.game_resources_dir, False);
			#print(filesToCopy);
			for file in filesToCopy:
				fromfile = self.game_resources_dir + self.ds + file;
				tofile = output_folder + "/data/" + file;

				game_resources_list.extend(["data\\" + file]);

				file_ext = util.get_str_extension(file);
				if (util.is_image_extension(file_ext)):
					image_resources.extend(["data\\" + file]);
				elif (util.is_audio_extension(file_ext)):
					# what do we do when it's an audio file idon't know?!
					pass;
				else:
					document_resources.extend(["data\\" + file]);

			# list of game resources in .data dir
			game_resources_str = "";
			game_image_resources_str = "";
			if len(game_resources_list) > 0:
				print("Generating resource list...");
				for item in game_resources_list:

					file_ext = util.get_str_extension(item);
					if (util.is_image_extension(file_ext)):
						game_image_resources_str += "<Image Include=\"" + item + "\" /> \n";
					else:
						game_resources_str += "<None Include=\"" + item + "\"> \n";
						game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">true</DeploymentContent> \n";
						game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">true</DeploymentContent> \n";
						game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">true</DeploymentContent> \n";
						game_resources_str += "	<DeploymentContent Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">true</DeploymentContent> \n";
						game_resources_str += "</None> \n";

			# list of sourcefiles
			print("Creating list of Source Files...");
			vcxproj_headerfiles = "";
			vcxproj_sourcefiles = "";
			for srcfile in self.src_files:

				#check if src file has a corresponding .h file. add that to the project...
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newfh = srcfile[0:findex] + ".h";
				newfhfull = self.ark2d_dir + self.ds + newfh;
				if (os.path.exists(newfhfull)):
					vcxproj_headerfiles += "<ClInclude Include=\"../../"+newfh+"\" /> \n";

				if h_ext == "c":
					vcxproj_sourcefiles += "<ClCompile Include=\"../../"+srcfile+"\" > \n";
					vcxproj_sourcefiles += "<CompileAsWinRT Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">false</CompileAsWinRT>\n";
					vcxproj_sourcefiles += "<CompileAsWinRT Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">false</CompileAsWinRT>\n";
					vcxproj_sourcefiles += "<CompileAsWinRT Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">false</CompileAsWinRT>\n";
					vcxproj_sourcefiles += "<CompileAsWinRT Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">false</CompileAsWinRT>\n";

					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_STORE;ARK2D_DEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_STORE;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_STORE;ARK2D_DEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_STORE;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";

					vcxproj_sourcefiles += "</ClCompile> \n";
				elif h_ext == "hlsl":
					hlsltype = "";
					if "pixel" in srcfile:
						hlsltype = "Pixel";
					elif "vertex" in srcfile:
						hlsltype = "Vertex";

					vcxproj_sourcefiles += "	<FxCompile Include=\"../../"+srcfile+"\"> \n ";
					vcxproj_sourcefiles += "		<FileType>Document</FileType> \n";
					vcxproj_sourcefiles += "		<DisableOptimizations Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">false</DisableOptimizations>\n"; # was true...
					vcxproj_sourcefiles += "		<DisableOptimizations Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">false</DisableOptimizations>\n";
					vcxproj_sourcefiles += "		<EnableDebuggingInformation Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">false</EnableDebuggingInformation>\n";
					vcxproj_sourcefiles += "		<EnableDebuggingInformation Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">false</EnableDebuggingInformation>\n";
					vcxproj_sourcefiles += "		<ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">" + hlsltype + "</ShaderType>\n";
					vcxproj_sourcefiles += "		<ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">" + hlsltype + "</ShaderType>\n";
					vcxproj_sourcefiles += "		<ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">" + hlsltype + "</ShaderType>\n";
					vcxproj_sourcefiles += "		<ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">" + hlsltype + "</ShaderType>\n";
					vcxproj_sourcefiles += "	</FxCompile> \n";

				elif h_ext == "cpp":
					vcxproj_sourcefiles += "<ClCompile Include=\"../../"+srcfile+"\" > \n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_STORE;ARK2D_DEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_STORE;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_STORE;ARK2D_DEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";
					vcxproj_sourcefiles += "<PreprocessorDefinitions Condition=\"'$(Configuration)|$(Platform)'=='Release|ARM'\">_CRT_SECURE_NO_WARNINGS;ARK2D_WINDOWS_STORE;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n";

					vcxproj_sourcefiles += "</ClCompile> \n";


				else:
					vcxproj_sourcefiles += "<ClCompile Include=\"../../"+srcfile+"\" /> \n";

			vcxproj_AdditionalIncludeDirs = "";
			vcxproj_AdditionalPreprocessorDefinitions = "";
			vcxproj_AdditionalX86DotLibs = "";
			vcxproj_AdditionalARMDotLibs = "";

			# modify vcxproj strings
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%GAME_RESOURCES%", game_resources_str)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%GAME_IMAGE_RESOURCES%", game_image_resources_str)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%COMPILE_HEADER_FILES%", vcxproj_headerfiles)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%COMPILE_SOURCE_FILES%", vcxproj_sourcefiles)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ADDITIONAL_INCLUDE_DIRECTORIES%", vcxproj_AdditionalIncludeDirs)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ADDITIONAL_PREPROCESSOR_DEFINITIONS%", vcxproj_AdditionalPreprocessorDefinitions)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ADDITIONAL_DOTLIB_FILES_X86%", vcxproj_AdditionalX86DotLibs)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ADDITIONAL_DOTLIB_FILES_ARM%", vcxproj_AdditionalARMDotLibs)]);

			# write sln file
			print("Write sln file...");
			f1 = open(output_folder + "/" + self.game_name_safe + ".sln", "w");
			f1.write(sln_contents);
			f1.close();

			# write vcxproj file
			print("Write vcxproj file...");
			f1 = open(output_folder + "/" + self.game_name_safe + ".vcxproj", "w");
			f1.write(vcxproj_contents);
			f1.close();

			# copy pch.h file/s
			print("Write pch.cpp file...");
			f1 = open(self.ark2d_dir + "/lib/windows-store/project-template/pch.cpp", "r");
			pch_cpp_contents = f1.read();
			f1.close();
			f1 = open(output_folder + "/pch.cpp", "w");
			f1.write(pch_cpp_contents);
			f1.close();

			# copy pch.h file/s
			print("Write pch.h file...");
			f1 = open(self.ark2d_dir + "/lib/windows-store/project-template/pch.h", "r");
			pch_h_contents = f1.read();
			f1.close();
			f1 = open(output_folder + "/pch.h", "w");
			f1.write(pch_h_contents);
			f1.close();

			# manifest file
			print("Create Package.appxmanifest file...");
			f1 = open(self.ark2d_dir + "/lib/windows-store/project-template/Package.appxmanifest", "r");
			appxmanifest_contents = f1.read();
			f1.close();
			appxmanifest_contents = util.str_replace(appxmanifest_contents, self.tag_replacements);
			f1 = open(output_folder + "/Package.appxmanifest", "w");
			f1.write(appxmanifest_contents);
			f1.close();

			# win8 game source file
			print("Create UWP Game Class...");
			f1 = open(self.ark2d_dir + "/lib/windows-store/project-template/WindowsUWPGame.cpp", "r");
			game_cpp_contents = f1.read();
			f1.close();

			game_cpp_contents = util.str_replace(game_cpp_contents, self.tag_replacements);
			game_cpp_contents = util.str_replace(game_cpp_contents, [("%GAME_WIDTH%", str(self.target_config['windows-store']['game_width']))]);
			game_cpp_contents = util.str_replace(game_cpp_contents, [("%GAME_HEIGHT%", str(self.target_config['windows-store']['game_height']))]);

			f1 = open(output_folder + "/WindowsUWPGame.cpp", "w");
			f1.write(game_cpp_contents);
			f1.close();

			# win8 game source file
			print("Create UWP Game Header...");
			f1 = open(self.ark2d_dir + "/lib/windows-store/project-template/WindowsUWPGame.h", "r");
			game_h_contents = f1.read();
			f1.close();
			f1 = open(output_folder + "/WindowsUWPGame.h", "w");
			f1.write(game_h_contents);
			f1.close();

			# copy resources in to wp8 game project folder.
			print("Copying data in...");
			print(self.game_resources_dir);
			self.mycopytree(self.game_resources_dir, output_folder + "/data/");
			self.mycopytree(self.game_resources_dir, output_folder + "/Debug/" + self.game_name_safe + "/AppX/data"); ## disable this until it works
			self.mycopytree(self.game_resources_dir, output_folder + "/Release/"+ self.game_name_safe + "/AppX/data/");

			# copy ark2d.dll in
			print("Copying ARK2D data in...");
			self.mycopytree(self.ark2d_dir + "\\lib\\windows-store\\project-template\\uwp", output_folder + "/data/ark2d/uwp/");



			# Shaders!
			mkdirs = [];
			mkdirs.extend([output_folder + "\\data\\ark2d\\shaders"]);
			mkdirs.extend([output_folder + "\\ARM"]);
			mkdirs.extend([output_folder + "\\ARM\\Debug"]);
			mkdirs.extend([output_folder + "\\ARM\\Debug\\ARK2D"]);
			util.makeDirectories(mkdirs);
			shutil.copy(self.ark2d_dir + "\\build\\windows-store\\ARM\\Debug\\libARK2D\\geometry-dx11-pixel.cso", output_folder + "/data/ark2d/shaders/basic-geometry/geometry-dx11-pixel.cso");
			shutil.copy(self.ark2d_dir + "\\build\\windows-store\\ARM\\Debug\\libARK2D\\geometry-dx11-vertex.cso", output_folder + "/data/ark2d/shaders/basic-geometry/geometry-dx11-vertex.cso");
			shutil.copy(self.ark2d_dir + "\\build\\windows-store\\ARM\\Debug\\libARK2D\\texture-dx11-pixel.cso", output_folder + "/data/ark2d/shaders/basic-texture/texture-dx11-pixel.cso");
			shutil.copy(self.ark2d_dir + "\\build\\windows-store\\ARM\\Debug\\libARK2D\\texture-dx11-vertex.cso", output_folder + "/data/ark2d/shaders/basic-texture/texture-dx11-vertex.cso");

			# DLLs
			#shutil.copy(self.ark2d_dir + "\\build\\windows-store\\ARM\\Debug\\libARK2D\\ARK2D_arm_debug.dll", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_arm_debug.dll");
			#shutil.copy(self.ark2d_dir + "\\build\\windows-store\\ARM\\Debug\\libARK2D\\ARK2D_arm_debug.lib", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_arm_debug.lib");
			shutil.copy(self.ark2d_dir + "\\build\\windows-store\\ARM\\Release\\libARK2D\\ARK2D_arm.dll", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_arm.dll");
			shutil.copy(self.ark2d_dir + "\\build\\windows-store\\ARM\\Release\\libARK2D\\ARK2D_arm.lib", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_arm.lib");

			shutil.copy(self.ark2d_dir + "\\build\\windows-store\\Debug\\libARK2D\\ARK2D_x86_debug.dll", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_x86_debug.dll");
			shutil.copy(self.ark2d_dir + "\\build\\windows-store\\Debug\\libARK2D\\ARK2D_x86_debug.lib", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_x86_debug.lib");
			shutil.copy(self.ark2d_dir + "\\build\\windows-store\\Release\\libARK2D\\ARK2D_x86.dll", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_x86.dll");
			shutil.copy(self.ark2d_dir + "\\build\\windows-store\\Release\\libARK2D\\ARK2D_x86.lib", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_x86.lib");

			shutil.copy(self.ark2d_dir + "\\build\\windows-store\\x64\\Debug\\libARK2D\\ARK2D_x64_debug.dll", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_x64_debug.dll");
			shutil.copy(self.ark2d_dir + "\\build\\windows-store\\x64\\Debug\\libARK2D\\ARK2D_x64_debug.lib", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_x64_debug.lib");
			shutil.copy(self.ark2d_dir + "\\build\\windows-store\\x64\\Release\\libARK2D\\ARK2D_x64.dll", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_x64.dll");
			shutil.copy(self.ark2d_dir + "\\build\\windows-store\\x64\\Release\\libARK2D\\ARK2D_x64.lib", self.game_dir + "\\" + self.build_folder + self.ds + self.platform + self.ds + "ARK2D_x64.lib");


			#print("One final header...");
			#self.generateARKH(output_folder + "/ARK.h");

			pass;

		pass;
	def startXboxOne(self):
		print("Building for Current Platform (" + self.platform + ")");

		#if (self.building_library):
		if True:

			output_folder = self.ark2d_dir + "/build/xbone";

			# make directories
			mkdirs = [];
			mkdirs.extend(self.mkdirs);
			util.makeDirectories(mkdirs);

			sln_contents = ""; ####
			vcxproj_contents = "";

			# dll sln and vcxproj files
			f1 = open(self.ark2d_dir + "/lib/xbone/project-template/project-template.sln", "r");
			f2 = open(self.ark2d_dir + "/lib/xbone/project-template/project-template.vcxproj", "r");
			sln_contents = f1.read();
			vcxproj_contents = f2.read();
			f1.close();
			f2.close();

			# modify sln/vcxproj files
			vcxproj_headerfiles = "";
			vcxproj_sourcefiles = "";
			for srcfile in self.src_files:

				#check if src file has a corresponding .h file. add that to the project...
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newfh = srcfile[0:findex] + ".h";
				newfhfull = self.ark2d_dir + self.ds + newfh;
				if (os.path.exists(newfhfull)):
					vcxproj_headerfiles += "<ClInclude Include=\"../../"+newfh+"\" /> \n";

				if h_ext == "c" or h_ext == "cpp":
					vcxproj_sourcefiles += "<ClCompile Include=\"../../"+srcfile+"\" /> \n";


			game_name_safe = "libARK2D";

			sln_contents = util.str_replace(sln_contents, [("%GAME_SHORT_NAME%", game_name_safe)]);

			vcxproj_contents = util.str_replace(vcxproj_contents, [("%COMPILE_HEADER_FILES%", vcxproj_headerfiles)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%COMPILE_SOURCE_FILES%", vcxproj_sourcefiles)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ARK2D_DIR%", self.ark2d_dir)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%GAME_SHORT_NAME%", game_name_safe)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%GAME_RESOURCES%", "")]);
			#vcxproj_contents = util.str_replace(vcxproj_contents, [("%GAME_IMAGE_RESOURCES%", game_image_resources_str)]);
			#vcxproj_contents = util.str_replace(vcxproj_contents, [("%COMPILE_HEADER_FILES%", vcxproj_headerfiles)]);
			#vcxproj_contents = util.str_replace(vcxproj_contents, [("%COMPILE_SOURCE_FILES%", vcxproj_sourcefiles)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ADDITIONAL_PREPROCESSOR_DEFINITIONS%", "")]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ADDITIONAL_INCLUDE_DIRECTORIES%", "")]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ADDITIONAL_DOTLIB_FILES%", "")]);


			# write sln file
			print("Write sln file...");
			f1 = open(output_folder + "/libARK2D.sln", "w");
			f1.write(sln_contents);
			f1.close();

			# write vcxproj file
			print("Write vcxproj file...");
			f1 = open(output_folder + "/libARK2D.vcxproj", "w");
			f1.write(vcxproj_contents);
			f1.close();

	def doVSDllTemplate(self, folderName):
		# output directory
		output_folder = self.ark2d_dir + "/build/" + folderName;# + self.output;
		print("out folder: " + output_folder);

		# make directories
		mkdirs = [];
		mkdirs.extend(self.mkdirs);
		util.makeDirectories(mkdirs);

		sln_contents = ""; ####
		vcxproj_contents = "";

		# dll sln and vcxproj files
		print self.ark2d_dir;
		f1 = open(self.ark2d_dir + "/lib/"+folderName+"/dll-template/dll-template.sln", "rb");
		f2 = open(self.ark2d_dir + "/lib/"+folderName+"/dll-template/dll-template.vcxproj", "rb");
		sln_contents = f1.read();
		vcxproj_contents = f2.read();
		f1.close();
		f2.close();

		# modify sln/vcxproj files
		vcxproj_headerfiles = "";
		vcxproj_sourcefiles = "".encode('utf8');
		for srcfile in self.src_files:

			#check if src file has a corresponding .h file. add that to the project...
			findex = srcfile.rfind('.');
			h_ext = srcfile[findex+1:len(srcfile)];
			newfh = srcfile[0:findex] + ".h";
			newfhfull = self.ark2d_dir + self.ds + newfh;
			if (os.path.exists(newfhfull)):
				vcxproj_headerfiles += "<ClInclude Include=\"../../"+newfh+"\" /> \n";

			if h_ext == "cpp":
				vcxproj_sourcefiles += "<ClCompile Include=\"../../"+srcfile+"\" /> \n";
			elif h_ext == "c":
				vcxproj_sourcefiles += "<ClCompile Include=\"../../"+srcfile+"\" > \n";
				vcxproj_sourcefiles += "	<CompileAsWinRT>false</CompileAsWinRT>\n";
				vcxproj_sourcefiles += "</ClCompile> \n";
			elif h_ext == "hlsl":
				hlsltype = "";
				if "pixel" in srcfile:
					hlsltype = "Pixel";
				elif "vertex" in srcfile:
					hlsltype = "Vertex";

				vcxproj_sourcefiles += "	<FxCompile Include=\"../../"+srcfile+"\"> \n ";
				vcxproj_sourcefiles += "		<FileType>Document</FileType> \n";
				vcxproj_sourcefiles += "		<DisableOptimizations Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">true</DisableOptimizations>\n"; # was true...
				vcxproj_sourcefiles += "		<DisableOptimizations Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">true</DisableOptimizations>\n";
				vcxproj_sourcefiles += "		<DisableOptimizations Condition=\"'$(Configuration)|$(Platform)'=='Debug|x64'\">true</DisableOptimizations>\n";
				vcxproj_sourcefiles += "		<EnableDebuggingInformation Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">true</EnableDebuggingInformation>\n";
				vcxproj_sourcefiles += "		<EnableDebuggingInformation Condition=\"'$(Configuration)|$(Platform)'=='Debug|ARM'\">true</EnableDebuggingInformation>\n";
				vcxproj_sourcefiles += "		<EnableDebuggingInformation Condition=\"'$(Configuration)|$(Platform)'=='Debug|x64'\">true</EnableDebuggingInformation>\n";
				vcxproj_sourcefiles += "		<ShaderType>" + hlsltype + "</ShaderType>\n";
				vcxproj_sourcefiles += "	</FxCompile> \n";



		ark2d_dir_extra_slashes = util.str_replace(self.ark2d_dir, [("\\", "\\\\")]);

		vcxproj_contents = util.str_replace(vcxproj_contents, [("%COMPILE_HEADER_FILES%", vcxproj_headerfiles.encode('utf8'))]);
		vcxproj_contents = util.str_replace(vcxproj_contents, [("%COMPILE_SOURCE_FILES%", vcxproj_sourcefiles.encode('utf8'))]);
		vcxproj_contents = util.str_replace(vcxproj_contents, [("%ARK2D_DIR%", ark2d_dir_extra_slashes.encode('utf8'))]);

		# get existing file contents, hash them against these new ones.
		# only overwrite if they don't match!
		f1 = open(output_folder + "/libARK2D.sln", "a+");
		f1.seek(0);
		existing_sln_contents = f1.read(); f1.close();
		existing_sln_hash = hashlib.md5(existing_sln_contents).hexdigest();
		new_sln_hash = hashlib.md5(sln_contents).hexdigest();

		f1 = open(output_folder + "/libARK2D.vcxproj", "a+");
		f1.seek(0);
		existing_vcxproj_contents = f1.read(); f1.close();
		existing_vcxproj_hash = hashlib.md5(existing_vcxproj_contents).hexdigest();
		new_vcxproj_hash = hashlib.md5(vcxproj_contents).hexdigest();


		# write sln file
		if new_sln_hash != existing_sln_hash:
			print("Write sln file...");
			f1 = open(output_folder + "/libARK2D.sln", "w");
			f1.write(sln_contents);
			f1.close();
		else:
			print("Skipping .sln file generation as hashes match.");

		# write vcxproj file
		if new_vcxproj_hash != existing_vcxproj_hash:
			print("Write vcxproj file...");
			f1 = open(output_folder + "/libARK2D.vcxproj", "w");
			f1.write(vcxproj_contents);
			f1.close();
		else:
			print("Skipping .vcxproj file generation as hashes match.");

	def msbuildproj(self, vcxproj):
		print("Compiling VS project...");
		starttime = time.time();
		ret = 0;
		#ret = subprocess.call(["MSBuild.exe", vcxproj, "/p:Configuration=Debug", "/p:Platform=x86"], shell=True);
		#ret = subprocess.call(["MSBuild.exe", vcxproj, "/p:Configuration=Debug", "/p:Platform=x64"], shell=True);
		ret = subprocess.call(["MSBuild.exe", vcxproj, "/p:Configuration=Debug", "/p:Platform=ARM"], shell=True);
		if ret != 0:
			print("stopping");
			return;
		#ret = subprocess.call(["MSBuild.exe", vcxproj, "/p:Configuration=Release", "/p:Platform=x86"], shell=True);
		#ret = subprocess.call(["MSBuild.exe", vcxproj, "/p:Configuration=Release", "/p:Platform=x64"], shell=True);
		#ret = subprocess.call(["MSBuild.exe", vcxproj, "/p:Configuration=Release", "/p:Platform=ARM"], shell=True);
		endtime = time.time();
		print("compilation took " + str(endtime - starttime) + " seconds");
		pass;

	def startWindowsVS2(self):
		print("Building for Current Platform (" + self.platform + ")");
		print("ark2d dir: " + self.ark2d_dir);

		# open config
		#f = open(self.ark2d_dir + "/config.json", "r");
		#fcontents = f.read();
		#f.close();
		#self.config = json.loads(fcontents);

		if (self.building_library):
			print("Building Windows dll.");

			self.doVSDllTemplate("windows");

			if (self.compileproj == True):
				self.msbuildproj(self.ark2d_dir + "/build/windows/libARK2D.vcxproj");
				pass;

		else:
			# self.startWindowsVS();

			print("Building Windows Desktop game.");

			# output directory
			output_folder = self.game_dir + "/build/" + self.output;
			game_name = self.game_name; #config['game_name'];
			game_name_safe = self.game_name_safe; #config['game_name_safe'];
			#game_short_name = self.game_short_name; #config['game_short_name'];
			game_description = self.game_description; #config['game_description'];
			game_resources_dir = self.game_resources_dir; #config['windows']['game_resources_dir'];
			#game_name_safe
			#game_class_name

			# make directories
			print("Making directories...");
			mkdirs = [];
			mkdirs.extend(self.mkdirs);
			mkdirs.extend([output_folder + "/Debug"]);
			mkdirs.extend([output_folder + "/Release"]);
			#mkdirs.extend([output_folder + "/Debug/data/ark2d"]);
			#mkdirs.extend([output_folder + "/Release/data/ark2d"]);
			util.makeDirectories(mkdirs);

			# get list of .libs and .dlls
			extra_dlls = [];
			extra_libs = [];
			extra_dlls = self.addLibrariesToArray(extra_dlls, self.libs, "dll");
			extra_libs = self.addLibrariesToArray(extra_libs, self.libs, "lib");

			sln_contents = "";
			vcxproj_contents = "";

			# dll sln and vcxproj files
			print("Making sln and vcxproj...");
			f1 = open(self.ark2d_dir + "\\lib\\windows\\project-template\\project-template.sln", "r");
			f2 = open(self.ark2d_dir + "/lib/windows/project-template/project-template.vcxproj", "r");
			f3 = open(self.ark2d_dir + "/lib/windows/project-template/project-template.vcxproj.user", "r");
			sln_contents = f1.read();
			vcxproj_contents = f2.read();
			vcxprojuser_contents = f3.read();
			f1.close();
			f2.close();
			f3.close();

			# modify sln strings
			print("Configuring sln file...");
			sln_contents = util.str_replace(sln_contents, [("%GAME_SHORT_NAME%", game_name_safe)]);

			# make spritesheets
			print("Generating spritesheets...");
			self.generateSpriteSheets();

			# resources to copy to game project. gotta do this early to generate the VS project
			game_resources_list = [];
			image_resources = [];
			audio_resources = [];
			document_resources = [];
			filesToCopy = util.listFiles(game_resources_dir, False);
			#print(filesToCopy);
			for file in filesToCopy:
				fromfile = game_resources_dir + self.ds + file;
				tofile = output_folder + "/data/" + file;

				game_resources_list.extend(["data\\" + file]);

				file_ext = util.get_str_extension(file);
				if (util.is_image_extension(file_ext)):
					image_resources.extend(["data\\" + file]);
				elif (util.is_audio_extension(file_ext)):
					# what do we do when it's an audio file idon't know?!
					pass;
				else:
					document_resources.extend(["data\\" + file]);

			# list of sourcefiles
			print("Creating list of Source Files...");
			vcxproj_headerfiles = "";
			vcxproj_sourcefiles = "";
			vcxproj_resourcefiles = "";

			for srcfile in self.src_files:

				#check if src file has a corresponding .h file. add that to the project...
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newfh = srcfile[0:findex] + ".h";
				newfhfull = self.ark2d_dir + self.ds + newfh;
				if (os.path.exists(newfhfull)):
					vcxproj_headerfiles += "<ClInclude Include=\"../../"+newfh+"\" /> \n";

				if h_ext == "c":
					vcxproj_sourcefiles += "<ClCompile Include=\"../../"+srcfile+"\" /> \n";
				elif h_ext == "hlsl":
					hlsltype = "";
					if "pixel" in srcfile:
						hlsltype = "Pixel";
					elif "vertex" in srcfile:
						hlsltype = "Vertex";

					vcxproj_sourcefiles += "	<FxCompile Include=\"../../"+srcfile+"\"> \n ";
					vcxproj_sourcefiles += "		<FileType>Document</FileType> \n";
					vcxproj_sourcefiles += "		<DisableOptimizations Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">false</DisableOptimizations>\n"; # was true...
					vcxproj_sourcefiles += "		<EnableDebuggingInformation Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">false</EnableDebuggingInformation>\n";
					vcxproj_sourcefiles += "		<ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Debug|Win32'\">" + hlsltype + "</ShaderType>\n";
					vcxproj_sourcefiles += "		<ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Release|Win32'\">" + hlsltype + "</ShaderType>\n";
					vcxproj_sourcefiles += "	</FxCompile> \n";

				elif h_ext == "rc":
					vcxproj_resourcefiles += "	<ResourceCompile Include=\"../../"+srcfile+"\" />";
				else:
					vcxproj_sourcefiles += "<ClCompile Include=\"../../"+srcfile+"\" /> \n";


			# extra include dirs
			vcxproj_AdditionalIncludeDirs = "";
			#if "include_dirs" in config['windows']:
			for includedir in self.include_dirs: #config['windows']['include_dirs']:
				includedir_actual = util.str_replace(includedir, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir), ("%ARK2D_DIR%", self.ark2d_dir), ("%GAME_DIR%", self.game_dir)]);
				vcxproj_AdditionalIncludeDirs += includedir_actual + ";";

			vcxproj_AdditionalPreprocessorDefinitions = "";
			for ppdefinition in self.preprocessor_definitions:
				ppdefinition_actual = ppdefinition;
				vcxproj_AdditionalPreprocessorDefinitions += ppdefinition_actual + ";";

			# additional lib files
			vcxproj_AdditionalDotLibs = "";
			for extra_lib in extra_libs:
				vcxproj_AdditionalDotLibs += ";" + extra_lib;



			# modify vcxproj strings
			game_image_resources_str = "";
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ARK2D_DIR%", self.ark2d_dir)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%GAME_SHORT_NAME%", game_name_safe)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%GAME_RESOURCES%", vcxproj_resourcefiles)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%GAME_IMAGE_RESOURCES%", game_image_resources_str)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%COMPILE_HEADER_FILES%", vcxproj_headerfiles)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%COMPILE_SOURCE_FILES%", vcxproj_sourcefiles)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ADDITIONAL_PREPROCESSOR_DEFINITIONS%", vcxproj_AdditionalPreprocessorDefinitions)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ADDITIONAL_INCLUDE_DIRECTORIES%", vcxproj_AdditionalIncludeDirs)]);
			vcxproj_contents = util.str_replace(vcxproj_contents, [("%ADDITIONAL_DOTLIB_FILES%", vcxproj_AdditionalDotLibs)]);

			# write sln file
			print("Write sln file...");
			f1 = open(output_folder + "/" + game_name_safe + ".sln", "w");
			f1.write(sln_contents);
			f1.close();

			# write vcxproj file
			print("Write vcxproj file...");
			f1 = open(output_folder + "/" + game_name_safe + ".vcxproj", "w");
			f1.write(vcxproj_contents);
			f1.close();

			# write vcxproj.user file
			print("Write vcxproj.user file...");
			f1 = open(output_folder + "/" + game_name_safe + ".vcxproj.user", "w");
			f1.write(vcxprojuser_contents);
			f1.close();


			# copy resources in to wp8 game project folder.
			print("Copying ark2d data in...");
			shutil.copytree(self.ark2d_dir + "/data/", game_resources_dir + "/ark2d/");

			print("Copying data in...");
			#shutil.copytree(game_resources_dir, output_folder + "/Development/data");
			shutil.copytree(game_resources_dir, output_folder + "/Debug/data"); ## disable this until it works
			shutil.copytree(game_resources_dir, output_folder + "/Release/data/");



			# copy ark2d.dll in
			print("Copying ARK2D data in...");


			# DLLs
			shutil.copy(self.ark2d_dir + "\\build\\windows\\Debug\\libARK2D.dll", self.game_dir + "\\" + self.build_folder + self.ds + self.output + self.ds + "Debug\\libARK2D.dll");
			shutil.copy(self.ark2d_dir + "\\build\\windows\\Debug\\libARK2D.lib", self.game_dir + "\\" + self.build_folder + self.ds + self.output + self.ds + "Debug\\libARK2D.lib");

			#shutil.copy(self.ark2d_dir + "\\build\\windows\\Development\\libARK2D.dll", self.game_dir + "\\" + self.build_folder + self.ds + self.output + self.ds + "Development\\libARK2D.dll");
			#shutil.copy(self.ark2d_dir + "\\build\\windows\\Development\\libARK2D.lib", self.game_dir + "\\" + self.build_folder + self.ds + self.output + self.ds + "Development\\libARK2D.lib");

			shutil.copy(self.ark2d_dir + "\\build\\windows\\Release\\libARK2D.dll", self.game_dir + "\\" + self.build_folder + self.ds + self.output + self.ds + "Release\\libARK2D.dll");
			shutil.copy(self.ark2d_dir + "\\build\\windows\\Release\\libARK2D.lib", self.game_dir + "\\" + self.build_folder + self.ds + self.output + self.ds + "Release\\libARK2D.lib");

			# ARK Dependency DLLs
			# debug

			shutil.copy(self.ark2d_dir + "\\lib\\windows\\alut.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Debug\\alut.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\freetype6.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Debug\\freetype6.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\glew32.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Debug\\glew32.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\libcurl.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Debug\\curllib.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\wrap_oal.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Debug\\wrap_oal.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\zlib1.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Debug\\zlib1.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\OpenAL32.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Debug\\OpenAL32.dll");
			#shutil.copy(self.ark2d_dir + "\\lib\\windows\\vs2013\\x86\\msvcr120d.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Debug\\msvcr120d.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\vs2017\\x86\\msvcp140d.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Debug\\msvcp140d.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\vs2017\\x86\\vcruntime140d.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Debug\\vcruntime140d.dll");
			#shutil.copy(self.ark2d_dir + "\\lib\\windows\\vs2013\\x86\\msvcr120.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Debug\\msvcr120.dll");
			#shutil.copy(self.ark2d_dir + "\\lib\\windows\\vs2013\\x86\\msvcp120.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Debug\\msvcp120.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\angelscript\\angelscriptd.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Debug\\angelscriptd.dll");


			#development
			"""
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\alut.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Development\\alut.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\freetype6.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Development\\freetype6.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\glew32.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Development\\glew32.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\libcurl.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Development\\curllib.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\wrap_oal.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Development\\wrap_oal.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\zlib1.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Development\\zlib1.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\OpenAL32.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Development\\OpenAL32.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\vs2013\\x86\\msvcr120.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Development\\msvcr120.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\vs2013\\x86\\msvcp120.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Development\\msvcp120.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\angelscript\\angelscript.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Development\\angelscript.dll");
			"""

			#release
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\alut.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Release\\alut.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\freetype6.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Release\\freetype6.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\glew32.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Release\\glew32.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\libcurl.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Release\\curllib.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\wrap_oal.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Release\\wrap_oal.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\zlib1.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Release\\zlib1.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\OpenAL32.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Release\\OpenAL32.dll");
			#shutil.copy(self.ark2d_dir + "\\lib\\windows\\vs2013\\x86\\msvcr120.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Release\\msvcr120.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\vs2017\\x86\\msvcp140.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Release\\msvcp140.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\vs2017\\x86\\vcruntime140.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Release\\vcruntime140.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\angelscript\\angelscript.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Release\\angelscript.dll");

			# copy any other dll dependencies..
			print("Copying ARK2D data in... (extra dlls)");
			for extradll in extra_dlls:
				print(extradll);
				extradll_name = util.get_str_filename(extradll);
				# shutil.copy(extradll, self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Development\\" + extradll_name);
				shutil.copy(extradll, self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Debug\\" + extradll_name);
				shutil.copy(extradll, self.game_dir + self.ds + self.build_folder + self.ds + self.output + "\\Release\\" + extradll_name);


			print("One final header...");
			self.generateARKH(output_folder + "/ARK.h");

			print("Done!");

	"""
	def startWindowsVS(self):
		print("Building for Current Platform (" + self.platform + ")");

		# open config
		f = open(self.ark2d_dir + "/config.json", "r");
		fcontents = f.read();
		f.close();
		self.config = json.loads(fcontents);

		gyp_executable = self.config['windows']['gyp_executable'];



		if (self.building_library):

			print("making directories");
			flascc_folder = self.config['windows']['ark2d_dir'] + "/build/windows";
			mkdirs = [];
			mkdirs.extend(self.mkdirs);
			util.makeDirectories(mkdirs);

			#projectname ark2d
			projectname = "ark2d";

			# generate gyp file.
			print("creating gyp file");
			gypfilename = self.game_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + projectname + ".gyp";

			gypfile = {};
			#gypfile['variables'] = ["GYP_MSVS_VERSION"];
			gypfile['defines'] = ['ARK2D_WINDOWS', "ARK2D_WINDOWS_DLL",  "_WIN32"]; #'ARK2D_IPHONE'];

			gypfile['targets'] = [];

			gypfiletarget = {};
			gypfiletarget['target_name'] = "libARK2D";
			gypfiletarget['type'] = "shared_library";
			gypfiletarget['include_dirs'] = [
				'../../src/ARK2D/vendor/windows',
				'../../lib/windows/includes',
				'../../src/ARK2D/vendor/spine/includes'

				];
			gypfiletarget['sources'] = [];

			#gypfiletarget['sources'].extend([
			#	self.ark2d_dir + self.ds + "src\\ARK2D\\vendor\\glew-vs.c"
			#])

			for srcfile in self.config['src_files']['windows']:
				gypfiletarget['sources'].extend(["../../"+srcfile]);

				#check if src file has a corresponding .h file. add that to the project...
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newfh = srcfile[0:findex] + ".h";
				newfhfull = self.game_dir + self.ds + newfh;
				if (os.path.exists(newfhfull)):
					gypfiletarget['sources'].extend(["../../"+newfh]);

			for srcfile in self.config['src_files']['all']:
				gypfiletarget['sources'].extend(["../../"+srcfile]);

				#check if src file has a corresponding .h file. add that to the project...
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newfh = srcfile[0:findex] + ".h";
				newfhfull = self.game_dir + self.ds + newfh;
				if (os.path.exists(newfhfull)):
					gypfiletarget['sources'].extend(["../../"+newfh]);

			gypfiletarget['sources!'] = [];
			gypfiletarget['dependencies'] = [];
			gypfiletarget['conditions'] = [];
			gypfiletargetcondition = {};
			gypfiletargetcondition['defines'] = ['ARK2D_WINDOWS',  "ARK2D_WINDOWS_DLL",  '_WIN32']; #, 'CF_EXCLUDE_CSTD_HEADERS'];
			gypfiletargetcondition['sources'] = [];
			gypfiletargetcondition['sources!'] = [];
			gypfiletargetcondition['link_settings'] = {};
			gypfiletargetcondition['link_settings']['libraries'] = [

				#'/Developer/SDKs/MacOSX10.7.sdk/System/Library/Frameworks/IOKit.framework',

				#config['dynamic_libraries']['windows'] + "/lib/osx/freetype/libfreetype.a",
			#	config['osx']['ark2d_dir'] + "/lib/osx/libcurl.a"
			];

			#for dylib in self.config['dynamic_libraries']['windows']:
			#	gypfiletargetcondition['link_settings']['libraries'].extend( [self.config['windows']['ark2d_dir'] + self.ds + dylib] );

			gypfiletargetcondition['link_settings']['libraries'].extend( [
				self.config['windows']['ark2d_dir'] + self.ds + "lib\\windows\\alut.lib",
				self.config['windows']['ark2d_dir'] + self.ds + "lib\\windows\\OpenAL32.lib",
				self.config['windows']['ark2d_dir'] + self.ds + "lib\\windows\\freetype6.lib",
				self.config['windows']['ark2d_dir'] + self.ds + "lib\\windows\\zlib1.lib",
				#self.config['windows']['ark2d_dir'] + self.ds + "lib\\windows\\glew32s.lib",
				self.config['windows']['ark2d_dir'] + self.ds + "lib\\windows\\curl\\Debug\\curllib.lib",
				"opengl32.lib",
				"msvcrt.lib",
				"winmm.lib"

			] );


			#"glew32.lib"

			#'../../lib/iphone/libfreetype.a

			if (self.debug):
				gypfiletargetcondition['defines'].extend(['ARK2D_DEBUG']);

			gypfiletargetcondition['ldflags'] = [
				"-lbz2",
				"-lcurl",
				"-lz",
				#"-L" + self.ark2d_dir + "/lib/osx",
				#"-L/usr/lib"
			];

			gypfiletargetcondition['link_settings!'] = [];


			gypfiletargetcondition['include_dirs'] = []; # ['../../src/ARK2D/vendor/windows'];

			# TODO:
			# make it generate VS2013 projects... :/

			# GYP_MSVS_VERSION=2013
			# or
			# GYP_MSVS_VERSION=2013e

			# -G msvs_version=2013

			windcondition = [];
			windcondition.extend(["OS == 'win'"]);
			windcondition.extend([gypfiletargetcondition]);
			gypfiletarget['conditions'].extend([windcondition]);

			gypfile['targets'].extend([gypfiletarget]);

			print("saving gyp file: " + gypfilename);
			f = open(gypfilename, "w")
			f.write(json.dumps(gypfile, sort_keys=True, indent=4));
			f.close();


			#delete xcode project?
			try:
				print("deleting visual studio project");
				os.system("rmdir -r -d " + self.build_folder + self.ds + self.platform + self.ds);
			except:
				print("could not delete visual studio project");

			# run gyp file.
			os.environ["GYP_MSVS_VERSION"] = "2013";
			# os.system("python " + gyp_executable + ".bat " + gypfilename + " --depth=../../src");
			os.system(gyp_executable + ".bat  --depth=../../src " + gypfilename);

			#exit(0);

			# do a bit of hacking to put the ignored libs in there.
			# edit libARK2D.vcxproj	and replace </OutputFile> with more stuff.
			vsprojectfilename = self.build_folder + self.ds + self.platform + self.ds + "libARK2D.vcxproj";
			print("hack the vs2012 project: " + vsprojectfilename);
			vsf = open(vsprojectfilename, "r")
			vsprojectcontents = vsf.read();
			vsf.close();

			#set libs
			vsprojectcontents = util.str_replace(vsprojectcontents, [("</OutputFile>", "</OutputFile><IgnoreSpecificDefaultLibraries>libc.lib;libcmt.lib;libcd.lib;libcmtd.lib;msvcrtd.lib;%(IgnoreSpecificDefaultLibraries)</IgnoreSpecificDefaultLibraries>")]);

			# debug build?
			if (self.debug):
				vsprojectcontents = util.str_replace(vsprojectcontents, [("</PreprocessorDefinitions>", "</PreprocessorDefinitions><DebugInformationFormat>EditAndContinue</DebugInformationFormat><Optimization>Disabled</Optimization>")]);
				vsprojectcontents = util.str_replace(vsprojectcontents, [("</Link>", "<GenerateDebugInformation>true</GenerateDebugInformation> <AssemblyDebug>true</AssemblyDebug> <ImageHasSafeExceptionHandlers>false</ImageHasSafeExceptionHandlers></Link>")]);


			# set shaders as HLSL type
			vsprojectcontents = util.str_replace(vsprojectcontents, [("<None Include=\"..\..\src\ARK2D\Graphics\HLSL\geometry-dx11-pixel.hlsl\"/>", "<FxCompile Include=\"..\..\src\ARK2D\Graphics\HLSL\geometry-dx11-pixel.hlsl\"><FileType>Document</FileType><ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Default|Win32'\">Pixel</ShaderType></FxCompile>")]);
			vsprojectcontents = util.str_replace(vsprojectcontents, [("<None Include=\"..\..\src\ARK2D\Graphics\HLSL\geometry-dx11-vertex.hlsl\"/>", "<FxCompile Include=\"..\..\src\ARK2D\Graphics\HLSL\geometry-dx11-vertex.hlsl\"><FileType>Document</FileType><ShaderType Condition=\"'$(Configuration)|$(Platform)'=='Default|Win32'\">Vertex</ShaderType></FxCompile>")]);

			vsf = open(vsprojectfilename, "w")
			vsf.write(vsprojectcontents);
			vsf.close();


			print("done. now compile with the xcode project.");

			exit(0);

		else: #building game

			print("making directories");
			flascc_folder = self.config['windows']['ark2d_dir'] + "/build/windows";
			mkdirs = [];
			mkdirs.extend(self.mkdirs);
			util.makeDirectories(mkdirs);

			f = open(self.game_dir + "/config.json", "r");
			fcontents = f.read();
			f.close();
			config = json.loads(fcontents);

			#projectname ark2d
			projectnameunsafe = config['game_name'];
			projectname = config['game_short_name'];

			# generate gyp file.
			print("creating gyp file");
			gypfilename = self.game_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + projectname + ".gyp";

			#print(gypfilename);
			#exit(0);

			gypfile = {};
			gypfile['defines'] = ['ARK2D_WINDOWS', "_WIN32"]; #'ARK2D_IPHONE'];

			gypfile['targets'] = [];

			gypfiletarget = {};
			gypfiletarget['target_name'] = projectnameunsafe;
			gypfiletarget['type'] = "executable";
			gypfiletarget['include_dirs'] = [
				self.config['windows']['ark2d_dir'] + "\\src\\ARK2D",
				self.config['windows']['ark2d_dir'] + "\\src\\ARK2D\\vendor\\windows",
				self.config['windows']['ark2d_dir'] + "\\src\\ARK2D\\vendor\\spine\\includes",
				self.config['windows']['ark2d_dir'] + "\\lib\\windows\\includes"
			];
			gypfiletarget['sources'] = [];


			# custom include dirs
			if "include_dirs" in config['windows']:
				for includedir in config['windows']['include_dirs']:
					includedir_actual = util.str_replace(includedir, [("%PREPRODUCTION_DIR%", config['windows']['game_preproduction_dir']), ("%ARK2D_DIR%", config['windows']['ark2d_dir'])]);
					gypfiletarget['include_dirs'].extend([includedir_actual]);

			#gypfiletarget['sources'].extend([
			#	self.ark2d_dir + self.ds + "src\\ARK2D\\vendor\\glew-vs.c"
			#])

			for srcfile in config['game_src_files']:
				gypfiletarget['sources'].extend(["../../"+srcfile]);

				#check if src file has a corresponding .h file. add that to the project...
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newfh = srcfile[0:findex] + ".h";
				newfhfull = self.game_dir + self.ds + newfh;
				if (os.path.exists(newfhfull)):
					gypfiletarget['sources'].extend(["../../"+newfh]);

			#for srcfile in config['src_files']['all']:
			#	gypfiletarget['sources'].extend(["../../"+srcfile]);
#
				#check if src file has a corresponding .h file. add that to the project...
#				findex = srcfile.rfind('.');
#				h_ext = srcfile[findex+1:len(srcfile)];
#				newfh = srcfile[0:findex] + ".h";
#				newfhfull = self.game_dir + self.ds + newfh;
#				if (os.path.exists(newfhfull)):
#					gypfiletarget['sources'].extend(["../../"+newfh]);

			gypfiletarget['sources!'] = [];
			gypfiletarget['dependencies'] = [];
			gypfiletarget['conditions'] = [];
			gypfiletargetcondition = {};
			gypfiletargetcondition['defines'] = ['ARK2D_WINDOWS', '_WIN32']; #, 'CF_EXCLUDE_CSTD_HEADERS'];
			gypfiletargetcondition['sources'] = [];
			gypfiletargetcondition['sources!'] = [];
			gypfiletargetcondition['link_settings'] = {};
			gypfiletargetcondition['link_settings']['libraries'] = [

				#'/Developer/SDKs/MacOSX10.7.sdk/System/Library/Frameworks/IOKit.framework',

				#config['dynamic_libraries']['windows'] + "/lib/osx/freetype/libfreetype.a",
			#	config['osx']['ark2d_dir'] + "/lib/osx/libcurl.a"
			];

			#for dylib in self.config['dynamic_libraries']['windows']:
			#	gypfiletargetcondition['link_settings']['libraries'].extend( [self.config['windows']['ark2d_dir'] + self.ds + dylib] );

			gypfiletargetcondition['link_settings']['libraries'].extend( [
				self.config['windows']['ark2d_dir'] + self.ds + "build\\windows\\Release\\libARK2D.lib"


			] );
			#"glew32.lib"


			#'../../lib/iphone/libfreetype.a

			if (self.debug):
				gypfiletargetcondition['defines'].extend(['ARK2D_DEBUG']);

			gypfiletargetcondition['ldflags'] = [
				#"-lbz2",
				#"-lcurl",
				#"-lz",
				#"-L" + self.ark2d_dir + "/lib/osx",
				#"-L/usr/lib"
			];

			gypfiletargetcondition['link_settings!'] = [

	        ];
			gypfiletargetcondition['include_dirs'] = []; # ['../../src/ARK2D/vendor/windows'];



			windcondition = [];
			windcondition.extend(["OS == 'win'"]);
			windcondition.extend([gypfiletargetcondition]);
			gypfiletarget['conditions'].extend([windcondition]);

			gypfile['targets'].extend([gypfiletarget]);

			print("saving gyp file: " + gypfilename);
			f = open(gypfilename, "w")
			f.write(json.dumps(gypfile, sort_keys=True, indent=4));
			f.close();


			#delete xcode project?
			try:
				print("deleting visual studio project");
				os.system("rmdir -r -d " + self.build_folder + self.ds + self.platform + self.ds);
			except:
				print("could not delete visual studio project");

			# run gyp file.
			os.environ["GYP_MSVS_VERSION"] = "2013";
			# os.system("python " + gyp_executable + ".bat " + gypfilename + " --depth=../../src");
			os.system(gyp_executable + ".bat  --depth=../../src " + gypfilename);

			# modify the vs project a bit
			# do a bit of hacking to put the ignored libs in there.
			# edit libARK2D.vcxproj	and replace </OutputFile> with more stuff.


			vsprojectfilename = self.build_folder + self.ds + self.platform + self.ds + self.game_short_name + ".vcxproj";
			print("hack the vs2012 project: " + vsprojectfilename);
			vsf = open(vsprojectfilename, "r")
			vsprojectcontents = vsf.read();
			vsf.close();

			# hack the vs2013 project
			vsprojectcontents = util.str_replace(vsprojectcontents, [("</OutputFile>", "</OutputFile><SubSystem>Windows</SubSystem><EntryPointSymbol>main</EntryPointSymbol>")]);

			# debug build?
			if (self.debug):
				vsprojectcontents = util.str_replace(vsprojectcontents, [("</PreprocessorDefinitions>", "</PreprocessorDefinitions><DebugInformationFormat>EditAndContinue</DebugInformationFormat><Optimization>Disabled</Optimization>")]);
				vsprojectcontents = util.str_replace(vsprojectcontents, [("</Link>", "<GenerateDebugInformation>true</GenerateDebugInformation> <AssemblyDebug>true</AssemblyDebug> <ImageHasSafeExceptionHandlers>false</ImageHasSafeExceptionHandlers></Link>")]);

			#vsprojectcontents = util.str_replace(vsprojectcontents, [("<SubSystem>", "<SubSystem>Windows")]);
			vsf = open(vsprojectfilename, "w")
			vsf.write(vsprojectcontents);
			vsf.close();


			# do asset ting
			print("copying assets");
			self.generateSpriteSheets();

			if (self.game_resources_dir != ''):
				print("copying game resources in to project:");
				#cpy_game_res = 'copy "' + self.game_resources_dir.replace('\\\\','\\') + '" "' + self.game_dir.replace('\\\\','\\') + '\\' + self.build_folder + '\\' + self.platform + '\\"';
				#print(cpy_game_res);
				#subprocess.call([cpy_game_res], shell=True);
				thisgameresdir = self.game_resources_dir.replace('\\\\','\\');
				thisgameresdir2 = self.game_dir.replace('\\\\','\\') + '\\' + self.build_folder + '\\' + self.platform + '\\data';
				try:
					os.system("rmdir /S /Q " + thisgameresdir2);
					shutil.copytree(thisgameresdir, thisgameresdir2);
				except:
					print("could not copy resources [from:"+thisgameresdir+",to:"+thisgameresdir2);
					pass;

			print("copying dlls... ");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\alut.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.platform + "\\alut.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\freetype6.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.platform + "\\freetype6.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\glew32.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.platform + "\\glew32.dll");
			shutil.copy(self.ark2d_dir + "\\build\\windows\\Release\\libARK2D.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.platform + "\\libARK2D.dll");
			# shutil.copy(self.ark2d_dir + "\\lib\\windows\\curl\\Debug\\curllib.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.platform + "\\curllib.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\libcurl.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.platform + "\\curllib.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\wrap_oal.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.platform + "\\wrap_oal.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\zlib1.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.platform + "\\zlib1.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\OpenAL32.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.platform + "\\OpenAL32.dll");

			# visual studio 2013 dlls
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\vs2013\\x86\\msvcr120.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.platform + "\\msvcr120.dll");
			shutil.copy(self.ark2d_dir + "\\lib\\windows\\vs2013\\x86\\msvcp120.dll", self.game_dir + self.ds + self.build_folder + self.ds + self.platform + "\\msvcp120.dll");


			print("done. now compile with the visual studio project.");

			exit(0);



		print(gyp_executable);

		return;
	"""

	def startGeneric(self):
		print("Building for Current Platform (" + self.platform + ")");

		#prepare dirs
		print("---");
		print("Making Directories");
		util.makeDirectories(self.mkdirs);

		# make sure cache file exists

		# compile cache thing
		cachefilename = "";
		#if (self.building_game):
			#cachefilename += self.game_dir + self.ds;

		cachefilename += self.game_dir + self.ds + self.build_folder + self.ds + self.output + self.ds + "build-cache" + self.ds  + "compiled.json";

		print("---");
		print("Loading build cache file: " + cachefilename);

		self.createCacheFile(cachefilename);
		f = open(cachefilename, "r")
		fcontents = f.read();
		f.close();
		fjson = json.loads(fcontents);
		fchanged = False;

		# TODO: generate block
		#if (sys.platform == "win32"):


		print("Loaded build cache file: " + cachefilename);

		print("---");
		print("Compiling Source Files: ");
		#print(self.src_files);

		#if (self.platform == "windows"):
		#	if (not self.building_game):
				#self.src_files.extend([
				#	"src\\ARK2D\\vendor\\glew-mingw.c"
				#]);



		#compile
		for h in self.src_files:
			compileStr = "";

			findex = h.rfind('.');
			h_ext = h[findex+1:len(h)];
			newf = h[0:findex] + ".o";
			newfd = h[0:findex] + ".d";


			if h_ext == 'c':
				compileStr += self.gccCompiler;
			elif h_ext == 'cpp':
				compileStr += self.gppCompiler;
			elif h_ext == 'mm':
				compileStr += self.objcCompiler;
			elif h_ext == 'rc':
				compileStr += self.resourceCompiler;

			if (compileStr == "skip"):
				continue;

			if (not h in fjson or fjson[h]['date_modified'] < os.stat(self.game_dir + self.ds + h).st_mtime):

				processThisFile = True;

				print(h);

				compileStr += " " + self.compilerOptions;

				if (h_ext == 'c' or h_ext == 'cpp' or h_ext == 'mm'):
					"""compileStr += " -O3 -Wall -c -fmessage-length=0 ";
					if (sys.platform == "darwin"): #compiling on mac
						if not "vendor" in newf:
							compileStr += " -mmacosx-version-min=10.6 -DARK2D_MACINTOSH -DARK2D_DESKTOP -DMAC_OS_X_VERSION_MIN_REQUIRED=1060 -x objective-c++ -fembed-bitcode ";

							# warnings
							compileStr += " -Wall -Winit-self -Woverloaded-virtual -Wuninitialized  "; #  -Wold-style-cast -Wmissing-declarations

							#compileStr += "-I /usr/X11/include ";
							#compileStr += "-I /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.7.sdk/usr/include ";
							compileStr += "-I /usr/include ";
							compileStr += "-I " + self.ark2d_dir + "/lib/includes";
							#compileStr += "-I /Developer/SDKs/MacOSX10.7.sdk/usr/include ";
							#compileStr += "-I /Developer/SDKs/MacOSX10.7.sdk/usr/include/c++/4.2.1 ";
							#compileStr += "-I /Developer/SDKs/MacOSX10.6.sdk/System/Library/Frameworks/Foundation.framework/Headers ";
							#compileStr += "-I /Developer/SDKs/MacOSX10.6.sdk/System/Library/Frameworks/ApplicationServices.framework/Headers ";
							#compileStr += "-I /Developer/SDKs/MacOSX10.6.sdk/System/Library/Frameworks/Cocoa.framework/Headers ";
							#compileStr += "-I /Developer/SDKs/MacOSX10.6.sdk/System/Library/Frameworks/OpenAL.framework/Headers ";
							#compileStr += "-I /Developer/SDKs/MacOSX10.6.sdk/System/Library/Frameworks/OpenGL.framework/Headers ";
							#compileStr += " -framework Foundation -framework ApplicationServices -framework Cocoa -framework OpenGL -framework OpenAL  ";
							#compileStr += " -stdlib=libc++ ";


						#  compileStr += " -march=i386 ";
						# compileStr += " -march=i386 ";
						#-march=i386 "; # i386
						#-arch i386
						compileStr += " -o \"";
						compileStr += self.game_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + newf + "\" \"" + self.game_dir + self.ds + h + "\" ";
					elif (sys.platform == "win32"):
						#compileStr += " -o \"" + self.build_folder + self.ds + self.platform + self.ds + newf + "\" \"" + h + "\" ";
						#compileStr += " -Wno-strict-aliasing -Wno-unused-but-set-variable -fpermissive ";
						#compileStr += " -o " + self.game_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + newf + " " + self.game_dir + self.ds + h + " ";
						compileStr += "-DARK2D_WINDOWS ";
						compileStr += "-DARK2D_DESKTOP ";
						if self.debug:
							compileStr += " -DARK2D_DEBUG ";

						compileStr += " -o " + self.game_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + newf + " " + self.game_dir + self.ds + h + " ";
					else:
						compileStr += " -o " + self.game_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + newf + " " + self.game_dir + self.ds + h + " ";
					"""
					compileStr += " -o " + self.game_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + newf + " " + self.game_dir + self.ds + h + " ";
				"""elif h_ext == 'rc':
					if (sys.platform == "win32"):
						#compileStr += self.game_dir + self.ds + h + " " + self.game_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + newf + " ";
						compileStr += self.game_dir + self.ds + h + " " +  self.game_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + newf + " ";
					else:
						processThisFile = False;
				"""
				if (processThisFile):
					fjson[h] = {"date_modified": os.stat(self.game_dir + self.ds + h).st_mtime };

					#print(compileStr);
					#subprocess.call(["dir"], shell=True);
					#subprocess.call([compileStr], shell=True);

					# the above did not work on win7 64bit.
					r = os.system(compileStr);
					if (r != 0):
						exit(0);
					fchanged = True;

					f = open(self.game_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + "build-cache" + self.ds + "compiled.json", "w")
					f.write(json.dumps(fjson, sort_keys=True, indent=4));
					f.close();
			else :
				#print (h + " - not changed");
				pass;


		# update compile cache thing
		if (fchanged == True):
			f = open(self.game_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + "build-cache" + self.ds + "compiled.json", "w")
			f.write(json.dumps(fjson, sort_keys=True, indent=4));
			f.close();
		else:
			print("...nothing to compile!");

		#link
		#self.doLink();



	def doLink(self):

		print("---")
		print("Linking Binary");
		if (sys.platform=="win32"):

			# copy ark2d/build/windows in to tmpdir
			builddirsorc = self.game_dir + self.ds + self.build_folder + self.ds+ self.platform;
			builddirdest = self.ark2d_tmpdir;
			try:
				#os.system("rmdir /S " + builddirdest + self.ds + self.build_folder + self.ds + self.platform);
				os.system("rmdir /S /Q " + builddirdest );
				shutil.copytree(builddirsorc, builddirdest);
			except:
				print("could not copy sources [from:"+builddirsorc+",to:"+builddirdest);
				return;
				pass;

			linkingStr = "";
			linkingStr += self.gppCompiler + " " + self.mingw_link + " " + self.linkingFlags + " -o" + self.game_dir + self.ds + self.build_artifact + "";
			#linkingStr += self.gppCompiler + " " + self.mingw_link + " -o" + self.build_artifact + "";

			for h in self.src_files:
				findex = h.rfind('.');
				newf = h[0:findex] + ".o";
				#print(newf);
				h_ext = h[findex+1:len(h)];
				linkingStr += " " + self.ark2d_tmpdir + self.ds + newf;

			for f in self.dll_files:
				if (self.building_library):
					#linkingStr += " " + self.game_dir + self.ds + f;
					linkingStr += " " + f;
				else:
					linkingStr += " " + f;


			for f in self.static_libraries:
				linkingStr += " -l" + f;
				#pass;

			#print(linkingStr);

			#subprocess.call([linkingStr], shell=True);
			#print(len(linkingStr));
			#os.system(linkingStr);
			#subprocess.call([ linkingStr ], shell=True);

			editsStrReplace = [("\\", "\\")];
			linkingStrClean = util.str_replace(linkingStr, editsStrReplace);

			linkbat = self.game_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + "dolink.bat";
			f = open(linkbat, "w")
			f.write(linkingStrClean);
			f.close();

			subprocess.call([ linkbat ], shell=True);






			#copy game resources in to .build
			if(self.building_game):

				#copying dll in to project.
				dll = self.ark2d_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + 'libARK2D.dll'
				dlldest = self.game_dir.replace('\\\\','\\') + '\\' + self.build_folder + '\\' + self.platform;
				try:
					shutil.copy(dll, dlldest);
				except:
					print("could not copy " + dll + " into " + dlldest);
					pass;

				#copying other dlls in to project.
				try:
					otherdlls = ['alut.dll', 'freetype6.dll', 'glew32.dll', 'OpenAL32.dll', 'wrap_oal.dll', 'zlib1.dll', 'libcurl.dll'];
					for one in otherdlls:
						one = self.ark2d_dir + self.ds + 'lib' + self.ds + self.platform + self.ds + one;
						shutil.copy(one, self.game_dir.replace('\\\\','\\') + '\\' + self.build_folder + '\\' + self.platform);
				except:
					pass;

				#generate spritesheets
				self.generateSpriteSheets();

				if (self.game_resources_dir != ''):
					print("copying game resources in to project:");
					#cpy_game_res = 'copy "' + self.game_resources_dir.replace('\\\\','\\') + '" "' + self.game_dir.replace('\\\\','\\') + '\\' + self.build_folder + '\\' + self.platform + '\\"';
					#print(cpy_game_res);
					#subprocess.call([cpy_game_res], shell=True);
					thisgameresdir = self.game_resources_dir.replace('\\\\','\\');
					thisgameresdir2 = self.game_dir.replace('\\\\','\\') + '\\' + self.build_folder + '\\' + self.platform + '\\data';
					try:
						os.system("rmdir /S /Q " + thisgameresdir2);
						shutil.copytree(thisgameresdir, thisgameresdir2);
					except:
						print("could not copy resources [from:"+thisgameresdir+",to:"+thisgameresdir2);
						pass;


		elif(sys.platform=="darwin"):


			if (self.building_library):
				linkingStr = "";
				linkingStr += self.gppCompiler + " -L " + self.game_dir + self.ds + "lib/osx/freetype -L /Developer/SDKs/MacOSX10.6.sdk/usr/lib -framework OpenGL -framework OpenAL -framework Foundation -framework Cocoa -framework ApplicationServices -lobjc -install_name @executable_path/../Frameworks/libARK2D.dylib " + self.linkingFlags + "  -dynamiclib -o " + self.game_dir + self.ds + self.build_artifact;
				#linkingStr += " -march=i386 ";

				for h in self.src_files:
					findex = h. rfind('.');
					newf = h[0:findex] + ".o";
					linkingStr += " " + self.game_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + newf;

				for f in self.dll_files:
					linkingStr += " " + f;

				for f in self.static_libraries:
					linkingStr += " -l" + f;

				print(linkingStr);

				subprocess.call([linkingStr], shell=True);

			elif(self.building_game):

				# we need to make the dirs for the .app file.
				gn = self.game_name.replace(' ', '\ ');
				app_folder = self.game_dir + self.ds + self.build_folder + self.ds + gn + ".app";
				contents_folder = app_folder + self.ds + "Contents";
				frameworks_folder = app_folder + self.ds + "Contents" + self.ds + "Frameworks";
				resources_folder = app_folder + self.ds + "Contents" + self.ds + "Resources";
				subprocess.call(['mkdir ' + app_folder], shell=True);
				subprocess.call(['mkdir ' + contents_folder ], shell=True);
				subprocess.call(['mkdir ' + contents_folder + self.ds + "MacOS"], shell=True);
				subprocess.call(['mkdir ' + resources_folder], shell=True);
				subprocess.call(['mkdir ' + resources_folder + self.ds + "data"], shell=True);
				subprocess.call(['mkdir ' + frameworks_folder], shell=True);

				#copying dylib in to project.
				dylibsrc = self.ark2d_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + 'libARK2D.dylib'
				subprocess.call(['cp ' + dylibsrc + ' ' + frameworks_folder + self.ds + 'libARK2D.dylib'], shell=True);


				#copy ark2d resources in to .app
				print("---");
				print("Copying ARK2D resources in to project:");
				cpyark2dres = 'cp -r ' + self.ark2d_dir + self.ds + 'data ' + resources_folder + self.ds + 'data' + self.ds + 'ark2d';
				print(cpyark2dres);
				subprocess.call([cpyark2dres], shell=True);

				#generate game spritesheets
				self.generateSpriteSheets();

				#copy game resources in to .app
				if (self.game_resources_dir != ''):
					print("---");
					print("Copying game resources in to project:");
					gme_rs_dir = self.game_resources_dir.replace(' ', '\ ').replace('&', '\&');
					cpy_game_res = 'cp -r ' + gme_rs_dir + ' ' + resources_folder;
					print(cpy_game_res);
					subprocess.call([cpy_game_res], shell=True);


				#copy icns in to .app folder
				if (self.mac_game_icns != ''):
					subprocess.call(['cp ' + self.mac_game_icns.replace(' ', '\ ').replace('&', '\&') + ' ' + resources_folder + self.ds + gn +'.icns'], shell=True);
				else:
					subprocess.call(['cp ' + resources_folder + self.ds + 'ark2d' + self.ds + 'icon.icns ' + resources_folder + self.ds + gn +'.icns'], shell=True);

				print("---");
				print("Generating plist file");
				cr = "\r";
				infoplistcontents  = "";
				infoplistcontents += "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + cr;
				infoplistcontents += "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">" + cr;
				infoplistcontents += "<plist version=\"1.0\">" + cr;
				infoplistcontents += "	<dict>" + cr;
				infoplistcontents += "		<key>CFBundleDevelopmentRegion</key>" + cr;
				infoplistcontents += "		<string>English</string>" + cr;
				infoplistcontents += "		<key>CFBundleExecutable</key>" + cr;
				infoplistcontents += "		<string>" + self.game_name + "</string>" + cr;
				infoplistcontents += "		<key>CFBundleIdentifier</key>" + cr;
				infoplistcontents += "		<string>com.ark2d." + self.game_short_name + "</string>" + cr;
				infoplistcontents += "		<key>CFBundleGetInfoString</key>" + cr;
				infoplistcontents += "		<string>" + self.config['game_name'] + ". Copyright " + self.developer_name + ".</string>" + cr;
				#infoplistcontents += "		<key>NSHumanReadableCopyright</key>" + cr;
				#infoplistcontents += "		<string>Copyright YEAR Thoname</string>" + cr;
				infoplistcontents += "		<key>CFBundleIconFile</key>" + cr;
				infoplistcontents += "		<string>" + self.game_name + "</string>" + cr;
				infoplistcontents += "	</dict>" + cr;
				infoplistcontents += "</plist>" + cr;

				f = open(contents_folder.replace('\ ', ' ') + self.ds + "Info.plist", "w");
				f.write(infoplistcontents);
				f.close();

				self.build_artifact = app_folder + self.ds + "Contents" + self.ds + "MacOS" + self.ds + gn;

				print("---");
				print("Creating Executable");

				linkingStr = "";
				linkingStr += self.gppCompiler + " -o " + self.build_artifact + " ";
				for h in self.src_files:
					findex = h.rfind('.');
					newf = h[0:findex] + ".o";
					h_ext = h[findex+1:len(h)];
					if (h_ext != 'rc'):
						linkingStr += " " + self.game_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + newf;

				for f in self.dll_files:
					linkingStr += " " + f;

				for f in self.static_libraries:
					linkingStr += " -l" + f;

				print(linkingStr);
				subprocess.call([linkingStr], shell=True);

				# update library search path for executable.
				#updatePathStr = "install_name_tool -change libARK2D.dylib @executable_path/../Frameworks/libARK2D.dylib " + self.game_name;
				#subprocess.call([updatePathStr], shell=True);

				#-march=i386
				#-framework OpenAL

				print("---");
				print("Build Complete");
				print("---");



	def startMac(self):
		self.startWindows();

	def startFlascc(self):
		print("flascc build");

		# open config
		print("opening config");
		f = open(self.game_dir + "/config.json", "r");
		fcontents = f.read();
		f.close();
		config = json.loads(fcontents);

		print("assigning vars");
		ark2d_dir = config['osx']['ark2d_dir'];
		flascc_dir = "/Users/ashleygwinnell/crossbridge/sdk";
		flexsdk_dir = "/Users/ashleygwinnell/flex_sdk_4_6";
		gsl3d_dir = "/Users/ashleygwinnell/Dropbox/ark2d/ARK2D/lib/flascc/GLS3D";

		if (self.building_library):

			print("making directories");
			flascc_folder = config['osx']['ark2d_dir'] + "/build/flascc";
			mkdirs = [];
			mkdirs.extend(self.mkdirs);
			util.makeDirectories(mkdirs);

			print("sorting out cache thing")
			cacheJSON = self.openCache("compiled");
			cacheChanged = False;

			#subprocess.call(["cp -r " + config['osx']['ark2d_dir'] + "/lib/flascc/Makefile " + flascc_folder+"/Makefile"], shell=True);

			#flascc_dir = "~/flascc/sdk";
			#flexsdk_dir = "~/flex_sdk";




			#LOCAL_C_INCLUDES := /Users/ashleygwinnell/Dropbox/ark2d/ARK2D/src/ARK2D/vendor/libcurl;
			print("generating makefile");
			#-Werror
			makefileStr = "";
			makefileStr += """

ARK2D:=""" + ark2d_dir + """
FLASCC:=""" + flascc_dir + """
GLS3D:=""" + gsl3d_dir + """

BASE_CFLAGS:= -Wall -Wno-write-strings -Wno-trigraphs

build:
	echo "Compile for flascc!"

	echo "Now compile a SWC"

	# compiling ark2d src files...\r\n""";

			thissourcefiles = [];
			thissourcefiles.extend(config['src_files']['flascc']);
			thissourcefiles.extend(config['src_files']['all']);


			srcindex = 0;
			srccount = len(thissourcefiles);
			for srcfile in thissourcefiles:
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newf = srcfile[0:findex] + ".o";

				if (not srcfile in cacheJSON or cacheJSON[srcfile]['date_modified'] < os.stat(ark2d_dir + self.ds + srcfile).st_mtime):

					compiler = "g++";
					if (h_ext == "c"):
						compiler = "gcc";
					#makefileStr += "	@echo \"---\"\r\n";
					makefileStr += "	@echo " + str(srcindex+1) + " of " + str(srccount) + ": \""+ srcfile + " \"\r\n";
					makefileStr += "	@\"$(FLASCC)/usr/bin/" + compiler + "\" $(BASE_CFLAGS) -O4 -DARK2D_FLASCC ";
					makefileStr += "-I$(GLS3D)/install/usr/include ";
					makefileStr += "-I$(ARK2D)/src/ARK2D/vendor/libcurl ";
					makefileStr += "-I$(ARK2D)/src/ARK2D/vendor/android/freetype/jni/include "
					makefileStr += "-I$(ARK2D)/src/ARK2D/vendor/spine/includes "
					makefileStr += "$(ARK2D)/" + srcfile + " ";
					makefileStr += "-c -o $(ARK2D)/build/flascc/" + newf + "";
					makefileStr += "\r\n";

					cacheJSON[srcfile] = {"date_modified": os.stat(ark2d_dir + self.ds + srcfile).st_mtime };
					cacheChanged = True;

				else:
					#print("skipping. no changes in this file. ");
					pass;

				srcindex += 1;
				pass;


			"""
			makefileStr += "	# linking (swc)...\r\n";
			linkingStr = "	@\"$(FLASCC)/usr/bin/g++\" $(BASE_CFLAGS) -O4 -DARK2D_FLASCC -o $(ARK2D)/build/flascc/libark2d.a ";
			for srcfile in thissourcefiles:
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newf = srcfile[0:findex] + ".o";
				linkingStr += " $(ARK2D)/build/flascc/" + newf + " ";
				pass;

			#linkingStr += " --enable-static --disable-shared ";
			linkingStr += " --disable-static --enable-shared -dynamiclib ";
			linkingStr += " -L$(GLS3D)/install/usr/lib/ -L$(ARK2D)/lib/flascc/install/usr/lib/";
			linkingStr += " -lGL -lfreetype ";
			#linkingStr += " -emit-swc=org.ashleygwinnell.ark2d  ";
			makefileStr += linkingStr;
			"""

			staticlibStr = "";
			staticlibStr += "	$(FLASCC)/usr/bin/ar cr $(ARK2D)/build/flascc/libark2d.a ";
			for srcfile in thissourcefiles:
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newf = srcfile[0:findex] + ".o";
				staticlibStr += " $(ARK2D)/build/flascc/" + newf + " ";
				pass;
			makefileStr += staticlibStr;
			#
			#	makefileStr += "/Users/ashleygwinnell/Dropbox/ark2d/ARK2D/" + srcfile + " \\";
			#	makefileStr += "\r\n";


			makefileStr += """ \


clean:
	#rm -f *.swf *.swc *.bc *.exe

""";

			f = open(flascc_folder+"/Makefile", "w");
			f.write(makefileStr);
			f.close();

			makeCmd = "make --directory=/Users/ashleygwinnell/Dropbox/ark2d/ARK2D/build/ -f /Users/ashleygwinnell/Dropbox/ark2d/ARK2D/build/flascc/Makefile";
			print("running makefile");
			print(makeCmd);
			subprocess.call([makeCmd], shell=True);

			# update compile cache thing
			print("saving cache file");
			if (cacheChanged == True):
				self.saveCache("compiled", cacheJSON);
			else:
				print("...nothing to compile!");

			pass;
		elif (self.building_game):
			print("----------");
			print("building game ");
			print("----------");

			game_dir = config['osx']['game_dir'];
			game_resources_dir = config['osx']['game_resources_dir'];
			flascc_folder = game_dir + "/build/flascc";

			print("----------");
			print("making directories");
			print("----------");
			mkdirs = [];
			mkdirs.extend(self.mkdirs);
			mkdirs.extend([ flascc_folder+"/gamevfs" ]);
			mkdirs.extend([ flascc_folder+"/data" ]);
			mkdirs.extend([ flascc_folder+"/data/ark2d" ]);
			mkdirs.extend([ flascc_folder+"/data/ark2d/fonts" ]);
			#mkdirs.extend([ flascc_folder+"/gamevfs/compiled" ]);
			util.makeDirectories(mkdirs);

			directoriesToCreate = util.listDirectories(game_resources_dir, False);
			for dir in directoriesToCreate:
				util.makeDirectories([game_dir + "/build/flascc/data/" + dir]);

			moreDirectoriesToCreate = util.listDirectories(game_dir+"/src", False);
			for dir in moreDirectoriesToCreate:
				util.makeDirectories([game_dir + "/build/flascc/src/" + dir]);

			print("----------");
			print("copying Preloader and Console files");
			print("----------");
			subprocess.call(["cp -r " + ark2d_dir + "/lib/flascc/PreLoader.as " + game_dir + "/build/flascc/PreLoader.as"], shell=True);
			subprocess.call(["cp -r " + ark2d_dir + "/lib/flascc/Console.as " + game_dir + "/build/flascc/Console.as"], shell=True);

			print("----------");
			print("copying Flascc .C file glue");
			print("----------");
			subprocess.call(["cp -r " + ark2d_dir + "/lib/flascc/flascc.cpp " + game_dir + "/src/flascc.cpp"], shell=True);

			#print("copying game files to build dir");
			#subprocess.call(["cp -r " + game_dir + "/data/ " + game_dir + "/build/flascc/data"], shell=True);

			print("----------");
			print("Creating/opening assets cache file...");
			print("----------");
			assetsCache = flascc_folder + "/build-cache/assets.json";
			assetsJson = self.openCacheFile(assetsCache);
			assetsChanged = False;

			#print("make mp3s and replace the oggs...");
			#game_resources_dir = game_dir + "/data";
			print("----------");
			print("Cool, now copying (game) files");
			print("----------");
			filesToCopy = util.listFiles(game_resources_dir, False);
			print(filesToCopy);
			for file in filesToCopy:
				fromfile = game_resources_dir + self.ds + file;
				tofile = game_dir + "/build/flascc/data/" + file;

				#replace spaces in paths on max osx with slash-spaces
				#fromfile = fromfile.replace(" ", "\ ");
				#tofile = tofile.replace(" ", "\ ");

				if (not fromfile in assetsJson or assetsJson[fromfile]['date_modified'] < os.stat(fromfile).st_mtime):
					file_ext = util.get_str_extension(file);
					if (file_ext == "ogg"): # resample
						print("resampling audio file from: " + fromfile + " to: " + tofile);
						#% cat inputfile | lame [options] - - > output
						subprocess.call(["oggdec "+fromfile+" --quiet --output=- | lame --quiet -h - - > "+tofile+""], shell=True);
					elif (file_ext == "wav"): # resample
						print("resampling audio file from: " + fromfile + " to: " + tofile);
						#% cat inputfile | lame [options] - - > output
						subprocess.call(["lame -V3 --quiet " +fromfile+ " "+tofile+""], shell=True);
					else: # standard copy
						print("copying file from: " + fromfile + " to: " + tofile);
						subprocess.call(["cp -r " + fromfile + " " + tofile], shell=True);

					assetsJson[fromfile] = {"date_modified": os.stat(fromfile).st_mtime };
					assetsChanged = True;

			if (assetsChanged == True):
				f = open(assetsCache, "w")
				f.write(json.dumps(assetsJson, sort_keys=True, indent=4));
				f.close();


			print("----------");
			print("Cool, now copy in ARK2D files...");
			subprocess.call(["cp -r " + ark2d_dir + "/data/ " + game_dir + "/build/flascc/data/ark2d"], shell=True);

			print("----------");
			print("generating index.html");
			game_width = config['flascc']['game_width'];
			game_height = config['flascc']['game_height'];
			indexpagestr = "";
			editsStrReplace = [("%GAME_NAME%", config['game_name']), ("%GAME_DESCRIPTION%", config['game_description']), ("%GAME_WIDTH%", str(game_width)), ("%GAME_HEIGHT%", str(game_height)), ("%COMPANY_NAME%", self.developer_name) ];
			f = open(ark2d_dir+"/lib/flascc/index.html", "r");
			indexpagestr = f.read();
			f.close();
			indexpagestr = util.str_replace(indexpagestr, editsStrReplace);
			f = open(flascc_folder+"/index.html", "w");
			f.write(indexpagestr);
			f.close();

			print("----------");
			print("generating makefile");
			print("----------");
			makefileStr = "";
			makefileStr += """

ARK2D:=""" + ark2d_dir + """
GAMEDIR:=""" + game_dir + """
FLASCC:=""" + flascc_dir + """
GLS3D:=""" + gsl3d_dir + """

BASE_CFLAGS:= -Wall -Wno-write-strings -Wno-trigraphs

build:
	@echo "----------"
	@echo "Compile for flascc!"
	@echo "----------"
	@echo "Generate Virtual FileSystem"
	$(FLASCC)/usr/bin/genfs --type=embed --name=gamevfs $(GAMEDIR)/build/flascc/data/ $(GAMEDIR)/build/flascc/gamevfs/gamevfs
	@echo "----------"
	@echo "Compile Virtual FileSystem"
	java -Xmx2g -jar $(FLASCC)/usr/lib/asc2.jar -merge -md -AS3 -strict -optimize \
		-import $(FLASCC)/usr/lib/builtin.abc \
		-import $(FLASCC)/usr/lib/playerglobal.abc \
		-import $(FLASCC)/usr/lib/BinaryData.abc \
		-import $(FLASCC)/usr/lib/ISpecialFile.abc \
		-import $(FLASCC)/usr/lib/IBackingStore.aBC \
		-import $(FLASCC)/usr/lib/IVFS.abc \
		-import $(FLASCC)/usr/lib/InMemoryBackingStore.abc \
		-import $(FLASCC)/usr/lib/PlayerKernel.abc \
		$(GAMEDIR)/build/flascc/gamevfs/gamevfs*.as -outdir $(GAMEDIR)/build/flascc/ -out gamevfs

	@echo "----------"
	@echo "Compile Console and Preloader"
	java -jar $(FLASCC)/usr/lib/asc2.jar -merge -md -AS3 -strict -optimize \
		-import $(FLASCC)/usr/lib/builtin.abc \
		-import $(FLASCC)/usr/lib/playerglobal.abc \
		-import $(GLS3D)/install/usr/lib/libGL.abc \
		-import $(FLASCC)/usr/lib/ISpecialFile.abc \
		-import $(FLASCC)/usr/lib/IBackingStore.abc \
		-import $(FLASCC)/usr/lib/IVFS.abc \
		-import $(FLASCC)/usr/lib/InMemoryBackingStore.abc \
		-import $(FLASCC)/usr/lib/AlcVFSZip.abc \
		-import $(FLASCC)/usr/lib/CModule.abc \
		-import $(FLASCC)/usr/lib/C_Run.abc \
		-import $(FLASCC)/usr/lib/BinaryData.abc \
		-import $(FLASCC)/usr/lib/PlayerKernel.abc \
		-import $(GAMEDIR)/build/flascc/gamevfs.abc \
		$(FLASCC)/usr/share/LSOBackingStore.as $(GAMEDIR)/build/flascc/Console.as -outdir $(GAMEDIR)/build/flascc -out Console

	java -jar $(FLASCC)/usr/lib/asc2.jar -merge -md -AS3 -strict -optimize \
		-import $(FLASCC)/usr/lib/builtin.abc \
		-import $(FLASCC)/usr/lib/playerglobal.abc \
		-import $(GLS3D)/install/usr/lib/libGL.abc \
		-import $(FLASCC)/usr/lib/ISpecialFile.abc \
		-import $(FLASCC)/usr/lib/IBackingStore.abc \
		-import $(FLASCC)/usr/lib/IVFS.abc \
		-import $(FLASCC)/usr/lib/CModule.abc \
		-import $(FLASCC)/usr/lib/C_Run.abc \
		-import $(FLASCC)/usr/lib/BinaryData.abc \
		-import $(FLASCC)/usr/lib/PlayerKernel.abc \
		-import $(GAMEDIR)/build/flascc/Console.abc \
		-import $(GAMEDIR)/build/flascc/gamevfs.abc \
		$(GAMEDIR)/build/flascc/PreLoader.as -swf com.adobe.flascc.preloader.PreLoader,"""+str(game_width)+""","""+str(game_height)+""",60 -outdir $(GAMEDIR)/build/flascc -out PreLoader

	@echo "----------"
""";

			thissourcefiles = [];
			thissourcefiles.extend(config['game_src_files']);
			thissourcefiles.extend([ "src/flascc.cpp" ]);

			srcindex = 0;
			srccount = len(thissourcefiles);
			for srcfile in thissourcefiles:
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newf = srcfile[0:findex] + ".o";

				compiler = "g++";
				if (h_ext == "c"):
					compiler = "gcc";
				elif (h_ext == "rc"):
					continue;

				makefileStr += "	@echo " + str(srcindex+1) + " of " + str(srccount) + ": \""+ srcfile + " \"\r\n";
				makefileStr += "	@\"$(FLASCC)/usr/bin/" + compiler + "\" $(BASE_CFLAGS) -O4 -DARK2D_FLASCC ";
				makefileStr += "-I$(GLS3D)/install/usr/include ";
				makefileStr += "-I$(ARK2D)/src/ARK2D/vendor/libcurl ";
				makefileStr += "-I$(ARK2D)/src/ARK2D/vendor/android/freetype/jni/include  "
				makefileStr += "-I$(ARK2D)/src/ARK2D/vendor/spine/includes "
				makefileStr += "$(GAMEDIR)/" + srcfile + " ";
				makefileStr += "-c -o $(GAMEDIR)/build/flascc/" + newf;
				makefileStr += "\r\n";

				srcindex += 1;
				pass;

			makefileStr += "	# linking...\r\n";
			linkingStr = "";
			#linkingStr += "\"" + flexsdk_dir + "/bin/mxmlc\" -static-link-runtime-shared-libraries -compiler.omit-trace-statements=false -library-path=MurmurHash.swc -debug=false swcdemo.as -o swcdemo.swf
			linkingStr += "	@\"$(FLASCC)/usr/bin/g++\" $(BASE_CFLAGS) -O4 -DARK2D_FLASCC ";
			for srcfile in thissourcefiles:
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newf = srcfile[0:findex] + ".o";

				if (h_ext == "rc"):
					continue;

				linkingStr += " $(GAMEDIR)/build/flascc/" + newf + " ";
				pass;


			print("opening config");
			f2 = open(self.ark2d_dir + "/config.json", "r");
			f2contents = f2.read();
			f2.close();
			arkconfig = json.loads(f2contents);
			arksrcfiles = []
			arksrcfiles.extend(arkconfig['src_files']['flascc']);
			arksrcfiles.extend(arkconfig['src_files']['all']);
			for srcfile in arksrcfiles:
				findex = srcfile.rfind('.');
				h_ext = srcfile[findex+1:len(srcfile)];
				newf = srcfile[0:findex] + ".o";
				if ("src/main" in srcfile[0:findex]):
					continue;
				else:
					linkingStr += " $(ARK2D)/build/flascc/" + newf + " ";
				pass;



			linkingStr += " -L$(GLS3D)/install/usr/lib/ ";
			linkingStr += " -L/Users/ashleygwinnell/Dropbox/ark2d/ARK2D/lib/flascc/install/usr/lib/ ";
			#linkingStr += " -L$(ARK2D)/build/flascc ";
			#linkingStr += " -lark2d ";
			linkingStr += " -lGL -lfreetype -lAS3++ -lFlash++ ";
			#linkingStr += " -lcurl ";
			linkingStr += " -pthread ";
			#-emit-swf=org.ashleygwinnell.defaultgame



			linkingStr += " $(FLASCC)/usr/lib/AlcVFSZip.abc $(GAMEDIR)/build/flascc/gamevfs.abc -swf-preloader=$(GAMEDIR)/build/flascc/PreLoader.swf -swf-version=18 -symbol-abc=$(GAMEDIR)/build/flascc/Console.abc -jvmopt=-Xmx4G ";
			linkingStr += " -swf-size="+str(game_width)+"x"+str(game_height)+" -emit-swf -o $(GAMEDIR)/build/flascc/game.swf -j4 ";
			makefileStr += linkingStr;


			f = open(flascc_folder+"/Makefile", "w");
			f.write(makefileStr);
			f.close();

			makeCmd = "make --directory=" + game_dir + "/build/ -f " + game_dir + "/build/flascc/Makefile";
			print("----------");
			print("running makefile");
			print("----------");
			print(makeCmd);
			subprocess.call([makeCmd], shell=True);

			print("----------");
			print("DONE! >:D");
			print("----------");

			pass;

		pass;

	def startUbuntuLinux(self):

		print("-------------------------");
		print("Linux");
		root_dir = "";
		if self.building_library:
			root_dir = self.config['linux']['ark2d_dir'];
		else:
			root_dir = self.game_dir;

		print("-------------------------");
		print("Make directories...")
		mkdirs = [];
		mkdirs.extend(self.mkdirs);

		if self.building_game:
			self.generateARKH(root_dir + "/src/ARK.h");

			mkdirs.extend([root_dir + "/build/" + self.output + "/data"]);
			mkdirs.extend([root_dir + "/build/" + self.output + "/data/ark2d"]);
			mkdirs.extend([root_dir + "/data/ark2d"]);

			directoriesToCreate = util.listDirectories(root_dir + "/src/", False);
			for dir in directoriesToCreate:
				util.makeDirectories([root_dir + "/build/" + self.output + "/src/" + dir]);


		util.makeDirectories(mkdirs);

		# Do we want to do the SDL build?
		useSDL2 = True;

		print("-------------------------");
		print("Loading build cache...")
		cacheJSON = self.openCache("compiled");
		cacheChanged = False;

		print("-------------------------");
		print("Compiling Source Files...");
		print("-------------------------");
		for srcFile in self.src_files:

			srcFileIndex = srcFile.rfind('.');
			srcFileExtension = srcFile[srcFileIndex+1:len(srcFile)];
			srcFileNew = srcFile[0:srcFileIndex] + ".o";

			compileStr = "";
			if srcFileExtension == 'c':
				compileStr += self.gccCompiler;
			elif srcFileExtension == 'cpp':
				compileStr += self.gppCompiler;
			elif srcFileExtension == 'rc':
				continue;

			compileStr += " -DARK2D_UBUNTU_LINUX ";
			compileStr += " -DARK2D_DESKTOP ";
			compileStr += " -DGL_GLEXT_PROTOTYPES ";

			if (useSDL2):
				compileStr += " -DARK2D_SDL2 ";

			compileStr += " -Wno-trigraphs -Wno-deprecated-declarations -Wreturn-type -fexceptions -fno-builtin-exit ";
			if self.building_library:
				compileStr += " -fPIC ";

			if srcFileExtension == 'c':
				compileStr += " -Wno-implicit-function-declaration  -Wno-implicit ";
			elif srcFileExtension == "cpp":
				compileStr += " -fpermissive ";

			compileStr += " -c ";
			if ("vendor" not in srcFile):
				compileStr += " -O3 ";

			compileStr += " -I /usr/include ";
			compileStr += " -I " + self.ark2d_dir + "/src/ARK2D/vendor/angelscript ";
			compileStr += " -I " + self.ark2d_dir + "/src/ARK2D/vendor/iphone ";
			compileStr += " -I " + self.ark2d_dir + "/src/ARK2D/vendor/spine/includes ";
			compileStr += " -I " + self.ark2d_dir + "/lib/ubuntu-linux/include ";
			compileStr += " -I " + self.ark2d_dir + "/src/ ";
			if (useSDL2):
				compileStr += " -I " + self.ark2d_dir + "/src/ ";


			if self.building_game:

				for includedir in self.include_dirs:
					includedir_actual = util.str_replace(includedir, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir), ("%ARK2D_DIR%", self.ark2d_dir), ("%GAME_DIR%", self.game_dir)]);
					compileStr += " -I " + includedir_actual + " ";


			compileStr += " -o \"" + root_dir + self.ds + self.build_folder + self.ds + self.output + self.ds + srcFileNew + "\"  \"" + srcFile + "\" ";
			compileStr += " -lrt ";

			if (not srcFile in cacheJSON or cacheJSON[srcFile]['date_modified'] < os.stat(srcFile).st_mtime):
				cacheJSON[srcFile] = {"date_modified": os.stat(srcFile).st_mtime };
				cacheChanged = True;

				print("Compiling " + srcFileNew);
				#print(compileStr);
				os.system(compileStr);

		if (cacheChanged == True):
			self.saveCache("compiled", cacheJSON);

		if (self.building_library):
			print("-------------------------");
			print("Creating Shared Object");
			linkStr = "";
			linkStr += "gcc -shared -o " + self.ark2d_dir + self.ds + "build/linux/libark2d.so ";
			for srcFile in self.src_files:
				srcFileIndex = srcFile.rfind('.');
				srcFileExtension = srcFile[srcFileIndex+1:len(srcFile)];
				srcFileNew = srcFile[0:srcFileIndex] + ".o";

				linkStr += self.ark2d_dir + "/" + self.build_folder + "/" + self.platform + "/" + srcFileNew + " ";
			linkStr += self.ark2d_dir + "/lib/ubuntu-linux/libangelscript.a ";

			print(linkStr);
			os.system(linkStr);
		elif (self.building_game):

			print("-------------------------");
			print("Copying Libraries ");
			os.system("cp " + self.ark2d_dir + "/build/linux/libark2d.so " + root_dir + "/build/" + self.output + "/libark2d.so");
			for libhere in self.libs:
				print("Copying " + libhere);
				os.system("cp " + libhere + " " + root_dir + "/build/" + self.output + "/ ");

			#if "libs" in self.config['linux']:
			#	for libhere in self.config['linux']['libs']:
			#		libhere_actual = util.str_replace(libhere, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir]), ("%ARK2D_DIR%", self.ark2d_dir])]);
			#		print("Copying " + libhere_actual);
			#		os.system("cp " + libhere_actual + " " + root_dir + "/build/" + self.output + "/ ");

			print("-------------------------");
			print("Creating Executable");
			executableStr = "";
			executableStr += "gcc -o " + root_dir + self.ds + "build/" + self.output + "/game ";
			for srcFile in self.src_files:
				srcFileIndex = srcFile.rfind('.');
				srcFileExtension = srcFile[srcFileIndex+1:len(srcFile)];
				srcFileNew = srcFile[0:srcFileIndex] + ".o";

				if srcFileExtension == 'rc':
					continue;

				executableStr += root_dir + "/" + self.build_folder + "/" + self.output + "/" + srcFileNew + " ";

			executableStr += " -L" + root_dir + "/" + self.build_folder + "/" + self.output + " ";
			executableStr += " -lark2d -lstdc++ ";
			executableStr += " -lm -lGL -lalut -lcurl -lGLU -lgcc ";
			if (useSDL2):
				executableStr += " -lSDL2 ";
			else:
				executableStr += " -lXinerama ";


			#if "libs" in self.config['linux']:
			#	for libhere in self.config['linux']['libs']:
			#		libhere_actual = util.str_replace(libhere, [("%PREPRODUCTION_DIR%", config['linux']['game_preproduction_dir']), ("%ARK2D_DIR%", config['linux']['ark2d_dir'])]);
			#		libhere_actual2 = libhere_actual[libhere_actual.rfind("/")+4:libhere_actual.rfind(".")];
			#		executableStr += " -l" + libhere_actual2 + " ";
			for libhere in self.libs:
				libhere_name = libhere[libhere.rfind("/")+4:libhere.rfind(".")];
				print(libhere_name);
				if (libhere_name.find(".") == -1):
					executableStr += " -l" + libhere_name + " ";

			#executableStr += " -Wl,-Bstatic -langelscript ";#" -Wl,-Bdynamic  ";


			print(executableStr);
			os.system(executableStr);

			print("-------------------------");
			print("Copying ARK2D Data Files ");
			os.system("cp -r " + self.ark2d_dir + "/data/* " + root_dir + "/data/ark2d ");
			os.system("cp -r " + self.ark2d_dir + "/lib/ubuntu-linux/libalut.so " + root_dir + "/build/" + self.output + "/libalut.so ");
			os.system("cp -r " + self.ark2d_dir + "/lib/ubuntu-linux/libalut.so.0 " + root_dir + "/build/" + self.output + "/libalut.so.0 ");
			os.system("cp -r " + self.ark2d_dir + "/lib/ubuntu-linux/libalut.so.0.1.0 " + root_dir + "/build/" + self.output + "/libalut.so.0.1.0 ");
			os.system("cp -r " + self.ark2d_dir + "/lib/ubuntu-linux/libopenal.so " + root_dir + "/build/" + self.output + "/libopenal.so ");
			os.system("cp -r " + self.ark2d_dir + "/lib/ubuntu-linux/libopenal.so.1 " + root_dir + "/build/" + self.output + "/libopenal.so.1 ");
			os.system("cp -r " + self.ark2d_dir + "/lib/ubuntu-linux/libopenal.so.1.14.0 " + root_dir + "/build/" + self.output + "/libopenal.so.1.14.0 ");
			if (useSDL2):
				os.system("cp -r " + self.ark2d_dir + "/lib/ubuntu-linux/libSDL2.so " + root_dir + "/build/" + self.output + "/libSDL2.so ");
				os.system("cp -r " + self.ark2d_dir + "/lib/ubuntu-linux/libSDL2-2.0.so " + root_dir + "/build/" + self.output + "/libSDL2-2.0.so");
				os.system("cp -r " + self.ark2d_dir + "/lib/ubuntu-linux/libSDL2-2.0.so.0 " + root_dir + "/build/" + self.output + "/libSDL2-2.0.so.0 ");
				os.system("cp -r " + self.ark2d_dir + "/lib/ubuntu-linux/libSDL2-2.0.so.0.2.0 " + root_dir + "/build/" + self.output + "/libSDL2-2.0.so.0.2.0 ");

				os.system("cp -r /usr/lib/x86_64-linux-gnu/libXss.so " + root_dir + "/build/" + self.output + "/libXss.so ");
				os.system("cp -r /usr/lib/x86_64-linux-gnu/libXss.so.1 " + root_dir + "/build/" + self.output + "/libXss.so.1 ");
				os.system("cp -r /usr/lib/x86_64-linux-gnu/libXss.so.1.0.0 " + root_dir + "/build/" + self.output + "/libXss.so.1.0.0 ");

				os.system("cp -r /usr/lib/x86_64-linux-gnu/libwayland-egl.so " + root_dir + "/build/" + self.output + "/libwayland-egl.so ");
				os.system("cp -r /usr/lib/x86_64-linux-gnu/libwayland-egl.so.1 " + root_dir + "/build/" + self.output + "/libwayland-egl.so.1 ");
				os.system("cp -r /usr/lib/x86_64-linux-gnu/libwayland-egl.so.1.0.0 " + root_dir + "/build/" + self.output + "/libwayland-egl.so.1.0.0 ");

				os.system("cp -r /usr/lib/x86_64-linux-gnu/libwayland-client.so " + root_dir + "/build/" + self.output + "/libwayland-client.so ");
				os.system("cp -r /usr/lib/x86_64-linux-gnu/libwayland-client.so.0 " + root_dir + "/build/" + self.output + "/libwayland-client.so.0 ");
				os.system("cp -r /usr/lib/x86_64-linux-gnu/libwayland-client.so.0.2.0 " + root_dir + "/build/" + self.output + "/libwayland-client.so.0.2.0 ");

				os.system("cp -r /usr/lib/x86_64-linux-gnu/libwayland-cursor.so " + root_dir + "/build/" + self.output + "/libwayland-cursor.so ");
				os.system("cp -r /usr/lib/x86_64-linux-gnu/libwayland-cursor.so.0 " + root_dir + "/build/" + self.output + "/libwayland-cursor.so.0 ");
				os.system("cp -r /usr/lib/x86_64-linux-gnu/libwayland-cursor.so.0.0.0 " + root_dir + "/build/" + self.output + "/libwayland-cursor.so.0.0.0 ");

				os.system("cp -r /usr/lib/x86_64-linux-gnu/libxkbcommon.so " + root_dir + "/build/" + self.output + "/libxkbcommon.so ");
				os.system("cp -r /usr/lib/x86_64-linux-gnu/libxkbcommon.so.0 " + root_dir + "/build/" + self.output + "/libxkbcommon.so.0 ");
				os.system("cp -r /usr/lib/x86_64-linux-gnu/libxkbcommon.so.0.0.0 " + root_dir + "/build/" + self.output + "/libxkbcommon.so.0.0.0 ");

				os.system("cp -r /usr/lib/x86_64-linux-gnu/libffi.so " + root_dir + "/build/" + self.output + "/libffi.so ");
				os.system("cp -r /usr/lib/x86_64-linux-gnu/libffi.so.6 " + root_dir + "/build/" + self.output + "/libffi.so.6 ");
				os.system("cp -r /usr/lib/x86_64-linux-gnu/libffi.so.6.0.1 " + root_dir + "/build/" + self.output + "/libffi.so.6.0.1 ");

				#os.system("cp -r " + self.ark2d_dir + "/lib/ubuntu-linux/libangelscript_s.so " + root_dir + "/build/" + self.output + "/libangelscript_s.so ");

			print("-------------------------");
			print("Copying Game Data Files ");
			os.system("cp -r " + root_dir + "/data/* " + root_dir + "/build/" + self.output + "/data ");


			print("-------------------------");
			print("Generating run.sh");
			run_sh = "";
			run_sh += "#/bin/sh \n";
			run_sh += "export LD_LIBRARY_PATH=.:$LD_LIBRARY_PATH\n";
			run_sh += "exec ./game";
			f = open(root_dir + "/build/" + self.output + "/run.sh", "w");
			f.write(run_sh);
			f.close();

			# make the sh file executable?
			os.system("chmod 0777 " + root_dir + "/" + self.build_folder + "/" + self.output + "/run.sh");
			os.system("chmod 0777 " + root_dir + "/" + self.build_folder + "/" + self.output + "/game");

			print("-------------------------");
			print("Finished!");
			print("-------------------------");



	def startHTML5(self):

		print("-------------------------");
		print("HTML5 " + self.platformOn);
		ark2d_dir = self.ark_config[self.platformOn]['ark2d_dir'];
		root_dir = self.ark_config[self.platformOn]['ark2d_dir'] if self.building_library else self.game_dir;
		emscripten_dir = self.ark_config['html5'][self.platformOn]['emscripten_dir'] if self.building_library else self.target_config['html5'][self.platformOn]['emscripten_dir'];
		emscripten_version = self.ark_config['html5'][self.platformOn]['emscripten_version'] if self.building_library else self.target_config['html5'][self.platformOn]['emscripten_version'];
		em_gcc = "python " + emscripten_dir + self.ds + "emscripten" + self.ds + emscripten_version + self.ds + "emcc";
		em_gpp = "python " + emscripten_dir + self.ds + "emscripten" + self.ds + emscripten_version + self.ds + "em++";

		print("-------------------------");
		print("Make directories...")
		mkdirs = [];
		mkdirs.extend(self.mkdirs);
		mkdirs.extend([root_dir + self.ds + self.build_folder + self.ds + self.platform]);

		if self.building_game:
			mkdirs.extend([root_dir + "/data/ark2d"]);
			mkdirs.extend([root_dir + "/build/html5/data"]);
			mkdirs.extend([root_dir + "/build/html5/data/ark2d"]);
			#mkdirs.extend([root_dir + "/build/html5/src/states"]); # TODO: read src dir and include any dirs here.

		game_src_dirs = util.listDirectories(root_dir+"/src", False);
		#print('game_src_dirs ');
		#print(game_src_dirs);
		for dir in game_src_dirs:
			mkdirs.extend([root_dir + "/build/html5/src/" + dir]);

		util.makeDirectories(mkdirs);

		print("-------------------------");
		print("Loading build cache...")
		cacheJSON = self.openCache("compiled");
		cacheChanged = False;

		optimisationlevel = "1";
		#%ARK2D_DIR%

		self.ldflags = [];

		#print self.tag_replacements;
		if (self.building_game):
			print("Add external modules to project")
			if "external_modules" in self.target_config:
				for module in self.target_config['external_modules']:
					print module

					try:
						moduleJsonFilename = module + self.ds + "module.json"
						f = open(moduleJsonFilename, "r")
						fcontents = f.read();
						f.close();
						fjson = json.loads(fcontents);

						print  (fjson);
						moduleObj = Module(self, module);
						#moduleObj.platforms.html5.sources_relative = False;
						fjson['platforms']['html5']['sources_relative'] = False;
						moduleObj.initFromConfig(fjson);

						print (moduleObj);

						#self.include_dirs.extend( moduleObj.platforms.html5.header_search_paths );

						self.src_files.extend(moduleObj.platforms.html5.sources);

						#gypfiletargetcondition['ldflags'].extend( moduleObj.platforms.ios.library_search_paths );
						self.ldflags.extend( moduleObj.platforms.html5.linker_flags );

						self.preprocessor_definitions.extend( moduleObj.platforms.html5.preprocessor_definitions )



						#ModuleUtil.addToGypConfig(moduleObj, 'html5', gypfiletarget, gypfiletargetcondition);
						#ModuleUtil.addToIOSBuild(moduleObj, self);

					except OSError as exc:
						print("Module config was not valid.");
						print(exc);
						exit(0);

		print("-------------------------");
		print("Compiling Sources");
		for srcFile in self.src_files:

			srcFileIndex = srcFile.rfind('.');
			srcFileExtension = srcFile[srcFileIndex+1:len(srcFile)];
			srcFileNew = srcFile[0:srcFileIndex] + ".o";

			compileStr = "";
			if srcFileExtension == 'c':
				compileStr += em_gcc;
			elif srcFileExtension == 'cpp' or srcFileExtension == 'mm':
				compileStr += em_gpp;
				compileStr += " -std=c++0x ";
				compileStr += " -stdlib=libc++ ";
			elif srcFileExtension == 'rc':
				continue;

			compileStr += " -DARK2D_EMSCRIPTEN_JS ";
			compileStr += " -DARK2D_DESKTOP ";
			compileStr += " -DGL_GLEXT_PROTOTYPES ";
			#compileStr += " --js-library " + root_dir + "/lib/html5/mylibrary.js";
			#compileStr += " EMCC_DEBUG=1 ";

			if (self.building_game):
				for item in self.target_config['defines']:
					compileStr += " -D" + item + " ";

			"""compileStr += " -Wno-trigraphs -Wno-deprecated-declarations -Wreturn-type -fexceptions "; #-fno-builtin-exit ";
			if self.building_library:
				compileStr += " -fPIC ";

			if srcFileExtension == 'c':
				compileStr += " -Wno-implicit-function-declaration  -Wno-implicit ";
			#elif srcFileExtension == "cpp":
				#compileStr += " -fpermissive ";
				"""


			compileStr += " -Wall -g ";

			#if (not self.debug):
				#compileStr += " -O1 ";

			#compileStr += " -v ";

			if (self.platformOn == "osx"):
				compileStr += " -DARK2D_EMSCRIPTEN_JS_ON_MACINTOSH ";

			compileStr += " -Wno-overloaded-virtual "
			compileStr += " -Wno-literal-conversion "
			compileStr += " -c ";
			#if ("vendor" not in srcFile):
			compileStr += " -s DEMANGLE_SUPPORT=1 ";

			#compileStr += " -s ALLOW_MEMORY_GROWTH=1 "
			#compileStr += " -s TOTAL_MEMORY=16777216 "
			compileStr += " -s TOTAL_MEMORY=134217728 ";
			compileStr += " -s USE_PTHREADS=0 ";
			#compileStr += " -s MODULARIZE=1 ";
			#compileStr += " -s EXPORT_FUNCTION_TABLES=1 ";
			compileStr += " -s EXPORTED_FUNCTIONS=\"['_main','_emscripten_run_thread', '_emscripten_gamepadConnected', '_emscripten_containerSetSize', '_AngelScriptUtil_MessageCallback', '_AngelScriptUtil_Print', '_emscripten_StateBasedGame_enterState']\" ";
			compileStr += " -s ASSERTIONS=2 ";
			compileStr += " -O" +optimisationlevel + " ";

			if self.building_game:
				compileStr += " -ffunction-sections ";

			compileStr += " -I " + self.ark2d_dir + "/src ";
			compileStr += " -I " + self.ark2d_dir + "/src/ARK2D/vendor/iphone ";
			compileStr += " -I " + self.ark2d_dir + "/src/ARK2D/vendor/spine/includes ";
			compileStr += " -I " + self.ark2d_dir + "/src/ARK2D/vendor/angelscript ";
			compileStr += " -I " + self.ark2d_dir + "/src/ARK2D/vendor/zlib123 ";

			if self.building_game:
				if "include_dirs" in self.game_config:
					for includedir in self.game_config['include_dirs']:
						includedir_actual = util.str_replace(includedir, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir), ("%ARK2D_DIR%", self.ark2d_dir)]);
						compileStr += " -I " + includedir_actual + " ";


			startFile = root_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds;
			if srcFileNew[0:3] == "../" or srcFileNew[0:1] == "/":
				startFile = "";
			compileStr += " -o \"" + startFile + srcFileNew + "\"  \"" + srcFile + "\" ";
			#compileStr += " -lrt ";

			if (not srcFile in cacheJSON or cacheJSON[srcFile]['date_modified'] < os.stat(srcFile).st_mtime):

				print(root_dir);
				print("Compiling " + srcFileNew);
				print(compileStr);
				returnval = os.system(compileStr);
				if returnval == 0:
					cacheJSON[srcFile] = {"date_modified": os.stat(srcFile).st_mtime };
					cacheChanged = True;
					self.saveCache("compiled", cacheJSON);
				else:
					print("ERROR");
					exit(0);

		if (cacheChanged == True):
			self.saveCache("compiled", cacheJSON);


		if (self.building_library):
			print("-------------------------");
			print("Creating Shared Object");
			linkStr = "";
			linkStr += em_gcc + " -s FULL_ES2=1 ";
			#if (not self.debug):

			#linkStr += " -s MODULARIZE=1 ";
			#linkStr += " -s EXPORT_FUNCTION_TABLES=1 ";
			linkStr += " -s DEMANGLE_SUPPORT=1 ";
			linkStr += " -s EXPORTED_FUNCTIONS=\"['_main','_emscripten_run_thread', '_emscripten_gamepadConnected', '_emscripten_containerSetSize', '_AngelScriptUtil_MessageCallback', '_AngelScriptUtil_Print', '_emscripten_StateBasedGame_enterState']\" ";
			linkStr += " -s ASSERTIONS=2 ";
			linkStr += " -g ";
			linkStr += " -O" +optimisationlevel + " ";
			linkStr += " -o " + self.ark2d_dir + self.ds + "build/html5/libark2d.bc ";
			#linkStr += " --js-library " + self.ark2d_dir + self.ds + "lib/html5/mylibrary.js ";
			for srcFile in self.src_files:
				srcFileIndex = srcFile.rfind('.');
				srcFileExtension = srcFile[srcFileIndex+1:len(srcFile)];
				srcFileNew = srcFile[0:srcFileIndex] + ".o";

				linkStr += self.ark2d_dir + "/" + self.build_folder + "/" + self.platform + "/" + srcFileNew + " ";

			print(linkStr);
			os.system(linkStr);

			print("-------------------------");
			print("Creating Shared Object as Modules");

			for index, module in enumerate( self.ark_config['modules'] ):

				moduleName = module;
				module = self.ark_config['modules'][moduleName];
				print("-------------------------");
				print("Module: " + moduleName);

				linkStr = "";
				linkStr += em_gcc + " -s FULL_ES2=1 ";
				#if (not self.debug):
				linkStr += " -s DEMANGLE_SUPPORT=1 ";
				linkStr += " -s EXPORTED_FUNCTIONS=\"['_main','_emscripten_run_thread', '_emscripten_gamepadConnected', '_emscripten_containerSetSize', '_AngelScriptUtil_MessageCallback', '_AngelScriptUtil_Print', '_emscripten_StateBasedGame_enterState']\" ";
				linkStr += " -s ASSERTIONS=2 ";
				linkStr += " -g ";
				linkStr += " -O" +optimisationlevel + " ";
				#linkStr += " --js-library " + self.ark2d_dir + self.ds + "lib/html5/mylibrary.js ";
				linkStr += " -o " + self.ark2d_dir + self.ds + "build/html5/libark2d_"+moduleName+".bc ";

				for srcFile in module['sources']:
					srcFileIndex = srcFile.rfind('.');
					srcFileExtension = srcFile[srcFileIndex+1:len(srcFile)];
					srcFileNew = srcFile[0:srcFileIndex] + ".o";

					linkStr += self.ark2d_dir + "/" + self.build_folder + "/" + self.platform + "/" + srcFileNew + " ";

				print(linkStr);
				os.system(linkStr);

		elif (self.building_game):
			print("-------------------------");
			print("Copying Libraries ");
			if ("modules" not in self.target_config):
				os.system("cp " + self.ark2d_dir + "/build/html5/libark2d.bc " + root_dir + "/build/html5/libark2d.bc");
			else:
				for module in self.target_config['modules']:
					os.system("cp " + self.ark2d_dir + "/build/html5/libark2d_" + module + ".bc " + root_dir + "/build/html5/libark2d_" + module + ".bc");

			print("-------------------------");
			print("Copying Game Data Files ");
			if (os.path.exists( root_dir + self.ds + "build/html5/data") ):
				os.system("rm -r " + root_dir + self.ds + "build/html5/data");
				util.makeDirectories([root_dir + "/build/html5/data"]);
				util.makeDirectories([root_dir + "/build/html5/data/ark2d"]);
			os.system("cp -r " + root_dir + "/data/* " + root_dir + "/build/html5/data ");

			print("-------------------------");
			print("Copying ARK2D Data Files ");
			os.system("cp -r " + ark2d_dir + "/data/* " + root_dir + "/data/ark2d ");

			print("-------------------------");
			print("Creating Executable");
			# remove first if it exists
			os.system("rm -r " + root_dir + self.ds + "build/html5/game.html");
			os.system("rm -r " + root_dir + self.ds + "build/html5/game.html.mem");
			os.system("rm -r " + root_dir + self.ds + "build/html5/game.js");
			os.system("rm -r " + root_dir + self.ds + "build/html5/game.data");
			os.system("rm -r " + root_dir + self.ds + "build/html5/index.html");

			executableStr = "";
			executableStr += em_gcc;
			#executableStr += " -s MODULARIZE=1 ";
			#executableStr += " -s EXPORT_FUNCTION_TABLES=1 ";
			executableStr += " -s FULL_ES2=1 ";
			executableStr += " -s DEMANGLE_SUPPORT=1 ";
			executableStr += " -s TOTAL_MEMORY=134217728 ";
			executableStr += " -s EXPORTED_FUNCTIONS=\"['_main','_emscripten_run_thread', '_emscripten_gamepadConnected', '_emscripten_containerSetSize', '_AngelScriptUtil_MessageCallback', '_AngelScriptUtil_Print', '_emscripten_StateBasedGame_enterState']\" ";
			executableStr += " -s ASSERTIONS=2 ";
			executableStr += " -g ";
			executableStr += " -O" +optimisationlevel + " ";
			#executableStr += " --js-library " + self.ark2d_dir + self.ds + "lib/html5/mylibrary.js ";
			executableStr += "-o " + root_dir + self.ds + "build/html5/game.html ";

			print  self.src_files;
			for srcFile in self.src_files:
				srcFileIndex = srcFile.rfind('.');
				srcFileExtension = srcFile[srcFileIndex+1:len(srcFile)];
				srcFileNew = srcFile[0:srcFileIndex] + ".o";

				if srcFileExtension == 'rc':
					continue;

				startFile = root_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds;
				if srcFileNew[0:3] == "../" or srcFileNew[0:1] == "/":
					startFile = "";

				executableStr += startFile + srcFileNew + " ";


			if ("modules" not in self.target_config):
				executableStr +=  root_dir + "/build/html5/libark2d.bc ";
			else:
				for module in self.target_config['modules']:
					executableStr +=  root_dir + "/build/html5/libark2d_" + module + ".bc ";

			if "libs" in self.target_config:
				for lib in self.target_config['libs']:
					lib2 = util.str_replace(lib, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir), ("%ARK2D_DIR%", self.ark2d_dir)]);
					if lib2[0:1] != '/':
						lib2 = root_dir + "/" + lib2;
					executableStr += lib2 + " ";


			executableStr += " -Wl ";
			executableStr += " --memory-init-file 1  ";

			executableStr += " -L" + root_dir + "/" + self.build_folder + "/" + self.platform + " ";
			#executableStr += " -lark2d";
			executableStr += " -lstdc++ -lm "; #-lalut -lcurl -lX11 ";
			#executableStr += " -lGLESv2 -lEGL ";


			#executableStr += " --preload-file ./data/ark2d/fonts/default.fnt "
			#####
			filesToBundle = util.listFiles(root_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + "data", False);
			#print(filesToBundle);
			for file in filesToBundle:
				thefile = "./data/" + file;
				executableStr += " --preload-file " + thefile + " ";

			print(executableStr);
			os.system(executableStr);

			print("-------------------------");
			print("Creating index.html ");
			game_width = self.target_config['html5']['game_width'];
			game_height = self.target_config['html5']['game_height'];
			indexpagestr = "";
			editsStrReplace = [("%ARK2D_DIR%", self.ark2d_dir), ("%GAME_NAME%", self.game_config['game']['name']), ("%GAME_DESCRIPTION%", self.game_config['game']['description']), ("%GAME_WIDTH%", str(game_width)), ("%GAME_HEIGHT%", str(game_height)), ("%GAME_HEIGHT_CENTER%", str((game_height/2)-10)), ("%COMPANY_NAME%", self.developer_name) ];

			templateFile = ark2d_dir+"/lib/html5/index.html";
			if "template" in self.target_config['html5']:
				templateFile = util.str_replace(self.target_config['html5']['template'], editsStrReplace);
			f = open(templateFile, "r");
			indexpagestr = f.read();
			f.close();
			indexpagestr = util.str_replace(indexpagestr, editsStrReplace);
			f = open(root_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + "index.html", "w");
			f.write(indexpagestr);
			f.close();

			if "editor" in self.target_config['html5']:
				if self.target_config['html5']['editor'] == True:
					# copy editor folder.
					self.mycopytree(ark2d_dir+"/lib/html5/editor", root_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + "editor" );



		print("-------------------------");
		print("Finished!");
		print("-------------------------");

		return;





	def clean(self):
		print("---");
		print("Cleaning Build");
		cm = "";
		if (self.platform == "xcode" or self.platform == "osx"):
			cm = "rm -r -d " + self.game_dir + self.ds + self.build_folder + self.ds + self.output;
		elif(self.platform == "windows"):
			cm = "rmdir /S /Q " + self.game_dir + self.ds + self.build_folder + self.ds + self.output;

		#subprocess.call([], shell=True);
		print(cm);
		try:
			buildresp = os.system(cm);
		except:
			print("could not remove dir");
			pass;

		if (self.platform == "windows"):
			cm = "rmdir /S /Q " + self.game_resources_dir + self.ds + "ark2d";
			print(cm);
			try:
				buildresp = os.system(cm);
			except:
				print("could not remove dir");
				pass;

	def processAssets(self):

		# copy /data folder into project, basically.

		if (self.platform == "ios"):
			#subprocess.call(["cp -r " + config['osx']['game_resources_dir'] + " " + self.game_dir + self.ds + self.build_folder + self.ds + self.platform + self.ds + "data/"], shell=True); #libark2d

			# define variables
			game_dir = self.game_dir;
			game_resources_dir = self.game_resources_dir;
			audio_quality = 5 if not 'audio_quality' in self.ios_config else self.ios_config['audio_quality'];

			print("Creating/opening assets cache file...");
			assetsCache = game_dir + self.ds + "build" + self.ds + self.platform + self.ds + "build-cache" + self.ds + "assets.json";
			assetsJson = self.openCacheFile(assetsCache);
			fchanged = False;

			print("Start copying files...")
			print("audio_quality " + str(audio_quality));
			filesToCopy = util.listFiles(game_resources_dir, False);
			print(filesToCopy);
			for file in filesToCopy:
				fromfile = game_resources_dir + self.ds + file;
				tofile = game_dir + self.ds + "build" + self.ds + self.platform + self.ds + "data" + self.ds + file;

				#replace spaces in paths on max osx with slash-spaces
				#fromfile = fromfile.replace(" ", "\ ");
				#tofile = tofile.replace(" ", "\ ");

				if (not fromfile in assetsJson or assetsJson[fromfile]['date_modified'] < os.stat(fromfile).st_mtime):
					file_ext = util.get_str_extension(file);
					if (file_ext == "ogg"): # resample
						print("resampling audio file from: " + fromfile + " to: " + tofile);
						code = subprocess.call([self.ark2d_dir +  "/../Tools/oggdec "+fromfile+" --quiet --output=- | " + self.ark2d_dir +  "/../Tools/oggenc --raw --quiet --quality=" + str(audio_quality) + " --output="+tofile+" -"], shell=True);
						if code != 0:
							print('could not copy ogg.');
							print('macOS help:');
							print('	* install brew:');
							print('	/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"');
							print('	* install vorbis-tools:');
							print('	brew install vorbis-tools');
							exit();
					else: # standard copy
						print("copying file from: " + fromfile + " to: " + tofile);

						# check directory exists. if not, make it.
						tofiledir = tofile[0:tofile.rfind("/")+1];
						if (not os.path.exists(tofiledir)):
							os.makedirs(tofiledir);

						#subprocess.call(["cp -r " + fromfile + " " + tofile], shell=True);
						shutil.copy2(fromfile, tofile);

					assetsJson[fromfile] = {"date_modified": os.stat(fromfile).st_mtime };
					fchanged = True;

			if (fchanged == True):
				f = open(assetsCache, "w")
				f.write(json.dumps(assetsJson, sort_keys=True, indent=4));
				f.close();


	def generateStrings(self):
		#print(self.config['resources']);
		if ("resources" in self.config and "strings" in self.config["resources"]):

			print("Generating Strings files...");
			self.config["resources"]["strings"]["source"] = util.str_replace(self.config["resources"]["strings"]["source"], self.tag_replacements);

			if (sys.platform == "win32"):
				stringsJSON = str(json.dumps(self.config["resources"]["strings"], separators=(',',':')));#.replace("\"", "\\\"");
				subprocess.call(["python", self.ark2d_dir + r"/__preproduction/polyglot/build.py", stringsJSON], shell=True);

			else:
				stringsJSON = str(json.dumps(self.config["resources"]["strings"], separators=(',',':')));#.replace("\"", "\\\"");
				compileLine = r"python " + self.ark2d_dir + r"/__preproduction/polyglot/build.py '" + stringsJSON + r"' ";

				print(compileLine);
				subprocess.call([compileLine], shell=True);




	def generateSpriteSheets(self):
		# print(self.config);
		if ("resources" in self.config and "spritesheets" in self.config["resources"]):

			#load cache file
			cacheJSON = self.openCache("spritesheets");
			cacheChanged = False;

			#generate sheets
			print("Generating SpriteSheets...");
			for spritesheet in self.config["resources"]["spritesheets"]:

				spritesheetName = spritesheet["name"];
				print(spritesheetName);

				generateThisSheet = False;
				for imageFile in spritesheet["files"]:
					#print( imageFile + " : " + str(cacheJSON[spritesheetName][imageFile]['date_modified']) + " : " + str(os.stat(self.game_dir + self.ds + imageFile).st_mtime) );
					#print(cacheJSON[spritesheetName]);
					if (not spritesheetName in cacheJSON or not imageFile in cacheJSON[spritesheetName] or cacheJSON[spritesheetName][imageFile]['date_modified'] < os.stat(self.game_dir + self.ds + imageFile).st_mtime):
						generateThisSheet = True;
						break;

				#only generate this sheets if it has a change in one of it's files.
				if (generateThisSheet == True):
					print("Generating SpriteSheet: " + spritesheet["output"]);
					spritesheet['game_dir'] = self.game_dir;
					spritesheet['game_preproduction_dir'] = self.game_preproduction_dir;

					#Previos implementation did not work correctly on win 7 64 bit. Escape character (Image\ Packer)
					#was ineffective. Solution is string literals (r + string) and calling arguments seperatly.
					#JSON format also changed, to remove escape characters.
					if(sys.platform == "win32"):
						spritesheetJSON = str(json.dumps(spritesheet, separators=(',',':')));
						print (spritesheetJSON);
						compileLine = self.ark2d_dir + r"\..\Tools\Image Packer\build\jar\ImagePacker.jar"
						subprocess.call(["java", "-jar", compileLine, spritesheetJSON], shell=True);
					#Old method, assumed to work on other platforms
					else:
						spritesheetJSON = str(json.dumps(spritesheet, separators=(',',':'))).replace("\"", "\\\"");
						compileLine = "java -jar " + self.ark2d_dir + "/../Tools/Image\ Packer/build/jar/ImagePacker.jar \"" + spritesheetJSON + "\"";
						print(compileLine);
						subprocess.call([compileLine], shell=True); # player


					#redocache
					cacheChanged = True;
					cacheJSON[spritesheetName] = {};
					for imageFile in spritesheet["files"]:
						cacheJSON[spritesheetName][imageFile] = {"date_modified": os.stat(self.game_dir + self.ds + imageFile).st_mtime };

					# if platform is android and etc1 is set. make a pkm file.
					if (self.platform == "android" and "etc1" in spritesheet and spritesheet['etc1'] == True):
						print("Generating PKM file for Android build...");
						pkmfile = self.game_dir + self.ds + "data" + self.ds + spritesheetName + ".png";
						#pkmstr = self.android_sdkdir + self.ds + "android-sdks" + self.ds + "tools" + self.ds + "etc1tool --encodeNoHeader " + pkmfile;
						pkmstr = self.android_sdkdir  + self.ds + "tools" + self.ds + "etc1tool " + pkmfile;
						print(pkmstr);
						subprocess.call([pkmstr], shell=True); #herpherpherp

						pkmbase = os.path.splitext(pkmfile)[0];
						os.rename(pkmbase + ".pkm", pkmbase + ".pkm_png")


				pass;

			if (cacheChanged == True):
				self.saveCache("spritesheets", cacheJSON);

			pass;
		pass;

	def openCache(self, filename):
		cachefilename = "";
		cachefilename += self.game_dir + self.ds + self.build_folder + self.ds + self.output + self.ds + "build-cache" + self.ds  + filename + ".json";
		self.createCacheFile(cachefilename);
		f = open(cachefilename, "r");
		fcontents = f.read();
		f.close();
		fjson = json.loads(fcontents);
		return fjson;

	def saveCache(self, filename, data):
		f = open(self.game_dir + self.ds + self.build_folder + self.ds + self.output + self.ds + "build-cache" + self.ds + filename + ".json", "w");
		f.write(json.dumps(data, sort_keys=True, indent=4));
		f.close();
		return;

	def getJsonFile(self, file, doReplace=False):
		print("getting json file: " + file);
		f = open(file, "r");
		fcontents = f.read();
		f.close();
		if (doReplace):
			fcontents = util.str_replace(fcontents, [("%ARK2D_DIR%", self.ark2d_dir)]);
		return json.loads(fcontents);




	def addLibrariesToArray(self, arr, lbs, extension=""): #, extension2=""):

		if (extension == ""):
			if (self.platform == "windows"):
				extension = "dll";
			elif (self.platform == "osx"):
				extension = "dylib";
			elif (self.platform == "linux"):
				extension = "so";

		for lib in lbs:
			file_ext = util.get_str_extension(lib);
			if file_ext == extension: #"dll":
				arr.extend([lib]);


		return arr;




	def startAndroid(self):
		print("Building Android");

		# open config


		# define vars.
		nl = "\r\n";

		if (self.building_game):

			android_projectType = 'intellij';

			#sdk version, not NDK.
			appplatformno = self.android_config['sdk_version'];
			appplatform = "android-" + str(appplatformno);
			ndkappplatformno = self.android_config['ndk_version'];
			ndkappplatform = "android-" + str(ndkappplatformno);

			print ("Android sdk version: " + str(appplatformno));

			self.android_billing = self.android_config['billing'] or False;
			#if (self.android_billing):
			#	self.android_config['gradle_libraries'] = ["market_licensing"];

			javaPackageName = "org." + self.developer_name_safe + "." + self.game_name_safe;

			audio_quality = self.android_config['audio_quality'];

			rootPath = self.game_dir;

			ndkprojectpath = self.game_dir;
			thisCreateDirs = [self.game_dir + self.ds + "build"];
			thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "build-cache"]);

			if (android_projectType == 'intellij'):
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe ]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "build"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "assets"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "assets" + self.ds + "ark2d"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "java"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "java" + self.ds + "org"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "java" + self.ds + "org" + self.ds + self.developer_name_safe]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "java" + self.ds + "org" + self.ds + self.developer_name_safe + self.ds + self.game_name_safe ]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "jniLibs" + self.ds + "armeabi"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "jniLibs" + self.ds + "armeabi-v7a"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "jniLibs" + self.ds + "x86"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "res"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "res" + self.ds + "raw"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "res" + self.ds + "xml"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "res" + self.ds + "drawable"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "res" + self.ds + "drawable-mdpi"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "res" + self.ds + "drawable-hdpi"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "res" + self.ds + "drawable-xhdpi"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "res" + self.ds + "drawable-xxhdpi"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "res" + self.ds + "drawable-xxxhdpi"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "res" + self.ds + "values"]);

				if (self.android_billing):
					thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "aidl"]);
					thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "aidl" + self.ds + "com"]);
					thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "aidl" + self.ds + "com" + self.ds + "android" + self.ds + "vending" + self.ds + "billing" ]);
					thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij" + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "java" + self.ds + "org" + self.ds + self.developer_name_safe + self.ds + self.game_name_safe + self.ds + "iab_util"]);


			else:
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "assets"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "assets" + self.ds + "ark2d"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "src"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "gen"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "libs"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "libs" + self.ds + "armeabi"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "libs" + self.ds + "armeabi-v7a"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "libs" + self.ds + "x86"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "obj"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "obj" + self.ds + "local"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "obj" + self.ds + "local" + self.ds + "armeabi"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "obj" + self.ds + "local" + self.ds + "armeabi-v7a"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "obj" + self.ds + "local" + self.ds + "x86"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "res"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "res" + self.ds + "raw"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "res" + self.ds + "drawable"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "res" + self.ds + "drawable-mdpi"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "res" + self.ds + "drawable-hdpi"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "res" + self.ds + "drawable-xhdpi"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "res" + self.ds + "drawable-xxhdpi"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "res" + self.ds + "drawable-xxxhdpi"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "res" + self.ds + "values"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "res" + self.ds + "xml"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "src" + self.ds + "org"]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "src" + self.ds + "org" + self.ds + "" + self.developer_name_safe]);
				thisCreateDirs.extend([rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "src" + self.ds + "org" + self.ds + "" + self.developer_name_safe + self.ds + self.game_name_safe]);
				pass;
			pass;
		else:

			#sdk version, not NDK.
			appplatformno = self.android_config['sdk_version'];
			appplatform = "android-" + str(appplatformno);
			ndkappplatformno = self.android_config['ndk_version'];
			ndkappplatform = "android-" + str(ndkappplatformno);

			rootPath = self.ark2d_dir;

			ndkprojectpath = self.ark2d_dir;
			thisCreateDirs = [ndkprojectpath + self.ds + "build"];
			pass;

		appbuilddir = rootPath + self.ds + "build" + self.ds + self.output;
		appbuildscript = rootPath + self.ds + "build" + self.ds + self.output + self.ds + "Android.mk";
		jnifolder = rootPath + self.ds + "jni";
		appbuildscript3 = rootPath + self.ds + "jni" + self.ds + "Application.mk";

		#check for spaces
		if (" " in ndkprojectpath) or (" " in self.android_ndkdir):
			print("Android build paths (and ndk directory) may not contain spaces.");
			return;


		thisCreateDirs.extend([appbuilddir, jnifolder]);

		# make some directories...
		util.makeDirectories(thisCreateDirs);
		#for thisstr in thisCreateDirs:
		#	print("mkdir " + thisstr);
		#	try:
		#		os.makedirs(thisstr);
		#	except OSError as exc:
		#		if exc.errno == errno.EEXIST:
		#			pass
		#		else: raise

		if (self.building_game):

			if (self.platform == "android" and self.ouya == True):

				if (android_projectType == 'intellij'):
					print("intellij not supported - ouya");
					exit();

				print("copying Ouya libs");
				shutil.copy(self.ouya_config['sdk'] + "/libs/ouya-sdk.jar", self.game_dir + self.ds + "build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "libs" + self.ds + "ouya-sdk.jar");

				print("copying Ouya store graphic");
				#if "ouya" in config:
				if "store_icon" in self.ouya_config:
					ouya_icon_full = util.str_replace(self.ouya_config['store_icon'], [("%PREPRODUCTION_DIR%", self.game_preproduction_dir)]);
					shutil.copy(ouya_icon_full, self.game_dir + self.ds + "build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "res" + self.ds + "drawable-xhdpi" + self.ds + "ouya_icon.png");

			if (self.platform == "android" and self.firetv == True):
				print("TODO: copy firetv libs...");
				# ...

			#make android.mk
			pnl = nl;
			nl = "\n";

			#if "libs" not in config['android']:
			#	config['android']['libs'] = [];

			self.ldflags = [];
			edits_shared_libraries_modules = "";
			print("Add external modules")
			if "external_modules" in self.target_config:
				for module in self.target_config['external_modules']:
					print module

					try:
						moduleJsonFilename = module + self.ds + "module.json"
						f = open(moduleJsonFilename, "r")
						fcontents = f.read();
						f.close();
						fjson = json.loads(fcontents);

						print  (fjson);
						moduleObj = Module(self, module);
						moduleObj.initFromConfig(fjson);

						print (moduleObj);

						self.include_dirs.extend( moduleObj.platforms.android.header_search_paths );

						self.src_files.extend(moduleObj.platforms.android.sources);

						#gypfiletargetcondition['ldflags'].extend( moduleObj.platforms.ios.library_search_paths );
						self.ldflags.extend( moduleObj.platforms.android.linker_flags );

						self.preprocessor_definitions.extend( moduleObj.platforms.android.preprocessor_definitions )
						#gypfiletargetcondition['link_settings']['libraries'].extend( moduleObj.platforms.ios.libraries );

						#for lib in moduleObj.platforms.android.libraries:
						#	edits_shared_libraries_modules += "implementation " + lib + "\n";;

						for aar in fjson['platforms']['android']['aars']:
							aar = util.str_replace(aar, self.tag_replacements);
							aar = util.str_replace(aar, [("%MODULE_DIR%", moduleObj.root)]);
							aar_name = util.get_str_filename_no_ext(aar);
							edits_shared_libraries_modules += "implementation project(':" + aar_name + "')\n";
							self.aars.extend([aar_name]);
							self.aar_paths.extend([aar]);



					except OSError as exc:
						print("Module config was not valid.");
						print(exc);
						exit(0);


			print("NDK");
			print("Creating Android.mk");
			android_make_file = "";
			android_make_file += "LOCAL_PATH := $(call my-dir)/../../" + nl + nl;
			android_make_file += "include $(CLEAR_VARS)" + nl+nl;
			android_make_file += "LOCAL_MODULE    := " + self.game_name_safe +  nl+nl; # Here we give our module name and source file(s)
			android_make_file += "LOCAL_C_INCLUDES := ";
			android_make_file += self.ark2d_dir + "/lib/includes/ ";
			android_make_file += self.ark2d_dir + "/src/ARK2D/vendor/android/libzip/jni/ ";
			android_make_file += self.ark2d_dir + "/src/ARK2D/vendor/android/openal/jni/include ";
			android_make_file += self.ark2d_dir + "/src/ARK2D/vendor/spine/includes ";
			android_make_file += self.ark2d_dir + "/src/ARK2D/vendor/angelscript ";
			android_make_file += self.ark2d_dir + "/src";
			for h in self.include_dirs:
				android_make_file += h + " ";
			android_make_file += nl;

			android_make_file += "LOCAL_CFLAGS := -DARK2D_ANDROID ";
			android_make_file += "-DGAME_DIR=" + self.game_dir + " ";
			android_make_file += "-DGAME_SRC_DIR=" + self.game_src_dir + " ";

			if (self.platformOn == "windows"):
				android_make_file += "-DARK2D_ANDROID_ON_WINDOWS ";
			elif (self.platformOn == "osx"):
				android_make_file += "-DARK2D_ANDROID_ON_MACINTOSH ";

			if (self.ouya == True):
				android_make_file += "-DARK2D_OUYA ";
			if (self.firetv == True):
				android_make_file += "-DARK2D_AMAZON ";

			android_make_file += "-fno-exceptions -fexceptions  -Wno-psabi "; # -fno-rtti
			if (self.debug):
				android_make_file += " -DARK2D_DEBUG -DDEBUG -DNDK_DEBUG -O0 ";
			else:
				android_make_file += " -O3 "; #-fno-strict-aliasing -mfpu=vfp -mfloat-abi=softfp ";

			for h in self.preprocessor_definitions:
				android_make_file += " -D" + h;
			android_make_file += nl+nl;

			android_make_file += "LOCAL_DEFAULT_CPP_EXTENSION := cpp" + nl+nl;
			android_make_file += "LOCAL_SRC_FILES := \\" + nl;
			for h in self.src_files: #foreach file on config...
				if (util.get_str_extension(h)!= "rc"):
					android_make_file += "	" + h + " \\" + nl;

			android_make_file += "	src/jni.cpp \\ " + nl;

			android_make_file += nl;
			#android_make_file += "LOCAL_LDLIBS := -lGLESv1_CM -ldl -llog -lz -lfreetype -lopenal -lark2d" + nl+nl;
			#android_make_file += "LOCAL_LDLIBS := -lGLESv2 -lGLESv1_CM -ldl -llog -lz -lfreetype -lopenal -lark2d" + nl+nl;
			android_make_file += "LOCAL_LDLIBS := -lGLESv2 -lEGL -ldl -llog -lz -lopenal -lzip -langelscript -lark2d "; #-lfreetype
			for h in self.ldflags:
				android_make_file += "-l" + h + " ";


			# custom game libraries (fmod, and things)
			lib_search_path = "";
			edits_shared_libraries = [];
			edits_shared_libraries_gradlejars = "";
			if "native_libraries" in self.android_config:
				for gamelibrary in self.android_config['native_libraries']:
					gamelibraryname = gamelibrary['name'];

					edits_shared_libraries.extend([gamelibraryname]);
					android_make_file += " -l" + gamelibraryname + " ";

					if "jars" in gamelibrary:
						for gamelibraryjar in gamelibrary['jars']:
							self.android_libs.extend([gamelibraryjar]);
							edits_shared_libraries_gradlejars += "implementation files('../../../../" + gamelibraryjar + "')\n";

					if "armeabi" in gamelibrary:
						path = gamelibrary['armeabi'];
						path = path[:path.rfind("/")];
						lib_search_path += "-L"+self.game_dir+self.ds+path + " ";
					if "armeabi-v7a" in gamelibrary:
						path = gamelibrary['armeabi-v7a'];
						path = path[:path.rfind("/")];
						lib_search_path += "-L"+self.game_dir+self.ds+path + " ";
					if "x86" in gamelibrary:
						path = gamelibrary['x86'];
						path = path[:path.rfind("/")];
						lib_search_path += "-L"+self.game_dir+self.ds+path + " ";


			android_make_file += lib_search_path;
			android_make_file += nl+nl;

			android_make_file += "include $(BUILD_SHARED_LIBRARY)" + nl;
			f = open(appbuildscript, "w");
			f.write(android_make_file);
			f.close();

			# make application.mk
			print("Creating Application.mk");
			application_make_file = "";
			application_make_file += "NDK_TOOLCHAIN_VERSION := 4.9" + nl;
			application_make_file += "APP_PROJECT_PATH := " + ndkprojectpath + nl;
			application_make_file += "APP_BUILD_SCRIPT := " + appbuildscript + nl;
			application_make_file += "NDK_APP_OUT=" + appbuilddir + nl;
			application_make_file += "NDK_PROJECT_PATH=" + ndkprojectpath + nl;
			#application_make_file += "APP_ABI := all" + nl;
			#application_make_file += "APP_ABI := armeabi"; # armeabi-v7a x86" + nl;

			#next 7 fix
			if (self.debug):
				application_make_file += "APP_ABI := armeabi-v7a " + nl;
			else:
				application_make_file += "APP_ABI := armeabi armeabi-v7a x86 ";
				application_make_file += nl;

			application_make_file += "APP_CPPFLAGS += -std=c++11 -frtti " + nl;
			application_make_file += "APP_STL := gnustl_shared" + nl; #c++_shared" + nl; #stlport_static
			application_make_file += "LOCAL_C_INCLUDES += " + self.android_ndkdir + "/sources/cxx-stl/gnu-libstdc++/4.9/include" + nl;

			f = open(appbuildscript3, "w");
			f.write(application_make_file);
			f.close();

			nl = pnl;

			#copy ark2d in to project
			print("Copying ARK2D in to android sdk");
			shutil.copy2(self.ark2d_dir + self.ds + "build" + self.ds + "android" + self.ds + "libs" + self.ds + "armeabi-v7a" + self.ds + "libark2d.so", self.android_ndkdir + self.ds + "platforms"+self.ds+ndkappplatform+self.ds+"arch-arm" + self.ds + "usr" + self.ds + "lib" + self.ds);
			if not self.debug:
				shutil.copy2(self.ark2d_dir + self.ds + "build" + self.ds + "android" + self.ds + "libs" + self.ds + "x86" + self.ds + "libark2d.so", self.android_ndkdir + self.ds + "platforms"+self.ds+ndkappplatform+self.ds+"arch-x86" + self.ds + "usr" + self.ds + "lib" + self.ds);

			#
			# Generate IntelliJ / Android Studio project.
			#
			if (android_projectType == 'intellij'):

				intellij_aar_template_folder = self.ark2d_dir + self.ds + "lib" + self.ds + "android" + self.ds + "library_projects" + self.ds + "aar_template";
				intellij_template_folder = self.ark2d_dir + self.ds + "lib" + self.ds + "android" + self.ds + "project-intellj";
				intellij_folder = rootPath+self.ds+"build" + self.ds + self.output + self.ds + "project-intellij";

				# write settings.gradle
				f = open(intellij_folder + self.ds + "settings.gradle", "w");
				f.write("include ':" + self.game_name_safe + "'\n");

				for aar in self.aars:
					f.write("include ':" + aar + "'\n");

				if 'gradle_libraries' in self.android_config:
					for gradle_library in self.android_config['gradle_libraries']:
						f.write("include ':" + gradle_library + "'\n");
				f.close();

				# copy project.iml, gradlew.bat, gradle.sh, build.gradle
				shutil.copy2(intellij_template_folder + self.ds + "build.gradle", intellij_folder + self.ds );
				shutil.copy2(intellij_template_folder + self.ds + "project-intellij.iml", intellij_folder + self.ds );
				shutil.copy2(intellij_template_folder + self.ds + "gradlew.bat", intellij_folder + self.ds );
				shutil.copy2(intellij_template_folder + self.ds + "gradlew",     intellij_folder + self.ds );

				# write local.properties ( this should not ever go in vcs )
				f = open(intellij_folder + self.ds + "local.properties", "w");
				f.write("sdk.dir=" + self.android_sdkdir);
				f.close();

				# copy aar projects in...
				for aar in self.aar_paths:
					aar_name = util.get_str_filename_no_ext(aar);
					module_dir = intellij_folder + self.ds + aar_name;
					util.makeDirectories([module_dir]);
					util.copyfilewithreplacements(intellij_aar_template_folder + self.ds + "build.gradle", module_dir + self.ds + "build.gradle", [("%MODULE_NAME%", aar_name)]);
					util.copyfilewithreplacements(intellij_aar_template_folder + self.ds + "module.iml", module_dir + self.ds + aar_name + ".iml", [("%MODULE_NAME%", aar_name)]);
					shutil.copy2(aar, module_dir + self.ds + aar_name + ".aar" );


				# copy libraries in.
				if 'gradle_libraries' in self.android_config:
					for gradle_library in self.android_config['gradle_libraries']:
						self.mycopytree( intellij_template_folder + self.ds + gradle_library, intellij_folder + self.ds + gradle_library );

				project_manifest_dir = intellij_folder + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main";
				project_assets_dir = intellij_folder + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "assets";
				project_src_dir = intellij_folder + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "java" + self.ds + "org" + self.ds + self.developer_name_safe + self.ds + self.game_name_safe;
				project_res_dir = intellij_folder + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "res";
				project_nlib_dir = intellij_folder + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "jniLibs";

				#copy iab aidl in.
				if (self.android_billing):
					shutil.copy2(intellij_template_folder + "/market_billing/IInAppBillingService.aidl", project_manifest_dir + "/aidl/com/android/vending/billing/");

			elif (android_projectType == 'eclipse'):

				project_manifest_dir = rootPath + "/build/" + self.output + "/project-eclipse";
				project_assets_dir = rootPath + self.ds + "build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "assets";
				project_src_dir = rootPath + "/build/" + self.output + "/project-eclipse/src/org/" + self.developer_name_safe + self.ds + self.game_name_safe;
				project_res_dir = rootPath + "/build/" + self.output + "/project-eclipse" + self.ds + "res";
				project_nlib_dir = rootPath + "/build/" + self.output + "/project-eclipse" + self.ds + "libs";


			# making asset directories
			print("Making new asset directories");
			directoriesToCreate = util.listDirectories(self.game_resources_dir, False);
			for dir in directoriesToCreate:
				util.makeDirectories([project_assets_dir + self.ds + dir]);

			#generate game spritesheets
			self.generateSpriteSheets();

			print("Creating/opening assets cache file...");
			assetsCache = rootPath + self.ds + "build" + self.ds + self.output + self.ds + "build-cache" + self.ds + "assets.json";
			assetsJson = self.openCacheFile(assetsCache);
			fchanged = False;

			print("Cool, now copying files")
			filesToCopy = util.listFiles(self.game_resources_dir, False);
			print(filesToCopy);
			for file in filesToCopy:
				fromfile = self.game_resources_dir + self.ds + file;
				tofile = project_assets_dir + self.ds + file;

				#replace spaces in paths on max osx with slash-spaces
				#fromfile = fromfile.replace(" ", "\ ");
				#tofile = tofile.replace(" ", "\ ");



				if (not fromfile in assetsJson or assetsJson[fromfile]['date_modified'] < os.stat(fromfile).st_mtime):
					file_ext = util.get_str_extension(file);
					if (file_ext == "ogg"): # resample
						print("resampling audio file from: " + fromfile + " to: " + tofile);
						#subprocess.call(["oggdec "+fromfile+" --quiet --output=- | oggenc --raw --quiet --quality=" + str(audio_quality) + " --output="+tofile+" -"], shell=True);
						subprocess.call([ self.ark2d_dir + "/../Tools/oggdec "+fromfile+" --quiet --output=- | " + self.ark2d_dir +  "/../Tools/oggenc --raw --quiet --quality=" + str(audio_quality) + " --output="+tofile+" -"], shell=True);
					#elif (file_ext == "wav"): # resample
					#	print("resampling audio file from: " + fromfile + " to: " + tofile);
						#% cat inputfile | lame [options] - - > output
						#subprocess.call(["ffmpeg -y -i " +fromfile+ " "+tofile], shell=True);
						#subprocess.call(["ffmpeg -i " +fromfile+ " -ac 1 "+tofile], shell=True); # mono.
						#subprocess.call(["lame -V0 --quiet " +fromfile+ " "+tofile+""], shell=True); #variable bit rate, 0 quality
						#subprocess.call(["lame -a --quiet " +fromfile+ " "+tofile+""], shell=True); #downmix to mono
					else:
						print("copying file from: " + fromfile + " to: " + tofile);
						#subprocess.call(["cp -r " + fromfile + " " + tofile], shell=True);
						shutil.copy2(fromfile, tofile);

					assetsJson[fromfile] = {"date_modified": os.stat(fromfile).st_mtime };
					fchanged = True;

			if (fchanged == True):
				f = open(assetsCache, "w")
				f.write(json.dumps(assetsJson, sort_keys=True, indent=4));
				f.close();


			editsSharedLibraries = "";
			for edit_shared_lib in edits_shared_libraries:
				editsSharedLibraries += "System.loadLibrary(\"" + edit_shared_lib + "\");" + nl + nl;


			#copy sample game c++/jni files...
			print("generating game jni files");
			print("	generating jni.h");
			editsStrReplace = [
				("%GAME_CLASS_NAME%", self.game_class_name),
				("%GAME_SHORT_NAME%", self.game_name_safe),
				("%GAME_NAME_SAFE%", self.game_name_safe),
				("%COMPANY_NAME%", self.developer_name_safe),
				("%PACKAGE_DOT_NOTATION%", javaPackageName),
				("%GAME_WIDTH%", str(self.android_config['game_width'])),
				("%GAME_HEIGHT%", str(self.android_config['game_height'])),
				("%GAME_ORIENTATION%", self.config['game']['orientation']),
				("%GAME_CLEAR_COLOR%", self.config['game']['clearcolor']),
				("%GAME_SHARED_LIBRARIES%", editsSharedLibraries)
			];

			# game services bits in java files.
			#editsGameServices = [("%GAME_SERVICES_BLOCKSTART%", "/*"), ("%GAME_SERVICES_BLOCKEND%", "*/") ];
			#if "game_services" in self.android_config:
			#	if (self.android_config['game_services']['use']):
			#		editsGameServices = [("%GAME_SERVICES_BLOCKSTART%", ""), ("%GAME_SERVICES_BLOCKEND%", "") ];
			editsGameServices = [("%GAME_SERVICES_BLOCKSTART%", ""), ("%GAME_SERVICES_BLOCKEND%", "") ];

			editsInAppBilling = [("%INAPPBILLING_BLOCKSTART%", "/*"), ("%INAPPBILLING_BLOCKEND%", "*/"), ("%INAPPBILLING_PUBLICKEY%", "") ];
			if (self.android_billing):
				editsInAppBilling = [("%INAPPBILLING_BLOCKSTART%", ""), ("%INAPPBILLING_BLOCKEND%", ""), ("%INAPPBILLING_PUBLICKEY%", self.android_config['billing_signature'] ) ];

			# stuff to hide from old android
			editsOldAndroid23 = [
				("%ANDROIDSDK16_BLOCKSTART%", "/*"),
				("%ANDROIDSDK16_BLOCKEND%", "*/"),
				("%ANDROIDSDK16_LINECOMMENT%", "//"),
				("%!ANDROIDSDK16_LINECOMMENT%", "")
			];

			# one signal push notifications
			editsOneSignal = [("%ONESIGNAL_BLOCKSTART%", "/*"), ("%ONESIGNAL_BLOCKEND%", "*/") ];
			if ( "onesignal" in self.android_config ):
				editsOneSignal = [
					("%ONESIGNAL_BLOCKSTART%", ""),
					("%ONESIGNAL_BLOCKEND%", ""),
					("%ONESIGNAL_APP_ID%", self.android_config['onesignal']['onesignal_app_id']),
					("%ONESIGNAL_GCM_SENDER_ID%", self.android_config['onesignal']['gcm_sender_id'])
				];

			# one signal push notifications
			editsIronsource = [("%IRONSOURCE_BLOCKSTART%", "/*"), ("%IRONSOURCE_BLOCKEND%", "*/") ];
			if ( "ironsource" in self.android_config ):
				editsIronsource = [
					("%IRONSOURCE_BLOCKSTART%", ""),
					("%IRONSOURCE_BLOCKEND%", ""),
					("%IRONSOURCE_APP_KEY%", self.android_config['ironsource']['app_key'])
				];

			editsGoogleAnalytics = [("%GOOGLEANALYTICS_BLOCKSTART%", "/*"), ("%GOOGLEANALYTICS_BLOCKEND%", "*/") ];
			if (True):
				editsGoogleAnalytics = [
					("%GOOGLEANALYTICS_BLOCKSTART%", ""),
					("%GOOGLEANALYTICS_BLOCKEND%", "")
				];

			if (appplatformno >= 16):
				print("Android sdk version is 16. We can use new Android features.")
				editsOldAndroid23 = [
					("%ANDROIDSDK16_BLOCKSTART%", ""),
					("%ANDROIDSDK16_BLOCKEND%", ""),
					("%ANDROIDSDK16_LINECOMMENT%", ""),
					("%!ANDROIDSDK16_LINECOMMENT%", "//")
				];

			# ouya things
			editsOuya = [("%OUYA_BLOCKSTART%", "/*"), ("%OUYA_BLOCKEND%", "*/"), ("%!OUYA_BLOCKSTART%", ""), ("%!OUYA_BLOCKEND%", ""), ("%OUYA_DEVELOPERID%", ""), ("%OUYA_ENTITLEMENT_ID%", "") ];
			if (self.ouya == True):
				editsOuya = [("%OUYA_BLOCKSTART%", ""), ("%OUYA_BLOCKEND%", ""), ("%!OUYA_BLOCKSTART%", "/*"), ("%!OUYA_BLOCKEND%", "*/"), ("%OUYA_DEVELOPERID%", self.ouya_config['developer_id']), ("%OUYA_ENTITLEMENT_ID%", self.ouya_config['ouya']['entitlement_id']) ];

			editsFireTV = [("%FIRETV_BLOCKSTART%", "/*"), ("%FIRETV_BLOCKEND%", "*/"), ("%!FIRETV_BLOCKSTART%", ""), ("%!FIRETV_BLOCKEND%", "")];
			if (self.firetv == True):
				editsFireTV = [("%FIRETV_BLOCKSTART%", ""), ("%FIRETV_BLOCKEND%", ""), ("%!FIRETV_BLOCKSTART%", "/*"), ("%!FIRETV_BLOCKEND%", "*/")];

			# ouya key.der signature file
			if (self.ouya == True):
				if "key_file" in self.ouya_config:
					actual_key_file = util.str_replace(self.ouya_config['key_file'], [("%PREPRODUCTION_DIR%", self.game_preproduction_dir)]);
					actual_kf_copy_cmd = "cp " + actual_key_file + " " + rootPath+"/build/" + self.output + "/project-eclipse/res/raw/key.der";
					print("Copying key file");
					print(actual_kf_copy_cmd);
					subprocess.call([actual_kf_copy_cmd], shell=True);
			elif (self.firetv == True):
				#...
				print("firetv key things");


			f = open(self.ark2d_dir+"/lib/android/jni.h", "r");
			fgamejnih = f.read();
			f.close();
			fgamejnih = util.str_replace(fgamejnih, editsStrReplace);
			f = open(rootPath+"/src/jni.h", "w");
			f.write(fgamejnih);
			f.close();

			print("	generating jni.cpp");
			f = open(self.ark2d_dir+"/lib/android/jni.cpp", "r");
			fgamejnicpp = f.read();
			f.close();
			fgamejnicpp = util.str_replace(fgamejnicpp, editsStrReplace);
			f = open(rootPath+"/src/jni.cpp", "w");
			f.write(fgamejnicpp);
			f.close();

			#build game apk.
			buildline = self.android_ndkdir + "/ndk-build";
			buildline += " NDK_PROJECT_PATH=" + ndkprojectpath;
			buildline += " NDK_APP_OUT=" + appbuilddir;
			buildline += " APP_PROJECT_PATH=" + ndkprojectpath;
			buildline += " APP_BUILD_SCRIPT=" + appbuildscript;
			buildline += " APP_PLATFORM=" + ndkappplatform;

			#nexus-7 fix.
			#application_make_file += "APP_ABI := armeabi armeabi-v7a " + nl; #x86" + nl;

			#buildline += " NDK_LOG=1";
			print("Building game");
			print(buildline);
			subprocess.call([buildline], shell=True);

			#print("Moving output to build folder");
			libsdir = ndkprojectpath + "/libs";

			print("removing temp folders");
			self.rmdir_recursive(jnifolder);
			#self.rmdir_recursive(libsdir);

			print("done c++ bits.");
			print("do androidy-javay bits...");
			try:
				print("using custom AndroidManifest.xml");
				androidManifestPath = self.android_config['override_manifest'];
				subprocess.call(['cp ' + androidManifestPath + " " + project_manifest_dir + "/AndroidManifest.xml"], shell=True);
				#todo: copy this to rootPath+"/build/android/project/AndroidManifest.xml";
			except:

				versionCodePieces = self.game_version.split('.');
				versionCode = str(versionCodePieces[0]) + str(versionCodePieces[1]).rjust(2, '0') + str(versionCodePieces[2]).rjust(2, '0');
				versionCode = "1";

				minSdkVersion = str(appplatformno);
				targetSdkVersion = str(16);

				if (self.firetv):
					minSdkVersion = str(17);
					targetSdkVersion = str(17);

				print("generating default AndroidManifest.xml");
				androidManifestContents = "";
				androidManifestContents += "<?xml version=\"1.0\" encoding=\"utf-8\"?>" + nl;
				androidManifestContents += "<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\"" + nl;
				androidManifestContents += "	package=\"" + javaPackageName + "\" " + nl;
				if (self.android_config['app_to_sd'] == True):
					androidManifestContents += "	android:installLocation=\"preferExternal\"" + nl;
				else:
					androidManifestContents += "	android:installLocation=\"internalOnly\"" + nl;
				androidManifestContents += "	android:isGame=\"true\"" + nl;
				androidManifestContents += "	android:versionCode=\"" + versionCode + "\" " + nl;
				androidManifestContents += "	android:versionName=\"" + self.game_version + "\"> " + nl;

				#androidManifestContents += "	<uses-sdk android:minSdkVersion=\"" + minSdkVersion + "\" android:targetSdkVersion=\"" + targetSdkVersion + "\"/>" + nl;
				#androidManifestContents += "	<uses-sdk />" + nl;
				androidManifestContents += "	<uses-feature android:glEsVersion=\"0x00020000\" android:required=\"true\" />" + nl;
				for permission in self.android_config['permissions']:
					androidManifestContents += "	<uses-permission android:name=\"android.permission." + permission + "\" />" + nl;
				if ('BILLING' in self.android_config['permissions']):
					androidManifestContents += "	<uses-permission android:name=\"com.android.vending.BILLING\" />" + nl;

				androidManifestContents += "	<application" + nl;

				if self.ouya == True or self.firetv == True:
					androidManifestContents += "		android:icon=\"@drawable/app_icon\" " + nl;
					androidManifestContents += "		android:label=\"@string/application_name\" " + nl;
				else:
					androidManifestContents += "		android:icon=\"@drawable/ic_launcher\" " + nl;
					androidManifestContents += "		android:label=\"@string/application_name\" " + nl;

				androidManifestContents += "		android:name=\"" + self.game_class_name + "Application\" " + nl;
				androidManifestContents += ">" + nl;
				#androidManifestContents += "		android:debuggable=\"true\"> " + nl;

				#game services
				#if "game_services" in self.android_config:
				#	if (self.android_config['game_services']['use']):
				#		androidManifestContents += "	<meta-data android:name=\"com.google.android.gms.games.APP_ID\" android:value=\"@string/app_id\" />" + nl;
				androidManifestContents += "	<meta-data android:name=\"com.google.android.gms.games.APP_ID\" android:value=\"@string/app_id\" />" + nl;

				if (self.firetv):
					androidManifestContents += "	<activity android:name=\"com.amazon.ags.html5.overlay.GameCircleUserInterface\" android:theme=\"@style/GCOverlay\" android:hardwareAccelerated=\"false\"></activity>" + nl;
					androidManifestContents += "	<activity " + nl;
					androidManifestContents += "		android:name=\"com.amazon.identity.auth.device.authorization.AuthorizationActivity\" " + nl;
					androidManifestContents += "		android:theme=\"@android:style/Theme.NoDisplay\" " + nl;
					androidManifestContents += "		android:allowTaskReparenting=\"true\" " + nl;
					androidManifestContents += "		android:launchMode=\"singleTask\">" + nl;
					androidManifestContents += "		<intent-filter>" + nl;
					androidManifestContents += "			<action android:name=\"android.intent.action.VIEW\" /> " + nl;
					androidManifestContents += "			<category android:name=\"android.intent.category.DEFAULT\" /> " + nl;
					androidManifestContents += "			<category android:name=\"android.intent.category.BROWSABLE\" /> " + nl;
					androidManifestContents += "			<data android:host=\"" + javaPackageName + "\" android:scheme=\"amzn\" /> " + nl;
					androidManifestContents += "		</intent-filter> " + nl;
					androidManifestContents += "	</activity> " + nl;
					androidManifestContents += "	<activity android:name=\"com.amazon.ags.html5.overlay.GameCircleAlertUserInterface\" " + nl;
					androidManifestContents += "		android:theme=\"@style/GCAlert\" " + nl;
					androidManifestContents += "		android:hardwareAccelerated=\"false\"></activity> " + nl;
					androidManifestContents += "	<receiver " + nl;
					androidManifestContents += "		android:name=\"com.amazon.identity.auth.device.authorization.PackageIntentReceiver\" " + nl;
					androidManifestContents += "		android:enabled=\"true\"> " + nl;
					androidManifestContents += "		<intent-filter> " + nl;
					androidManifestContents += "			<action android:name=\"android.intent.action.PACKAGE_INSTALL\" /> " + nl;
					androidManifestContents += "			<action android:name=\"android.intent.action.PACKAGE_ADDED\" /> " + nl;
					androidManifestContents += "			<data android:scheme=\"package\" /> " + nl;
					androidManifestContents += "		</intent-filter> " + nl;
					androidManifestContents += "	</receiver>";

				androidManifestContents += "		<activity" + nl;
				androidManifestContents += "			android:name=\"." + self.game_class_name + "Activity\" " + nl;
				androidManifestContents += "			android:label=\"@string/application_name\" " + nl;
				if self.firetv == True:
					androidManifestContents += "			android:configChanges=\"keyboard|keyboardHidden|navigation\" " + nl;
				else:
					androidManifestContents += "			android:configChanges=\"orientation|keyboardHidden\" " + nl;
				androidManifestContents += "			android:theme=\"@android:style/Theme.NoTitleBar.Fullscreen\"> " + nl;
				androidManifestContents += "			<intent-filter>" + nl;
				androidManifestContents += "				<action android:name=\"android.intent.action.MAIN\" /> " + nl;
				androidManifestContents += "				<category android:name=\"android.intent.category.LAUNCHER\" /> " + nl;

				if self.ouya == True:
					androidManifestContents += "				<category android:name=\"tv.ouya.intent.category.GAME\" /> " + nl;

				androidManifestContents += "			</intent-filter>" + nl;
				androidManifestContents += "		</activity>" + nl;

				if "ironsource" in self.android_config:
					androidManifestContents += "<meta-data android:name=\"com.google.android.gms.version\" android:value=\"@integer/google_play_services_version\" />" + nl;

					androidManifestContents += "<activity " + nl;
					androidManifestContents += " 	android:name=\"com.supersonicads.sdk.controller.ControllerActivity\" " + nl
					androidManifestContents += " 	android:configChanges=\"orientation|screenSize\" " + nl
					androidManifestContents += " 	android:hardwareAccelerated=\"true\" /> " + nl
					androidManifestContents += " <activity " + nl
					androidManifestContents += " 	android:name=\"com.supersonicads.sdk.controller.InterstitialActivity\" " + nl
					androidManifestContents += " 	android:configChanges=\"orientation|screenSize\" " + nl
					androidManifestContents += " 	android:hardwareAccelerated=\"true\" " + nl
					androidManifestContents += " 	android:theme=\"@android:style/Theme.Translucent\" /> " + nl
					androidManifestContents += " <activity " + nl
					androidManifestContents += " 	android:name=\"com.supersonicads.sdk.controller.OpenUrlActivity\" " + nl
					androidManifestContents += " 	android:configChanges=\"orientation|screenSize\" " + nl
					androidManifestContents += " 	android:hardwareAccelerated=\"true\" " + nl
					androidManifestContents += " 	android:theme=\"@android:style/Theme.Translucent\" />" + nl

				androidManifestContents += "	</application>" + nl;
				androidManifestContents += "</manifest>" + nl;
				f = open( project_manifest_dir + "/AndroidManifest.xml", "w");
				f.write(androidManifestContents);
				f.close();
				androidManifestPath = project_manifest_dir + "/AndroidManifest.xml";

			# ...
			ic_launcher_name = "ic_launcher.png";
			if self.ouya == True or self.firetv == True:
				ic_launcher_name = "app_icon.png";

			print("copying icon in to eclipse project: ");
			if ("icon" in self.android_config):
				if not self.android_config['icon']['use_master_icon']:
					icon_xxxhdpi = self.android_config['icon']['xxxhdpi'];
					icon_xxhdpi = self.android_config['icon']['xxhdpi'];
					icon_xhdpi = self.android_config['icon']['xhdpi'];
					icon_hdpi = self.android_config['icon']['hdpi'];
					icon_mdpi = self.android_config['icon']['mdpi'];
					icon_nodpi = self.android_config['icon']['nodpi'];

					icon_xxxhdpi = util.str_replace(icon_xxxhdpi, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir)]);
					icon_xxhdpi = util.str_replace(icon_xxhdpi, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir)]);
					icon_xhdpi = util.str_replace(icon_xhdpi, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir)]);
					icon_hdpi = util.str_replace(icon_hdpi, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir)]);
					icon_mdpi = util.str_replace(icon_mdpi, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir)]);
					icon_nodpi = util.str_replace(icon_nodpi, [("%PREPRODUCTION_DIR%", self.game_preproduction_dir)]);

					#subprocess.call(['cp ' + icon_xxhdpi + " " + rootPath+"/build/android/project-eclipse/res/drawable-xxhdpi/ic_launcher.png"], shell=True);
					#subprocess.call(['cp ' + icon_xhdpi + " " + rootPath+"/build/android/project-eclipse/res/drawable-xhdpi/ic_launcher.png"], shell=True);
					#subprocess.call(['cp ' + icon_hdpi + " " + rootPath+"/build/android/project-eclipse/res/drawable-hdpi/ic_launcher.png"], shell=True);
					#subprocess.call(['cp ' + icon_mdpi + " " + rootPath+"/build/android/project-eclipse/res/drawable-mdpi/ic_launcher.png"], shell=True);
					#subprocess.call(['cp ' + icon_nodpi + " " + rootPath+"/build/android/project-eclipse/res/drawable/ic_launcher.png"], shell=True);

					shutil.copy2(icon_xxxhdpi, project_res_dir + self.ds + "drawable-xxxhdpi" + self.ds + ic_launcher_name);
					shutil.copy2(icon_xxhdpi, project_res_dir + self.ds + "drawable-xxhdpi" + self.ds + ic_launcher_name);
					shutil.copy2(icon_xhdpi, project_res_dir + self.ds + "drawable-xhdpi" + self.ds + ic_launcher_name);
					shutil.copy2(icon_hdpi, project_res_dir + self.ds + "drawable-hdpi" + self.ds + ic_launcher_name);
					shutil.copy2(icon_mdpi, project_res_dir + self.ds + "drawable-mdpi" + self.ds + ic_launcher_name);
					shutil.copy2(icon_nodpi, project_res_dir + self.ds + "drawable" + self.ds + ic_launcher_name);

				else:
					if (self.android_config['icon']['icon'] != ''):
						icon_expanded = util.str_replace(self.android_config['icon']['icon'], self.tag_replacements);
						subprocess.call(['cp ' + icon_expanded + " " + project_res_dir + "/drawable/" + ic_launcher_name], shell=True);
					#else:
					#	subprocess.call(['cp ' + self.ark2d_dir + "/__preproduction/icon/512.png " + rootPath+"/build/android/project-eclipse/res/drawable/ic_launcher.png"], shell=True);


			# adding default libs & library projects
			self.android_config['ark_libs'] = [];
			if (android_projectType == 'eclipse'):
				self.android_config['ark_libs'].extend([self.ark2d_dir + "/lib/android/libs/android-support-v4.jar"]);
				self.android_config['ark_libs'].extend([self.ark2d_dir + "/lib/android/libs/libGoogleAnalyticsV2.jar"]);


			self.android_config['ark_library_projects'] = [];
			temp_library_projects = [];
			if (android_projectType == 'eclipse'):
				temp_library_projects.extend([self.ark2d_dir + "/lib/android/library_projects/play_licensing/library"]);
				temp_library_projects.extend([self.ark2d_dir + "/lib/android/library_projects/play_services"]);

			if (self.firetv == True):
				temp_library_projects.extend([self.ark2d_dir + "/lib/android/library_projects/GameCircleSDK"]);

			# we need the relative path stupidly. :/
			# count number of forward slashes in project path and in ark2d path and then we have
			#  the difference number of ../s
			#count_slashes_in_ark2d = self.ark2d_dir.count(self.ds);
			#count_slashes_in_project = rootPath.count(self.ds);
			for library_project in temp_library_projects:
				this_path = "../../../" + os.path.relpath(library_project, rootPath);
				print(this_path);
				self.android_config['ark_library_projects'].extend([this_path]);
				#this_library_project = "../../../";
				#for each_slash in range(count_slashes_in_project - count_slashes_in_ark2d)
				#	this_library_project += "../";

			#print("AHAHA");
			#return;

			#config['android']['ark_library_projects']


			if (android_projectType == 'eclipse'):
				print("------");
				print("Copying libs to eclipse project...");
				#if ("libs" in self.android_config):
				if (len(self.android_libs) > 0):
					for lib in self.android_libs: #config['libs']:
						libf = lib[lib.rfind(self.ds)+1:len(lib)];
						print("	copying " + lib + " in to project as " + libf + "...");

						#subprocess.call(['cp ' + rootPath + "/" + lib + " " + rootPath+"/build/android/project-eclipse/libs/" + libf], shell=True);
						shutil.copy2(lib, rootPath + self.ds + "build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "libs" + self.ds + libf);

				print("------");
				print("Copying ark libs to eclipse project...")
				for lib in self.android_config['ark_libs']:
					libf = lib[lib.rfind(self.ds)+1:len(lib)];
					print("	copying " + lib + " in to project as " + libf + "...");
					shutil.copy2(lib, rootPath + self.ds + "build" + self.ds + self.output + self.ds + "project-eclipse" + self.ds + "libs" + self.ds + libf);

				print("------");
				print("generating eclipse project.properties");
				projectPropertiesContents = "";

				if (self.firetv):
					projectPropertiesContents += "target=Amazon.com:Amazon Fire TV SDK Addon:17";
				else:
					projectPropertiesContents += "target=" + appplatform;

				library_project_count = 1;

				if len(self.android_libraryprojects) > 0:
					projectPropertiesContents += nl;
					for library_project in self.android_libraryprojects: #android_config['library_projects']:
						projectPropertiesContents += "android.library.reference." + str(library_project_count) + "=../../../" + library_project;
						projectPropertiesContents += nl;
						library_project_count += 1;

				if "ark_library_projects" in self.android_config:
					projectPropertiesContents += nl;
					for library_project in self.android_config['ark_library_projects']:
						projectPropertiesContents += "android.library.reference." + str(library_project_count) + "=" + library_project;
						projectPropertiesContents += nl;
						library_project_count += 1;


				f = open(rootPath+"/build/" + self.output + "/project-eclipse/project.properties", "w");
				f.write(projectPropertiesContents);
				f.close();

				#generate project .classpath file
				print("------");
				print("create project .classpath file");
				androidProjectClasspathContents = "";
				androidProjectClasspathContents += "<?xml version=\"1.0\" encoding=\"UTF-8\"?> " + nl;
				androidProjectClasspathContents += "<classpath> " + nl;
				androidProjectClasspathContents += "	<classpathentry kind=\"src\" path=\"src\"/> " + nl;
				androidProjectClasspathContents += "	<classpathentry kind=\"src\" path=\"gen\"/> " + nl;
				androidProjectClasspathContents += "	<classpathentry kind=\"con\" path=\"com.android.ide.eclipse.adt.ANDROID_FRAMEWORK\"/> " + nl;
				androidProjectClasspathContents += "	<classpathentry exported=\"true\" kind=\"con\" path=\"com.android.ide.eclipse.adt.LIBRARIES\"/> " + nl;
				androidProjectClasspathContents += " 	<classpathentry kind=\"con\" path=\"com.android.ide.eclipse.adt.DEPENDENCIES\" /> ";

				if ("libs" in self.android_config):
					for lib in self.android_libs: #_config['libs']:
						libf = lib[lib.rfind(self.ds)+1:len(lib)];
						androidProjectClasspathContents += "<classpathentry exported=\"true\" kind=\"lib\" path=\"libs/" + libf + "\"/>" + nl;

				if ("ark_libs" in self.android_config):
					for lib in self.android_config['ark_libs']:
						libf = lib[lib.rfind(self.ds)+1:len(lib)];
						androidProjectClasspathContents += "<classpathentry exported=\"true\" kind=\"lib\" path=\"libs/" + libf + "\"/>" + nl;

				# force ouya-sdk lib into classpath
				if self.ouya == True:
					androidProjectClasspathContents += "<classpathentry exported=\"true\" kind=\"lib\" path=\"libs/ouya-sdk.jar\"/>" + nl;

				androidProjectClasspathContents += "	<classpathentry kind=\"output\" path=\"bin/classes\"/> " + nl;
				androidProjectClasspathContents += "</classpath> " + nl;
				f = open(rootPath+"/build/"+ self.output + "/project-eclipse/.classpath", "w");
				f.write(androidProjectClasspathContents);
				f.close();

			#
			# generate ids.xml
			#
			print("------");
			print("create ids.xml");
			if "override_ids" in self.android_config:
				print("using custom ids.xml");
				androidIdsPath = self.android_config['override_ids'];
				subprocess.call(['cp ' + androidIdsPath + " " + project_res_dir + "/values/ids.xml"], shell=True);
				#todo: copy this to rootPath+"/build/android/project-eclipse/res/values/ids.xml";
			else:
				print("generating default ids.xml");

				androidStringsXmlContents = "";
				androidStringsXmlContents += "<?xml version=\"1.0\" encoding=\"utf-8\"?>" + nl;
				androidStringsXmlContents += "<resources>" + nl;
				androidStringsXmlContents += "	<string name=\"app_id\">";

				didgameservices = False;
				if "game_services" in self.android_config:
					if (self.android_config['game_services']['use']):
						androidStringsXmlContents += str(self.android_config['game_services']['app_id']);
						didgameservices = True;

				if (didgameservices == False):
					androidStringsXmlContents += "1";

				androidStringsXmlContents += "</string>" + nl;
				androidStringsXmlContents += "	<string name=\"achievement_id_test\">1</string>" + nl;
				androidStringsXmlContents += "</resources>" + nl;
				f = open(project_res_dir + "/values/ids.xml", "w");
				f.write(androidStringsXmlContents);
				f.close();

			#
			# generate strings.xml
			#
			print("------");
			print("create strings.xml");
			if "override_strings" in self.android_config:
				print("using custom strings.xml");
				androidStringsPath = self.android_config['override_strings'];
				subprocess.call(['cp ' + androidStringsPath + " " + project_res_dir + "/values/strings.xml"], shell=True);
				#todo: copy this to rootPath+"/build/android/project-eclipse/res/values/ids.xml";

			else:
				game_name_forstrings = self.game_name.replace("'", "\\'");
				game_description_forstrings = self.game_description.replace("'", "\\'").replace("-", ":");
				androidStringsXmlContents = "";
				androidStringsXmlContents += "<?xml version=\"1.0\" encoding=\"utf-8\"?>" + nl;
				androidStringsXmlContents += "<resources>" + nl;
				androidStringsXmlContents += "	<string name=\"application_name\">" + game_name_forstrings + "</string>" + nl;
				androidStringsXmlContents += "	<string name=\"application_description\">" + game_description_forstrings + "</string>" + nl;
				androidStringsXmlContents += "	<string name=\"gamehelper_sign_in_failed\">Failed to sign in. Please check your network connection and try again.</string>" + nl;
				androidStringsXmlContents += "	<string name=\"gamehelper_app_misconfigured\">The application is incorrectly configured. Check that the package name and signing certificate match the client ID created in Developer Console. Also, if the application is not yet published, check that the account you are trying to sign in with is listed as a tester account. See logs for more information.</string>" + nl;
				androidStringsXmlContents += "	<string name=\"gamehelper_license_failed\">License check failed.</string>" + nl;
				androidStringsXmlContents += "	<string name=\"gamehelper_unknown_error\">Unknown error.</string>" + nl;
				androidStringsXmlContents += "</resources>" + nl;
				f = open(project_res_dir +  "/values/strings.xml", "w");
				f.write(androidStringsXmlContents);
				f.close();

			#
			# more intellij/gradle files
			#
			if (android_projectType == 'intellij'):
				# write build.gradle
				f = open(intellij_template_folder + self.ds + "game" + self.ds + "build.gradle", "r");
				fcontents = f.read(); f.close();
				fcontents = util.str_replace(fcontents, editsStrReplace);
				fcontents = util.str_replace(fcontents, editsOneSignal);
				fcontents = util.str_replace(fcontents, editsIronsource);
				fcontents = util.str_replace(fcontents, editsGoogleAnalytics);
				fcontents = util.str_replace(fcontents, [("%ADDITIONAL_JAR_FILES%", edits_shared_libraries_gradlejars)]);
				fcontents = util.str_replace(fcontents, [("%ADDITIONAL_MODULES%", edits_shared_libraries_modules)]);
				f = open(intellij_folder + self.ds + self.game_name_safe + self.ds + "build.gradle", "w");
				f.write(fcontents);
				f.close();

				#write nine.iml file
				f = open(intellij_template_folder + self.ds + "game" + self.ds + "game.iml", "r");
				fcontents = f.read(); f.close();
				fcontents = util.str_replace(fcontents, editsStrReplace);
				f = open(intellij_folder + self.ds + self.game_name_safe + self.ds + self.game_name_safe + ".iml", "w");
				f.write(fcontents);
				f.close();

			#
			# copy sample game java files...
			#
			fgamefile = "";
			fgamecontents = "";
			try:
				print("using custom GameActivity.java");
				fgamefile = self.android_config['override_activity'];

			except:
				print("using default (generated) GameActivity.java");
				fgamefile = self.ark2d_dir + "/lib/android/GameActivity.java";
				pass;

			f = open(fgamefile, "r");
			fgamecontents = f.read(); f.close(); #fgamecontents = fgamecontents.decode("utf8");
			fgamecontents = util.str_replace(fgamecontents, editsStrReplace);
			fgamecontents = util.str_replace(fgamecontents, editsOldAndroid23);
			fgamecontents = util.str_replace(fgamecontents, editsGameServices);
			fgamecontents = util.str_replace(fgamecontents, editsInAppBilling);
			fgamecontents = util.str_replace(fgamecontents, editsOuya);
			fgamecontents = util.str_replace(fgamecontents, editsFireTV);
			fgamecontents = util.str_replace(fgamecontents, editsOneSignal);
			fgamecontents = util.str_replace(fgamecontents, editsIronsource);
			fgamecontents = util.str_replace(fgamecontents, editsGoogleAnalytics);
			f = open(project_src_dir + self.ds + self.game_class_name + "Activity.java", "w");
			f.write(fgamecontents);
			f.close();

			f = open(self.ark2d_dir + "/lib/android/GameApplication.java", "r");
			fgamecontents = f.read(); f.close(); #fgamecontents = fgamecontents.decode("utf8");
			fgamecontents = util.str_replace(fgamecontents, editsStrReplace);
			fgamecontents = util.str_replace(fgamecontents, editsOldAndroid23);
			fgamecontents = util.str_replace(fgamecontents, editsGameServices);
			fgamecontents = util.str_replace(fgamecontents, editsInAppBilling);
			fgamecontents = util.str_replace(fgamecontents, editsOuya);
			fgamecontents = util.str_replace(fgamecontents, editsFireTV);
			fgamecontents = util.str_replace(fgamecontents, editsOneSignal);
			fgamecontents = util.str_replace(fgamecontents, editsIronsource);
			fgamecontents = util.str_replace(fgamecontents, editsGoogleAnalytics);
			f = open(project_src_dir + self.ds + self.game_class_name + "Application.java", "w");
			f.write(fgamecontents);
			f.close();

			if "googleanalytics" in self.android_config:
				analyticsContents = "<?xml version=\"1.0\" encoding=\"utf-8\" ?>" + nl;
				analyticsContents += "<resources>";
				analyticsContents += "	<!--Replace placeholder ID with your tracking ID-->";
				analyticsContents += "	<string name=\"ga_trackingId\">" + self.android_config['googleanalytics']['tracking_id'] + "</string>";
				analyticsContents += "	<!--Enable automatic activity tracking-->";
				analyticsContents += "	<bool name=\"ga_autoActivityTracking\">true</bool>";
				analyticsContents += "	<!--Enable automatic exception tracking-->";
				analyticsContents += "	<bool name=\"ga_reportUncaughtExceptions\">true</bool>";
				analyticsContents += "</resources>";
				f = open(intellij_folder + self.ds + self.game_name_safe + self.ds + "src" + self.ds + "main" + self.ds + "res" + self.ds + "xml" + self.ds + "analytics.xml", "w");
				f.write(analyticsContents);
				f.close();

			# if not overriding
			if "override_activity" not in self.android_config:
				#ARK Game Helper
				print("using GameHelper.java, BaseGameActivity.java, etc.");

				base_classes = [
					'BaseGameActivity.java',
					'BaseGameUtils.java',
					'GameHelper.java',
					'GameHelperUtils.java'
				];
				if (self.android_billing):
					base_classes.extend([
						'iab_util/Base64.java',
						'iab_util/Base64DecoderException.java',
						'iab_util/IabException.java',
						'iab_util/IabHelper.java',
						'iab_util/IabResult.java',
						'iab_util/Inventory.java',
						'iab_util/Purchase.java',
						'iab_util/Security.java',
						'iab_util/SkuDetails.java'
					]);

				for jfile in base_classes:
					f = open(self.ark2d_dir + "/lib/android/" + jfile, "r");
					fgamecontents = f.read(); f.close();
					fgamecontents = util.str_replace(fgamecontents, editsStrReplace);
					fgamecontents = util.str_replace(fgamecontents, editsOldAndroid23);
					fgamecontents = util.str_replace(fgamecontents, editsGameServices);
					fgamecontents = util.str_replace(fgamecontents, editsInAppBilling);
					fgamecontents = util.str_replace(fgamecontents, editsOneSignal);
					fgamecontents = util.str_replace(fgamecontents, editsIronsource);
					fgamecontents = util.str_replace(fgamecontents, editsGoogleAnalytics);
					f = open(project_src_dir + self.ds +  jfile, "w");
					f.write(fgamecontents);
					f.close();

				if (android_projectType == 'eclipse'):
					# copy android-support-v4 in.
					f = open(self.ark2d_dir + "/lib/android/libs/android-support-v4.jar", "r");
					fgamecontents = f.read(); f.close();
					f = open(rootPath+"/build/" + self.output + "/project-eclipse/libs/android-support-v4.jar", "w");
					f.write(fgamecontents);
					f.close();


			# additional source files
			print("copying additional source files");
			if "src_files" in self.android_config:
				for src_file in self.android_srcfiles: #config['src_files']:
					f = open(src_file, "r");
					extrasrccontents = f.read();
					f.close();
					extrasrccontents = util.str_replace(extrasrccontents, editsStrReplace);
					extrasrccontents = util.str_replace(extrasrccontents, editsOldAndroid23);


					findex = src_file.rfind('/');
					small_src_file = src_file[findex+1:len(src_file)];
					#newf = src_file[0:findex] + ".o";
					#newfd = src_file[0:findex] + ".d";

					f = open(project_src_dir + self.ds + small_src_file, "w");
					f.write(extrasrccontents);
					f.close();


			#copying library/s in to project.
			print("Copying ark2d and game.so in to project.");
			ds = self.ds;


			#
			# freetype
			#
			print("copying in freetype library");
			"""
			#subprocess.call(["cp -r " +self.ark2d_dir + "/src/ARK2D/vendor/android/freetype/obj/local/armeabi-v7a/ " + rootPath+"/build/android/project-eclipse/libs/armeabi-v7a"], shell=True); #libfreetype
			#subprocess.call(["cp -r " +self.ark2d_dir + "/src/ARK2D/vendor/android/freetype/obj/local/armeabi-v7a/ " + rootPath+"/build/android/project-eclipse/obj/local/armeabi-v7a"], shell=True);
			self.mycopytree(self.ark2d_dir+ds+"src"+ds+"ARK2D"+ds+"vendor"+ds+"android"+ds+"freetype"+ds+"obj"+ds+"local"+ds+"armeabi-v7a", rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"libs"+ds+"armeabi-v7a");
			self.mycopytree(self.ark2d_dir+ds+"src"+ds+"ARK2D"+ds+"vendor"+ds+"android"+ds+"freetype"+ds+"obj"+ds+"local"+ds+"armeabi-v7a", rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"obj"+ds+"local"+ds+"armeabi-v7a");
			if (not self.debug):
				#subprocess.call(["cp -r " +self.ark2d_dir + "/src/ARK2D/vendor/android/freetype/obj/local/armeabi/ " + rootPath+"/build/android/project-eclipse/libs/armeabi"], shell=True); #libfreetype
				#subprocess.call(["cp -r " +self.ark2d_dir + "/src/ARK2D/vendor/android/freetype/obj/local/armeabi/ " + rootPath+"/build/android/project-eclipse/obj/local/armeabi"], shell=True);
				self.mycopytree(self.ark2d_dir+ds+"src"+ds+"ARK2D"+ds+"vendor"+ds+"android"+ds+"freetype"+ds+"obj"+ds+"local"+ds+"armeabi", rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"libs"+ds+"armeabi");
				self.mycopytree(self.ark2d_dir+ds+"src"+ds+"ARK2D"+ds+"vendor"+ds+"android"+ds+"freetype"+ds+"obj"+ds+"local"+ds+"armeabi", rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"obj"+ds+"local"+ds+"armeabi");
			"""

			vendor_android = self.ark2d_dir+ds+"src"+ds+"ARK2D"+ds+"vendor"+ds+"android";

			#
			# openal
			#
			print("copying in openal library");
			self.mycopytree(vendor_android+ds+"openal"+ds+"libs"+ds+"armeabi-v7a", project_nlib_dir+ds+"armeabi-v7a");
			if (not self.debug):
				self.mycopytree(vendor_android+ds+"openal"+ds+"libs"+ds+"armeabi", project_nlib_dir+ds+"armeabi");
				self.mycopytree(vendor_android+ds+"openal"+ds+"libs"+ds+"x86", project_nlib_dir+ds+"x86");

			#
			# libzip
			#
			print("copying in libzip library");
			self.mycopytree(vendor_android+ds+"libzip"+ds+"libs"+ds+"armeabi-v7a", project_nlib_dir+ds+"armeabi-v7a");
			if (not self.debug):
				self.mycopytree(vendor_android+ds+"libzip"+ds+"libs"+ds+"armeabi", project_nlib_dir+ds+"armeabi");
				self.mycopytree(vendor_android+ds+"libzip"+ds+"libs"+ds+"x86", project_nlib_dir+ds+"x86");

			#
			# libangelscript
			#
			print("copying in libangelscript library");
			self.mycopytree(vendor_android+ds+"angelscript"+ds+"libs"+ds+"armeabi-v7a", project_nlib_dir+ds+"armeabi-v7a");
			if (not self.debug):
				self.mycopytree(vendor_android+ds+"angelscript"+ds+"libs"+ds+"armeabi", project_nlib_dir+ds+"armeabi");
				self.mycopytree(vendor_android+ds+"angelscript"+ds+"libs"+ds+"x86", project_nlib_dir+ds+"x86");

			# extra obj/locals for eclipse. are these debug libs?
			if (android_projectType == 'eclipse'):
				self.mycopytree(vendor_android+ds+"openal"+ds+"libs"+ds+"armeabi-v7a", rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"obj"+ds+"local"+ds+"armeabi-v7a");
				self.mycopytree(vendor_android+ds+"libzip"+ds+"libs"+ds+"armeabi-v7a", rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"obj"+ds+"local"+ds+"armeabi-v7a");
				self.mycopytree(vendor_android+ds+"angelscript"+ds+"libs"+ds+"armeabi-v7a", rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"obj"+ds+"local"+ds+"armeabi-v7a");

				if (not self.debug):
					self.mycopytree(vendor_android+ds+"openal"+ds+"libs"+ds+"armeabi", rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"obj"+ds+"local"+ds+"armeabi");
					self.mycopytree(vendor_android+ds+"openal"+ds+"libs"+ds+"x86", 	   rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"obj"+ds+"local"+ds+"x86");
					self.mycopytree(vendor_android+ds+"libzip"+ds+"libs"+ds+"armeabi", rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"obj"+ds+"local"+ds+"armeabi");
					self.mycopytree(vendor_android+ds+"libzip"+ds+"libs"+ds+"x86", 	   rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"obj"+ds+"local"+ds+"x86");
					self.mycopytree(vendor_android+ds+"angelscript"+ds+"libs"+ds+"armeabi", rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"obj"+ds+"local"+ds+"armeabi");
					self.mycopytree(vendor_android+ds+"angelscript"+ds+"libs"+ds+"x86", rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"obj"+ds+"local"+ds+"x86");

			#
			# custom libraries e.g. fmod, spine...
			#
			print("copying in custom libraries");
			if "native_libraries" in self.android_config:
				for gamelibrary in self.android_config['native_libraries']:
					gamelibraryname = gamelibrary['name'];

					print("copying in " + gamelibraryname + " library");
					shutil.copy(self.game_dir+ds+gamelibrary['armeabi-v7a'], project_nlib_dir+ds+"armeabi-v7a");
					if (not self.debug and "armeabi" in gamelibrary):
						shutil.copy(self.game_dir+ds+gamelibrary['armeabi'], project_nlib_dir+ds+"armeabi");

					if (not self.debug and "x86" in gamelibrary):
						shutil.copy(self.game_dir+ds+gamelibrary['x86'], project_nlib_dir+ds+"x86");


					if (android_projectType == 'eclipse'):
						shutil.copy(self.game_dir+ds+gamelibrary['armeabi-v7a'], rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"obj"+ds+"local"+ds+"armeabi-v7a");
						if (not self.debug and "armeabi" in gamelibrary):
							shutil.copy(self.game_dir+ds+gamelibrary['armeabi'], rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"obj"+ds+"local"+ds+"armeabi");
						if (not self.debug and "x86" in gamelibrary):
							shutil.copy(self.game_dir+ds+gamelibrary['x86'], rootPath+ds+"build"+ds+self.output+ds+"project-eclipse"+ds+"obj"+ds+"local"+ds+"x86");


			#
			# ark2d
			#
			print("copying in ark2d libraries");
			#ark2d_built_libs = self.ark2d_dir+self.ds+"build"+self.ds+"android"+self.ds+"libs";
			ark2d_built_libs = self.ark2d_dir+self.ds+"build"+self.ds+"android"+self.ds+"local";
			self.mycopytree(ark2d_built_libs+self.ds+"armeabi-v7a", project_nlib_dir+self.ds+"armeabi-v7a");
			if (not self.debug):
				self.mycopytree(ark2d_built_libs+self.ds+"armeabi", project_nlib_dir+self.ds+"armeabi");
				self.mycopytree(ark2d_built_libs+self.ds+"x86", project_nlib_dir+self.ds+"x86");

			if (android_projectType == 'eclipse'):
				self.mycopytree(ark2d_built_libs+self.ds+"armeabi-v7a", rootPath+self.ds+"build"+self.ds+self.output+self.ds+"project-eclipse"+self.ds+"obj"+self.ds+"local"+self.ds+"armeabi-v7a");
				if (not self.debug):
					self.mycopytree(ark2d_built_libs+self.ds+"armeabi", rootPath+self.ds+"build"+self.ds+self.output+self.ds+"project-eclipse"+self.ds+"obj"+self.ds+"local"+self.ds+"armeabi");
					self.mycopytree(ark2d_built_libs+self.ds+"x86", rootPath+self.ds+"build"+self.ds+self.output+self.ds+"project-eclipse"+self.ds+"obj"+self.ds+"local"+self.ds+"x86");
			elif (android_projectType == "intellij"):
				self.mycopytree(ark2d_built_libs+self.ds+"armeabi-v7a", rootPath+self.ds+"build"+self.ds+self.output+self.ds+"project-intellij"+self.ds+self.game_name_safe+self.ds+"src"+self.ds+"main"+self.ds+"jniLibs"+self.ds+"armeabi-v7a");
				if (not self.debug):
					self.mycopytree(ark2d_built_libs+self.ds+"armeabi", rootPath+self.ds+"build"+self.ds+self.output+self.ds+"project-intellij"+self.ds+self.game_name_safe+self.ds+"src"+self.ds+"main"+self.ds+"jniLibs"+self.ds+"armeabi");
					self.mycopytree(ark2d_built_libs+self.ds+"x86",     rootPath+self.ds+"build"+self.ds+self.output+self.ds+"project-intellij"+self.ds+self.game_name_safe+self.ds+"src"+self.ds+"main"+self.ds+"jniLibs"+self.ds+"x86");

			#
			# ark2d (local)
			#
			print("copying in ark2d libraries (local)");
			self.mycopytree(rootPath+self.ds+"build"+self.ds+self.output+self.ds+"local"+self.ds+"armeabi-v7a", project_nlib_dir+self.ds+"armeabi-v7a");
			if (not self.debug):
				self.mycopytree(rootPath+self.ds+"build"+self.ds+self.output+self.ds+"local"+self.ds+"armeabi", project_nlib_dir+self.ds+"armeabi");
				self.mycopytree(rootPath+self.ds+"build"+self.ds+self.output+self.ds+"local"+self.ds+"x86", project_nlib_dir+self.ds+"x86");

			if (android_projectType == 'eclipse'):
				self.mycopytree(rootPath+self.ds+"build"+self.ds+self.output+self.ds+"local"+self.ds+"armeabi-v7a", rootPath+self.ds+"build"+self.ds+self.output+self.ds+"project-eclipse"+self.ds+"obj"+self.ds+"local"+self.ds+"armeabi-v7a");
				if (not self.debug):
					self.mycopytree(rootPath+self.ds+"build"+self.ds+self.output+self.ds+"local"+self.ds+"armeabi", rootPath+self.ds+"build"+self.ds+self.output+self.ds+"project-eclipse"+self.ds+"obj"+self.ds+"local"+self.ds+"armeabi");
					self.mycopytree(rootPath+self.ds+"build"+self.ds+self.output+self.ds+"local"+self.ds+"x86", rootPath+self.ds+"build"+self.ds+self.output+self.ds+"project-eclipse"+self.ds+"obj"+self.ds+"local"+self.ds+"x86");

			#
			# copying ark2d resources in to assets folder.
			#
			#subprocess.call(["cp -r " +self.ark2d_dir + "/data/ " + rootPath+"/build/android/project-eclipse/assets/ark2d"], shell=True);
			print("copying in ark2d resources");
			self.mycopytree(self.ark2d_dir + self.ds + "data", project_assets_dir + self.ds + "ark2d");

			#
			# remove obj files
			#
			if (android_projectType == 'intellij'):
				self.rmdir_recursive(project_nlib_dir + self.ds + "armeabi-v7a" + self.ds + "objs");
				if (not self.debug):
					self.rmdir_recursive(project_nlib_dir + self.ds + "armeabi" + self.ds + "objs");
					self.rmdir_recursive(project_nlib_dir + self.ds + "x86" + self.ds + "objs");

			#print("removing temp libs dir?");
			try:
				self.rmdir_recursive(libsdir);
			except:
				print("could not remove libsdir. this probably means compilation failed.");
				exit(0);

		elif (self.building_library):

			f = open(self.ark2d_dir + self.ds + "config.json", "r");
			fcontents = f.read();
			f.close();
			config = json.loads(fcontents);

			ndkdir = config[self.platformOn]['android']['ndk_dir'];

			"""
			#copy stuff in vendor to ndk directory.
			#freetype
			print("copying vendor headers (freetype)");
			#copyfreetype1 = 'cp -r ' + ndkprojectpath + '/src/ARK2D/vendor/android/freetype/jni/include ' + ndkdir + "/platforms/"+ndkappplatform+"/arch-arm/usr/";
			#copyfreetype2 = 'cp -r ' + ndkprojectpath + '/src/ARK2D/vendor/android/freetype/jni/include ' + ndkdir + "/platforms/"+ndkappplatform+"/arch-x86/usr/";
			#subprocess.call([copyfreetype1], shell=True);
			#subprocess.call([copyfreetype2], shell=True);
			self.mycopytree(ndkprojectpath + self.ds + 'src' + self.ds + 'ARK2D' + self.ds + 'vendor' + self.ds + 'android' + self.ds + 'freetype' + self.ds + 'jni' + self.ds + 'include', self.android_ndkdir + self.ds + "platforms"+self.ds + ndkappplatform+self.ds+"arch-arm" + self.ds + "usr" + self.ds + "include");
			self.mycopytree(ndkprojectpath + self.ds + 'src' + self.ds + 'ARK2D' + self.ds + 'vendor' + self.ds + 'android' + self.ds + 'freetype' + self.ds + 'jni' + self.ds + 'include', self.android_ndkdir + self.ds + "platforms"+self.ds + ndkappplatform+self.ds+"arch-x86" + self.ds + "usr" + self.ds + "include");

	"""
			# full rebuild with logs...:
			# -B NDK_LOG=1
			print("Compiling vendor sources (freetype)");
			libfreetypedir = ndkprojectpath + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "android" + self.ds + "freetype";
			compilefreetype1 = self.android_ndkdir + self.ds + "ndk-build NDK_PROJECT_PATH=" + libfreetypedir +" APP_PROJECT_PATH=" + libfreetypedir + " APP_BUILD_SCRIPT=" + libfreetypedir + self.ds + "jni" + self.ds + "Android.mk APP_PLATFORM=" + ndkappplatform;
			print(compilefreetype1);
			subprocess.call([compilefreetype1], shell=True);
			#subprocess.call(['cp -r ' + libfreetypedir + "/obj/local/armeabi-v7a/libfreetype.a " + self.android_ndkdir + "/platforms/"+ndkappplatform+"/arch-arm/usr/lib"], shell=True);
			shutil.copy(libfreetypedir + self.ds + "obj" + self.ds + "local" + self.ds + "armeabi-v7a" + self.ds + "libfreetype.a", self.android_ndkdir + self.ds + "platforms" + self.ds + ndkappplatform+ self.ds + "arch-arm" + self.ds + "usr" + self.ds + "lib" + self.ds);
			shutil.copy(libfreetypedir + self.ds + "obj" + self.ds + "local" + self.ds + "x86" + self.ds + "libfreetype.a", self.android_ndkdir + self.ds + "platforms" + self.ds + ndkappplatform+ self.ds + "arch-x86" + self.ds + "usr" + self.ds + "lib" + self.ds);

			#return;


			#openal
			print("copying vendor headers (openal)");
			#copyopenal1 = 'cp -r ' + ndkprojectpath + '/src/ARK2D/vendor/android/openal/jni/include ' + ndkdir + "/platforms/"+ndkappplatform+"/arch-arm/usr/";
			#copyopenal2 = 'cp -r ' + ndkprojectpath + '/src/ARK2D/vendor/android/openal/jni/include ' + ndkdir + "/platforms/"+ndkappplatform+"/arch-x86/usr/";
			#subprocess.call([copyopenal1], shell=True);
			#subprocess.call([copyopenal2], shell=True);
			self.mycopytree(ndkprojectpath + self.ds + 'src' + self.ds + 'ARK2D' + self.ds + 'vendor' + self.ds + 'android' + self.ds + 'openal' + self.ds + 'jni' + self.ds + 'include', self.android_ndkdir + self.ds + "platforms"+self.ds + ndkappplatform+self.ds+"arch-arm" + self.ds + "usr" + self.ds + "include");
			self.mycopytree(ndkprojectpath + self.ds + 'src' + self.ds + 'ARK2D' + self.ds + 'vendor' + self.ds + 'android' + self.ds + 'openal' + self.ds + 'jni' + self.ds + 'include', self.android_ndkdir + self.ds + "platforms"+self.ds + ndkappplatform+self.ds+"arch-x86" + self.ds + "usr" + self.ds + "include");

			print("Compiling vendor sources (openal)");
			libopenaldir = ndkprojectpath + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "android" + self.ds + "openal";
			compileopenal1 = self.android_ndkdir + self.ds + "ndk-build NDK_PROJECT_PATH=" + libopenaldir +" APP_PROJECT_PATH=" + libopenaldir + " APP_BUILD_SCRIPT=" + libopenaldir + self.ds +"jni" + self.ds + "Android.mk APP_PLATFORM=" + ndkappplatform;
			print(compileopenal1);
			subprocess.call([compileopenal1], shell=True);
			#subprocess.call(['cp -r ' + libopenaldir + "/libs/armeabi-v7a/libopenal.so " + ndkdir + "/platforms/"+ndkappplatform+"/arch-arm/usr/lib"], shell=True);
			#nexus7update subprocess.call(['cp -r ' + libopenaldir + "/libs/armeabi-v7a/libopenal.so " + ndkdir + "/platforms/"+ndkappplatform+"/arch-arm/usr/lib"], shell=True);
			shutil.copy(libopenaldir + self.ds + "libs" + self.ds + "armeabi-v7a" + self.ds + "libopenal.so", self.android_ndkdir + self.ds + "platforms" + self.ds + ndkappplatform+ self.ds + "arch-arm" + self.ds + "usr" + self.ds + "lib" + self.ds);
			shutil.copy(libopenaldir + self.ds + "libs" + self.ds + "x86" + self.ds + "libopenal.so", self.android_ndkdir + self.ds + "platforms" + self.ds + ndkappplatform+ self.ds + "arch-x86" + self.ds + "usr" + self.ds + "lib" + self.ds);

			#openal
			#print("copying vendor headers (libzip)");
			#print("NOT");
			#copyopenal1 = 'cp -r ' + ndkprojectpath + '/src/ARK2D/vendor/android/libzip/jni/zip.h ' + ndkdir + "/platforms/"+ndkappplatform+"/arch-arm/usr/include/";
			#copyopenal2 = 'cp -r ' + ndkprojectpath + '/src/ARK2D/vendor/android/libzip/jni/zip.h ' + ndkdir + "/platforms/"+ndkappplatform+"/arch-x86/usr/include/";
			#subprocess.call([copyopenal1], shell=True);
			#subprocess.call([copyopenal2], shell=True);

			print("Compiling vendor sources (libzip)");
			libzipdir = ndkprojectpath + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "android" + self.ds + "libzip";
			compilelibzip1 = self.android_ndkdir + self.ds + "ndk-build NDK_PROJECT_PATH=" + libzipdir +" APP_PROJECT_PATH=" + libzipdir + " APP_BUILD_SCRIPT=" + libzipdir + self.ds + "jni" + self.ds + "Android.mk APP_PLATFORM=" + ndkappplatform;
			print(compilelibzip1);
			subprocess.call([compilelibzip1], shell=True);
			#subprocess.call(['cp -r ' + libzipdir + "/libs/armeabi-v7a/libzip.so " + ndkdir + "/platforms/"+ndkappplatform+"/arch-arm/usr/lib"], shell=True);
			shutil.copy(libzipdir + self.ds + "libs" + self.ds + "armeabi-v7a" + self.ds + "libzip.so", self.android_ndkdir + self.ds + "platforms" + self.ds + ndkappplatform+ self.ds + "arch-arm" + self.ds + "usr" + self.ds + "lib" + self.ds);
			shutil.copy(libzipdir + self.ds + "libs" + self.ds + "x86" + self.ds + "libzip.so", self.android_ndkdir + self.ds + "platforms" + self.ds + ndkappplatform+ self.ds + "arch-x86" + self.ds + "usr" + self.ds + "lib" + self.ds);

			print("Compiling vendor sources (libangelscript)");
			libangelscriptdir = ndkprojectpath + self.ds + "src" + self.ds + "ARK2D" + self.ds + "vendor" + self.ds + "android" + self.ds + "angelscript";
			compilelibangelscript1 = self.android_ndkdir + self.ds + "ndk-build NDK_PROJECT_PATH=" + libangelscriptdir +" APP_PROJECT_PATH=" + libangelscriptdir + " APP_BUILD_SCRIPT=" + libangelscriptdir + self.ds + "jni" + self.ds + "Android.mk APP_PLATFORM=" + ndkappplatform;
			print(compilelibangelscript1);
			subprocess.call([compilelibangelscript1], shell=True);
			#subprocess.call(['cp -r ' + libangelscriptdir + "/libs/armeabi-v7a/libangelscript.so " + ndkdir + "/platforms/"+ndkappplatform+"/arch-arm/usr/lib"], shell=True);
			shutil.copy(libangelscriptdir + self.ds + "libs" + self.ds + "armeabi-v7a" + self.ds + "libangelscript.so", self.android_ndkdir + self.ds + "platforms" + self.ds + ndkappplatform+ self.ds + "arch-arm" + self.ds + "usr" + self.ds + "lib" + self.ds);
			shutil.copy(libangelscriptdir + self.ds + "libs" + self.ds + "x86" + self.ds + "libangelscript.so", self.android_ndkdir + self.ds + "platforms" + self.ds + ndkappplatform+ self.ds + "arch-x86" + self.ds + "usr" + self.ds + "lib" + self.ds);


			#libcurl
			#print("Compiling vendor sources (libcurl)");
			#libcurldir = ndkprojectpath + "/src/ARK2D/vendor/android/curl-android";
			#compilelibcurl1 = ndkdir + "/ndk-build NDK_PROJECT_PATH=" + libcurldir +" APP_PROJECT_PATH=" + libcurldir + " APP_BUILD_SCRIPT=" + libcurldir + "/Android.mk APP_PLATFORM=" + ndkappplatform;
			#print(compilelibcurl1);
			#subprocess.call([compilelibcurl1], shell=True);
			#subprocess.call(['cp -r ' + libcurldir + "/libs/armeabi/libcurl.so " + ndkdir + "/platforms/"+ndkappplatform+"/arch-arm/usr/lib"], shell=True);


			nl = "\n";
			mds = "/";
			#make android.mk
			print("Creating Android.mk");
			android_make_file = "";
			android_make_file += "LOCAL_PATH := $(call my-dir)/../../" + nl + nl;
			android_make_file += "include $(CLEAR_VARS)" + nl+nl;
			android_make_file += "LOCAL_MODULE    := ark2d" + nl+nl; # Here we give our module name and source file(s)
			#android_make_file += "LOCAL_C_INCLUDES := $(LOCAL_PATH)/../libzip/ $(LOCAL_PATH)/../libpng/" + nl;
			android_make_file += "LOCAL_C_INCLUDES := ";
			android_make_file += "$(LOCAL_PATH)" + mds + "src" + mds + "ARK2D" + mds + "vendor" + mds + "android" + mds + "libzip" + mds + "jni" + mds + " ";
			android_make_file += "$(LOCAL_PATH)/lib/includes ";
			android_make_file += "$(LOCAL_PATH)/src/ARK2D/vendor/spine/includes ";
			android_make_file += "$(LOCAL_PATH)/src/ARK2D/vendor/angelscript ";
			android_make_file += nl;
			#android_make_file += "LOCAL_STATIC_LIBRARIES := libzip libpng" + nl;
			#android_make_file += "LOCAL_C_INCLUDES += external/stlport/stlport" + nl+nl;
			android_make_file += "LOCAL_SHARED_LIBRARIES += libstdc++ " + nl+nl;

			android_make_file += "LOCAL_CFLAGS := -DARK2D_ANDROID ";
			if (self.platformOn == "windows"):
				android_make_file += "-DARK2D_ANDROID_ON_WINDOWS ";
			elif (self.platformOn == "osx"):
				android_make_file += "-DARK2D_ANDROID_ON_MACINTOSH ";

			if (self.ouya == True):
				android_make_file += "-DARK2D_OUYA ";
			if (self.firetv == True):
				android_make_file += "-DARK2D_AMAZON ";

			android_make_file += "-DDISABLE_IMPORTGL -fno-exceptions -fexceptions -Wno-psabi  "; #-fno-rtti
			if (self.debug):
				android_make_file += " -DARK2D_DEBUG -DDEBUG -DNDK_DEBUG -O0 ";
			else:
				android_make_file += " -O3 "; #-fno-strict-aliasing -mfpu=vfp -mfloat-abi=softfp ";
			android_make_file += nl+nl;

			android_make_file += "LOCAL_DEFAULT_CPP_EXTENSION := cpp" + nl+nl;
			android_make_file += "LOCAL_SRC_FILES := \\" + nl;
			for h in self.src_files: #foreach file on config...
				android_make_file += "	" + h + " \\" + nl;
			android_make_file += nl;
			#android_make_file += "LOCAL_LDLIBS := -lGLESv1_CM -ldl -llog -lz -lfreetype -lopenal -lzip" + nl+nl;
			#android_make_file += "LOCAL_LDLIBS := -lGLESv2 -lGLESv1_CM -ldl -llog -lz -lfreetype -lopenal -lzip" + nl+nl;
			android_make_file += "LOCAL_LDLIBS := -lGLESv2 -lEGL -ldl -llog -landroid -lz -lfreetype -lopenal -lzip -langelscript " + nl+nl; # -lfreetype
			#android_make_file += "LOCAL_SHARED_LIBRARIES :=   " + nl+nl;


			android_make_file += "include $(BUILD_SHARED_LIBRARY)" + nl;
			f = open(appbuildscript, "w");
			f.write(android_make_file);
			f.close();

			#make application.mk
			print("Creating Application.mk");
			application_make_file = "";
			application_make_file += "NDK_TOOLCHAIN_VERSION := 4.9" + nl;
			application_make_file += "APP_PROJECT_PATH := " + ndkprojectpath + nl;
			application_make_file += "APP_BUILD_SCRIPT := " + appbuildscript + nl;
			application_make_file += "NDK_APP_OUT=" + appbuilddir + nl;
			application_make_file += "NDK_PROJECT_PATH=" + ndkprojectpath + nl;


			# nexus7 fixes?!
			#application_make_file += "APP_ABI := all" + nl;
			if (self.debug):
				application_make_file += "APP_ABI := armeabi-v7a " + nl; #x86" + nl;
			else:
				application_make_file += "APP_ABI := x86 armeabi armeabi-v7a ";
				#if (ndkappplatformno >= )
				#application_make_file += "x86 ";
				application_make_file += nl; #x86" + nl;

			application_make_file += "APP_CPPFLAGS += -std=c++11 -frtti " + nl;
			application_make_file += "APP_STL := gnustl_shared" + nl;
			#application_make_file += "APP_STL := c++_shared" + nl;
			application_make_file += "LOCAL_C_INCLUDES += " + self.android_ndkdir + "/sources/cxx-stl/gnu-libstdc++/4.9/include" + nl;

			f = open(appbuildscript3, "w");
			f.write(application_make_file);
			f.close();

			buildline = ndkdir + self.ds + "ndk-build";
			buildline += " NDK_PROJECT_PATH=" + ndkprojectpath;
			buildline += " NDK_APP_OUT=" + appbuilddir;
			buildline += " APP_PROJECT_PATH=" + ndkprojectpath;
			buildline += " APP_BUILD_SCRIPT=" + appbuildscript;
			buildline += " APP_PLATFORM=" + ndkappplatform;
			#buildline += " NDK_LOG=1";
			print("Building library");
			print(buildline);
			subprocess.call([buildline], shell=True);

			print("Moving output to build folder");
			libsdir = ndkprojectpath + self.ds + "libs";
			#libsdir2 = ndkprojectpath + self.ds + "libs";
			#subprocess.call(["cp -r " + libsdir + " " + appbuilddir + self.ds ], shell=True);
			print("libsdir: " + libsdir);
			self.mycopytree( libsdir, appbuilddir + self.ds + "libs");

			print("removing temp folders");
			self.rmdir_recursive(libsdir);
			self.rmdir_recursive(jnifolder);

			print("done!");

		else:
			pass;



	def mycopytree(self, src, dst, symlinks=False, ignore=None):
		if not os.path.exists(dst):
			os.makedirs(dst)

		for itemm in os.listdir(src):
			s = os.path.join(src, itemm)
			d = os.path.join(dst, itemm)
			if os.path.isdir(s):
				self.mycopytree(s, d, symlinks, ignore)
			else:
				if not os.path.exists(d) or os.stat(src).st_mtime - os.stat(dst).st_mtime > 1:
					shutil.copy2(s, d)


	def fixLocalPath(self, str):
		if (self.platform == "windows" or self.platform == "windows-phone" or self.platform == "windows-store"):
			str = util.str_replace(str, [("/", "\\")]);
			if (not str.startswith("C:\\") and not str.startswith("D:\\")):
				str = self.game_dir + self.ds + str;
		elif (self.platform == "osx" or self.platform == "linux"):
			if (not str.startswith("/") and not str.startswith("../")):
				str = self.game_dir + self.ds + str;
		return str;


	def start(self):

		if (self.platform == "android" or self.platform == "ouya" or self.platform == "firetv"):
			self.startAndroid();
		elif (self.platform == "ios"):
			platform = IOSBuild(self);
			platform.start();
		elif (self.platform == "windows-old"):
			self.startWindows();
		elif (self.platform == "windows"):
			self.startWindowsVS2();
		elif (self.platform == "windows-store"):
			self.startWindowsStore();
		elif (self.platform == "windows-phone"):
			self.startWindowsPhone();
		elif (self.platform == "xbone"):
			self.startXboxOne();
		#elif(self.platform == "osx"):
		#	self.startMac();
		elif(self.platform == "ubuntu-linux" or self.platform == "linux"):
			self.startUbuntuLinux();
		elif(self.platform == "osx"):
			platform = MacBuild(self);
			platform.start();
		elif(self.platform == "flascc"):
			self.startFlascc();
		elif(self.platform == "html5"):
			self.startHTML5();
		else:
			print(self.platform);
			print("platform " + self.platform + " is not supported yet");


	pass;
