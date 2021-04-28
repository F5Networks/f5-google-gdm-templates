# Writers Guide to editing and generating Documentation

## TOC

- [Overview](#Overview)
- [Dependencies](#dependencies)
- [Setup](#Setup)
- [Workflow](#Workflow)
- [Errata](#Errata)

## Overview

The new system that will be used across all clouds to generate the documentation is being developed first in the GCP 
templates.  This is the instruction manual to working with the new documentation system. Feedback is encouraged.

## Dependencies

Docker.  

This is the only requirement.  We've packed all the unix goodness we
need for the generation of the documentations and templates in a docker image available on the internal docker repository.  Just follow the setup
instructions after you install docker and then you should be good to try out the workflow.  Good luck!

1. Install Docker [[Windows]](https://docs.docker.com/docker-for-windows/install/)[[Mac]](https://docs.docker.com/docker-for-mac/install/)

*note: after this is complete make sure to leave the docker app running on your computer.  It needs to be running for the rest of this to work.*

## Setup

You will only have to do these seven steps once to get the docker image.  Don't be frightened.

`docker pull quay.pdsea.f5net.com/kuebler/cloudsolutions:Docs`

Ok, I lied.  It was one step.

## Workflow

Now lets use the linux enviroment provided by the docker container you just downloaded to build the project.

Note: You may need to share your drive in docker first.

1. Use git to check out the google template project as normal.
2. Open a command prompt or PowerShell window (Windows) or terminal (Mac).
3. cd into the root directory of the project you just checked out from git
4. `docker run -it -v $(pwd):/git/google quay.pdsea.f5net.com/kuebler/cloudsolutions:Docs bash` - Note: Windows users may need to use ```{pwd}``` instead of ```(pwd)```
5. `cd /git/google`
6. `ls`

You should see the root of the project directory, as the docker container mounted it with the `-v` option of the above command.

1. `cd build`
2. `make`

That should create all the final artifacts in `target` by parsing and compiling the templates in `src`.  You can 
now inspect what was generated into the `target` directory and see what you 
need to edit.  Refer to the [OVERVIEW.md](OVERVIEW.md) for information on how the template/readmes are organized and 
how the jinja templates in `src` become compiled `.md` and `.json` files

Edit the files in `src`, `make`, inspect and repeat until the generated files in `target` are to your satisfaction.

1. `make publish` will place the generated files into the root of the project and you can then push them up into
gitswarm as you are used to doing from windows.
2. `exit`

 This last command will exit out of the docker session, which will automatically stop the container.

 ***Congratulations, you have just used our cloud solutions docker container to generate our READMEs!!!***

## Errata

[Docker Docs](https://docs.docker.com/)
