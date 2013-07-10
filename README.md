pcl
===

Pipeline creation language compiler and run-time.

pcl is licensed using the [GNU Lesser General Public License Version 3](http://www.gnu.org/licenses/lgpl.txt).

This project was developed as part of the [MosesCore FP7 Project](http://www.statmt.org/mosescore/).

Dependencies
------------

The PCL compiler depends on [PLY](http://www.dabeaz.com/ply/) v3.4 which is a lexing and parsing library. You can install this either by downloading the [PLY-3.4](http://www.dabeaz.com/ply/ply-3.4.tar.gz) tarball and follow the instructions. Or, run `sudo easy_install ply`.

The PCL compiler and runtime relies on the Pypeline submodule found in the `libs` directory. Initialise the submodule with `git submodule update --init` and either:
   * Set your `PYTHONPATH` environment variable to `<clone root dir>/pcl/libs/pypeline/src`, or
   * Install Pypeline using the instructions in the submodule.
