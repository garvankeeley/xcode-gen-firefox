# xcode-gen-firefox
Generate an Xcode project for firefox editing. This won't fully compile, but is useful for code completion and project navigation. It is also useful for debugging through Xcode.

clone with `git clone --recursive` to get the required submodule

Run after a mach build, like this:
./generate-proj.py <path to source> <path to object dir>

In my case, it looks like this:
./generate-proj.py ../mozilla-central ../obj-ff-dbg

