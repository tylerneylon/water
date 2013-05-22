# modules

Modules are add-ons to water that increase or improve functionality.
I'd like the core of water to be very small and minimalistic, but
enough to support basic use and self-expansion of use cases, meaning
that it includes a simple package management system to install modules
like this.

Outside of running a file in a manner analogous to running a python
script, I'd like to give water a series of expandable commands that
it can run a bit like git commands (see below for syntax). There
will be some built-in commands, such as for package management,
and then some added commands based on modules.

Every subdirectory here is treated as a command that water can run.

In the future, I may consider more standalone additions that are run
independently, as opposed to being run as a command of water. But
those could go in another location, and this directory could still
be devoted to modules-invoked-as-water-commands.

# How to run a command

The current way to invoke a module is to run:

    water -module_name <args>

so that the simple and traditional invocation on a source file still works:

    water <filename> <args>

the distinction being the leading dash, where we expect no filename to
start with a dash. In the future I could use a syntax like this:

    water -- <filename> <args>

to allow arbitrary filenames.

# Directory structure / how water knows about and runs commands

Every directory name becomes the name of the module.
Nothing is imported by default - only when a command
is actually invoked by the user.

In that case, water imports a same-name file from that
directory:

    # The Python implementation of water imports this:
    <water_dir>/modules/<module_name>/<module_name>.py

and runs `<module_name>.main(args)` on that file.

In the future, this setup might change.

