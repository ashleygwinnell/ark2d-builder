import os
import errno

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

	def get_str_extension(self, str):
		findex = str.rfind('.');
		h_ext = str[findex+1:len(str)];
		return h_ext;

	def get_str_filename(self, str):
		findex = str.rfind(self.ds);
		filename = str[findex+1:len(str)];
		return filename;

	def get_str_filename2(self, str):
		findex = str.rfind("/");
		filename = str[findex+1:len(str)];
		return filename;

	def is_image_extension(self, ext):
		if (ext == "png" or ext == "tga" or ext == "bmp" or ext == "gif" or ext == "jpg" or ext == "pkm_png"):
			return True;
		return False;

	def is_audio_extension(self, ext):
		if (ext == "ogg" or ext == "mp3" or ext == "wav"):
			return True;
		return False;
