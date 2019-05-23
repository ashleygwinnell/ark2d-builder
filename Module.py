from Util import *
util = Util();

class ModuleUtil:
	@staticmethod
	def addToIOSBuild(moduleObj, iosBuild):
		iosBuild.moduleLinkerFlags += " ".join(moduleObj.platforms.ios.linker_flags);


class ModulePlatformAndroid:
	def __init__(self):
		self.aars = [];

class ModulePlatformHTML5:
	def __init__(self):
		pass;

class ModulePlatformIOS:
	def __init__(self):
		self.framework_search_paths = [];

class ModulePlatform:
	def __init__(self, module):
		self.module = module;
		self.sources = [];
		self.sources_relative = True;
		self.framework_search_paths = [];
		self.header_search_paths = [];
		self.library_search_paths = [];
		self.linker_flags = [];
		self.preprocessor_definitions = [];
		self.libraries = [];
		self.libraries_simulator = [];
		pass;

	def initFromConfig(self, config):

		for source_file in config['sources']:
			source_file = util.str_replace(source_file, self.module.builder.tag_replacements);
			source_file = util.str_replace(source_file, [("%MODULE_DIR%", self.module.root)]);
			#util.fixFilePath(source_file);

			# relative path from build folder e.g. build/ios/ to that
			if (source_file[0:1] == "/" and self.sources_relative == True):
				print 'rel'
				source_file =  util.makeRelativePath(self.module.builder.build_folder + self.module.builder.ds + self.module.builder.output, source_file );

			self.sources.extend([source_file]);

		if "framework_search_paths" in config:
			for framework_path in config['framework_search_paths']:
				framework_path = util.str_replace(framework_path, self.module.builder.tag_replacements);
				framework_path = util.str_replace(framework_path, [("%MODULE_DIR%", self.module.root)]);
				self.framework_search_paths.extend([framework_path]);
				print framework_path;

		if "header_search_paths" in config:
			for header in config['header_search_paths']:
				header = util.str_replace(header, self.module.builder.tag_replacements);
				header = util.str_replace(header, [("%MODULE_DIR%", self.module.root)]);
				self.header_search_paths.extend([header]);
				print header;

		if "library_search_paths" in config:
			for lib in config['library_search_paths']:
				lib = util.str_replace(lib, self.module.builder.tag_replacements);
				lib = util.str_replace(lib, [("%MODULE_DIR%", self.module.root)]);
				self.library_search_paths.extend(["-L"+lib]);

		if "linker_flags" in config:
			for lib in config['linker_flags']:
				lib = util.str_replace(lib, self.module.builder.tag_replacements);
				lib = util.str_replace(lib, [("%MODULE_DIR%", self.module.root)]);
				self.linker_flags.extend([lib]);

		if "libraries" in config:
			for lib in config['libraries']:
				#print lib;
				if (isinstance(lib, basestring)):
					lib = util.str_replace(lib, self.module.builder.tag_replacements);
					lib = util.str_replace(lib, [("%MODULE_DIR%", self.module.root)]);
					self.libraries.extend([lib]);
				else:
					print("** LIB was a complex data object: " + str(lib) + " ");
					pass;

		if "preprocessor_definitions" in config:
			self.preprocessor_definitions = config['preprocessor_definitions'];

class ModulePlatforms:
	def __init__(self):
		self.ios = False;
		self.android = False;
		self.html5 = False;
		self.macos = False;
		pass;

	def __setitem__(self, key, item):
		self[key] = item;
		pass;

	def __getitem__(self, key):
		return self[key];


class Module:
	def __init__(self, builder, rootDirectory):
		self.name = "";
		self.root = rootDirectory;
		self.builder = builder;
		self.platforms = ModulePlatforms();


	def initFromConfig(self, config):
		self.name = config['name'];

		if ("ios" in config['platforms']):
			ios = ModulePlatform(self);
			ios.initFromConfig(config['platforms']['ios']);
			self.platforms.ios = ios;

		if ("android" in config['platforms']):
			android = ModulePlatform(self);
			android.initFromConfig(config['platforms']['android']);
			self.platforms.android = android;

		if ("html5" in config['platforms']):
			html5 = ModulePlatform(self);
			html5.sources_relative =False;
			html5.initFromConfig(config['platforms']['html5']);
			self.platforms.html5 = html5;

		if ("macos" in config['platforms']):
			macos = ModulePlatform(self);
			macos.initFromConfig(config['platforms']['macos']);
			self.platforms.macos = macos;

	def addToGypConfig(self, platformin, gypfiletarget, gypfiletargetcondition):

		try:
			platform = False;
			if (platformin == 'macos'):
				platform = self.platforms.macos;
			elif(platformin == 'ios'):
				platform = self.platforms.ios;
			elif(platformin == 'android'):
				platform = self.platforms.android;
			elif(platformin == 'html5'):
				platform = self.platforms.html5;

			gypfiletargetcondition['include_dirs'].extend( platform.header_search_paths );

			gypfiletarget['sources'].extend( platform.sources );

			gypfiletargetcondition['xcode_framework_dirs'].extend( platform.framework_search_paths );
			gypfiletargetcondition['xcode_settings']['FRAMEWORK_SEARCH_PATHS'].extend( platform.framework_search_paths );
			gypfiletarget['xcode_framework_dirs'].extend( platform.framework_search_paths );

			gypfiletargetcondition['ldflags'].extend( platform.library_search_paths );
			gypfiletargetcondition['ldflags'].extend( platform.linker_flags );

			gypfiletargetcondition['xcode_settings']['GCC_PREPROCESSOR_DEFINITIONS'] += " ".join(platform.preprocessor_definitions);
			gypfiletargetcondition['link_settings']['libraries'].extend( platform.libraries );
		except Exception as e:
			print ("ERROR");
			print(e);

