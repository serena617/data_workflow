from setuptools import setup
import workflow
import subprocess

SETUP_ARGS = dict(
    name="workflow",
    version=workflow.__version__,
    description="SNS data workflow manager",
    author='NScD Oak Ridge National Laboratory',
    author_email='ndav@email.ornl.gov',
    url="http://neutrons.github.com/",
    license='GNU LGPL',
    long_description=open('README.md').read(),
    platforms=['POSIX'],
    options={'clean': {'all': 1}},
    zip_safe = False,
    entry_points = {'console_scripts':["workflowmgr = workflow.sns_post_processing:run",]},
    packages=["workflow", "workflow.database", "workflow.database.report"],
        classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Networking',
        ],

)

if __name__ == '__main__':
    # Get the git commit information so we can store the exact version
    try:
        git_version = subprocess.check_output(["git", "describe", "--abbrev=100"]).replace('\n','')
    except:
        # Could not get git commit information, just install using 
        # the main version number
        git_version = workflow.__version__
        
    fd = open("workflow/git_version.py", 'w')
    fd.write("# Git revision information\n")
    fd.write("__git_version__ = \"%s\"\n" % git_version)
    fd.close()

    setup(**SETUP_ARGS)
