import boto3
import json
import os
import sys

readme = """
	A Python script that can be used to upload a directory contents to a bucket in S3
	Used for managing simple S3-hosted websites.

	Usage:

		python upload.py

	This uploads all valid files (except those in the excluced directories specified in config)

		python upload.py index.html error.html css/main.css

	This only uploads the specified files
"""


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CFG_FILE = "upload_cfg.json"
# CFG file needs to look like so:
demo_cfg_file = """
	{
		"site_name": "<name of the S3 bucket (also domain name of your site",
		"region_name": "<region in which your S3 bucket exists",
		"aws_secret": "<your aws secret>",
		"aws_access_key_id": "<your aws key id>"
		"excluded_dirs": ["assets"]
	}
"""

# map file extensions to ContentTypes
CONTENT_TYPES = {
	'jpg': 'image/jpeg',
	'jpeg': 'image/jpeg',
	'css': 'text/css',
	'html': 'text/html',
	'png': 'image/png',
	'js': 'text/javascript',
	'ico': 'image/x-icon',
	'gif': 'image/gif',
	'svg': 'image/svg+xml',
	'txt': 'text/plain'
}


def get_uploadable_files(directory, excluded_dirs):
	files = []
	for f in os.listdir(directory):
		if f != sys.argv[0] and not f.startswith('.'):
			dir_file = os.path.join(directory.replace('.', ''), f)
			if os.path.isfile(dir_file):
				files.append(dir_file)
			if os.path.isdir(dir_file):
				if dir_file not in excluded_dirs:
					files = files + get_uploadable_files(dir_file, excluded_dirs)
	return files


def get_content_type(filepath):
	suffix = filepath.split('.')[-1]
	return CONTENT_TYPES.get(suffix, None)


def load_config():
	try:
		f = open(os.path.join(BASE_DIR, CFG_FILE), 'r')
	except IOError:
		print("Failed to load config file: %s" % CFG_FILE)
		sys.exit()
	try:
		cfg = json.loads(f.read())
	except ValueError:
		print("Could not parse config file: %s" % CFG_FILE)
		sys.exit()
	return cfg


if __name__ == "__main__":
	cfg = load_config()
	s3 = boto3.client('s3',
		aws_access_key_id=cfg['aws_access_key_id'],
		aws_secret_access_key=cfg['aws_secret'],
		region_name=cfg['region_name']
	)
	files = sys.argv[1:] if len(sys.argv) > 1 else []
	files = files or get_uploadable_files('.', cfg['excluded_dirs'])
	if files:
		print("Uploading files to: %s" % cfg['site_name'])
	for f in files:
		ct = get_content_type(f)
		if ct:
			print("Uploading file: %s" % f)
			try:
				s3.upload_file(os.path.join(BASE_DIR, f), cfg['site_name'], f,  ExtraArgs={'ACL':'public-read', 'ContentType': ct})
			except OSError:
				print("ERROR! Could not find file to upload: %s" % f)
		else:
			print("Not uploading unknown file type: %s" % f)
	print("Done!")