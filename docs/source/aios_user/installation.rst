.. _aios_installation:

Installation
============
Prerequsites
------------
* Anaconda
* Python: 3.9-3.11
* Git

.. _build_from_source:

Build from source
-----------------
Git clone AIOS repository

.. code-block:: console

    $ conda create -n aios python=3.x # from 3.9 to 3.11
    $ git clone https://github.com/agiresearch/AIOS.git
    $ conda activate aios
    $ cd AIOS

Install from requirements-cuda.txt if you have cuda environment,

.. code-block:: console

    $ pip install -r requirements-cuda.txt

or else you can install from requirements.txt

.. code-block:: console

    $ pip install -r requirements.txt


Build in Docker
---------------
We also provide the installation in docker. Here we just give some command examples to help you get started.
For more details about how to use docker, you can refer to https://docker-curriculum.com/.

Make sure you are in the folder that contains the Dockerfile and then run

.. code-block:: console

    $ sudo docker build -t aios . # docker by default requires sudo permission

And then start the docker based on your environment.

.. code-block:: console

    $ sudo docker run --gpus all -it --name aios aios # use when gpus are available
    $ sudo docker run -it --name aios aios # use when gpus are not available

Then you will have access to the environment built by docker and run AIOS.

If you have exited the AIOS docker and re-enter it and run next time. You can use the following commands

.. code-block:: console

    $ sudo docker start aios # First, start aios container
    $ sudo docker attach aios # Then, attach to the container
