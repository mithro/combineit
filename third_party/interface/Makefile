
all:
	mkdir dist || true
	cat ./source/iutil.js ./source/fisheye.js > ./dist/interface.js
	java -jar ../jquery/build/google-compiler-20100917.jar --js ./dist/interface.js --warning_level QUIET --js_output_file ./dist/interface.min.js
