#!/usr/local/bin/python
import sys
import fnmatch
import os
import re
import shutil
from collections import defaultdict

try:
    from mod_pbxproj.mod_pbxproj import XcodeProject
except:
    print "Module missing. Incomplete git clone! Run `git submodule update --init --recursive`"
    sys.exit(1)

path_to_src = ''
path_to_objdir = ''
sources = dict()
unified_sources = dict()
defines = set()
other_flags = set()
includes = set()

def path_join(base, *others):
    items = [x if x[0] != '/' else x[1:] for x in others if x]
    return os.path.join(base, *tuple(items))

def find(rootdir, file):
    matches = {}
    for root, dirs, filenames in os.walk(rootdir):
        dirs[:] = [d for d in dirs if not d[0] == '.' \
                   if not d[0]== '_' \
                   if not 'win32' in d \
                   if not 'libopus' in d \
                   if not 'sctp' in d \
                   if not 'libvpx' in d]
        for filename in filenames:
            if filename == file:
                matches[root.replace(rootdir, '')] = filename
    return matches

def add_src_dir(s, sources):
    if '/' in s:
        items = s.split('/')
        curr = sources
        for i in items:
            if i.__len__() < 1:
                continue
            if not i in curr:
                curr[i] = dict()
            curr = curr[i]
        return curr
    else:
        if not s in sources:
            sources[s] = dict()
            return sources[s]

if __name__ == "__main__":
    if sys.argv.__len__() != 3:
        print('Args: <path to firefox source> <path to objdir> ')
        sys.exit(1)

    try:
        os.mkdir('firefox.xcodeproj')
    except:
        pass
    shutil.copy('stub_project.pbxproj', 'firefox.xcodeproj/project.pbxproj')

    path_to_src = os.path.abspath(sys.argv[1])
    path_to_objdir = os.path.abspath(sys.argv[2])

    mozbuilds = find(path_to_src, 'moz.build')
    backends = find(path_to_objdir, 'backend.mk')
    backends.update({'/nsprpub/config': 'autoconf.mk',
                     '/config' : ('autoconf.mk','autoconf-js.mk')})

    sys.path.append('/tmp')

    def extract_headers(s):
        return set(re.findall(r" '?(\S+\.h)\b", s))

    for key,value in mozbuilds.iteritems():
        int = open('/tmp/xcode_gen.py', 'w')
        int.write("from collections import defaultdict\n")
        int.write("CONFIG = defaultdict(lambda: '')\n")
        int.write("CONFIG['MOZ_WIDGET_TOOLKIT'] = 'cocoa'\n")
        int.write("CONFIG['OS_TARGET'] = 'Darwin'\n")
        int.write("CONFIG['OS_ARCH'] = 'Darwin'\n")
        int.write("CONFIG['NECKO_COOKIES'] = 1\n")
        int.write("SOURCES=[]\nUNIFIED_SOURCES=[]\n")
        int.write("DEFINES= defaultdict(lambda:None)\n")
        file_size = int.tell()
        infile = path_join(path_to_src, key, value)
        found = 0
        with open(infile) as f:
            content = f.readlines();
            found_uni = False
            last_line_written = -1
            for i in range(content.__len__()):
                if '.h' in content[i]:
                    src_dict = add_src_dir(key, sources)
                    if not '' in src_dict:
                        src_dict[''] = set()
                    src_dict[''] |= extract_headers(content[i])

                if found_uni and content[i].strip() == ']':
                    int.write(content[i])
                    last_line_written = i
                    found_uni = False
                    continue

                if 'UNIFIED_SOURCES' in content[i]:
                    found_uni = True
                    if content[i][0] == ' ':
                        found_no_indent = False
                        for j in range(i - 1 , last_line_written, -1):
                            if content[j].__len__() > 3 and content[j][0] != ' ' and 'elif ' not in content[j] and 'else:' not in content[j]:
                                for k in range(j, i):
                                    content[k] = re.sub(r'( +)([A-Za-z.]+ \+?)(=.+)', r'\1foo\3', content[k])
                                    int.write(content[k])
                                    last_line_written = k
                                found_no_indent = True
                                break
                        if not found_no_indent:
                            for k in range(last_line_written + 1, i):
                                content[k] = re.sub(r'( +)([A-Za-z.]+ \+?)(=.+)', r'\1foo\3', content[k])
                                int.write(content[k])
                                last_line_written = k
                if found_uni:
                    int.write(content[i])
                    last_line_written = i
                    if content[i].strip().endswith(']'):
                        found_uni = False

        has_data = int.tell() - file_size > 1
        int.close()

        if not has_data :
            continue

        try:
            xcode_gen
            os.remove('/tmp/xcode_gen.pyc')
            reload(xcode_gen)
        except NameError:
            pass

        import xcode_gen
        
        unified = set([path_join(key, x) for x in xcode_gen.UNIFIED_SOURCES])
        hfiles = []
        cfiles = []
        for cfile in unified:
            hfile = cfile.rsplit('.',1)[0] + '.h'
            if os.path.isfile(path_join(path_to_src, hfile)):
                            hfiles.append(hfile.rsplit('/')[-1])
            cfiles.append(cfile.rsplit('/')[-1])
        unified = set(hfiles) | set(cfiles)
        
        unified_src_dict = add_src_dir(key, unified_sources)
        if not '' in unified_src_dict:
            unified_src_dict[''] = set()
        unified_src_dict[''] |= unified

    def extract_defines(s):
        defs = re.findall(r'-D(\S+)', s)
        defs = [x for x in defs if not re.search('\/|XPCOM_GLUE|CC=|CXX=|CFLAGS|target=', x)]
        return set(defs)

    def extract_include(s):
        incs = re.findall(r'-I(\S+)', s)
        incs = [x for x in incs if '//' not in x]
        return set(incs)

    def process_backend(key, value):
        global defines, includes
        infile = path_join(path_to_objdir, key, value)
        with open(infile) as f:
            for line in f:
                m = re.search(r'[A-Z]+SRCS .?= (.+)(\.cpp|\.mm|\.cc\.c|\.m)', line)
                if ('Unified_' not in line and '.mn' not in line and
                    '.manifest' not in line and ":" not in line and m):
                    src_dict = add_src_dir(key, sources)
                    if not '' in src_dict:
                        src_dict[''] = set()
                    src_dict[''].add(''.join(m.group(1,2)))
                if 'DEFINE' in line:
                    defines |= extract_defines(line)
                if 'INCLUDES +=' in line or '_CFLAGS +=' in line or '_CXXFLAGS +=' in line:
                    defines |= extract_defines(line)
                    line = line.replace('$(topsrcdir)', path_to_src)
                    line = line.replace('$(srcdir)', path_to_src + key)
                    line = line.replace('$(LIBXUL_DIST)', path_join(path_to_objdir, 'dist'))
                    includes |= extract_include(line)

    for key,value in backends.iteritems():
        if isinstance(value, tuple):
            for i in value:
                try:
                    process_backend(key, i)
                except:
                    pass
        else:
            try:
                process_backend(key, value)
            except:
                pass
    
    # missing stuff
    includes.update([path_join(path_to_objdir, 'ipc/ipdl/_ipdlheaders'),
                     path_join(path_to_objdir, 'dist/include'),
                     path_join(path_to_objdir, 'js/src/ctypes/libffi/include'),
                     path_join(path_to_objdir, 'dist/include/mozilla'),
                     path_join(path_to_objdir, 'memory/jemalloc/src/include'),
                     path_join(path_to_objdir, 'dist/include/nss'),
                     path_join(path_to_objdir, 'dist/include/nspr')])
    #defines.update(['ACCESSIBILITY', 'MOZILLA_INTERNAL_API', 'XP_MACOSX', 'MOZ_WIDGET_COCOA', 'MOZ_XUL=1'])
    #-DMOZILLA_CLIENT -DMOZ_MEDIA_NAVIGATOR -DAB_CD=en-US -DNO_NSPR_10_SUPPORT

    project = XcodeProject.Load('firefox.xcodeproj/project.pbxproj')

    def create(d, parent=None, parent_path=None):
        it = iter(sorted(d.iteritems()))
        for k,v in it:
            #print "key:" + k + " value:" + str(v)
            if isinstance(v, dict):
                srcpath = ''
                if not parent:
                    srcpath = path_join(path_to_src, k)
                else:
                    srcpath = path_join(parent_path, k)
                group = project.get_or_create_group(k, path=srcpath, parent=parent)
                create(v, group, srcpath)
            else:
                for src in sorted(v):
                    project.add_file(path_join(parent_path, src), parent=parent)

    create(sources)
    create(unified_sources)
    
    #project.backup()
    project.save()

    prev = None
    defines_sorted = []
    for item in sorted(defines):
        item = item.replace('\\', '')
        if item.count("'")%2 != 0 or item.count('"')%2 != 0:
            continue

        loc = item.find('=')
        if loc > -1:
            key = item[0:loc]
        else:
            key = item
        if not prev or (prev and prev != key):
            defines_sorted.append(item)
        prev = key

    shutil.copyfile('stub_xcconfig','config.xcconfig')
    f = open('config.xcconfig', 'a')
    f.write("GCC_PREFIX_HEADER = " + path_join(path_to_src, 'memory/mozalloc/mozalloc.h'))
    f.write("\nGCC_PREPROCESSOR_DEFINITIONS = " + ' '.join(defines_sorted))
    f.write("\nHEADER_SEARCH_PATHS = " + ' '.join(includes))
    f.close()

