
all: third_party

third_party: jquery-mobile jquery

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
		mkdir dist; \
		mv -vf jquery.mobile-*.min.js dist/jquery-mobile.min.js; \
		mv -vf jquery.mobile-*.min.css dist/jquery-mobile.min.css; \
		mv -vf jquery.mobile-*.js dist/jquery-mobile.js; \
		mv -vf jquery.mobile-*.css dist/jquery-mobile.css; \
		cp -rvf themes/default/images dist/images; \
		git reset --hard; \
		echo "jquery-mobile done!"

clean:
	find -name \*.pyc -delete
	git clean -f -d

deploy:
	../google_appengine/appcfg.py update -v .

.PHONY: all jquery jquery-mobile deploy
