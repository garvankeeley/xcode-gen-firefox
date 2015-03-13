# xcode-gen-firefox

Don't use this :). Use this instead:
https://bugzilla.mozilla.org/show_bug.cgi?id=1063329

Generate an Xcode project for firefox editing. This won't fully compile, but is useful for code completion and project navigation. It is also useful for debugging through Xcode.

clone with `git clone --recursive` to get the required submodule

Run after a mach build, like this:
./generate-proj.py `path to source` `path to object dir`

In my case, it looks like this:
./generate-proj.py ../mozilla-central ../obj-ff-dbg

Open the xcode project, build (about 10% or files will fail to compile), let the indexing complete, 
and you should have functional code completion, predictive errors/warnings as you code, 
and good navigation.

Although functional, it is a fundamentally flawed hack as it ignores most of the build backend logic. 
Xcode project generation should be part of the Firefox build system to be done properly.
