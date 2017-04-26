import os
import errno
import hashlib;
import sys

class Util:
	def __init__(self):
		pass;

	def str_replace(self, str, edits):
		for search, replace in edits:
			str = str.replace(search, replace);
		return str;

	def makeDirectories(self, dir):
		for thisstr in dir:
			print("mkdir " + thisstr);
			try:
				os.makedirs(thisstr);
			except OSError as exc:
				if exc.errno == errno.EEXIST:
					pass
				else: raise
		pass;

	def getDirectorySeparator(self):
		if sys.platform == "win32":
			return "\\";
		return "/";

	def get_str_extension(self, str):
		findex = str.rfind('.');
		h_ext = str[findex+1:len(str)];
		return h_ext;

	def get_str_filename(self, str):
		ds = self.getDirectorySeparator();
		findex = str.rfind(ds);
		filename = str[findex+1:len(str)];
		return filename;

	def get_str_filename2(self, str):
		findex = str.rfind("/");
		filename = str[findex+1:len(str)];
		return filename;

	def replace_str_extension(self, str, ext):
		findex = str.rfind('.');
		h_ext = str[findex+1:len(str)];
		newfh = str[0:findex] + "." + ext;
		return newfh;

	def file_exists(self, f):
		return (os.path.exists(f));

	def is_image_extension(self, ext):
		if (ext == "png" or ext == "tga" or ext == "bmp" or ext == "gif" or ext == "jpg" or ext == "pkm_png"):
			return True;
		return False;

	def is_audio_extension(self, ext):
		if (ext == "ogg" or ext == "mp3" or ext == "wav"):
			return True;
		return False;

	def copyfileifdifferent(self, source, dest):
		f1 = open(source, "r");
		new_contents = f1.read(); f1.close();
		new_hash = hashlib.md5(new_contents).hexdigest();

		try:
			f2 = open(dest, "r");
			existing_contents = f2.read(); f2.close();
			existing_hash = hashlib.md5(existing_contents).hexdigest();
		except:
			pass;

		if new_hash != existing_hash:
			print("Copy file if different...");
			f1 = open(dest, "w");
			f1.write(new_contents);
			f1.close();
		else:
			print("Skipping " + source + " file as hashes match.");

	def listFiles(self, dir, usefullname=True, appendStr = ""):
		ds = self.getDirectorySeparator();

		thelist = [];
		for name in os.listdir(dir):
			if (self.get_str_extension(name) == "DS_Store"):
				continue;

			full_name = os.path.join(dir, name);
			#print(full_name);

			if os.path.isdir(full_name):
				thelist.extend(self.listFiles(full_name, usefullname, appendStr + name + ds));
			else:
				if usefullname==True:
					thelist.extend([appendStr + full_name]);
				else:
					thelist.extend([appendStr + name]);
		return thelist;

	def listDirectories(self, dir, usefullname=True, appendStr = ""):
		ds = self.getDirectorySeparator();

		thelist = [];
		for name in os.listdir(dir):
			full_name = os.path.join(dir, name);

			#thelist.extend([full_name]);
			if os.path.isdir(full_name):
				if usefullname==True:
					thelist.extend([appendStr + full_name]);
				else:
					thelist.extend([appendStr + name]);

				#thelist.extend([full_name]);
				thelist.extend(self.listDirectories(full_name, usefullname, appendStr + name + ds));
			#else:
			#	os.remove(full_name);
		return thelist;


