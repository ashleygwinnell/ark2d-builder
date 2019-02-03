from Util import *
util = Util();

class ModulePlatform:
	def __init__(self, module):
		self.module = module;
		self.framework_search_paths = [];
		self.header_search_paths = [];
		self.library_search_paths = [];
		self.preprocessor_definitions = [];
		self.libraries = [];
		pass;

	def initFromConfig(self, config):
		self.framework_search_paths = config['framework_search_paths'];
		self.header_search_paths = config['header_search_paths'];

		for lib in config['library_search_paths']:
			lib = util.str_replace(lib, self.module.builder.tag_replacements);
			lib = util.str_replace(lib, [("%MODULE_DIR%", self.module.root)]);
			self.library_search_paths.extend(["-L"+lib]);

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



