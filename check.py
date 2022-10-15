import sys
import re
from os import getenv
import requests
import yaml

def get_ids(baseurl):
	url = f'{baseurl}potiboard.php?mode=catalog'
	response = requests.get(url)
	pattern = re.compile(r'\s*<p>\[(\d+)\] \d{4}/\d{2}/\d{2}\(\w{3}\) \d{2}:\d{2}.+</p>')
	ids = []
	for line in response.text.splitlines():
		result = pattern.fullmatch(line)
		if result:
			ids.append(int(result.group(1)))
	return ids

def post_entry(mastodon_url, access_token, status, visibility='unlisted'):
	url = f'{mastodon_url}api/v1/statuses'
	headers = {'Authorization': f'Bearer {access_token}'}
	payload = {'status': status, 'visibility': visibility}
	r = requests.post(url, data=payload, headers=headers)
	return r.status_code == 200

if __name__ == '__main__':
	config_filename = 'config.yml'
	with open(config_filename, encoding='utf-8') as file:
		config = yaml.safe_load(file)
	ids = get_ids(config['potiboard_url'])
	new_id = -1
	for id in ids:
		if id == config['last_id']:
			break
		new_id = id
	if new_id > config['last_id']:
		access_token = getenv('MASTODON_ACCESS_TOKEN')
		entry_url = f'{config["potiboard_url"]}potiboard.php?res={new_id}'
		status = f'{config["message"]}\n{entry_url}'
		if post_entry(config['mastodon_url'], access_token, status):
			config['last_id'] = new_id
			with open(config_filename, 'w', encoding='utf-8') as file:
				yaml.dump(config, file, default_flow_style=False, allow_unicode=True)
			print('Info: Found new entry.')
			sys.exit(0)
		else:
			print('Error: Failed post to Mastodon.')
			sys.exit(1)
	else:
		print('Info: No new entry.')
		sys.exit(0)
