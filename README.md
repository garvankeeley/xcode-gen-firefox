# xcode-gen-firefox
Generate an Xcode project for firefox editing. This won't fully compile, but is useful for code completion and project navigation. It is also useful for debugging through Xcode.

clone with `git clone --recursive` to get the required submodule

Run after a mach build, like this:
./generate-proj.py <path to source> <path to object dir>

In my case, it looks like this:
./generate-proj.py ../mozilla-central ../obj-ff-dbg

Open the xcode project, build (about 20 files will fail), let the indexing complete, 
and you should have functional code completion, predictive errors/warnings as you code, 
and good navigation.

It is fundamentally flawed in that it doesn't distinguish between libxul and users of libxul, 
so most of the files that don't build (i.e. in browser/) are due to that. 
