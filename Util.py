import os
import errno
import hashlib;
import sys
import linecache
import struct
import imghdr

class Util:
	def __init__(self):
		pass;

	def str_replace(self, str, edits):
		for search, replace in edits:
			str = str.replace(search, replace);
		return str;

	def underscoresToCamelCase(self, str):
		bits = str.split("_")
		str = "";
		bitIndex = 0;
		for bit in bits:
			if bitIndex > 0:
				bit = bit.capitalize();
			str += bit;
			bitIndex += 1;
		return str;

	def printException(self):
		exc_type, exc_obj, tb = sys.exc_info()
		f = tb.tb_frame
		lineno = tb.tb_lineno
		filename = f.f_code.co_filename
		linecache.checkcache(filename)
		line = linecache.getline(filename, lineno, f.f_globals)
		print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)


	def makeDirectories(self, dir):
		for thisstr in dir:
			#print("mkdir " + thisstr);
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

	def get_str_filename_no_ext(self, str):
		filename = self.get_str_filename(str);
		dotindex = filename.rfind(".");
		filename2 = filename[0:dotindex];
		return filename2;

	def strip_folder(self, str, folder):
		index = str.find(folder);
		return str[index:len(str)];

	def strip_extension(self, str):
		findex = str.rfind('.');
		return str[0:findex];

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

	def get_image_size(self, fname):
		'''Determine the image type of fhandle and return its size.
		from draco'''
		with open(fname, 'rb') as fhandle:
			head = fhandle.read(24)
			if len(head) != 24:
				return
			if imghdr.what(fname) == 'png':
				check = struct.unpack('>i', head[4:8])[0]
				if check != 0x0d0a1a0a:
					return
				width, height = struct.unpack('>ii', head[16:24])
			elif imghdr.what(fname) == 'gif':
				width, height = struct.unpack('<HH', head[6:10])
			elif imghdr.what(fname) == 'jpeg':
				try:
					fhandle.seek(0) # Read 0xff next
					size = 2
					ftype = 0
					while not 0xc0 <= ftype <= 0xcf:
						fhandle.seek(size, 1)
						byte = fhandle.read(1)
						while ord(byte) == 0xff:
							byte = fhandle.read(1)
						ftype = ord(byte)
						size = struct.unpack('>H', fhandle.read(2))[0] - 2
					# We are at a SOFn block
					fhandle.seek(1, 1)  # Skip `precision' byte.
					height, width = struct.unpack('>HH', fhandle.read(4))
				except Exception: #IGNORE:W0703
					return
			else:
				return
			return width, height

	def copyfilewithreplacements(self, fro, to, replacements):
		print("copyfilewithreplacements...");
		f1 = open(fro, "r");
		contents = f1.read();
		f1.close();

		contents = self.str_replace(contents, replacements);
		f1 = open(to, "w");
		f1.write(contents);
		f1.close();
		return;

	def copyfileifdifferent(self, source, dest):
		f1 = open(source, "r");
		new_contents = f1.read(); f1.close();
		new_hash = hashlib.md5(new_contents).hexdigest();

		try:
			f2 = open(dest, "r");
			existing_contents = f2.read(); f2.close();
			existing_hash = hashlib.md5(existing_contents).hexdigest();
		except:
			existing_hash = "";
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

			if os.path.isdir(full_name):
				thisAppendStr = appendStr + name + ds;
				if ("../" in dir):
					thisAppendStr = appendStr;

				#print('dir ' + thisAppendStr);
				thelist.extend(self.listFiles(full_name, usefullname, thisAppendStr));
			else:
				#print(full_name);
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

	def makeRelativePath(self, fr, to):
		# we need the relative path stupidly. :/
		# count number of forward slashes in project path and in ark2d path and then we have
		#  the difference number of ../s
		#ds = "/"
		#count_slashes_in_fr = fr.count(ds);
		#count_slashes_in_to = to.count(ds);
		return os.path.relpath(to, fr);
			#print(this_path);
			#self.android_config['ark_library_projects'].extend([this_path]);
			#this_library_project = "../../../";
			#for each_slash in range(count_slashes_in_project - count_slashes_in_ark2d)
			#	this_library_project += "../";


