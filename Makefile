# Copyright (c) 2010 Google Inc. All rights reserved.
# Use of this source code is governed by a Apache-style license that can be
# found in the LICENSE file.

all: submodules third_party

submodules:
	git submodule init
	git submodule update

third_party: interface jquery jquery-mobile jquery-ui

interface:
	cd third_party/interface; \
		make; \
		echo "jquery interface done!"

jquery:
	# Disable stupid crlf mode
	echo "* -crlf" > third_party/jquery/.git/info/attributes
	
	# Build a better .gitignore
	cat third_party/jquery/.gitignore > third_party/jquery/.git/info/exclude
	echo "dist" >> third_party/jquery/.git/info/exclude
	
	cd third_party/jquery; \
		make; \
		git reset --hard; \
		echo "jquery done!"

jquery-mobile:
	# Build a better .gitignore
	cat third_party/jquery-mobile/.gitignore > third_party/jquery-mobile/.git/info/exclude
	echo "dist" >> third_party/jquery-mobile/.git/info/exclude
	
	cd third_party/jquery-mobile; \
		make; \
		rm -rf dist; \
		mkdir dist; \
		mv -vf jquery.mobile-*.min.js dist/jquery-mobile.min.js; \
		mv -vf jquery.mobile-*.min.css dist/jquery-mobile.min.css; \
		mv -vf jquery.mobile-*.js dist/jquery-mobile.js; \
		mv -vf jquery.mobile-*.css dist/jquery-mobile.css; \
		cp -rvf themes/default/images dist/images; \
		git reset --hard; \
		echo "jquery-mobile done!"

jquery-ui:
	# Build a better .gitignore
	cat third_party/jquery-ui/.gitignore > third_party/jquery-ui/.git/info/exclude
	echo "build/dist-custom" >> third_party/jquery-ui/.git/info/exclude
	
	cd third_party/jquery-ui/build; \
		ant; \
		rm -rf dist-custom; \
		git reset --hard; \
		mkdir dist-custom; \
		cp dist/*/ui/jquery-ui.js dist-custom/; \
		cp dist/*/ui/minified/jquery-ui.min.js dist-custom/; \
		cp dist/*/themes/base/jquery-ui.css dist-custom/; \
		cp dist/*/themes/base/minified/jquery-ui.min.css dist-custom/; \
		cp -r dist/*/themes/base/images dist-custom/; \
		echo "jquery-mobile done!"
		

clean:
	find -name \*.pyc -delete
	git clean -f -d

deploy:
	../google_appengine/appcfg.py update -v .

.PHONY: all jquery jquery-mobile deploy
