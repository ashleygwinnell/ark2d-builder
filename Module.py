from Util import *
util = Util();

class ModulePlatformAndroid:
	def __init__(self):
		self.aars = [];

class ModulePlatformIOS:
	def __init__(self):
		self.framework_search_paths = [];

class ModulePlatform:
	def __init__(self, module):
		self.module = module;
		self.sources = [];
		self.framework_search_paths = [];
		self.header_search_paths = [];
		self.library_search_paths = [];
		self.linker_flags = [];
		self.preprocessor_definitions = [];
		self.libraries = [];
		pass;

	def initFromConfig(self, config):

		for source_file in config['sources']:
			source_file = util.str_replace(source_file, self.module.builder.tag_replacements);
			source_file = util.str_replace(source_file, [("%MODULE_DIR%", self.module.root)]);
			#util.fixFilePath(source_file);

			# relative path from build folder e.g. build/ios/ to that
			if (source_file[0:1] == "/"):
				source_file =  util.makeRelativePath(self.module.builder.build_folder + self.module.builder.ds + self.module.builder.output, source_file );

			self.sources.extend([source_file]);

		if "framework_search_paths" in config:
			for framework_path in config['framework_search_paths']:
				framework_path = util.str_replace(framework_path, self.module.builder.tag_replacements);
				framework_path = util.str_replace(framework_path, [("%MODULE_DIR%", self.module.root)]);
				self.framework_search_paths.extend([framework_path]);
				print framework_path;

		for header in config['header_search_paths']:
			header = util.str_replace(header, self.module.builder.tag_replacements);
			header = util.str_replace(header, [("%MODULE_DIR%", self.module.root)]);
			self.header_search_paths.extend([header]);
			print header;

		for lib in config['library_search_paths']:
			lib = util.str_replace(lib, self.module.builder.tag_replacements);
			lib = util.str_replace(lib, [("%MODULE_DIR%", self.module.root)]);
			self.library_search_paths.extend(["-L"+lib]);

		for lib in config['linker_flags']:
			lib = util.str_replace(lib, self.module.builder.tag_replacements);
			lib = util.str_replace(lib, [("%MODULE_DIR%", self.module.root)]);
			self.linker_flags.extend([lib]);

		for lib in config['libraries']:
			lib = util.str_replace(lib, self.module.builder.tag_replacements);
			lib = util.str_replace(lib, [("%MODULE_DIR%", self.module.root)]);
			self.libraries.extend([lib]);

		self.preprocessor_definitions = config['preprocessor_definitions'];

class ModulePlatforms:
	def __init__(self):
		self.ios = False;
		self.android = False;
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



