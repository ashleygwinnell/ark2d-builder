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

if __name__ == "__main__":

	try:

		print("---------------------");
		print("ARK2D Module includes");
		print("---------------------");
		print("Starting");

		f = open("../config.json");
		fcontents = f.read();
		f.close();
		ark_config = json.loads(fcontents);

		for module in ark_config['modules']:
			print(module);
			moduleheaders = [];
			m = ark_config['modules'][module];
			if "root" in m:
				root = m['root'];
				sources = m['sources'];
				for source in sources:
					newf = util.str_replace(source, [(root, "")]);
					newf = util.replace_str_extension(newf, 'h');
					if util.file_exists("../"+root+newf):
						moduleheaders.extend([newf]);

				#print moduleheaders;

				generatedfile =  "/* \n";
				generatedfile += " * ARK2D GENERATED FILE. DO NOT OVERWRITE. \n";
				generatedfile += " * Include all '" + module + "' module header files.\n";
				generatedfile += " */ \n";
				for moduleheader in moduleheaders:
					generatedfile += "#include \"" + moduleheader + "\"\n";

				#print (generatedfile);

				allincludesfile = "../" + root + "+.h";
				print(allincludesfile);

				f1 = open(allincludesfile, "w");
				f1.write(generatedfile);
				f1.close();




		input("Done.");
		exit(0);

	except Exception as exc:
		print(exc);
		exit(1);
	except SystemExit as exc:
		print(exc);
		exit(1);
	except:
		print "urg";
		exit(1);
